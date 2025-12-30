from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import pandas as pd
from influxdb_client import InfluxDBClient
import warnings
from influxdb_client.client.warnings import MissingPivotFunction
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse
from fastapi import Request
import numpy as np
from fastapi import Query
import json
import yaml
import requests
import time

warnings.simplefilter("ignore", MissingPivotFunction)

app = FastAPI()

# Allow your React app to talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your actual domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_config(config_file='generator_config.yaml'):
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

config = load_config()

# Load configuration from YAML
influxdb_config = config.get('influxdb', {})

# Use environment variables if available, fallback to config
INFLUXDB_URL = os.getenv('INFLUXDB_URL', influxdb_config.get('url', 'http://localhost:8086'))
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN', influxdb_config.get('token', ''))
INFLUXDB_ORG = os.getenv('INFLUXDB_ORG', influxdb_config.get('org', 'mlr'))
INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET', influxdb_config.get('bucket', 'stbd_gen'))

# Initialize clients
influx_client = InfluxDBClient(
    url=INFLUXDB_URL,
    token=INFLUXDB_TOKEN,
    org=INFLUXDB_ORG,
    timeout=60_000)

# Global storage for agent heartbeats
agent_heartbeats = {}

def sanitize_numeric(value, default=0):
    """Sanitize numeric values for JSON compliance, handling NaN and infinity"""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        if pd.isna(value) or value == float('inf') or value == float('-inf'):
            return default
    return value

def sanitize_string(value, default="unknown"):
    """Sanitize string values for JSON compliance, handling 'nan' strings"""
    if value is None:
        return default
    # Convert to string and check for 'nan' representation
    str_value = str(value).lower()
    if str_value in ['nan', 'none', 'null', '']:
        return default
    return str(value)

def sanitize_for_json(obj):
    """Recursively sanitize any object for JSON serialization"""
    import math
    
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0
        return obj
    elif obj is None:
        return None
    else:
        # For any pandas-specific types, convert to basic Python types
        try:
            if pd.isna(obj):
                return None
        except (TypeError, ValueError):
            pass
        
        # Convert numpy/pandas types to basic Python types
        if hasattr(obj, 'item'):  # numpy scalars
            try:
                return sanitize_for_json(obj.item())
            except (ValueError, AttributeError):
                pass
        
        return obj


def _calculate_load_band(power_output: float | int | None,
                        engine_speed: float | int | None,
                        rated_power: float | int | None = 150) -> str:
    """Classify load using controller-reported percentage values."""
    try:
        engine_speed_val = float(engine_speed or 0)
    except (TypeError, ValueError):
        engine_speed_val = 0.0

    if engine_speed_val < 100:
        return "0%"

    try:
        raw_output = float(power_output or 0)
    except (TypeError, ValueError):
        raw_output = 0.0

    load_percentage = raw_output
    if load_percentage > 125:
        if load_percentage <= 12500:
            load_percentage = load_percentage / 100
        elif rated_power:
            try:
                load_percentage = (raw_output / float(rated_power)) * 100
            except (TypeError, ValueError, ZeroDivisionError):
                load_percentage = 0.0

    if load_percentage < 20:
        return "0-20%"
    if load_percentage < 40:
        return "20-40%"
    if load_percentage < 60:
        return "40-60%"
    if load_percentage < 80:
        return "60-80%"
    return "80-100%"


def _pivot_baseline_dataframe(df: pd.DataFrame | list[pd.DataFrame]) -> pd.DataFrame:
    """Normalize baseline query results into a single wide dataframe."""
    if isinstance(df, list):
        df = pd.concat(df, ignore_index=True) if df else pd.DataFrame()

    if df is None or df.empty:
        return pd.DataFrame()

    if {'_field', '_value'}.issubset(df.columns):
        index_cols = ['_time']
        for col in (
            'load_band', 'period_type', 'alert_level', 'mode',
            'analysis_type', 'agent_state'
        ):
            if col in df.columns:
                index_cols.append(col)

        df = df.pivot_table(
            index=index_cols,
            columns='_field',
            values='_value',
            aggfunc='last'
        ).reset_index()
        df.columns.name = None

    return df


def _sanitize_baseline_row(row: pd.Series) -> dict:
    """Convert a baseline dataframe row into a JSON-serializable dict."""
    baseline = {
        "timestamp": str(row.get("_time", "")),
        "load_band": row.get("load_band", "unknown"),
        "period_type": row.get("period_type", "daily"),
    }

    fields_to_copy = [
        # averages
        'avg_engine_speed', 'avg_run_speed', 'avg_oil_pressure', 'avg_power_output',
        'avg_coolant_temperature', 'avg_fuel_pressure', 'avg_fuel_temperature',
        'avg_fuel_rate', 'avg_intake_air_temperature', 'avg_intake_air_pressure',
        # stddevs
        'stddev_engine_speed', 'stddev_oil_pressure', 'stddev_fuel_pressure',
        'stddev_fuel_temperature', 'stddev_fuel_rate', 'stddev_intake_air_temperature',
        'stddev_intake_air_pressure',
        # min/max
        'min_oil_pressure', 'max_oil_pressure', 'min_fuel_pressure', 'max_fuel_pressure',
        'min_fuel_temperature', 'max_fuel_temperature', 'min_fuel_rate', 'max_fuel_rate',
        'min_intake_air_temperature', 'max_intake_air_temperature', 'min_intake_air_pressure',
        'max_intake_air_pressure',
        # trends
        'oil_pressure_trend', 'coolant_temperature_trend', 'fuel_pressure_trend',
        'fuel_temperature_trend', 'fuel_rate_trend', 'intake_air_temperature_trend',
        'intake_air_pressure_trend', 'trend_slope',
        # metadata
        'sample_count'
    ]

    for field in fields_to_copy:
        baseline[field] = sanitize_numeric(row.get(field))

    return baseline


BASELINE_METRIC_FIELDS = {
    'engine_speed': ('avg_engine_speed', 'stddev_engine_speed'),
    'engine_oil_pressure': ('avg_oil_pressure', 'stddev_oil_pressure'),
    'coolant_temperature': ('avg_coolant_temperature', 'stddev_coolant_temperature'),
    'engine_fuel_pressure': ('avg_fuel_pressure', 'stddev_fuel_pressure'),
    'engine_fuel_rate': ('avg_fuel_rate', 'stddev_fuel_rate'),
    'engine_fuel_temperature': ('avg_fuel_temperature', 'stddev_fuel_temperature'),
    'intake_air_temperature': ('avg_intake_air_temperature', 'stddev_intake_air_temperature'),
    'intake_air_pressure': ('avg_intake_air_pressure', 'stddev_intake_air_pressure')
}


LIVE_STATS_FIELD_MAP = {
    'engine_speed': 'Engine_Speed',
    'engine_oil_pressure': 'Engine_Oil_Pressure',
    'coolant_temperature': 'Engine_Coolant_Temperature',
    'engine_fuel_pressure': 'Engine_Fuel_Pressure',
    'engine_fuel_rate': 'Engine_Fuel_Rate',
    'engine_fuel_temperature': 'Engine_Fuel_Temperature',
    'intake_air_temperature': 'Intake_Air_Temperature',
    'intake_air_pressure': 'Intake_Air_Pressure',
    'generator_power': 'Generator_Total_Real_Power',
    'engine_run_speed': 'Engine_Run_Speed'
}
    
@app.get("/api/live-stats")
async def get_live_stats():
    query_api = influx_client.query_api()

    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -2m)
      |> filter(fn: (r) =>
        r._measurement == "generator_metrics" and (
          r._field == "Engine_Speed" or
          r._field == "Engine_Oil_Pressure" or
          r._field == "Engine_Coolant_Temperature" or
          r._field == "Engine_Fuel_Rate" or
          r._field == "Battery_Voltage" or
          r._field == "Controller_Temperature" or
          r._field == "Engine_Fuel_Pressure" or
          r._field == "Engine_Fuel_Temperature" or
          r._field == "Intake_Air_Temperature" or
          r._field == "Intake_Air_Pressure" or
          r._field == "ECM_Model" or
          r._field == "ECM_Fault_Codes" or
          r._field == "Total_Runtime_Hours" or
          r._field == "Total_Runtime_Loaded_Hours" or
          r._field == "Total_Runtime_Unloaded_Hours" or
          r._field == "Total_Runtime_kW_Hours" or
          r._field == "Total_Number_of_Starts" or
          r._field == "Total_Runtime_Hours_Since_Maintenance" or
          r._field == "Operating_Days_Since_Last_Maintenance" or
          r._field == "Number_of_Starts_Since_Last_Maintenance" or
          r._field == "System_Voltage" or
          r._field == "System_Frequency" or
          r._field == "Rated_Current" or
          r._field == "Genset_kW_Rating" or
          r._field == "Genset_Model_Number_1-2" or
          r._field == "Genset_Model_Number_3-4" or
          r._field == "Genset_Model_Number_5-6" or
          r._field == "RMS_Generator_Voltage_L1-L2" or
          r._field == "RMS_Generator_Voltage_L2-L3" or
          r._field == "RMS_Generator_Voltage_L3-L1" or
          r._field == "RMS_Generator_Voltage_Line_to_Line_Average" or
          r._field == "RMS_Generator_Voltage_L1-N" or
          r._field == "RMS_Generator_Voltage_L2-N" or
          r._field == "RMS_Generator_Voltage_L3-N" or
          r._field == "RMS_Generator_Voltage_Line_to_Neutral_Average" or
          r._field == "RMS_Generator_Current_L1" or
          r._field == "RMS_Generator_Current_L2" or
          r._field == "RMS_Generator_Current_L3" or
          r._field == "RMS_Generator_Current_Average" or
          r._field == "Generator_Frequency" or
          r._field == "Generator_Real_Power_L1" or
          r._field == "Generator_Real_Power_L2" or
          r._field == "Generator_Real_Power_L3" or
          r._field == "Generator_Total_Real_Power" or
          r._field == "Generator_Reactive_Power_L1" or
          r._field == "Generator_Reactive_Power_L2" or
          r._field == "Generator_Reactive_Power_L3" or
          r._field == "Generator_Reactive_Power" or
          r._field == "Generator_Apparent_Power_L1" or
          r._field == "Generator_Apparent_Power_L2" or
          r._field == "Generator_Apparent_Power_L3" or
          r._field == "Generator_Apparent_Power" or
          r._field == "Generator_Power_Factor_L1" or
          r._field == "Generator_Power_Factor_L2" or
          r._field == "Generator_Power_Factor_L3" or
          r._field == "Generator_Power_Factor_Average" or
          r._field == "Generator_Phase_Angle_Voltage_L1-Voltage_L2" or
          r._field == "RMS_Bus_Voltage_L1-L2" or
          r._field == "RMS_Bus_Voltage_L2-L3" or
          r._field == "RMS_Bus_Voltage_L3-L1" or
          r._field == "RMS_Bus_Voltage_Average_Line_to_Line" or
          r._field == "Total_Bus_Real_Power" or
          r._field == "Total_Bus_Reactive_Power" or
          r._field == "Bus_Frequency"
        )
      )
      |> aggregateWindow(every: 1s, fn: last, createEmpty: false)
      |> last()
    '''

    result = query_api.query(org=INFLUXDB_ORG, query=query)
    latest = {}

    for table in result:
        for record in table.records:
            latest[record.get_field()] = record.get_value()

    return latest

@app.get("/api/active-events")
async def get_active_events():
    client = InfluxDBClient(
        url=INFLUXDB_URL,
        token=INFLUXDB_TOKEN,
        org=INFLUXDB_ORG
    )
    query_api = client.query_api()

    # Tme range for events is currentl set to 5 minutes
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -1m) 
      |> filter(fn: (r) => r._measurement == "generator_events")
      |> filter(fn: (r) => r._field == "message")
      |> sort(columns: ["_time"], desc: true)
      |> keep(columns: ["_time", "_value", "param_id", "fmi", "level"])
    '''

    try:
        tables = query_api.query(query)
        seen = {}
        
        for table in tables:
            for row in table.records:
                key = f"{row['param_id']}-{row['fmi']}-{row['level']}"
                if key not in seen:
                    seen[key] = {
                        "time": row["_time"].isoformat(),
                        "message": row["_value"],
                        "param_id": row["param_id"],
                        "fmi": row["fmi"],
                        "level": row["level"]
                    }

        events = list(seen.values())
        return {"count": len(events), "events": events}

    except Exception as e:
        return {"error": str(e)}

    finally:
        client.close()



@app.get("/api/trend")
async def get_trend(field: str = Query(...), hours: int = 2, interval: str = "1m"):
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -{hours}h)
      |> filter(fn: (r) =>
        r._measurement == "generator_metrics" and
        r._field == "{field}"
      )
      |> aggregateWindow(every: {interval}, fn: last, createEmpty: false)
    '''

    result = influx_client.query_api().query_data_frame(org=INFLUXDB_ORG, query=query)

    if isinstance(result, list):
        result = pd.concat(result, ignore_index=True)
    if result.empty:
        return []

    result = result.replace([np.inf, -np.inf], np.nan).dropna()
    result["_time"] = result["_time"].astype(str)

    return result.to_dict(orient="records")
    
@app.get("/api/load-trend")
async def get_load_trend():
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -2h)
      |> filter(fn: (r) =>
        r._measurement == "generator_metrics" and
        r._field == "Generator_Apparent_Power"
      )
      |> aggregateWindow(every: 15s, fn: last, createEmpty: false)
      |> keep(columns: ["_time", "_value"])
    '''

    result = influx_client.query_api().query_data_frame(org=INFLUXDB_ORG, query=query)

    if isinstance(result, list):
        result = pd.concat(result, ignore_index=True)
    if result.empty:
        return []

    result = result.replace([np.inf, -np.inf], np.nan).dropna()
    result["_time"] = result["_time"].astype(str)
    result.rename(columns={"_value": "Load_Percent"}, inplace=True)

    return result.to_dict(orient="records")

@app.get("/api/logs")
async def get_logs():
    log_path = "/app/logs/modbus_poller.log"
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            last_lines = lines[-100:]  # last 100 lines
            return {"log": "".join(last_lines)}
    except FileNotFoundError:
        return {"log": "Modbus poller log file not found. The poller may not have started yet."}
    except Exception as e:
        return {"log": f"Error reading logs: {str(e)}"}


@app.get("/api/powertrain-status")
async def get_powertrain_status():
    """Get current PowertrainAgent status and latest analysis"""
    
    # First check agent heartbeat for real-time health status
    heartbeat = agent_heartbeats.get("powertrain-agent")
    if not heartbeat or (time.time() - heartbeat["received_at"]) > 30:
        return {
            "agent_state": "OFFLINE",
            "analysis_summary": "PowertrainAgent is offline - no recent heartbeat",
            "error": "No recent agent heartbeat - agent appears offline"
        }
    
    query_api = influx_client.query_api()
    
    # Get latest powertrain analysis - get most recent records
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -1h)
      |> filter(fn: (r) => r._measurement == "powertrain_analysis")
      |> filter(fn: (r) => exists r.agent_state)
      |> sort(columns: ["_time"], desc: true)
      |> limit(n: 50)
    '''
    
    try:
        result = query_api.query_data_frame(org=INFLUXDB_ORG, query=query)
        
        if isinstance(result, list):
            result = pd.concat(result, ignore_index=True)
        
        if result.empty:
            return {"status": "No recent PowertrainAgent analysis found"}
        
        # Prefer the latest AI/GATEWAY analysis; fallback to overall latest if none
        ai_mask = False
        if 'mode' in result.columns:
            ai_mask = ai_mask | (result['mode'] == 'AI')
        if 'analysis_type' in result.columns:
            ai_mask = ai_mask | (result['analysis_type'] == 'GATEWAY')

        ai_rows = result[ai_mask] if isinstance(ai_mask, pd.Series) else pd.DataFrame()
        if not ai_rows.empty:
            latest_timestamp = ai_rows['_time'].max()
            preferred_rows = ai_rows[ai_rows['_time'] == latest_timestamp]
        else:
            latest_timestamp = result['_time'].max()
            latest_rows = result[result['_time'] == latest_timestamp]
            preferred_rows = latest_rows
            if 'mode' in latest_rows.columns and (latest_rows['mode'] == 'AI').any():
                preferred_rows = latest_rows[latest_rows['mode'] == 'AI']
            elif 'analysis_type' in latest_rows.columns and (latest_rows['analysis_type'] == 'GATEWAY').any():
                preferred_rows = latest_rows[latest_rows['analysis_type'] == 'GATEWAY']
        
        # Convert to dictionary from the most recent timestamp only
        latest_data = {}
        alerts_list = []
        
        # Process all fields from the most recent timestamp (prefer AI/GATEWAY rows if available)
        rows_to_process = preferred_rows
        for _, row in rows_to_process.iterrows():
            # Store tags from the most recent timestamp
            if '_time' not in latest_data:
                latest_data['alert_level'] = sanitize_string(row.get('alert_level', 'UNKNOWN'), 'UNKNOWN')
                latest_data['load_band'] = sanitize_string(row.get('load_band', 'unknown'), 'unknown')
                latest_data['agent_state'] = sanitize_string(row.get('agent_state', 'UNKNOWN'), 'UNKNOWN')
                latest_data['_time'] = row.get('_time')
                
            field_name = row.get('_field')
            field_value = row.get('_value')
            
            # Store field values with sanitization for JSON compliance
            if field_name and field_value is not None:
                # Collect AI alerts from description fields (written by logger)
                if field_name == 'description':
                    alerts_list.append({
                        "severity": sanitize_string(row.get('alert_level', 'INFO'), 'INFO'),
                        "description": sanitize_string(field_value)
                    })
                # Sanitize numeric values that could be NaN or infinity
                if isinstance(field_value, (int, float)):
                    latest_data[field_name] = sanitize_numeric(field_value)
                else:
                    latest_data[field_name] = sanitize_string(field_value)
        
        # Handle timestamp conversion safely
        timestamp_value = latest_data.get("_time", "")
        if hasattr(timestamp_value, 'isoformat'):
            timestamp_str = timestamp_value.isoformat().replace("T", " ").replace("Z", "")
        else:
            timestamp_str = str(timestamp_value).replace("T", " ").replace("Z", "")

        # Parse analysis_sections JSON if present
        if 'analysis_sections' in latest_data:
            try:
                latest_data['analysis_sections'] = json.loads(latest_data['analysis_sections'])
            except Exception:
                latest_data['analysis_sections'] = None
                
        # Get current AI status and frequency from agent configuration
        current_ai_enabled = latest_data.get("ai_enabled", True)  # Default from analysis
        current_frequency = 5  # Default frequency
        
        try:
            # Check ai_global_status for the latest AI settings (both ai_enabled and frequency)
            config_query = f'''
            from(bucket: "{INFLUXDB_BUCKET}")
              |> range(start: -7d)
              |> filter(fn: (r) => r._measurement == "ai_global_status" and (r._field == "ai_enabled" or r._field == "analysis_frequency"))
              |> last()
            '''
            
            config_result = query_api.query_data_frame(org=INFLUXDB_ORG, query=config_query)
            
            if isinstance(config_result, list):
                config_result = pd.concat(config_result, ignore_index=True)
            
            if not config_result.empty:
                # Process each config field
                for _, row in config_result.iterrows():
                    field_name = row.get('_field')
                    field_value = row.get('_value')
                    
                    if field_name == "ai_enabled":
                        # ai_enabled from ai_global_status takes precedence over agent data
                        current_ai_enabled = bool(field_value)
                    elif field_name == "analysis_frequency":
                        current_frequency = int(sanitize_numeric(field_value, 5))
                
        except Exception:
            # Keep the defaults if config query fails
            pass
        
        # Get bootstrap status information
        bootstrap_status = "unknown"
        bootstrap_progress = 0
        bootstrap_timestamp = None
        baseline_count = 0
        
        try:
            # Query for bootstrap status
            bootstrap_query = f'''
            from(bucket: "{INFLUXDB_BUCKET}")
              |> range(start: -30d)
              |> filter(fn: (r) => r._measurement == "powertrain_system_status")
              |> last()
            '''
            
            bootstrap_result = query_api.query_data_frame(org=INFLUXDB_ORG, query=bootstrap_query)
            
            if isinstance(bootstrap_result, list):
                bootstrap_result = pd.concat(bootstrap_result, ignore_index=True)
            
            if not bootstrap_result.empty:
                # Process unpivoted InfluxDB data - extract values by field
                bootstrap_completed = False
                bootstrap_progress = 0
                baseline_count = 0
                bootstrap_timestamp = None
                
                for _, row in bootstrap_result.iterrows():
                    field_name = row.get('_field')
                    field_value = row.get('_value')
                    
                    if field_name == 'bootstrap_completed':
                        bootstrap_completed = bool(field_value)
                    elif field_name == 'bootstrap_progress':
                        bootstrap_progress = sanitize_numeric(field_value, 0)
                    elif field_name == 'baseline_count':
                        baseline_count = int(sanitize_numeric(field_value, 0))
                    
                    # Use _time from any row (should be same for all fields)
                    if bootstrap_timestamp is None:
                        bootstrap_timestamp = row.get('_time')
                
                # Determine status
                if bootstrap_completed and baseline_count > 0:
                    bootstrap_status = "complete"
                elif bootstrap_progress > 0 and bootstrap_progress < 100:
                    bootstrap_status = "in_progress"
                elif bootstrap_completed and baseline_count == 0:
                    bootstrap_status = "completed_no_baselines"
                else:
                    bootstrap_status = "needed"
            else:
                # No bootstrap record found - bootstrap needed
                bootstrap_status = "needed"
                
        except Exception as e:
            # If we can't get bootstrap status, default to unknown
            bootstrap_status = "unknown"
        
        response_data = {
            "timestamp": timestamp_str,
            "alert_level": latest_data.get("alert_level", "UNKNOWN"),
            "load_band": latest_data.get("load_band", "unknown"),
            "agent_state": heartbeat.get("agent_state", "UNKNOWN"),  # Use heartbeat data
            "ai_enabled": bool(current_ai_enabled),
            "frequency": current_frequency or 5,
            "heartbeat": bool(latest_data.get("heartbeat", False)),
            "engine_speed": latest_data.get("engine_speed", 0),
            "engine_oil_pressure": latest_data.get("engine_oil_pressure", 0),
            "generator_power": latest_data.get("generator_power", 0),
            "coolant_temperature": latest_data.get("coolant_temperature", 0),
            "analysis_summary": latest_data.get("analysis_summary", "No summary available"),
            "ai_analysis": latest_data.get("ai_analysis", ""),
            "analysis_sections": latest_data.get("analysis_sections"),
            "alerts": alerts_list,
            "bootstrap_status": bootstrap_status or "unknown",
            "bootstrap_progress": bootstrap_progress,
            "bootstrap_timestamp": bootstrap_timestamp.isoformat() if isinstance(bootstrap_timestamp, datetime) else None,
            "baseline_count": baseline_count
        }
        
        # Final sanitization pass to catch any remaining NaN values
        return sanitize_for_json(response_data)
        
    except Exception as e:
        # Emergency fallback with minimal data
        return sanitize_for_json({
            "timestamp": "unknown",
            "alert_level": "UNKNOWN", 
            "load_band": "unknown",
            "agent_state": "UNKNOWN",
            "ai_enabled": True,
            "frequency": 5,
            "heartbeat": False,
            "engine_speed": 0,
            "engine_oil_pressure": 0,
            "generator_power": 0,
            "coolant_temperature": 0,
            "analysis_summary": "PowertrainAgent status unavailable",
            "ai_analysis": "",
            "bootstrap_status": "unknown",
            "bootstrap_progress": 0,
            "bootstrap_timestamp": None,
            "baseline_count": 0,
            "error": f"Failed to get powertrain status: {str(e)}"
        })

@app.get("/api/powertrain-trends")
async def get_powertrain_trends(hours: int = 24):
    """Get PowertrainAgent trend analysis"""
    query_api = influx_client.query_api()
    
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -{hours}h)
      |> filter(fn: (r) => r._measurement == "powertrain_analysis" and (
        r._field == "engine_oil_pressure" or
        r._field == "engine_speed" or
        r._field == "generator_power"
      ))
      |> aggregateWindow(every: 15m, fn: mean, createEmpty: false)
    '''
    
    try:
        result = query_api.query_data_frame(org=INFLUXDB_ORG, query=query)
        
        if isinstance(result, list):
            result = pd.concat(result, ignore_index=True)
        
        if result.empty:
            return []
        
        result = result.replace([np.inf, -np.inf], np.nan).dropna()
        result["_time"] = result["_time"].astype(str)
        
        return result.to_dict(orient="records")
        
    except Exception as e:
        return {"error": f"Failed to get powertrain trends: {str(e)}"}

@app.get("/api/powertrain-alerts")
async def get_powertrain_alerts(hours: int = 24):
    """Get recent PowertrainAgent alerts"""
    query_api = influx_client.query_api()
    
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -{hours}h)
      |> filter(fn: (r) => r._measurement == "powertrain_analysis" and 
        (r.mode == "LOCAL" or r.mode == "AI") and
        (r.alert_level == "INFO" or r.alert_level == "WARNING" or r.alert_level == "CRITICAL"))
      |> sort(columns: ["_time"], desc: true)
      |> limit(n: 200)
    '''
    
    try:
        result = query_api.query_data_frame(org=INFLUXDB_ORG, query=query)
        
        result = _pivot_baseline_dataframe(result)

        if result.empty:
            return []
        
        result = result.sort_values('_time', ascending=False)
        result = result.drop_duplicates(subset=['_time', 'load_band', 'alert_level'], keep='first')

        alerts = []
        for _, row in result.head(100).iterrows():
            description = row.get('description') or row.get('analysis_summary') or "Analysis alert"
            alert = {
                "timestamp": str(row.get("_time", "")),
                "severity": row.get("alert_level", "INFO"),
                "description": description,
                "load_band": row.get("load_band", "unknown"),
                "mode": row.get("mode", "UNKNOWN"),
                "analysis_type": row.get("analysis_type", "UNKNOWN"),
                "engine_oil_pressure": sanitize_numeric(row.get("oil_pressure") or row.get("engine_oil_pressure", 0)),
                "engine_speed": sanitize_numeric(row.get("engine_speed", 0)),
                "generator_power": sanitize_numeric(row.get("generator_power", 0)),
                "coolant_temperature": sanitize_numeric(row.get("coolant_temperature", 0)),
                "resolved": bool(row.get("resolved", False))
            }
            alerts.append(alert)

        return sanitize_for_json(alerts)
        
    except Exception as e:
        return {"error": f"Failed to get powertrain alerts: {str(e)}"}

@app.get("/api/powertrain-baselines")
async def get_powertrain_baselines(load_band: str = "0-20%", days: int = 30):
    """Get PowertrainAgent historical baselines"""
    query_api = influx_client.query_api()
    
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -{days}d)
      |> filter(fn: (r) => r._measurement == "powertrain_baselines" and 
        r.load_band == "{load_band}")
      |> sort(columns: ["_time"], desc: false)
    '''
    
    try:
        result = query_api.query_data_frame(org=INFLUXDB_ORG, query=query)
        result = _pivot_baseline_dataframe(result)

        if result.empty:
            return {"message": f"No baseline data found for load band {load_band}"}

        baselines = []
        for _, row in result.sort_values('_time').iterrows():
            baselines.append(_sanitize_baseline_row(row))

        return baselines

    except Exception as e:
        return {"error": f"Failed to get powertrain baselines: {str(e)}"}

@app.get("/api/powertrain-local-analysis")
async def get_powertrain_local_analysis():
    """Get latest PowertrainAgent LOCAL analysis results with statistical deviations"""
    query_api = influx_client.query_api()
    
    # Get latest LOCAL analysis entry
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -2h)
      |> filter(fn: (r) => r._measurement == "powertrain_analysis" and r.analysis_type == "LOCAL")
      |> sort(columns: ["_time"], desc: true)
      |> limit(n: 50)
    '''
    
    try:
        result = query_api.query_data_frame(org=INFLUXDB_ORG, query=query)
        
        if isinstance(result, list):
            result = pd.concat(result, ignore_index=True)
        
        if result.empty:
            return {"message": "No recent LOCAL analysis found"}
        
        # Get the most recent timestamp 
        latest_timestamp = result['_time'].max()
        latest_rows = result[result['_time'] == latest_timestamp]
        
        # Extract data from most recent LOCAL analysis
        analysis_data = {}
        current_metrics = {}
        
        for _, row in latest_rows.iterrows():
            # Store tags and metadata
            if 'load_band' not in analysis_data:
                analysis_data['timestamp'] = str(row.get('_time', ''))
                analysis_data['load_band'] = sanitize_string(row.get('load_band', 'unknown'), 'unknown')
                analysis_data['alert_level'] = sanitize_string(row.get('alert_level', 'INFO'), 'INFO')
                analysis_data['agent_state'] = sanitize_string(row.get('agent_state', 'UNKNOWN'), 'UNKNOWN')
                
            # Store field values
            field_name = row.get('_field')
            field_value = row.get('_value')
            
            if field_name and field_value is not None:
                if isinstance(field_value, (int, float)):
                    analysis_data[field_name] = sanitize_numeric(field_value)
                    
                    # Extract current metric values for comparison table (all parameters analyzed by LOCAL analysis)
                    if field_name in ['engine_speed', 'engine_oil_pressure', 'generator_power', 'coolant_temperature',
                                    'engine_fuel_pressure', 'engine_fuel_temperature', 'engine_fuel_rate',
                                    'intake_air_temperature', 'intake_air_pressure', 'engine_run_speed']:
                        current_metrics[field_name] = sanitize_numeric(field_value)
                else:
                    analysis_data[field_name] = sanitize_string(field_value)

        # Supplement current metrics with latest live stats and compute live load band
        analysis_metrics_snapshot = current_metrics.copy()

        try:
            live_stats = await get_live_stats()
        except Exception:
            live_stats = {}

        live_metrics = {}
        current_load_band = None

        if isinstance(live_stats, dict):
            power_output_live = live_stats.get('Generator_Total_Real_Power')
            engine_speed_live = live_stats.get('Engine_Speed')
            rated_power_live = live_stats.get('Genset_kW_Rating')

            for metric_key, influx_key in LIVE_STATS_FIELD_MAP.items():
                value = live_stats.get(influx_key)
                if value is not None:
                    numeric_value = sanitize_numeric(value)
                    live_metrics[metric_key] = numeric_value
                    current_metrics[metric_key] = numeric_value

            if power_output_live is not None or engine_speed_live is not None:
                current_load_band = _calculate_load_band(
                    power_output=power_output_live,
                    engine_speed=engine_speed_live,
                    rated_power=rated_power_live
                )

        # Fetch most recent baseline for this load band
        baseline_stats = {}
        baseline_timestamp = None
        analysis_load_band = analysis_data.get('load_band', 'unknown')
        load_band = current_load_band or analysis_load_band
        if load_band in (None, '', 'unknown', '0%'):
            load_band = analysis_load_band

        if load_band and load_band != 'unknown':
            baseline_query = f'''
            from(bucket: "{INFLUXDB_BUCKET}")
              |> range(start: -30d)
              |> filter(fn: (r) => r._measurement == "powertrain_baselines" and 
                r.load_band == "{load_band}")
              |> sort(columns: ["_time"], desc: true)
              |> limit(n: 1)
            '''

            try:
                baseline_df = query_api.query_data_frame(org=INFLUXDB_ORG, query=baseline_query)
                baseline_df = _pivot_baseline_dataframe(baseline_df)
                if not baseline_df.empty:
                    latest_baseline = baseline_df.iloc[0]
                    baseline_timestamp = str(latest_baseline.get('_time', ''))
                    for metric_key, (avg_field, std_field) in BASELINE_METRIC_FIELDS.items():
                        baseline_stats[metric_key] = {
                            'average': sanitize_numeric(latest_baseline.get(avg_field)),
                            'stddev': sanitize_numeric(latest_baseline.get(std_field))
                        }
                    baseline_stats['sample_count'] = int(latest_baseline.get('sample_count', 0) or 0)
            except Exception as baseline_error:
                # Don't fail the endpoint if baseline lookup has issues
                print(f"Baseline lookup failed: {baseline_error}")

        # Fetch structured LOCAL alerts stored by the agent (sigma-based deviations)
        alerts = []
        try:
            alerts_query = f'''
            from(bucket: "{INFLUXDB_BUCKET}")
              |> range(start: -2h)
              |> filter(fn: (r) => r._measurement == "powertrain_analysis"
                and r.analysis_type == "LOCAL"
                and r._field == "description")
              |> sort(columns: ["_time"], desc: true)
              |> limit(n: 50)
            '''
            alerts_df = query_api.query_data_frame(org=INFLUXDB_ORG, query=alerts_query)
            if isinstance(alerts_df, list):
                alerts_df = pd.concat(alerts_df, ignore_index=True)

            # Only keep alerts from the most recent LOCAL analysis run
            if alerts_df is not None and not alerts_df.empty:
                latest_alerts_df = alerts_df[alerts_df['_time'] == latest_timestamp]

                # Deduplicate identical messages from the same run while preserving order
                seen = set()
                for _, row in latest_alerts_df.iterrows():
                    level = sanitize_string(row.get('alert_level', 'INFO'), 'INFO')
                    message = sanitize_string(row.get('_value', 'Alert'), 'Alert')
                    key = (level, message)
                    if key in seen:
                        continue
                    seen.add(key)
                    alerts.append({
                        "timestamp": str(row.get('_time', '')),
                        "level": level,
                        "message": message,
                        "load_band": sanitize_string(row.get('load_band', 'unknown'), 'unknown')
                    })
        except Exception:
            pass
        
        # Map alert levels to colors for frontend
        color_mapping = {
            "INFO": "green",
            "WARNING": "yellow", 
            "CRITICAL": "red"
        }
        
        response = {
            "timestamp": analysis_data.get('timestamp', ''),
            "load_band": current_load_band or analysis_load_band,
            "analysis_load_band": analysis_load_band,
            "current_load_band": current_load_band or analysis_load_band,
            "overall_alert_level": analysis_data.get('alert_level', 'INFO'),
            "alert_color": color_mapping.get(analysis_data.get('alert_level', 'INFO'), 'green'),
            "agent_state": analysis_data.get('agent_state', 'UNKNOWN'),
            "alerts": alerts,
            "current_metrics": current_metrics,
            "analysis_metrics_snapshot": analysis_metrics_snapshot,
            "live_metrics": live_metrics,
            "analysis_summary": analysis_data.get('analysis_summary', 'No summary available'),
            "baseline_available": analysis_data.get('baseline_available', True),
            "parameters_analyzed": analysis_data.get('parameters_analyzed', len(BASELINE_METRIC_FIELDS)),
            "baseline_stats": baseline_stats,
            "baseline_timestamp": baseline_timestamp,
            "baseline_reference_load_band": load_band
        }
        
        return sanitize_for_json(response)
        
    except Exception as e:
        return {"error": f"Failed to get powertrain local analysis: {str(e)}"}

@app.get("/api/powertrain-memory")
async def get_powertrain_memory(knowledge_type: str = "all", days: int = 7, load_band: str = None):
    """Get PowertrainAgent accumulated memory/insights"""
    query_api = influx_client.query_api()
    
    # Build filter clause
    filter_parts = ['r._measurement == "powertrain_ai_memory"']
    
    if knowledge_type != "all":
        filter_parts.append(f'r.knowledge_type == "{knowledge_type}"')
    
    if load_band:
        filter_parts.append(f'r.load_band == "{load_band}"')
    
    filter_clause = ' and '.join(filter_parts)
    
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -{days}d)
      |> filter(fn: (r) => {filter_clause})
      |> sort(columns: ["_time"], desc: true)
      |> limit(n: 60)
    '''
    
    try:
        result = query_api.query_data_frame(org=INFLUXDB_ORG, query=query)
        
        if isinstance(result, list):
            result = pd.concat(result, ignore_index=True)
        
        if result.empty:
            return {"message": "No memory data found", "insights": []}
        
        insights = []
        
        # Filter for insight_text records specifically
        insight_text_records = result[result['_field'] == 'insight_text']
        
        if not insight_text_records.empty:
            for _, row in insight_text_records.iterrows():
                value = row['_value']
                insight = {
                    "timestamp": str(row["_time"]),
                    "knowledge_type": str(row["knowledge_type"]), 
                    "insight_text": str(value),
                }
                insights.append(insight)
        
        # Sort by timestamp descending
        insights.sort(key=lambda x: x["timestamp"], reverse=True)
        insights = insights[:60]
        
        return {"insights": insights, "total_count": len(insights)}
        
    except Exception as e:
        return {"error": f"Failed to get powertrain memory: {str(e)}"}


@app.post("/api/ai/toggle")
async def toggle_global_ai():

    from fastapi import APIRouter
    from influxdb_client import Point
    from influxdb_client.client.write_api import SYNCHRONOUS
    from datetime import datetime
    try:
        current_status = await get_global_ai_status()
        current_ai_enabled = current_status["ai_enabled"]
        new_ai_enabled = not current_ai_enabled

        point = Point("ai_global_status") \
            .field("ai_enabled", new_ai_enabled) \
            .field("updated_by", "frontend_toggle") \
            .time(datetime.utcnow())

        write_api = influx_client.write_api(write_options=SYNCHRONOUS)
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)

        return {
            "success": True,
            "ai_enabled": new_ai_enabled,
            "previous_state": current_ai_enabled,
            "updated_at": datetime.utcnow().isoformat(),
            "message": f"Global AI analysis {'enabled' if new_ai_enabled else 'disabled'}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to toggle global AI status: {str(e)}"
        }

# Reader for the AI Global Status
@app.get("/api/ai/status")
async def get_global_ai_status():
    """Get current application-wide AI analysis status"""
    query_api = influx_client.query_api()
    
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -7d)
      |> filter(fn: (r) => r._measurement == "ai_global_status" and r._field == "ai_enabled")
      |> last()
    '''
    
    try:
        result = query_api.query_data_frame(org=INFLUXDB_ORG, query=query)
        
        if isinstance(result, list):
            result = pd.concat(result, ignore_index=True)
        
        if not result.empty:
            ai_enabled = bool(result.iloc[0]['_value'])
            last_updated = str(result.iloc[0]['_time'])
            return {
                "ai_enabled": ai_enabled,
                "source": "database",
                "last_updated": last_updated
            }
        else:
            # Fallback to environment variable
            env_value = os.getenv('GLOBAL_AI_ENABLED', 'true')
            ai_enabled = env_value.lower() == 'true'
            return {
                "ai_enabled": ai_enabled,
                "source": "environment",
                "last_updated": None
            }
        
    except Exception as e:
        # Fallback to environment variable on error
        env_value = os.getenv('GLOBAL_AI_ENABLED', 'true')
        ai_enabled = env_value.lower() == 'true'
        return {
            "ai_enabled": ai_enabled,
            "source": "environment_fallback",
            "error": str(e)
        }


@app.post("/api/agents/ai-frequency")
async def update_agents_frequency(request: Request):
    """Update global agents analysis frequency"""
    from influxdb_client import Point
    from influxdb_client.client.write_api import SYNCHRONOUS
    
    try:
        # Get request body
        body = await request.json()
        frequency = body.get("frequency")
        
        # Validate frequency
        valid_frequencies = [1, 3, 5, 10, 15, 30]
        if frequency not in valid_frequencies:
            return {
                "success": False,
                "error": f"Invalid frequency. Must be one of: {valid_frequencies}"
            }
        
        # Store frequency in InfluxDB
        write_api = influx_client.write_api(write_options=SYNCHRONOUS)
        
        point = Point("ai_global_status") \
            .field("analysis_frequency", frequency) \
            .field("updated_by", "frontend_frequency") \
            .time(datetime.utcnow())
        
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
        
        return {
            "success": True,
            "frequency": frequency,
            "updated_at": datetime.utcnow().isoformat(),
            "message": f"Analysis frequency updated to {frequency} minutes"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to update frequency: {str(e)}"
        }

@app.get("/api/gateway-ping")
async def ping_gateway():
    """Ping the gateway service to check connectivity"""
    try:
        # Get gateway URL from environment or use default
        gateway_url = os.getenv('GATEWAY_URL', 'http://gateway:8003')
        
        # Make request to gateway root endpoint with 10-second timeout
        response = requests.get(f"{gateway_url}/", timeout=10)
        
        # Check if response status is OK
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK':
                return {
                    "status": "OK",
                    "message": "Gateway connection successful",
                    "service": data.get('service', 'Unknown'),
                    "version": data.get('version', 'Unknown')
                }
            else:
                return {
                    "status": "ERROR",
                    "message": f"Gateway returned unexpected status: {data.get('status', 'Unknown')}"
                }
        else:
            return {
                "status": "ERROR", 
                "message": f"Gateway returned HTTP {response.status_code}"
            }
            
    except requests.exceptions.Timeout:
        return {
            "status": "TIMEOUT",
            "message": "Gateway ping timed out after 10 seconds"
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "CONNECTION_ERROR", 
            "message": "Could not connect to gateway service"
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Gateway ping failed: {str(e)}"
        }

@app.get("/api/gateway-health")
async def check_gateway_health():
    """Check gateway memory manager health status"""
    try:
        # Get gateway URL from environment or use default
        gateway_url = os.getenv('GATEWAY_URL', 'http://gateway:8003')
        
        # Make request to gateway health endpoint with 15-second timeout
        response = requests.get(f"{gateway_url}/health", timeout=15)
        
        # Check if response status is OK
        if response.status_code == 200:
            data = response.json()
            
            # Extract memory manager status from components
            components = data.get('components', {})
            memory_status = components.get('memory_manager', 'unknown')
            
            return {
                "status": "OK" if memory_status == "OK" else "ERROR",
                "memory_manager": memory_status,
                "message": "Gateway health check successful" if memory_status == "OK" else f"Memory manager status: {memory_status}"
            }
        else:
            return {
                "status": "ERROR", 
                "memory_manager": "unhealthy",
                "message": f"Gateway returned HTTP {response.status_code}"
            }
            
    except requests.exceptions.Timeout:
        return {
            "status": "TIMEOUT",
            "memory_manager": "timeout", 
            "message": "Gateway health check timed out after 15 seconds"
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "CONNECTION_ERROR",
            "memory_manager": "unreachable",
            "message": "Could not connect to gateway service"
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "memory_manager": "error",
            "message": f"Gateway health check failed: {str(e)}"
        }

@app.get("/api/gateway-prompt-health")
async def check_gateway_prompt_builder():
    """Check Prompt Builder health via gateway"""
    import requests

    try:
        # Get gateway URL from environment or use default
        gateway_url = os.getenv('GATEWAY_URL', 'http://gateway:8003')
        
        # Make request to the prompt builder health endpoint
        response = requests.get(f"{gateway_url}/api/health/prompt", timeout=15)
        
        # Check if response is OK
        if response.status_code == 200:
            data = response.json()
            
            prompt_len = data.get("prompt_length", 0)
            prompt_preview = data.get("prompt_preview", "")
            contains_metrics = bool(data.get("contains_metrics"))
            component_status = data.get("status", "unknown")
            
            return {
                "status": "OK" if component_status == "healthy" and prompt_len > 50 and contains_metrics else "WARN",

                "prompt_length": prompt_len,
                "contains_metrics": contains_metrics,
                "component_status": component_status,
                "message": "Prompt Builder is healthy" if component_status == "healthy" else "Prompt Builder returned limited or degraded response",
                "preview": prompt_preview[:100] + "..." if prompt_preview else "No prompt returned"
            }
        else:
            return {
                "status": "ERROR",
                "message": f"Gateway returned HTTP {response.status_code}",
                "component_status": "unhealthy"
            }

    except requests.exceptions.Timeout:
        return {
            "status": "TIMEOUT",
            "message": "Prompt Builder health check timed out after 15 seconds",
            "component_status": "timeout"
        }

    except requests.exceptions.ConnectionError:
        return {
            "status": "CONNECTION_ERROR",
            "message": "Could not connect to gateway service",
            "component_status": "unreachable"
        }

    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Prompt Builder health check failed: {str(e)}",
            "component_status": "error"
        }

@app.get("/api/gateway-ai-health")
async def check_gateway_ai():
    import requests

    try:
        gateway_url = os.getenv('GATEWAY_URL', 'http://gateway:8003')
        response = requests.get(f"{gateway_url}/api/health/ai", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "OK" if data.get("status") == "healthy" else "WARN",
                "model": data.get("model_used"),
                "latency_ms": data.get("latency_ms"),
                "preview": data.get("response_preview", "")[:100],
                "message": "AI available" if data.get("status") == "healthy" else data.get("message")
            }
        else:
            return {"status": "ERROR", "message": f"AI check failed: HTTP {response.status_code}"}

    except requests.exceptions.Timeout:
        return {"status": "TIMEOUT", "message": "AI request timed out"}
    except Exception as e:
        return {"status": "ERROR", "message": f"AI health check failed: {str(e)}"}

@app.post("/api/agent-heartbeat")
async def receive_agent_heartbeat(request: Request):
    """Receive heartbeat from agents for health monitoring"""
    try:
        heartbeat = await request.json()
        agent_heartbeats[heartbeat["agent_id"]] = {
            **heartbeat,
            "received_at": time.time()
        }
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
