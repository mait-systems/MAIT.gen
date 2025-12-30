#!/usr/bin/env python3
"""
PowertrainAgent Gateway Edition - Local agent using MAIT Prompt Gateway
Version 2.1 - Local Memory construction, statistical analysis.

This agent collects data locally and sends to proprietary gateway for analysis.

"""

import os
import sys
import time
import logging
import yaml
import argparse
import requests
import math
import threading
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from influx_query import InfluxQueryManager, HistoricalSummary
from gateway_client import GatewayClient
from logger import PowertrainLogger

from baseline_calculator import BaselineCalculator
from local_analysis import LocalAnalyzer


@dataclass
class PowertrainMetrics:
    """Current powertrain metrics snapshot"""
    timestamp: datetime
    engine_speed: float
    engine_run_speed: float
    engine_oil_pressure: float
    engine_fuel_pressure: float
    engine_fuel_temperature: float
    engine_fuel_rate: float
    intake_air_temperature: float
    intake_air_pressure: float
    generator_total_real_power: float
    engine_coolant_temperature: float
    load_band: str
    
    def to_dict(self) -> dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'engine_speed': self.engine_speed,
            'engine_run_speed': self.engine_run_speed,
            'engine_oil_pressure': self.engine_oil_pressure,
            'engine_fuel_pressure': self.engine_fuel_pressure,
            'engine_fuel_temperature': self.engine_fuel_temperature,
            'engine_fuel_rate': self.engine_fuel_rate,
            'intake_air_temperature': self.intake_air_temperature,
            'intake_air_pressure': self.intake_air_pressure,
            'generator_total_real_power': self.generator_total_real_power,
            'engine_coolant_temperature': self.engine_coolant_temperature,
            'load_band': self.load_band
        }

class PowertrainAgentGateway:
    """
    Simplified PowertrainAgent that uses gateway for all AI analysis
    Handles data collection and basic monitoring locally
    """
    
    def __init__(self, config_path: str = "generator_config.yaml"):
        """Initialize the Gateway-enabled PowertrainAgent"""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.baseline_calculator = BaselineCalculator(self.config)
        
        # Initialize local managers (data only)
        self.influx_manager = InfluxQueryManager(self.config)
        self.result_logger = PowertrainLogger(self.config)
        
        # Initialize local statistical analyzer
        self.local_analyzer = LocalAnalyzer(self.config, self.influx_manager)
        
        # Initialize gateway client (replaces memory_manager and prompt_builder)
        gateway_config = self.config.copy()
        gateway_config['gateway_url'] = os.getenv('GATEWAY_URL', self.config.get('gateway_url', 'http://localhost:8002'))
        gateway_config['gateway_api_key'] = os.getenv('GATEWAY_API_KEY', self.config.get('gateway_api_key', 'dev-key-123'))
        self.gateway_client = GatewayClient(gateway_config)
        
        # Control and state tracking - read initial AI state from InfluxDB
        self.ai_analysis_enabled = self._read_initial_ai_state()
        self.agent_active = True

        # Initialize AI status and emit a startup heartbeat so the backend sees the agent immediately
        if self.ai_analysis_enabled:
            self.ai_status = "ENABLED"
        else:
            self.ai_status = "DISABLED"
        self._send_startup_heartbeat("ACTIVE")
        
        # AI status tracking with semantic states
        self.last_gateway_success = None
        
        # Analysis frequency (read from environment variable, fallback to 5 minutes)
        try:
            self.analysis_interval_minutes = int(os.getenv('POWERTRAIN_INTERVAL', '5'))
        except (ValueError, TypeError):
            self.logger.warning("Invalid POWERTRAIN_INTERVAL environment variable, using default 5 minutes")
            self.analysis_interval_minutes = 5
        self.config_refresh_counter = 0
        
        # Site identification for gateway
        self.site_id = self.config.get('site_id', 'default-site')
        
        # Start independent health ping thread
        threading.Thread(target=self._health_ping_loop, daemon=True).start()
        
    def _read_initial_ai_state(self) -> bool:
        """Read initial AI enabled state from InfluxDB, fallback to environment variable"""
        self.logger.debug("Reading initial AI enabled state...")
        
        try:
            bucket = self.config['influxdb']['bucket']
            org = self.config['influxdb']['org']
            self.logger.debug(f"Querying InfluxDB for AI state - bucket: {bucket}, org: {org}")
            
            # Query for latest AI enabled setting
            query = f'''
            from(bucket: "{bucket}")
              |> range(start: -7d)
              |> filter(fn: (r) => r._measurement == "ai_global_status" and r._field == "ai_enabled")
              |> last()
            '''
            
            result = self.influx_manager.client.query_api().query(org=org, query=query)
            
            for table in result:
                for record in table.records:
                    ai_enabled = record.get_value()
                    if ai_enabled is not None:
                        self.logger.info(f"Successfully read AI enabled state from InfluxDB: {ai_enabled}")
                        return bool(ai_enabled)
            
            self.logger.info("No AI enabled configuration found in InfluxDB")
                        
        except Exception as e:
            self.logger.warning(f"Could not read AI state from InfluxDB (InfluxDB may not be ready): {str(e)}")
        
        # Fallback to environment variable (default disabled)
        env_ai_enabled = os.getenv('POWERTRAIN_AI_ENABLED', 'false').lower() == 'true'
        self.logger.info(f"Using AI enabled state from environment variable: {env_ai_enabled}")
        return env_ai_enabled

        self.logger.info(f"PowertrainAgent Gateway Edition initialized")
        self.logger.info(f"Gateway URL: {gateway_config['gateway_url']}")
        self.logger.info(f"AI Enabled: {self.ai_analysis_enabled}")
        
        # Set initial AI status based on configuration (no startup gateway tests)
        if self.ai_analysis_enabled:
            self.logger.info("AI analysis enabled - will validate gateway when needed")
            self.ai_status = "ENABLED"
        else:
            self.logger.info("AI analysis disabled - running in local mode only")
            self.ai_status = "DISABLED"
        
        # Send immediate startup heartbeat to show agent status
        self._send_startup_heartbeat("ACTIVE")
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            return config
        except Exception as e:
            print(f"Error loading config: {e}")
            sys.exit(1)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging_config = self.config.get('logging', {})
        log_level = getattr(logging, logging_config.get('level', 'INFO'))
        log_file = logging_config.get('filename', 'powertrain_agent_gateway.log')
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        return logging.getLogger('PowertrainAgentGateway')
    
    def _refresh_config_from_influxdb(self):
        """Refresh frequency and AI settings from InfluxDB config"""
        try:
            bucket = self.config['influxdb']['bucket']
            org = self.config['influxdb']['org']
            
            # Query for both AI settings from ai_global_status
            config_query = f'''
            from(bucket: "{bucket}")
              |> range(start: -7d)
              |> filter(fn: (r) => r._measurement == "ai_global_status" and (r._field == "ai_enabled" or r._field == "analysis_frequency"))
              |> last()
            '''
            
            config_result = self.influx_manager.client.query_api().query(org=org, query=config_query)
            
            for table in config_result:
                for record in table.records:
                    field = record.get_field()
                    value = record.get_value()
                    
                    if field == "analysis_frequency" and value:
                        try:
                            frequency_int = int(value)
                            if frequency_int != self.analysis_interval_minutes:
                                self.logger.info(f"Updated analysis frequency from {self.analysis_interval_minutes} to {frequency_int} minutes")
                                self.analysis_interval_minutes = frequency_int
                        except (ValueError, TypeError):
                            pass  # Keep current frequency on conversion error
                    
                    elif field == "ai_enabled" and value is not None:
                        new_ai_enabled = bool(value)
                        if new_ai_enabled != self.ai_analysis_enabled:
                            self.logger.info(f"AI analysis setting changed from {self.ai_analysis_enabled} to {new_ai_enabled}")
                            old_ai_enabled = self.ai_analysis_enabled
                            self.ai_analysis_enabled = new_ai_enabled
                            
                            # Update AI status based on global setting
                            if new_ai_enabled:
                                self.ai_status = "ENABLED"
                                self.logger.info("AI analysis enabled")
                            else:
                                self.ai_status = "DISABLED"
                                self.logger.info("AI analysis disabled")
                        
        except Exception as e:
            self.logger.debug(f"Could not refresh config from InfluxDB: {str(e)}")
      
    def _get_live_data_from_api(self) -> Optional[Dict[str, float]]:
        """Get live data from backend API instead of direct InfluxDB queries"""
        try:
            backend_base = os.getenv('BACKEND_URL', 'http://backend:8001')
            backend_url = f"{backend_base.rstrip('/')}/api/live-stats"
            response = requests.get(backend_url, timeout=10)
            response.raise_for_status()
            
            live_data = response.json()
            self.logger.debug(f"Retrieved live data from backend API: {len(live_data)} metrics")
            return live_data
            
        except requests.exceptions.Timeout:
            self.logger.error("Backend API request timed out")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get live data from backend API: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error processing backend API response: {e}")
            return None

    def get_current_metrics(self) -> Optional[PowertrainMetrics]:
        """Get current powertrain metrics from backend API"""

        def _safe_number(val, default=0.0):
            """Coerce to float when possible; return default on None/NaN/non-numeric."""
            try:
                num = float(val)
                if math.isnan(num):
                    return default
                return num
            except (TypeError, ValueError):
                return default

        try:
            live_data = self._get_live_data_from_api()
            
            if not live_data:
                self.logger.warning("No live data available from backend API")
                return None
            
            # Handle potential NaN/non-numeric values with proper fallbacks
            engine_speed = _safe_number(live_data.get('Engine_Speed', 0))
            
            # Calculate load band locally with engine state awareness
            power_output = _safe_number(live_data.get('Generator_Total_Real_Power', 0))
            load_band = self._calculate_load_band(power_output, engine_speed, live_data.get('Genset_kW_Rating', 150))
            
            engine_run_speed = _safe_number(live_data.get('Engine_Run_Speed', 0))
            engine_oil_pressure = _safe_number(live_data.get('Engine_Oil_Pressure', 0))
            engine_fuel_pressure = _safe_number(live_data.get('Engine_Fuel_Pressure', 0))
            engine_fuel_temperature = _safe_number(live_data.get('Engine_Fuel_Temperature', 0))
            engine_fuel_rate = _safe_number(live_data.get('Engine_Fuel_Rate', 0))
            intake_air_temperature = _safe_number(live_data.get('Intake_Air_Temperature', 0))
            intake_air_pressure = _safe_number(live_data.get('Intake_Air_Pressure', 0))
            engine_coolant_temperature = _safe_number(live_data.get('Engine_Coolant_Temperature', 0))
            
            metrics = PowertrainMetrics(
                timestamp=datetime.now(),
                engine_speed=engine_speed,
                engine_run_speed=engine_run_speed,
                engine_oil_pressure=engine_oil_pressure,
                engine_fuel_pressure=engine_fuel_pressure,
                engine_fuel_temperature=engine_fuel_temperature,
                engine_fuel_rate=engine_fuel_rate,
                intake_air_temperature=intake_air_temperature,
                intake_air_pressure=intake_air_pressure,
                generator_total_real_power=power_output,
                engine_coolant_temperature=engine_coolant_temperature,
                load_band=load_band
            )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error getting current metrics: {str(e)}")
            return None
    
    def run_analysis(self) -> Optional[Dict[str, Any]]:
        """
        Main analysis method
        """
        try:
            # Get current metrics
            current_metrics = self.get_current_metrics()
            if not current_metrics:
                self.logger.error("Cannot run analysis without current metrics")
                return None
            
            # Check engine state - immediate pause/resume logic (regardless of AI state)
            engine_speed = current_metrics.engine_speed
            self.logger.info(f"Engine speed: {engine_speed}, agent_active: {self.agent_active}")
            
            if engine_speed == 0 or math.isnan(engine_speed):
                # Engine stopped or invalid data - pause agent immediately
                if self.agent_active:
                    self.logger.info(f"Engine stopped (speed: {engine_speed}) - pausing agent immediately")
                    self.agent_active = False
                    return None
            else:
                # Engine running - ensure agent is active and baselines are current for this load band
                required_band = current_metrics.load_band if current_metrics.load_band else None

                if not self.agent_active:
                    self.logger.info(f"Engine activity detected (speed: {engine_speed}) - resuming agent")
                    self.agent_active = True
                    try:
                        self.logger.info("Agent resumed - checking baseline status")
                        self._check_and_update_baselines(required_band)
                    except Exception as e:
                        self.logger.warning(f"Baseline check failed during resume: {e}")
                else:
                    try:
                        self._check_and_update_baselines(required_band)
                    except Exception as e:
                        self.logger.warning(f"Baseline check failed during analysis: {e}")
                                
            # ALWAYS run local analysis first
            local_analysis = self.local_analyzer.analyze_metrics(current_metrics)
            local_alerts = local_analysis.get('alerts', [])
            local_insights = local_analysis.get('insights', [])

            if local_insights:
                formatted_insights = "\n- ".join(local_insights)
                self.logger.info(f"Local analysis insights:\n- {formatted_insights}")
            
            # Store local analysis with LOCAL tag
            agent_state = self._get_current_agent_state(current_metrics)
            local_storage = {
                'timestamp': current_metrics.timestamp,
                'current_metrics': current_metrics.to_dict(),
                'memory_context': {},
                'ai_analysis': str(local_analysis.get('analysis', [])),
                'analysis_summary': f"Local analysis - {local_analysis.get('mode', 'LOCAL')}",
                'alert_level': local_analysis.get('alert_level', 'INFO'),
                'recommendations': local_analysis.get('insights', []),
                'alerts': local_alerts,
                'agent_state': agent_state,
                'ai_enabled': self.ai_analysis_enabled,
                'analysis_type': 'LOCAL',  # New tag
                'mode': 'LOCAL',
                'heartbeat': False
            }
            self.result_logger.store_analysis_result(local_storage)
            
            # Try gateway AI analysis if enabled
            gateway_analysis = None
            if self.ai_analysis_enabled:
                self.logger.info("Attempting gateway AI analysis")
                try:
                    gateway_analysis = self.gateway_client.analyze(
                        metrics=current_metrics.to_dict(),
                        site_id=self.site_id,
                        ai_enabled=self.ai_analysis_enabled
                    )
                    
                    # Store gateway analysis with GATEWAY tag if successful
                    if gateway_analysis:
                        gateway_summary = gateway_analysis.get('analysis_summary')
                        if not gateway_summary:
                            analysis_list = gateway_analysis.get('analysis') or []
                            if isinstance(analysis_list, list) and analysis_list:
                                gateway_summary = analysis_list[0]
                        gateway_summary = gateway_summary or "Gateway AI analysis"

                        alert_level = gateway_analysis.get('alert_level')
                        if not alert_level:
                            alerts = gateway_analysis.get('alerts') or []
                            severity_priority = ['CRITICAL', 'WARNING', 'INFO']
                            for sev in severity_priority:
                                if any((alert.get('severity') or '').upper() == sev for alert in alerts):
                                    alert_level = sev
                                    break
                            if not alert_level:
                                alert_level = 'INFO'

                        gateway_storage = {
                            'timestamp': current_metrics.timestamp,
                            'current_metrics': current_metrics.to_dict(),
                            'memory_context': {},
                            'ai_analysis': gateway_summary,
                            'analysis_summary': gateway_summary,
                            'alert_level': alert_level,
                            'recommendations': gateway_analysis.get('recommendations', []),
                            'alerts': gateway_analysis.get('alerts', []),
                            'analysis_sections': gateway_analysis.get('analysis_sections'),
                            'agent_state': agent_state,
                            'ai_enabled': True,
                            'analysis_type': 'GATEWAY',
                            'mode': 'AI',
                            'heartbeat': False
                        }
                        self.result_logger.store_analysis_result(gateway_storage)
                        
                        # Update AI status on success
                        self.ai_status = "ENABLED"
                        self.last_gateway_success = datetime.now()
                        self.logger.info("Gateway analysis successful - AI status: ENABLED")
                        
                except Exception as e:
                    self.logger.warning(f"Gateway analysis failed: {e}")
                    self.ai_status = "ENABLED"  # Keep trying
            else:
                self.ai_status = "DISABLED"  # AI disabled
            
            # Return local analysis for compatibility
            analysis_result = local_analysis
            self.logger.info(f"Analysis cycle completed - Local: {local_analysis.get('mode', 'LOCAL')}, Gateway: {'SUCCESS' if gateway_analysis else 'SKIPPED/FAILED'}")
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {str(e)}")
            return {
                "analysis": ["Analysis system error"],
                "alerts": [{"level": "CRITICAL", "message": f"Analysis failed: {str(e)}", "analysis_type": "system_error"}],
                "insights": ["Analysis system unavailable"],
                "mode": "ERROR",
                "alert_level": "CRITICAL",
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_current_agent_state(self, current_metrics: PowertrainMetrics) -> str:
        """Determine the current agent state - simplified binary logic"""
        if not self.agent_active:
            return "PAUSED"
        else:
            return "ACTIVE"


    def _send_startup_heartbeat(self, state: str = "ACTIVE"):
        """Send startup heartbeat to show agent status immediately"""
        try:
            # Get minimal data for startup heartbeat (may not be available yet)
            live_data = {}
            try:
                live_data = self._get_live_data_from_api()
                if not live_data:
                    live_data = {}
            except Exception:
                # Backend API might not be ready yet, use defaults
                live_data = {}
            
            # Create minimal metrics for startup heartbeat
            startup_metrics = PowertrainMetrics(
                timestamp=datetime.now(),
                engine_speed=live_data.get('Engine_Speed', 0),
                engine_run_speed=live_data.get('Engine_Run_Speed', 0),
                engine_oil_pressure=live_data.get('Engine_Oil_Pressure', 0),
                engine_fuel_pressure=live_data.get('Engine_Fuel_Pressure', 0),
                engine_fuel_temperature=live_data.get('Engine_Fuel_Temperature', 0),
                engine_fuel_rate=live_data.get('Engine_Fuel_Rate', 0),
                intake_air_temperature=live_data.get('Intake_Air_Temperature', 0),
                intake_air_pressure=live_data.get('Intake_Air_Pressure', 0),
                generator_total_real_power=live_data.get('Generator_Total_Real_Power', 0),
                engine_coolant_temperature=live_data.get('Engine_Coolant_Temperature', 0),
                load_band=self._calculate_load_band(live_data.get('Generator_Total_Real_Power', 0), live_data.get('Engine_Speed', 0), live_data.get('Genset_kW_Rating', 150))
            )
            
            # Create startup status message based on state
            if state == "ACTIVE":
                ai_status_desc = "LOCAL MODE" if self.ai_status == "DISABLED" else self.ai_status
                status_message = f"PowertrainAgent initialized successfully. AI Status: {ai_status_desc}. Ready to begin analysis cycles."
                analysis_summary = "AGENT ACTIVE"
            elif state == "PAUSED":
                status_message = "PowertrainAgent is paused - monitoring for engine activity to resume analysis."
                analysis_summary = "AGENT PAUSED"
            elif state == "OFFLINE":
                status_message = "PowertrainAgent is offline - unable to connect to required services."
                analysis_summary = "AGENT OFFLINE"
            else:
                status_message = f"PowertrainAgent status update: {state}"
                analysis_summary = f"AGENT {state}"
            
            # Create startup heartbeat result with proper format
            startup_result = {
                'timestamp': startup_metrics.timestamp,
                'current_metrics': startup_metrics.to_dict(),
                'memory_context': {},
                'ai_analysis': status_message,
                'analysis_summary': analysis_summary,
                'alert_level': 'HEARTBEAT', # chose this label so it gets ignored by the frontend and will not be displayed anywhere
                'recommendations': [],
                'agent_state': state,
                'ai_enabled': self.ai_analysis_enabled,
                'analysis_type': 'LOCAL',
                'heartbeat': True
            }         
        
            # Store startup heartbeat
            self.result_logger.store_analysis_result(startup_result)
            self.logger.info(f"Startup heartbeat sent - agent state: {state}, AI status: {self.ai_status}")
            
        except Exception as e:
            self.logger.error(f"Failed to send startup heartbeat: {e}")

    def _send_heartbeat(self):
        """Send heartbeat when agent is paused to communicate state"""
        try:
            # AI activation logic - activate if enabled but not yet online
            if (self.ai_analysis_enabled and 
                self.ai_status == "DISABLED" and 
                self.agent_active is not None):  # Only if agent operational (not OFFLINE)
                self.logger.info("AI enabled while paused - updating status")
                self.ai_status = "ENABLED"
            
            
            # Get minimal data for heartbeat
            live_data = self._get_live_data_from_api()
            if not live_data:
                live_data = {}
            
            # Create minimal metrics for heartbeat
            heartbeat_metrics = PowertrainMetrics(
                timestamp=datetime.now(),
                engine_speed=live_data.get('Engine_Speed', 0),
                engine_run_speed=live_data.get('Engine_Run_Speed', 0),
                engine_oil_pressure=live_data.get('Engine_Oil_Pressure', 0),
                engine_fuel_pressure=live_data.get('Engine_Fuel_Pressure', 0),
                engine_fuel_temperature=live_data.get('Engine_Fuel_Temperature', 0),
                engine_fuel_rate=live_data.get('Engine_Fuel_Rate', 0),
                intake_air_temperature=live_data.get('Intake_Air_Temperature', 0),
                intake_air_pressure=live_data.get('Intake_Air_Pressure', 0),
                generator_total_real_power=live_data.get('Generator_Total_Real_Power', 0),
                engine_coolant_temperature=live_data.get('Engine_Coolant_Temperature', 0),
                load_band=self._calculate_load_band(live_data.get('Generator_Total_Real_Power', 0), live_data.get('Engine_Speed', 0), live_data.get('Genset_kW_Rating', 150))
            )
            
            # Create heartbeat analysis result with proper format
            heartbeat_result = {
                'timestamp': heartbeat_metrics.timestamp,
                'current_metrics': heartbeat_metrics.to_dict(),
                'memory_context': {},
                'ai_analysis': 'PowertrainAgent is paused due to engine stopped. Monitoring for engine activity to resume analysis.',
                'analysis_summary': 'AGENT PAUSED - monitoring for engine activity',
                'alert_level': 'HEARTBEAT', # chose this label so it gets ignored by the frontend and will not be displayed anywhere
                'recommendations': [],
                'agent_state': 'PAUSED',
                'ai_enabled': self.ai_analysis_enabled,
                'analysis_type': 'LOCAL',
                'heartbeat': True
            }
            
            # Store heartbeat
            self.result_logger.store_analysis_result(heartbeat_result)
            self.logger.debug("Heartbeat sent - agent state: PAUSED")
            
        except Exception as e:
            self.logger.error(f"Failed to send heartbeat: {e}")
    
    def _calculate_load_band(self, power_output: float, engine_speed: float = 0, rated_power: float = 150) -> str:
        """Calculate load band treating input power as percentage of rating."""
        if engine_speed < 100:
            return "0%"

        try:
            raw_output = float(power_output or 0)
        except (TypeError, ValueError):
            raw_output = 0.0

        load_percentage = raw_output
        if load_percentage > 125:
            if load_percentage <= 12500:
                load_percentage = load_percentage / 100
            elif rated_power > 0:
                load_percentage = (raw_output / rated_power) * 100

        if load_percentage < 20:
            return "0-20%"
        if load_percentage < 40:
            return "20-40%"
        if load_percentage < 60:
            return "40-60%"
        if load_percentage < 80:
            return "60-80%"
        return "80-100%"
    
    def _health_ping_loop(self):
        """Independent health ping every 10 seconds"""
        while True:
            try:
                backend_url = os.getenv('BACKEND_URL', 'http://localhost:8001')
                requests.post(f"{backend_url}/api/agent-heartbeat", json={
                    "agent_id": "powertrain-agent",
                    "agent_state": "PAUSED" if not self.agent_active else "ACTIVE",
                    "ai_status": self.ai_status,
                    "timestamp": datetime.now().isoformat()
                }, timeout=2)
            except Exception as e:
                self.logger.error(f"Heartbeat post failed: {e}")
            
            time.sleep(10)  # Always 10 seconds

    # Agent fetches data from Influx and calls baseline_calculator to calculate the baselines + write them into the db
    def recalculate_all_baselines(self, days_back: int = 30) -> int:
        """Recalculate baselines using BaselineCalculator"""
        try:
            self.logger.info(f"Starting baseline recalculation for last {days_back} days")

            # Get historical data with load_band classification
            historical_data = self.influx_manager.get_all_historical_data(days_back)

            if historical_data is None or historical_data.empty:
                self.logger.warning("No historical data available")
                return 0

            # Use BaselineCalculator for comprehensive analysis
            baselines = self.baseline_calculator.calculate_load_band_baselines(
                historical_data, self.influx_manager, days_back
            )

            self.logger.info(f"Baseline recalculation completed: {len(baselines)} baselines created")
            return len(baselines)

        except Exception as e:
            self.logger.error(f"Failed to recalculate baselines: {e}")
            return 0


    # 3 Methods to check whether the memory exists, if it does, how old is it, if there is no memory
    # or the memory is too old, recalculate the baselines with baseline_calculator and write in influx

    def _baseline_status_exists(self) -> bool:
        """Check if baseline status exists in InfluxDB"""
        try:
            query = f'''
            from(bucket: "{self.config['influxdb']['bucket']}")
              |> range(start: -30d)
              |> filter(fn: (r) => r._measurement == "powertrain_system_status")
              |> last()
            '''
            result = self.influx_manager.client.query_api().query(query=query, org=self.config['influxdb']['org'])
            return len(list(result)) > 0
        except Exception as e:
            self.logger.error(f"Failed to check baseline status: {e}")
            return False
    
    def _get_baseline_age_days(self) -> int:
        """Get age of baselines in days"""
        try:
            query = f'''
            from(bucket: "{self.config['influxdb']['bucket']}")
              |> range(start: -30d)
              |> filter(fn: (r) => r._measurement == "powertrain_system_status" and r._field == "bootstrap_timestamp")
              |> last()
            '''
            result = self.influx_manager.client.query_api().query(query=query, org=self.config['influxdb']['org'])
            
            for table in result:
                for record in table.records:
                    bootstrap_time = record.get_value()
                    if bootstrap_time:
                        if isinstance(bootstrap_time, str):
                            bootstrap_dt = datetime.fromisoformat(bootstrap_time.replace('Z', '+00:00'))
                        else:
                            bootstrap_dt = bootstrap_time
                        age_days = (datetime.now(bootstrap_dt.tzinfo) - bootstrap_dt).days
                        return age_days
            return 999  # Very old if not found
        except Exception as e:
            self.logger.error(f"Failed to get baseline age: {e}")
            return 999

    def _check_and_update_baselines(self, required_load_band: Optional[str] = None):
        """Check baseline status and update if needed."""
        try:
            # 1. First boot check
            if not self._baseline_status_exists():
                self.logger.info("No baseline status found - initial system setup")
                self.recalculate_all_baselines()
                return

            # 2. Age check
            baseline_age_days = self._get_baseline_age_days()
            if baseline_age_days > 7:
                self.logger.info(f"Baselines are {baseline_age_days} days old - recalculating")
                self.recalculate_all_baselines()
                return

            # 3. Ensure the current load band has coverage
            if required_load_band and self._band_needs_baseline(required_load_band):
                self.logger.info(
                    "Recalculating baseline for active load band %s",
                    required_load_band
                )
                self._recalculate_baseline_for_band(required_load_band)
                return

            # 4. All good
            self.logger.info(f"Baselines are current ({baseline_age_days} days old)")

        except Exception as e:
            self.logger.error(f"Failed to check and update baselines: {e}")

    def _band_needs_baseline(self, load_band: str) -> bool:
        """Return True if the specified load band lacks a usable baseline."""
        try:
            baselines = self.influx_manager.get_latest_baselines(load_band)
            if not baselines:
                self.logger.info("No baseline found for load band %s", load_band)
                return True

            baseline = baselines[0]
            try:
                zero_fields = (
                    float(baseline.avg_engine_speed) == 0.0 and
                    float(baseline.avg_oil_pressure) == 0.0 and
                    float(baseline.avg_power_output) == 0.0 and
                    float(baseline.sample_count) == 0
                )
            except Exception:
                zero_fields = False

            if zero_fields:
                self.logger.info(
                    "Baseline for load band %s contains only placeholder values",
                    load_band
                )
                return True

            return False

        except Exception as e:
            self.logger.warning(
                "Baseline lookup failed for load band %s: %s", load_band, e
            )
            return True

    def _recalculate_baseline_for_band(self, load_band: str, days_back: int = 30) -> int:
        """Recalculate baseline for a single load band using recent history."""
        try:
            historical_data = self.influx_manager.get_historical_data_for_band(load_band, days_back)
            if historical_data is None or historical_data.empty:
                self.logger.warning(
                    "Cannot recalculate baseline for %s - no historical data available",
                    load_band
                )
                return 0

            baselines = self.baseline_calculator.calculate_load_band_baselines(
                historical_data,
                self.influx_manager,
                days_back,
                preserve_existing=False
            )

            created = sum(1 for baseline in baselines if baseline.load_band == load_band)
            self.logger.info(
                "Recalculated baseline for load band %s (created %s entries)",
                load_band,
                created
            )
            return created

        except Exception as e:
            self.logger.error(
                "Failed to recalculate baseline for load band %s: %s",
                load_band,
                e
            )
            return 0

    def run(self):
        """Main agent run loop"""
        self.logger.info("Starting PowertrainAgent Gateway Edition main loop")
        
        last_heartbeat = datetime.now()
        heartbeat_interval = 10  # Send heartbeat every 10 seconds when paused
        
        try:
            while True:
                if not self.agent_active:
                    # Agent is paused, check for engine activity and send heartbeat
                    self.logger.info("Agent paused - waiting for engine activity...")
                    
                    # Refresh configuration every heartbeat to detect AI toggle changes immediately
                    self._refresh_config_from_influxdb()
                    
                    # Send heartbeat if enough time has passed
                    if (datetime.now() - last_heartbeat).total_seconds() > heartbeat_interval:
                        self._send_heartbeat()
                        last_heartbeat = datetime.now()
                    
                    time.sleep(10)  # Check every 10 seconds when paused
                    
                    # Quick check for engine activity
                    live_data = self._get_live_data_from_api()
                    if live_data:
                        engine_speed = live_data.get('Engine_Speed', 0)
                        if not math.isnan(engine_speed) and engine_speed > 0:
                            self.logger.info(f"Engine activity detected (speed: {engine_speed}) - resuming agent")
                            self.agent_active = True
                    continue
                
                # Refresh configuration periodically
                self.config_refresh_counter += 1
                if self.config_refresh_counter >= 1:  # Every cycle
                    self._refresh_config_from_influxdb()
                    self.config_refresh_counter = 0
                
                # Run analysis
                start_time = time.time()
                analysis_result = self.run_analysis()
                end_time = time.time()
                
                # Check if agent was paused during analysis
                if not self.agent_active:
                    self.logger.info("Agent paused during analysis - entering pause mode")
                    continue  # Go back to paused mode loop
                
                if analysis_result:
                    cycle_time = end_time - start_time
                    self.logger.info(f"Analysis cycle completed in {cycle_time:.2f}s - Mode: {analysis_result.get('mode', 'UNKNOWN')}")
                else:
                    self.logger.warning("Analysis cycle failed")
                
                # Sleep until next analysis
                sleep_time = self.analysis_interval_minutes * 60
                self.logger.info(f"Sleeping for {sleep_time/60:.1f} minutes until next analysis")
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            self.logger.info("Agent stopped by user")
        except Exception as e:
            self.logger.error(f"Agent error: {str(e)}")
        finally:
            self.logger.info("PowertrainAgent Gateway Edition stopped")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='PowertrainAgent Gateway Edition')
    parser.add_argument('--config', default='generator_config.yaml', help='Configuration file path')
    parser.add_argument('--single-run', action='store_true', help='Run single analysis and exit')
    
    args = parser.parse_args()
    
    try:
        agent = PowertrainAgentGateway(args.config)
        
        if args.single_run:
            print("Running single analysis...")
            result = agent.run_analysis()
            if result:
                print(f"Analysis completed - Mode: {result.get('mode', 'UNKNOWN')}")
                print(f"Analysis: {result.get('analysis', [])[:2]}")  # First 2 items
            else:
                print("Analysis failed")
        else:
            agent.run()
            
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
