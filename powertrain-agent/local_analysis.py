#!/usr/bin/env python3
"""
Local Statistical Analyzer for PowertrainAgent
Provides intelligent local analysis using historical baseline comparison
"""

import logging
import math
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from influxdb_client.client.warnings import MissingPivotFunction

from influx_query import InfluxQueryManager
import warnings

warnings.simplefilter("ignore", MissingPivotFunction)

# PowertrainMetrics is defined in agent_powertrain_gateway.py
# Using string type hints to avoid circular imports



class LocalAnalyzer:
    """
    Statistical analysis engine for powertrain metrics
    Provides intelligent monitoring without gateway dependency
    """
    
    def __init__(self, config: dict, influx_manager: InfluxQueryManager):
        """Initialize local analyzer with configuration and InfluxDB client"""
        self.config = config
        self.influx_manager = influx_manager
        self.logger = logging.getLogger('LocalAnalyzer')
        
        # Statistical thresholds (sigma multipliers)
        self.warning_threshold = 2.0   # 2 sigma
        self.critical_threshold = 3.0  # 3 sigma
        
        # Parameter mapping for statistical analysis
        self.parameter_mappings = [
            ('engine_speed', 'avg_engine_speed', 'stddev_engine_speed', 'Engine Speed', 'RPM'),
            ('engine_oil_pressure', 'avg_oil_pressure', 'stddev_oil_pressure', 'Oil Pressure', 'kPa'),
            ('engine_coolant_temperature', 'avg_coolant_temperature', 'stddev_coolant_temperature', 'Coolant Temperature', '°C'),
            ('engine_fuel_pressure', 'avg_fuel_pressure', 'stddev_fuel_pressure', 'Fuel Pressure', 'kPa'),
            ('engine_fuel_temperature', 'avg_fuel_temperature', 'stddev_fuel_temperature', 'Fuel Temperature', '°C'),
            ('engine_fuel_rate', 'avg_fuel_rate', 'stddev_fuel_rate', 'Fuel Rate', 'l/hr'),
            ('intake_air_temperature', 'avg_intake_air_temperature', 'stddev_intake_air_temperature', 'Intake Air Temperature', '°C'),
            ('intake_air_pressure', 'avg_intake_air_pressure', 'stddev_intake_air_pressure', 'Intake Air Pressure', 'kPa'),
        ]
        
        self.logger.info("LocalAnalyzer initialized with statistical thresholds")
    
    def analyze_metrics(self, current_metrics: "PowertrainMetrics") -> Dict[str, Any]:
        """
        Main analysis method - performs statistical analysis using baseline comparison
        
        Args:
            current_metrics: PowertrainMetrics object with current data
            
        Returns:
            Dictionary with analysis results, alerts, insights, and metadata
        """
        self.logger.info("Running local statistical analysis")
        
        alerts = []
        insights = []
        alert_level = "INFO"
        
        try:
            # Retrieve historical baselines for statistical analysis
            baselines = self._get_recent_baselines(current_metrics.load_band)
            use_statistical_analysis = len(baselines) > 0
            
            # Perform statistical analysis if baselines are available
            if use_statistical_analysis:
                alerts, alert_level = self._generate_alerts(current_metrics, baselines)
                insights = self._generate_insights(current_metrics, baselines, len(baselines))
            else:
                insights = self._generate_no_baseline_insights(current_metrics)
            
            # Build structured result
            result = {
                "analysis": [
                    "LOCAL MODE - Statistical analysis using historical baselines",
                    f"Load band: {current_metrics.load_band}",
                    f"Engine running at {current_metrics.engine_speed:.0f} RPM" if current_metrics.engine_speed > 0 else "Engine stopped"
                ],
                "alerts": alerts,
                "insights": insights,
                "mode": "LOCAL",
                "alert_level": alert_level,
                "timestamp": current_metrics.timestamp.isoformat(),
                "baseline_available": use_statistical_analysis,
                "parameters_analyzed": len(self.parameter_mappings)
            }
            
            self.logger.debug(f"Analysis completed - Alert level: {alert_level}, Alerts: {len(alerts)}")
            return result
            
        except Exception as e:
            self.logger.error(f"Local analysis error: {str(e)}")
            return self._generate_error_result(current_metrics, str(e))
    
    def _get_recent_baselines(self, load_band: str) -> Dict[str, Any]:
        """
        Get recent baseline data for statistical threshold analysis
        
        Args:
            load_band: Current load band for baseline lookup
            
        Returns:
            Dictionary with baseline statistics or empty dict if unavailable
        """
        try:
            bucket = self.config['influxdb']['bucket']
            org = self.config['influxdb']['org']
            
            # Query for most recent baseline for this load band
            query = f'''
            from(bucket: "{bucket}")
              |> range(start: -30d)
              |> filter(fn: (r) => r._measurement == "powertrain_baselines" and 
                r.load_band == "{load_band}")
              |> sort(columns: ["_time"], desc: true)
              |> limit(n: 1)
            '''
            
            result = self.influx_manager.client.query_api().query_data_frame(org=org, query=query)
            
            if isinstance(result, list):
                result = pd.concat(result, ignore_index=True)
            
            if result.empty:
                self.logger.debug(f"No baseline data found for load band {load_band}")
                return {}
            
            if {'_field', '_value'}.issubset(result.columns):
                result = result.pivot_table(
                    index=['load_band', '_time'],
                    columns='_field',
                    values='_value',
                    aggfunc='last'
                ).reset_index()
                result.columns.name = None

            # Extract baseline statistics into dictionary
            baseline_row = result.iloc[0]
            baselines = {}
            
            # Add all available baseline fields
            baseline_fields = [
                'avg_engine_speed', 'stddev_engine_speed',
                'avg_oil_pressure', 'stddev_oil_pressure', 
                'avg_fuel_pressure', 'stddev_fuel_pressure',
                'avg_fuel_temperature', 'stddev_fuel_temperature',
                'avg_fuel_rate', 'stddev_fuel_rate',
                'avg_coolant_temperature', 'stddev_coolant_temperature',
                'avg_intake_air_temperature', 'stddev_intake_air_temperature',
                'avg_intake_air_pressure', 'stddev_intake_air_pressure'
            ]
            
            for field in baseline_fields:
                value = baseline_row.get(field)
                if value is not None and not pd.isna(value):
                    baselines[field] = float(value)
            
            self.logger.debug(f"Retrieved {len(baselines)} baseline values for {load_band}")
            return baselines
            
        except Exception as e:
            self.logger.debug(f"Failed to get baseline data: {str(e)}")
            return {}
    
    def _check_baseline_threshold(self, value: float, avg_field: str, stddev_field: str, baselines: Dict[str, Any]) -> Optional[str]:
        """
        Check if a value is within baseline statistical thresholds
        
        Args:
            value: Current metric value
            avg_field: Field name for baseline average (e.g., 'avg_fuel_pressure')
            stddev_field: Field name for baseline standard deviation (e.g., 'stddev_fuel_pressure')
            baselines: Dictionary containing baseline statistics
            
        Returns:
            'OK', 'WARNING', or 'CRITICAL' based on statistical deviation, None if no baseline data
        """
        try:
            avg = baselines.get(avg_field)
            stddev = baselines.get(stddev_field)
            
            if avg is None or stddev is None:
                return None  # No baseline data available
            
            # Calculate deviation from baseline mean
            deviation = abs(value - avg)
            
            # Statistical thresholds
            warning_threshold = self.warning_threshold * stddev
            critical_threshold = self.critical_threshold * stddev
            
            if deviation > critical_threshold:
                return 'CRITICAL'
            elif deviation > warning_threshold:
                return 'WARNING'
            else:
                return 'OK'
                
        except Exception:
            return None  # Error in calculation
    
    def _generate_alerts(self, current_metrics: "PowertrainMetrics", baselines: Dict[str, Any]) -> tuple[List[Dict], str]:
        """
        Generate alerts based on statistical analysis
        
        Args:
            current_metrics: Current powertrain metrics
            baselines: Historical baseline data
            
        Returns:
            Tuple of (alerts_list, highest_alert_level)
        """
        alerts = []
        alert_level = "INFO"
        
        # Check each parameter against statistical baselines
        for attr_name, avg_field, stddev_field, param_name, unit in self.parameter_mappings:
            value = getattr(current_metrics, attr_name, 0)
            
            if value > 0:  # Only check parameters with valid readings
                status = self._check_baseline_threshold(value, avg_field, stddev_field, baselines)
                
                if status == 'CRITICAL':
                    alerts.append({
                        "level": "CRITICAL",
                        "message": f"{param_name} critically outside normal range",
                        "value": value,
                        "unit": unit,
                        "analysis_type": "statistical"
                    })
                    alert_level = "CRITICAL"
                elif status == 'WARNING':
                    alerts.append({
                        "level": "WARNING",
                        "message": f"{param_name} outside normal range",
                        "value": value,
                        "unit": unit,
                        "analysis_type": "statistical"
                    })
                    if alert_level == "INFO":
                        alert_level = "WARNING"
        
        return alerts, alert_level
    
    def _generate_insights(self, current_metrics: "PowertrainMetrics", baselines: Dict[str, Any], baseline_count: int) -> List[str]:
        """
        Generate insights based on analysis results
        
        Args:
            current_metrics: Current powertrain metrics
            baselines: Historical baseline data
            baseline_count: Number of baseline parameters available
            
        Returns:
            List of insight strings
        """
        insights = []
        
        insights.append(f"Statistical analysis using {current_metrics.load_band} load band baselines")
        insights.append(f"Analyzing {baseline_count} baseline parameters")
        
        # Engine state insight
        if current_metrics.engine_speed > 0:
            insights.append(f"Engine operational at {current_metrics.engine_speed:.0f} RPM")
        else:
            insights.append("Engine stopped - monitoring for activity")
        
        return insights
    
    def _generate_no_baseline_insights(self, current_metrics: "PowertrainMetrics") -> List[str]:
        """Generate insights when no baseline data is available"""
        insights = []
        
        insights.append("No baseline data available - statistical analysis unavailable")
        insights.append(f"Load band: {current_metrics.load_band}")
        
        if current_metrics.engine_speed > 0:
            insights.append(f"Engine running at {current_metrics.engine_speed:.0f} RPM")
        else:
            insights.append("Engine stopped")
            
        return insights
    
    def _generate_error_result(self, current_metrics: "PowertrainMetrics", error_msg: str) -> Dict[str, Any]:
        """Generate error result when analysis fails"""
        return {
            "analysis": ["LOCAL MODE - Statistical analysis error"],
            "alerts": [],
            "insights": ["Statistical analysis error", error_msg],
            "mode": "LOCAL",
            "alert_level": "WARNING",
            "timestamp": current_metrics.timestamp.isoformat(),
            "baseline_available": False,
            "parameters_analyzed": 0,
            "error": error_msg
        }
