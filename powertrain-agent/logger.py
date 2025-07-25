#!/usr/bin/env python3
"""
PowertrainLogger - Results storage and logging for PowertrainAgent
Handles storage of analysis results, alerts, and system logs
"""

import json
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
from influxdb_client import Point

from influx_query import InfluxQueryManager

class PowertrainLogger:
    """
    Handles logging and storage of PowertrainAgent results including:
    - Analysis results storage
    - Alert management
    - Performance tracking
    - System health logging
    """
    
    def __init__(self, config: dict):
        """Initialize logger with InfluxDB connection"""
        self.config = config
        self.influx_manager = InfluxQueryManager(config)
        self.logger = logging.getLogger('PowertrainLogger')
        
        # Alert thresholds
        self.alert_config = {
            'oil_pressure_critical': 150,    # kPa
            'oil_pressure_warning': 250,     # kPa
            'rpm_deviation_warning': 50,     # RPM
            'rpm_deviation_critical': 100,   # RPM
            'consecutive_warnings': 3,       # Number before escalation
            'consecutive_criticals': 2       # Number before shutdown alert
        }
        
        # Performance tracking
        self.analysis_count = 0
        self.alert_count = {'OK': 0, 'INFO': 0, 'WARNING': 0, 'CRITICAL': 0, 'ERROR': 0}
        
        self.logger.info("PowertrainLogger initialized")
    
    def store_analysis_result(self, analysis_result: Dict[str, Any]) -> bool:
        """
        Store complete analysis result in InfluxDB
        
        Args:
            analysis_result: Dictionary containing full analysis data
            
        Returns:
            True if storage successful
        """
        try:
            # Handle timestamp - could be string or datetime object
            timestamp_value = analysis_result['timestamp']
            if isinstance(timestamp_value, str):
                timestamp = datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
            elif isinstance(timestamp_value, datetime):
                timestamp = timestamp_value
            else:
                timestamp = datetime.now()
            
            current_metrics = analysis_result.get('current_metrics', {})
            alert_level = analysis_result.get('alert_level', 'INFO')
            
            # Store main analysis result
            point = Point("powertrain_analysis") \
                .tag("load_band", current_metrics.get('load_band', 'unknown')) \
                .tag("alert_level", alert_level) \
                .field("engine_speed", current_metrics.get('engine_speed', 0)) \
                .field("engine_run_speed", current_metrics.get('engine_run_speed', 0)) \
                .field("engine_oil_pressure", current_metrics.get('engine_oil_pressure', 0)) \
                .field("generator_power", current_metrics.get('generator_total_real_power', 0)) \
                .field("coolant_temperature", current_metrics.get('engine_coolant_temperature', 0)) \
                .field("ai_analysis", analysis_result.get('ai_analysis', '')) \
                .field("analysis_summary", self._extract_summary(analysis_result.get('ai_analysis', ''))) \
                .time(timestamp)
            
            self.influx_manager.write_api.write(
                bucket=self.influx_manager.bucket,
                org=self.influx_manager.org,
                record=point
            )
            
            # Store recommendations separately if they exist
            recommendations = analysis_result.get('recommendations', [])
            if recommendations:
                self._store_recommendations(recommendations, timestamp, alert_level)
            
            # Update performance tracking
            self.analysis_count += 1
            self.alert_count[alert_level] = self.alert_count.get(alert_level, 0) + 1
            
            self.logger.info(f"Stored analysis result with alert level: {alert_level}")
            
            # Handle alerts based on severity
            self._process_alert(analysis_result)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store analysis result: {e}")
            return False
    
    def _store_recommendations(self, recommendations: List[str], timestamp: datetime, alert_level: str):
        """Store recommendations as separate records"""
        try:
            for i, recommendation in enumerate(recommendations):
                point = Point("powertrain_recommendations") \
                    .tag("alert_level", alert_level) \
                    .tag("priority", str(i + 1)) \
                    .field("recommendation", recommendation) \
                    .field("status", "pending") \
                    .time(timestamp)
                
                self.influx_manager.write_api.write(
                    bucket=self.influx_manager.bucket,
                    org=self.influx_manager.org,
                    record=point
                )
                
        except Exception as e:
            self.logger.error(f"Failed to store recommendations: {e}")
    
    def _extract_summary(self, ai_analysis: str) -> str:
        """Extract a brief summary from AI analysis"""
        try:
            lines = ai_analysis.split('\n')
            for line in lines:
                line = line.strip()
                if 'POWERTRAIN HEALTH SUMMARY' in line.upper():
                    # Get the next non-empty line
                    idx = lines.index(line)
                    for i in range(idx + 1, min(idx + 5, len(lines))):
                        next_line = lines[i].strip()
                        if next_line and not next_line.startswith('#'):
                            return next_line[:200]  # Truncate to 200 chars
            
            # Fallback: use first meaningful line
            for line in lines[:10]:
                line = line.strip()
                if len(line) > 20 and not line.startswith('#'):
                    return line[:200]
            
            return "Analysis completed"
            
        except Exception:
            return "Summary extraction failed"
    
    def _process_alert(self, analysis_result: Dict[str, Any]):
        """Process alerts based on analysis results"""
        try:
            alert_level = analysis_result.get('alert_level', 'INFO')
            current_metrics = analysis_result.get('current_metrics', {})
            
            if alert_level in ['WARNING', 'CRITICAL']:
                self._create_alert_record(analysis_result)
                
                # Check for consecutive alerts
                self._check_consecutive_alerts(alert_level)
                
                # Check specific metric thresholds
                self._check_metric_thresholds(current_metrics, alert_level)
                
        except Exception as e:
            self.logger.error(f"Alert processing failed: {e}")
    
    def _create_alert_record(self, analysis_result: Dict[str, Any]):
        """Create alert record in InfluxDB"""
        try:
            timestamp = datetime.fromisoformat(analysis_result['timestamp'])
            alert_level = analysis_result.get('alert_level', 'INFO')
            current_metrics = analysis_result.get('current_metrics', {})
            
            # Extract key alert information
            alert_description = self._generate_alert_description(analysis_result)
            
            point = Point("powertrain_alerts") \
                .tag("severity", alert_level) \
                .tag("load_band", current_metrics.get('load_band', 'unknown')) \
                .tag("alert_type", "powertrain_analysis") \
                .field("description", alert_description) \
                .field("oil_pressure", current_metrics.get('engine_oil_pressure', 0)) \
                .field("engine_speed", current_metrics.get('engine_speed', 0)) \
                .field("power_output", current_metrics.get('generator_total_real_power', 0)) \
                .field("resolved", False) \
                .time(timestamp)
            
            self.influx_manager.write_api.write(
                bucket=self.influx_manager.bucket,
                org=self.influx_manager.org,
                record=point
            )
            
            self.logger.warning(f"Created {alert_level} alert: {alert_description}")
            
        except Exception as e:
            self.logger.error(f"Failed to create alert record: {e}")
    
    def _generate_alert_description(self, analysis_result: Dict[str, Any]) -> str:
        """Generate human-readable alert description"""
        try:
            alert_level = analysis_result.get('alert_level', 'INFO')
            current_metrics = analysis_result.get('current_metrics', {})
            ai_analysis = analysis_result.get('ai_analysis', '')
            
            # Extract key metrics
            oil_pressure = current_metrics.get('engine_oil_pressure', 0)
            engine_speed = current_metrics.get('engine_speed', 0)
            power_output = current_metrics.get('generator_total_real_power', 0)
            load_band = current_metrics.get('load_band', 'unknown')
            
            # Check specific conditions
            if oil_pressure < self.alert_config['oil_pressure_critical']:
                return f"Critical: Oil pressure {oil_pressure:.1f} kPa below safe threshold ({load_band} load)"
            elif oil_pressure < self.alert_config['oil_pressure_warning']:
                return f"Warning: Low oil pressure {oil_pressure:.1f} kPa detected ({load_band} load)"
            
            # Check RPM deviation
            run_speed = current_metrics.get('engine_run_speed', engine_speed)
            rpm_deviation = abs(engine_speed - run_speed)
            if rpm_deviation > self.alert_config['rpm_deviation_critical']:
                return f"Critical: Engine speed deviation {rpm_deviation:.1f} RPM from target"
            elif rpm_deviation > self.alert_config['rpm_deviation_warning']:
                return f"Warning: Engine speed deviation {rpm_deviation:.1f} RPM from target"
            
            # Fallback to AI analysis summary
            summary = self._extract_summary(ai_analysis)
            return f"{alert_level}: {summary}"
            
        except Exception:
            return f"{alert_level}: Powertrain analysis alert"
    
    def _check_consecutive_alerts(self, current_alert_level: str):
        """Check for consecutive alerts and escalate if needed"""
        try:
            # This would query recent alerts to check for patterns
            # For now, just log the occurrence
            if current_alert_level == 'CRITICAL':
                self.logger.critical("CRITICAL alert generated - immediate attention required")
            elif current_alert_level == 'WARNING':
                self.logger.warning("WARNING alert generated - monitor closely")
                
        except Exception as e:
            self.logger.error(f"Consecutive alert check failed: {e}")
    
    def _check_metric_thresholds(self, metrics: Dict[str, Any], alert_level: str):
        """Check individual metric thresholds"""
        try:
            oil_pressure = metrics.get('engine_oil_pressure', 0)
            
            # Oil pressure checks
            if oil_pressure < self.alert_config['oil_pressure_critical']:
                self.logger.critical(f"Oil pressure CRITICAL: {oil_pressure:.1f} kPa")
                # Could trigger external alerts here
            elif oil_pressure < self.alert_config['oil_pressure_warning']:
                self.logger.warning(f"Oil pressure WARNING: {oil_pressure:.1f} kPa")
                
        except Exception as e:
            self.logger.error(f"Metric threshold check failed: {e}")
    
    def get_recent_alerts(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """
        Get recent alerts for monitoring
        
        Args:
            hours_back: Hours to look back for alerts
            
        Returns:
            List of alert dictionaries
        """
        try:
            query = f'''
            from(bucket: "{self.influx_manager.bucket}")
              |> range(start: -{hours_back}h)
              |> filter(fn: (r) => r._measurement == "powertrain_alerts")
              |> sort(columns: ["_time"], desc: true)
              |> limit(n: 50)
            '''
            
            result = self.influx_manager.query_api.query_data_frame(
                org=self.influx_manager.org, query=query
            )
            
            if isinstance(result, list):
                result = pd.concat(result, ignore_index=True)
                
            if result.empty:
                return []
            
            alerts = []
            for _, row in result.iterrows():
                alert = {
                    'timestamp': pd.to_datetime(row['_time']).isoformat(),
                    'severity': row.get('severity', 'INFO'),
                    'description': row.get('description', ''),
                    'load_band': row.get('load_band', 'unknown'),
                    'oil_pressure': row.get('oil_pressure', 0),
                    'engine_speed': row.get('engine_speed', 0),
                    'resolved': row.get('resolved', False)
                }
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Failed to get recent alerts: {e}")
            return []
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get PowertrainAgent performance statistics"""
        try:
            return {
                'total_analyses': self.analysis_count,
                'alert_breakdown': self.alert_count.copy(),
                'uptime': 'Running',  # Would calculate actual uptime
                'last_analysis': datetime.now().isoformat(),
                'system_health': 'Operational'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get performance stats: {e}")
            return {'error': str(e)}
    
    def log_system_event(self, event_type: str, message: str, severity: str = 'INFO'):
        """
        Log system events for monitoring
        
        Args:
            event_type: Type of event (startup, shutdown, error, etc.)
            message: Event message
            severity: Event severity level
        """
        try:
            point = Point("powertrain_system_events") \
                .tag("event_type", event_type) \
                .tag("severity", severity) \
                .field("message", message) \
                .field("system_status", "running") \
                .time(datetime.now())
            
            self.influx_manager.write_api.write(
                bucket=self.influx_manager.bucket,
                org=self.influx_manager.org,
                record=point
            )
            
            # Also log to standard logger
            log_method = getattr(self.logger, severity.lower(), self.logger.info)
            log_method(f"[{event_type}] {message}")
            
        except Exception as e:
            self.logger.error(f"Failed to log system event: {e}")
    
    def close(self):
        """Close logger and connections"""
        try:
            self.log_system_event('shutdown', 'PowertrainLogger shutting down')
            self.influx_manager.close()
            self.logger.info("PowertrainLogger closed")
            
        except Exception as e:
            self.logger.error(f"Error during logger close: {e}")