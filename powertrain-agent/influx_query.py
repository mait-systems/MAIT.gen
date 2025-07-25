#!/usr/bin/env python3
"""
InfluxDB Query Manager for PowertrainAgent
Handles all database interactions including live data queries and historical data access
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import logging

@dataclass
class HistoricalSummary:
    """Historical summary statistics for a specific load band and time period"""
    load_band: str
    time_period: str
    avg_engine_speed: float
    avg_run_speed: float
    avg_oil_pressure: float
    avg_power_output: float
    stddev_engine_speed: float
    stddev_oil_pressure: float
    sample_count: int
    min_oil_pressure: float
    max_oil_pressure: float
    trend_slope: float
    confidence_level: float
    start_time: datetime
    end_time: datetime

class InfluxQueryManager:
    """
    Manages all InfluxDB queries for PowertrainAgent including:
    - Live data retrieval
    - Historical data queries
    - Memory storage and retrieval
    - Statistical aggregations
    """
    
    def __init__(self, config: dict):
        """Initialize InfluxDB client and configuration"""
        self.config = config
        self.influxdb_config = config.get('influxdb', {})
        
        self.client = InfluxDBClient(
            url=self.influxdb_config.get('url', 'http://localhost:8086'),
            token=self.influxdb_config.get('token', ''),
            org=self.influxdb_config.get('org', 'mlr'),
            timeout=60_000
        )
        
        self.bucket = self.influxdb_config.get('bucket', 'stbd_gen')
        self.org = self.influxdb_config.get('org', 'mlr')
        self.query_api = self.client.query_api()
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        
        self.logger = logging.getLogger('InfluxQueryManager')
        self.logger.info("InfluxDB Query Manager initialized")
    
    def get_latest_powertrain_data(self, window_minutes: int = 2) -> Optional[Dict[str, float]]:
        """
        Get the latest powertrain-specific metrics from InfluxDB
        
        Args:
            window_minutes: Time window to look back for latest data
            
        Returns:
            Dictionary with latest metric values or None if no data
        """
        try:
            # Use the same query format as the working live-stats API
            query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: -{window_minutes}m)
              |> filter(fn: (r) =>
                r._measurement == "generator_metrics" and (
                  r._field == "Engine_Speed" or
                  r._field == "Engine_Run_Speed" or
                  r._field == "Engine_Oil_Pressure" or
                  r._field == "Generator_Total_Real_Power" or
                  r._field == "Engine_Coolant_Temperature"
                )
              )
              |> last()
            '''
            
            result = self.query_api.query_data_frame(org=self.org, query=query)
            
            if isinstance(result, list):
                result = pd.concat(result, ignore_index=True)
            
            if result.empty:
                self.logger.warning("No live powertrain data found")
                return None
            
            # Convert to dictionary using _field and _value columns
            latest_data = {}
            for _, row in result.iterrows():
                field_name = row['_field']
                field_value = row['_value']
                
                # Convert to float safely
                try:
                    latest_data[field_name] = float(field_value)
                except (ValueError, TypeError):
                    latest_data[field_name] = 0.0
            
            self.logger.debug(f"Retrieved live data: {len(latest_data)} metrics")
            return latest_data
            
        except Exception as e:
            self.logger.error(f"Failed to get latest powertrain data: {e}")
            return None
    
    def get_historical_data_range(self, hours_back: int = 24) -> Optional[pd.DataFrame]:
        """
        Get historical powertrain data for a specified time range
        
        Args:
            hours_back: Number of hours to look back
            
        Returns:
            DataFrame with historical data or None if no data
        """
        try:
            query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: -{hours_back}h)
              |> filter(fn: (r) => r._measurement == "generator_metrics" and (
                r._field == "Engine_Speed" or
                r._field == "Engine_Run_Speed" or
                r._field == "Engine_Oil_Pressure" or
                r._field == "Generator_Total_Real_Power" or
                r._field == "Engine_Coolant_Temperature"
              ))
              |> aggregateWindow(every: 1m, fn: last, createEmpty: false)
              |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            result = self.query_api.query_data_frame(org=self.org, query=query)
            
            if isinstance(result, list):
                result = pd.concat(result, ignore_index=True)
            
            if result.empty:
                return None
            
            # Clean data
            result = result.replace([np.inf, -np.inf], np.nan).dropna()
            result['_time'] = pd.to_datetime(result['_time'])
            result = result.sort_values('_time')
            
            self.logger.info(f"Retrieved {len(result)} historical data points from last {hours_back} hours")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get historical data: {e}")
            return None
    
    def get_all_historical_data(self) -> Optional[pd.DataFrame]:
        """
        Get ALL historical powertrain data for bootstrap process
        
        Returns:
            DataFrame with all available historical data
        """
        try:
            query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: 0)
              |> filter(fn: (r) => r._measurement == "generator_metrics" and (
                r._field == "Engine_Speed" or
                r._field == "Engine_Run_Speed" or
                r._field == "Engine_Oil_Pressure" or
                r._field == "Generator_Total_Real_Power" or
                r._field == "Engine_Coolant_Temperature"
              ))
              |> aggregateWindow(every: 5m, fn: last, createEmpty: false)
              |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            result = self.query_api.query_data_frame(org=self.org, query=query)
            
            if isinstance(result, list):
                result = pd.concat(result, ignore_index=True)
                
            if result.empty:
                self.logger.warning("No historical data found for bootstrap")
                return None
            
            # Clean and prepare data
            result = result.replace([np.inf, -np.inf], np.nan).dropna()
            result['_time'] = pd.to_datetime(result['_time'])
            result = result.sort_values('_time')
            
            # Add load band classification
            result['load_band'] = result['Generator_Total_Real_Power'].apply(self._classify_load_band)
            
            self.logger.info(f"Retrieved {len(result)} total historical data points for bootstrap")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get all historical data: {e}")
            return None
    
    def _classify_load_band(self, power_percentage: float) -> str:
        """Classify power output into load bands"""
        if pd.isna(power_percentage) or power_percentage < 0:
            return "0%"
        elif power_percentage < 20:
            return "0-20%"
        elif power_percentage < 40:
            return "20-40%"
        elif power_percentage < 60:
            return "40-60%"
        elif power_percentage < 80:
            return "60-80%"
        else:
            return "80-100%"
    
    def store_historical_baseline(self, baseline: HistoricalSummary):
        """
        Store historical baseline summary in InfluxDB
        
        Args:
            baseline: HistoricalSummary object to store
        """
        try:
            point = Point("powertrain_baselines") \
                .tag("load_band", baseline.load_band) \
                .tag("period_type", baseline.time_period) \
                .field("avg_engine_speed", baseline.avg_engine_speed) \
                .field("avg_run_speed", baseline.avg_run_speed) \
                .field("avg_oil_pressure", baseline.avg_oil_pressure) \
                .field("avg_power_output", baseline.avg_power_output) \
                .field("stddev_engine_speed", baseline.stddev_engine_speed) \
                .field("stddev_oil_pressure", baseline.stddev_oil_pressure) \
                .field("sample_count", baseline.sample_count) \
                .field("min_oil_pressure", baseline.min_oil_pressure) \
                .field("max_oil_pressure", baseline.max_oil_pressure) \
                .field("trend_slope", baseline.trend_slope) \
                .field("confidence_level", baseline.confidence_level) \
                .time(baseline.end_time)
            
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            self.logger.debug(f"Stored baseline for {baseline.load_band} - {baseline.time_period}")
            
        except Exception as e:
            self.logger.error(f"Failed to store historical baseline: {e}")
    
    def get_historical_baselines(self, load_band: str, time_period: str = "hourly", 
                               days_back: int = 30) -> List[HistoricalSummary]:
        """
        Retrieve historical baselines for analysis context
        
        Args:
            load_band: Load band to filter by
            time_period: Time period type (hourly, daily, weekly)
            days_back: Number of days to look back
            
        Returns:
            List of HistoricalSummary objects
        """
        try:
            query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: -{days_back}d)
              |> filter(fn: (r) => r._measurement == "powertrain_baselines" and
                r.load_band == "{load_band}" and
                r.period_type == "{time_period}")
              |> sort(columns: ["_time"], desc: false)
            '''
            
            result = self.query_api.query_data_frame(org=self.org, query=query)
            
            if isinstance(result, list):
                result = pd.concat(result, ignore_index=True)
                
            if result.empty:
                return []
            
            # Convert to HistoricalSummary objects
            baselines = []
            for _, row in result.iterrows():
                baseline = HistoricalSummary(
                    load_band=row.get('load_band', load_band),
                    time_period=row.get('period_type', time_period),
                    avg_engine_speed=row.get('avg_engine_speed', 0),
                    avg_run_speed=row.get('avg_run_speed', 0),
                    avg_oil_pressure=row.get('avg_oil_pressure', 0),
                    avg_power_output=row.get('avg_power_output', 0),
                    stddev_engine_speed=row.get('stddev_engine_speed', 0),
                    stddev_oil_pressure=row.get('stddev_oil_pressure', 0),
                    sample_count=int(row.get('sample_count', 0)),
                    min_oil_pressure=row.get('min_oil_pressure', 0),
                    max_oil_pressure=row.get('max_oil_pressure', 0),
                    trend_slope=row.get('trend_slope', 0),
                    confidence_level=row.get('confidence_level', 0),
                    start_time=pd.to_datetime(row['_time']),
                    end_time=pd.to_datetime(row['_time'])
                )
                baselines.append(baseline)
            
            self.logger.debug(f"Retrieved {len(baselines)} baselines for {load_band} - {time_period}")
            return baselines
            
        except Exception as e:
            self.logger.error(f"Failed to get historical baselines: {e}")
            return []
    
    def store_event_memory(self, event_type: str, severity: str, description: str, 
                          context_data: dict, pattern_id: str = None):
        """
        Store event memory for pattern recognition
        
        Args:
            event_type: Type of event (anomaly, maintenance, operational, degradation)
            severity: Severity level (INFO, WARNING, CRITICAL)
            description: Human-readable description
            context_data: Additional context data as dictionary
            pattern_id: Optional pattern identifier for recurring events
        """
        try:
            point = Point("powertrain_event_memory") \
                .tag("event_type", event_type) \
                .tag("severity", severity) \
                .field("description", description) \
                .field("context_json", str(context_data)) \
                .time(datetime.now())
            
            if pattern_id:
                point = point.tag("pattern_id", pattern_id)
            
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            self.logger.debug(f"Stored event memory: {event_type} - {severity}")
            
        except Exception as e:
            self.logger.error(f"Failed to store event memory: {e}")
    
    def store_ai_memory(self, knowledge_type: str, insight_text: str, 
                       supporting_metrics: dict, confidence: str = "medium"):
        """
        Store AI-generated insights for memory persistence
        
        Args:
            knowledge_type: Type of knowledge (trend, pattern, correlation, prediction)
            insight_text: AI-generated insight text
            supporting_metrics: Metrics that support this insight
            confidence: Confidence level (low, medium, high)
        """
        try:
            point = Point("powertrain_ai_memory") \
                .tag("knowledge_type", knowledge_type) \
                .tag("confidence", confidence) \
                .tag("validation_status", "pending") \
                .field("insight_text", insight_text) \
                .field("supporting_metrics", str(supporting_metrics)) \
                .field("creation_date", datetime.now().isoformat()) \
                .time(datetime.now())
            
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            self.logger.debug(f"Stored AI memory: {knowledge_type} - {confidence}")
            
        except Exception as e:
            self.logger.error(f"Failed to store AI memory: {e}")
    
    def get_recent_events(self, days_back: int = 7) -> List[dict]:
        """
        Get recent events for context building
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of event dictionaries
        """
        try:
            query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: -{days_back}d)
              |> filter(fn: (r) => r._measurement == "powertrain_event_memory")
              |> sort(columns: ["_time"], desc: true)
              |> limit(n: 50)
            '''
            
            result = self.query_api.query_data_frame(org=self.org, query=query)
            
            if isinstance(result, list):
                result = pd.concat(result, ignore_index=True)
                
            if result.empty:
                return []
            
            events = []
            for _, row in result.iterrows():
                event = {
                    'timestamp': pd.to_datetime(row['_time']).isoformat(),
                    'event_type': row.get('event_type', 'unknown'),
                    'severity': row.get('severity', 'INFO'),
                    'description': row.get('description', ''),
                    'context': row.get('context_json', '{}')
                }
                events.append(event)
            
            self.logger.debug(f"Retrieved {len(events)} recent events")
            return events
            
        except Exception as e:
            self.logger.error(f"Failed to get recent events: {e}")
            return []
    
    def close(self):
        """Close InfluxDB client connection"""
        if self.client:
            self.client.close()
            self.logger.info("InfluxDB connection closed")