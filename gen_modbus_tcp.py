#!/usr/bin/env python3
# v 2.1 (20 July 2025) Major Modifications:
# - Implemented configuration-based approach with external YAML file
# - Added command-line argument to specify config file
# - Made the code more modular and reusable across different generators
# - Preserved all functionality from v1.1
# - Added infinite retry logic with exponential backoff
# - Version without emojis for systems with limited Unicode support
# - Enhanced console output and logging for both Docker and manual runs

import pymodbus
import random
import time
import sys
import os
import logging
import argparse
import yaml

from pymodbus.client.sync import ModbusTcpClient
from pymodbus.transaction import ModbusRtuFramer
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Global variables
FIELD_TYPES = {}

# Decision-Maker 3500 flags certain raw register values to indicate "unknown" data.
# These constants capture the documented ranges so we can discard bad readings before
# they appear as spikes (e.g., Apparent Power jumping to ~655%).
INVALID_REGISTER_FLAGS = {
    0xFFC0,  # Unsupported register flag
}

INVALID_REGISTER_FLAG_RANGES = (
    (0x7FE0, 0x7FFF),  # Signed INT unknown/invalid
    (0xFFE0, 0xFFFF),  # Unsigned INT unknown/invalid
)


def is_invalid_register_flag(raw_value: int) -> bool:
    """Return True when the 16-bit raw value matches a Decision-Maker invalid flag."""
    if raw_value in INVALID_REGISTER_FLAGS:
        return True

    for start, end in INVALID_REGISTER_FLAG_RANGES:
        if start <= raw_value <= end:
            return True

    return False

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Modbus Generator Monitor')
    parser.add_argument('--config', '-c', default='generator_config.yaml',
                        help='Path to the configuration file (default: generator_config.yaml)')
    return parser.parse_args()

def load_config(config_path):
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as config_file:
            return yaml.safe_load(config_file)
    except Exception as e:
        print(f"Error loading configuration from {config_path}: {e}")
        sys.exit(1)

def setup_logging(logging_config, max_size_bytes=10485760, backup_count=5):
    """Configure logging based on configuration with size limits"""
    # Get the root logger
    logger = logging.getLogger()
    
    # Clear any existing handlers
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)
    
    # Set the log level
    level = getattr(logging, logging_config.get('level', 'INFO'))
    logger.setLevel(level)
    
    # Determine log file path based on environment
    if os.path.exists('/app/logs'):
        # Docker environment - use shared logs directory
        log_dir = '/app/logs'
        os.makedirs(log_dir, exist_ok=True)
        log_filename = os.path.join(log_dir, 'modbus_poller.log')
    else:
        # Local development - use current directory
        log_filename = logging_config.get('filename', 'generator_output.log')
    
    # Create rotating file handler
    file_handler = RotatingFileHandler(
        filename=log_filename,
        maxBytes=max_size_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    
    # Create console handler for manual runs
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Set the format
    formatter = logging.Formatter(
        fmt=logging_config.get('format', '%(asctime)s [%(levelname)s] %(message)s'),
        datefmt=logging_config.get('datefmt', '%H:%M:%S')
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add both handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    print(f"[LOGGING] Log file: {log_filename}")

def setup_influxdb(influxdb_config):
    """Configure and return InfluxDB client"""
    try:
        client = InfluxDBClient(
            url=influxdb_config.get('url', 'http://localhost:8086'),
            token=influxdb_config.get('token', ''),
            org=influxdb_config.get('org', 'mlr')
        )
        return client, client.write_api(write_options=SYNCHRONOUS)
    except Exception as e:
        logging.error(f"Error setting up InfluxDB client: {e}")
        sys.exit(1)

def create_modbus_client(connection_config):
    """Create a Modbus RTU over TCP Client based on configuration"""
    return ModbusTcpClient(
        host=connection_config.get('host', '192.168.127.254'), 
        port=connection_config.get('port', 502), 
        framer=ModbusRtuFramer
    )

def check_connection_and_get_ecm_model(client, config):
    """
    Verify Modbus connection by reading the ECM Model register with retry
    
    Args:
        client (ModbusSerialClient): Modbus client instance
        config (dict): Configuration dictionary
    
    Returns:
        int or None: ECM Model number if connection successful, None otherwise
    """
    connection_config = config.get('connection', {})
    retries = connection_config.get('retries', 5)
    delay = connection_config.get('retry_delay', 0.1)
    unit_id = connection_config.get('unit_id', 1)
    
    # Get ECM Model register address
    ecm_model_address = config['registers']['ECM Model']['address'] - 1
    
    for attempt in range(retries):
        try:
            result = client.read_holding_registers(ecm_model_address, 1, unit=unit_id)
            
            if not result.isError():
                ecm_model = result.registers[0]
                logging.info(f"Successfully connected. ECM Model: {ecm_model}")
                return ecm_model
            else:
                logging.warning(f"Modbus error on ECM Model read (attempt {attempt + 1}): {result}")
        
        except Exception as e:
            logging.warning(f"Error checking ECM Model (attempt {attempt + 1}): {e}")
        
        time.sleep(delay)

    logging.error("Failed to read ECM Model after multiple attempts.")
    return None

def is_value_anomalous(name, value, thresholds):
    """
    Check if a value is anomalous based on its name and value
    
    Args:
        name (str): Register name
        value (float): Register value
        thresholds (dict): Threshold configuration dictionary
    
    Returns:
        bool: True if value is anomalous, False otherwise
    """
    # Check for obviously invalid values (common Modbus error indicators)
    if value in [32767, 32764, 32765, 32766, 3276.7, 3276.4, 3276.5, 3276.6]:
        return True
        
    # Determine threshold category based on register name and units
    threshold_category = 'default'
    
    if 'Temperature' in name:
        threshold_category = 'temperature'
    elif 'Pressure' in name:
        threshold_category = 'pressure'
    elif 'Angle' in name or 'Degrees' in name:
        threshold_category = 'degrees'
    elif 'Frequency' in name or 'Hz' in name:
        threshold_category = 'frequency'
    elif 'Voltage' in name:
        threshold_category = 'voltage'
    elif 'Current' in name:
        threshold_category = 'current'
    elif 'Power' in name or 'kW' in name:
        threshold_category = 'power'
    elif '% of' in name:
        threshold_category = 'percentage'
    elif 'Rate' in name or 'l/hr' in name:
        threshold_category = 'flow'
        
    threshold_values = thresholds.get(threshold_category, thresholds['default'])
    
    # Check if value is outside thresholds
    return value > threshold_values['max'] or value < threshold_values['min']

def read_engine_speed(client, config):
    """
    Special function to read engine speed to determine if generator is running
    
    Args:
        client (ModbusSerialClient): Modbus client instance
        config (dict): Configuration dictionary
        
    Returns:
        int: Engine speed in RPM, or 0 if error
    """
    connection_config = config.get('connection', {})
    unit_id = connection_config.get('unit_id', 1)
    speed_reg = config['registers']['Engine Speed']
    
    for attempt in range(5): #5 attempts to read
        try:
            result = client.read_holding_registers(
                address=speed_reg['address'] - 1,
                count=1,
                unit=unit_id
            )
            
            if not result.isError():
                speed = result.registers[0]
                return speed
        except Exception as e:
            logging.warning(f"Error reading engine speed (attempt {attempt + 1}): {e}")
        
        time.sleep(0.2)
    
    return 0  # Default to 0 if reading fails

def read_register(client, name, register_info, engine_running, config, influxdb_bucket, influxdb_org, write_api):
    """
    Read a single register with retry and scaling, applying correction for anomalous values.
    
    Args:
        client (ModbusSerialClient): Modbus client instance
        name (str): Register name
        register_info (dict): Register configuration
        engine_running (bool): Flag indicating if engine is running
        config (dict): Configuration dictionary
        
    Returns:
        str: Formatted register reading
    """
    connection_config = config.get('connection', {})
    unit_id = connection_config.get('unit_id', 1)
    thresholds = config.get('anomaly_thresholds', {})
    
    for attempt in range(5):  # Try up to 5 times
        try:
            result = client.read_holding_registers(
                address=register_info['address'] - 1,  # Modbus uses 0-based
                count=1,
                unit=unit_id
            )
            
            if not result.isError():
                raw_value = result.registers[0]

                if is_invalid_register_flag(raw_value):
                    # Controller explicitly marked this reading as invalid. Avoid writing the raw
                    # 65k-style flag so downstream consumers don’t display bogus spikes.
                    if any(term in name for term in ['Total', 'Hours', 'Starts', 'Runtime', 'Number of']):
                        logging.debug(f"Skipping {name} due to Decision-Maker invalid flag: {raw_value}")
                        return f"{name}: Invalid"

                    processed_value = 0
                    logging.info(f"Corrected invalid register flag for {name}: raw={raw_value}, set to 0")
                else:
                    processed_value = (raw_value / register_info.get('scale', 1)) if 'scale' in register_info else raw_value

                # If engine is not running or the value is anomalous, set non-cumulative values to 0
                # Keep cumulative values (runtime, starts, etc.) as they are
                if is_value_anomalous(name, processed_value, thresholds):
                    if not any(term in name for term in ['Total', 'Hours', 'Starts', 'Runtime', 'Number of']):
                        processed_value = 0
                        logging.info(f"Corrected anomalous value for {name}: raw={raw_value}, set to 0")
                
                write_to_influx(name, processed_value, register_info['units'], influxdb_bucket, influxdb_org, write_api)
                return f"{name}: {processed_value} {register_info['units']}"
            else:
                logging.warning(f"Modbus error reading {name}, attempt {attempt + 1}")

        except Exception as e:
            logging.warning(f"Exception reading {name}, attempt {attempt + 1}: {e}")
        
        time.sleep(0.2)  # small pause before retry
    
    return f"{name}: Error"

SEEN_EVENTS = {}
EVENT_EXPIRY_POLLS = 3  # How many polls before we consider an event "cleared"

def read_active_events(client, config, write_api, influxdb_bucket, influxdb_org):
    global SEEN_EVENTS
    events_cfg = config.get('events', {})
    ignore_codes = events_cfg.get('ignore_codes', [])
    base_address = events_cfg.get('base_address')
    max_events = events_cfg.get('max_events', 7)
    event_map = events_cfg.get('map', {})
    unit_id = config.get('connection', {}).get('unit_id', 1)

    try:
        result = client.read_holding_registers(address=base_address - 1, count=1, unit=unit_id)
        if result.isError():
            logging.warning("Failed to read number of active events")
            return []

        num_events = result.registers[0]
        event_msg = f"{num_events} active event(s) found"
        print(event_msg)
        logging.info(event_msg)

        current_seen_keys = set()
        events = []

        for i in range(min(num_events, max_events)):
            event_start = base_address + 1 + i * 4 - 1
            result = client.read_holding_registers(address=event_start, count=4, unit=unit_id)
            if result.isError():
                logging.warning(f"Failed to read event {i+1}")
                continue

            regs = result.registers
            level_fmi = regs[0]
            object_id = regs[1]
            event_id = regs[2]
            param_id = regs[3]

            level = (level_fmi >> 8) & 0xFF
            fmi = level_fmi & 0xFF
            key = f"{fmi}-{level}-{param_id}"

            description = event_map.get(key, f"Unknown Event: Level={level}, FMI={fmi}, Param={param_id}")
            event_msg = f"[EVENT {i+1}] {description}"
            print(event_msg)
            logging.info(event_msg)

            current_seen_keys.add(key)
            events.append({
                "event": i+1,
                "description": description,
                "level": level,
                "fmi": fmi,
                "param_id": param_id,
                "object_id": object_id,
                "event_id": event_id
            })

            # Update or insert into SEEN_EVENTS
            SEEN_EVENTS[key] = {
                "remaining": EVENT_EXPIRY_POLLS,
                "payload": {
                    "param_id": str(param_id),
                    "fmi": str(fmi),
                    "level": str(level),
                    "object_id": str(object_id),
                    "event_id": str(event_id),
                    "message": description
                }
            }

        # Decrease counters for missing events
        for key in list(SEEN_EVENTS.keys()):
            if key not in current_seen_keys:
                SEEN_EVENTS[key]["remaining"] -= 1
                if SEEN_EVENTS[key]["remaining"] <= 0:
                    del SEEN_EVENTS[key]
                    logging.info(f"Event cleared: {key}")

        # Write all active (non-expired) events
        for key, info in SEEN_EVENTS.items():
            if info["remaining"] > 0 and key not in ignore_codes:
                try:
                    payload = info["payload"]
                    point = Point("generator_events") \
                        .tag("param_id", payload["param_id"]) \
                        .tag("fmi", payload["fmi"]) \
                        .tag("level", payload["level"]) \
                        .tag("object_id", payload["object_id"]) \
                        .tag("event_id", payload["event_id"]) \
                        .field("message", payload["message"]) \
                        .time(datetime.utcnow())
                    write_api.write(bucket=influxdb_bucket, org=influxdb_org, record=point)
                except Exception as e:
                    logging.warning(f"Failed to write event heartbeat: {e}")

        return events

    except Exception as e:
        logging.error(f"Error reading events: {e}")
        return []


def write_to_influx(name, value, unit, bucket, org, write_api):
    """Write a data point to InfluxDB with consistent typing based on previous writes"""
    global FIELD_TYPES
    field_name = name.replace(" ", "_")
    point = Point("generator_metrics").tag("unit", unit)
    
    try:
        # Handle string values
        if isinstance(value, str):
            point = point.field(field_name, value)
            FIELD_TYPES[field_name] = 'string'
        else:
            # Check if we've seen this field before
            if field_name in FIELD_TYPES:
                # Use the previously used type
                if FIELD_TYPES[field_name] == 'int':
                    point = point.field(field_name, int(value))
                else:
                    point = point.field(field_name, float(value))
            else:
                # First time seeing this field, try to determine its natural type
                if value == int(value):  # If it's a whole number
                    point = point.field(field_name, int(value))
                    FIELD_TYPES[field_name] = 'int'
                else:
                    point = point.field(field_name, float(value))
                    FIELD_TYPES[field_name] = 'float'
        
        point = point.time(datetime.utcnow())
        write_api.write(bucket=bucket, org=org, record=point)
    
    except Exception as e:
        if "field type conflict" in str(e):
            # Extract type from error message
            if "already exists as type integer" in str(e):
                FIELD_TYPES[field_name] = 'int'
                # Retry with integer type
                try:
                    point = Point("generator_metrics").tag("unit", unit)
                    point = point.field(field_name, int(value))
                    point = point.time(datetime.utcnow())
                    write_api.write(bucket=bucket, org=org, record=point)
                    logging.info(f"Successfully wrote {field_name} as integer: {int(value)}")
                except Exception as retry_error:
                    logging.warning(f"Failed retry for {field_name}: {retry_error}")
            elif "already exists as type float" in str(e):
                FIELD_TYPES[field_name] = 'float'
                # Retry with float type
                try:
                    point = Point("generator_metrics").tag("unit", unit)
                    point = point.field(field_name, float(value))
                    point = point.time(datetime.utcnow())
                    write_api.write(bucket=bucket, org=org, record=point)
                    logging.info(f"Successfully wrote {field_name} as float: {float(value)}")
                except Exception as retry_error:
                    logging.warning(f"Failed retry for {field_name}: {retry_error}")
            else:
                logging.warning(f"Error writing to InfluxDB for {field_name}: {e}")
        else:
            logging.warning(f"Error writing to InfluxDB for {field_name}: {e}")

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def connect_with_retry(client, config, max_retries=None):
    """
    Attempt to connect to Modbus with retry logic and exponential backoff
    
    Args:
        client: Modbus client instance
        config: Configuration dictionary
        max_retries: Maximum number of retries (None for infinite)
    
    Returns:
        tuple: (connected, ecm_model) - connected is bool, ecm_model is int or None
    """
    connection_config = config.get('connection', {})
    host = connection_config.get('host', 'unknown')
    port = connection_config.get('port', 502)
    
    retry_count = 0
    base_delay = 5  # Start with 5 second delay
    max_delay = 60  # Maximum 60 second delay
    
    while max_retries is None or retry_count < max_retries:
        try:
            retry_count += 1
            
            msg = f"[CONNECT] Attempting to connect to Modbus gateway at {host}:{port} (attempt {retry_count})"
            logging.info(msg)
            print(msg)
            
            # Try to connect
            if client.connect():
                msg = f"[SUCCESS] Connected to Modbus gateway at {host}:{port}"
                logging.info(msg)
                print(msg)
                
                # Verify connection by reading ECM Model
                msg = "[VERIFY] Reading ECM Model to verify connection..."
                logging.info(msg)
                print(msg)
                
                ecm_model = check_connection_and_get_ecm_model(client, config)
                if ecm_model is not None:
                    msg = f"[VERIFIED] Connection verified! ECM Model: {ecm_model}"
                    logging.info(msg)
                    print(msg)
                    return True, ecm_model
                else:
                    msg = "[WARNING] Connected to gateway but failed to read ECM Model"
                    logging.warning(msg)
                    print(msg)
                    client.close()
            else:
                msg = f"[FAILED] Failed to connect to Modbus gateway at {host}:{port}"
                logging.warning(msg)
                print(msg)
        
        except Exception as e:
            msg = f"[ERROR] Connection error: {e}"
            logging.error(msg)
            print(msg)
            try:
                client.close()
            except:
                pass
        
        # Calculate delay with exponential backoff
        delay = min(base_delay * (2 ** min(retry_count - 1, 5)), max_delay)
        
        if max_retries is None or retry_count < max_retries:
            msg = f"[RETRY] Retrying in {delay} seconds..."
            logging.info(msg)
            print(msg)
            time.sleep(delay)
        
    msg = f"[FAILED] Failed to connect after {retry_count} attempts"
    logging.error(msg)
    print(msg)
    return False, None

def monitor_connection_health(client, config):
    """
    Check if the connection is still healthy by attempting a simple read
    
    Returns:
        bool: True if connection is healthy, False otherwise
    """
    try:
        # Try to read engine speed as a health check
        engine_speed = read_engine_speed(client, config)
        return True
    except Exception as e:
        msg = f"[HEALTH] Connection health check failed: {e}"
        logging.warning(msg)
        print(msg)
        return False

def main():
    """Main function to run Modbus generator data polling"""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Load configuration
    config = load_config(args.config)
    
    # Setup logging
    setup_logging(config['logging'], max_size_bytes=5*1024*1024, backup_count=3)
    
    msg = "[START] Starting Generator Monitoring System..."
    logging.info(msg)
    print(msg)
    
    # Setup InfluxDB
    influxdb_config = config.get('influxdb', {})
    influx_client, write_api = setup_influxdb(influxdb_config)
    
    # Create Modbus client
    client = create_modbus_client(config.get('connection', {}))
    
    connected = False
    ecm_model = None
    connection_failures = 0
    max_connection_failures = 5  # Reconnect after 5 consecutive failures
    
    try:
        while True:  # Main monitoring loop - runs forever
            
            # Connect or reconnect if needed
            if not connected:
                connected, ecm_model = connect_with_retry(client, config)
                if not connected:
                    msg = "[ERROR] Unable to establish connection. Retrying..."
                    logging.error(msg)
                    print(msg)
                    time.sleep(30)  # Wait 30 seconds before trying again
                    continue
                else:
                    connection_failures = 0  # Reset failure counter on successful connection
            
            try:
                # Continuous polling loop (only when connected)
                msg = "[POLL] Starting data polling..."
                logging.info(msg)
                print(msg)
                
                poll_count = 0
                while connected:
                    try:
                        # Periodic connection health check (every 10 polls)
                        if poll_count % 10 == 0:
                            if not monitor_connection_health(client, config):
                                msg = "[DISCONNECT] Connection lost during polling"
                                logging.warning(msg)
                                print(msg)
                                connected = False
                                connection_failures += 1
                                break
                        
                        clear_screen()  # Clear the terminal screen before updating
                        
                        # First, check if the engine is running by reading the engine speed
                        engine_speed = read_engine_speed(client, config)
                        engine_running = engine_speed > 0
                        status = "RUNNING" if engine_running else "STOPPED"
                        
                        # Print status header
                        header = f"\n[CONNECTED] Generator Status (ECM Model: {ecm_model})"
                        print(header)
                        logging.info(header.strip())
                        print("=" * 50)
                        status_msg = f"[STATUS] Generator: {status} | Poll #{poll_count + 1}"
                        print(status_msg)
                        logging.info(status_msg)
                        print("=" * 50)
                        
                        # Print active events
                        events = read_active_events(client, config, write_api, 
                                                  influxdb_config.get('bucket'), 
                                                  influxdb_config.get('org'))
                        events_msg = f"[EVENTS] Active Events: {len(events) if isinstance(events, list) else 0}"
                        print(events_msg)
                        logging.info(events_msg)
                        
                        # Poll and print all registers
                        registers = config.get('registers', {})
                        for name, register_info in registers.items():
                            if name != 'ECM Model' and name != 'Engine Speed':
                                result = read_register(client, name, register_info, engine_running, config, 
                                                    influxdb_config.get('bucket'), 
                                                    influxdb_config.get('org'),
                                                    write_api)
                                print(result)
                                logging.info(result)
                            elif name == 'Engine Speed':
                                # Use the already read engine speed value
                                speed_msg = f"Engine Speed: {engine_speed} RPM"
                                print(speed_msg)
                                logging.info(speed_msg)
                                write_to_influx('Engine Speed', engine_speed, 'RPM', 
                                               influxdb_config.get('bucket'), 
                                               influxdb_config.get('org'),
                                               write_api)
                        
                        poll_count += 1
                        wait_msg = f"\n[WAIT] Next poll in 2-3 seconds... (Failures: {connection_failures})"
                        print(wait_msg)
                        logging.info(wait_msg.strip())
                        
                        # Wait before next poll
                        time.sleep(2 + random.uniform(0.2, 0.8))
                        
                    except Exception as poll_error:
                        msg = f"[POLL ERROR] Polling error: {poll_error}"
                        logging.error(msg)
                        print(msg)
                        connection_failures += 1
                        
                        if connection_failures >= max_connection_failures:
                            msg = f"[RECONNECT] Too many failures ({connection_failures}), reconnecting..."
                            logging.warning(msg)
                            print(msg)
                            connected = False
                            client.close()
                            break
                        else:
                            time.sleep(5)  # Short pause before retrying
                            
            except Exception as e:
                msg = f"[SYSTEM ERROR] Unexpected error in polling loop: {e}"
                logging.error(msg)
                print(msg)
                connected = False
                connection_failures += 1
                time.sleep(10)
    
    except KeyboardInterrupt:
        msg = "[STOP] Polling stopped by user"
        logging.info(msg)
        print(msg)
    except Exception as e:
        msg = f"[FATAL] Fatal error: {e}"
        logging.error(msg)
        print(msg)
    finally:
        try:
            client.close()
            influx_client.close()
            msg = "[CLEANUP] Connections closed"
            logging.info(msg)
            print(msg)
        except:
            pass

if __name__ == "__main__":
    main()
