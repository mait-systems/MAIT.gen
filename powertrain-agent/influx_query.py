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
from influxdb_client.client.warnings import MissingPivotFunction
import logging
import warnings

warnings.simplefilter("ignore", MissingPivotFunction)

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
    oil_pressure_trend: float
    avg_coolant_temperature: float
    coolant_temperature_trend: float
    avg_fuel_pressure: float
    stddev_fuel_pressure: float
    min_fuel_pressure: float
    max_fuel_pressure: float
    fuel_pressure_trend: float
    avg_fuel_temperature: float
    stddev_fuel_temperature: float
    min_fuel_temperature: float
    max_fuel_temperature: float
    fuel_temperature_trend: float
    avg_fuel_rate: float
    stddev_fuel_rate: float
    min_fuel_rate: float
    max_fuel_rate: float
    fuel_rate_trend: float
    avg_intake_air_temperature: float
    stddev_intake_air_temperature: float
    min_intake_air_temperature: float
    max_intake_air_temperature: float
    intake_air_temperature_trend: float
    avg_intake_air_pressure: float
    stddev_intake_air_pressure: float
    min_intake_air_pressure: float
    max_intake_air_pressure: float
    intake_air_pressure_trend: float
    trend_slope: float
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
        import os
        self.config = config
        self.influxdb_config = config.get('influxdb', {})
        
        # Use environment variables if available, fallback to config
        influx_url = os.getenv('INFLUXDB_URL', self.influxdb_config.get('url'))
        influx_token = os.getenv('INFLUXDB_TOKEN', self.influxdb_config.get('token'))
        influx_org = os.getenv('INFLUXDB_ORG', self.influxdb_config.get('org'))
        
        self.client = InfluxDBClient(
            url=influx_url,
            token=influx_token,
            org=influx_org,
            timeout=60_000
        )
        
        self.bucket = os.getenv('INFLUXDB_BUCKET', self.influxdb_config.get('bucket'))
        self.org = influx_org
        self.query_api = self.client.query_api()
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        
        self.logger = logging.getLogger('InfluxQueryManager')
        self.logger.info("InfluxDB Query Manager initialized")

    
    def get_latest_baselines(self, load_band: str | None = None) -> List[HistoricalSummary]:
        """Fetch the most recent baseline per load band so stale runs of bootstrap retain coverage."""
        try:
            band_filter = "" if load_band is None else f" and r.load_band == \"{load_band}\""
            query = f"""
            from(bucket: \"{self.bucket}\")
              |> range(start: -180d)
              |> filter(fn: (r) => r._measurement == \"powertrain_baselines\"{band_filter})
              |> sort(columns: [\"_time\"], desc: true)
            """
            result = self.query_api.query_data_frame(org=self.org, query=query)
            if isinstance(result, list):
                result = pd.concat(result, ignore_index=True)
            if result.empty:
                return []
            if {'_field', '_value'}.issubset(result.columns):
                result = result.pivot_table(
                    index=['load_band', '_time'],
                    columns='_field',
                    values='_value',
                    aggfunc='last'
                ).reset_index()
                result.columns.name = None
            result = result.sort_values(['load_band', '_time'], ascending=[True, False])
            latest = result.drop_duplicates(subset=['load_band'], keep='first')
            baselines: List[HistoricalSummary] = []
            for _, row in latest.iterrows():
                baselines.append(HistoricalSummary(
                    load_band=row.get('load_band', 'unknown'),
                    time_period=row.get('period_type', 'daily'),
                    avg_engine_speed=row.get('avg_engine_speed', 0.0),
                    avg_run_speed=row.get('avg_run_speed', 0.0),
                    avg_oil_pressure=row.get('avg_oil_pressure', 0.0),
                    avg_power_output=row.get('avg_power_output', 0.0),
                    stddev_engine_speed=row.get('stddev_engine_speed', 0.0),
                    stddev_oil_pressure=row.get('stddev_oil_pressure', 0.0),
                    sample_count=int(row.get('sample_count', 0)),
                    min_oil_pressure=row.get('min_oil_pressure', 0.0),
                    max_oil_pressure=row.get('max_oil_pressure', 0.0),
                    oil_pressure_trend=row.get('oil_pressure_trend', 0.0),
                    avg_coolant_temperature=row.get('avg_coolant_temperature', 0.0),
                    coolant_temperature_trend=row.get('coolant_temperature_trend', 0.0),
                    avg_fuel_pressure=row.get('avg_fuel_pressure', 0.0),
                    stddev_fuel_pressure=row.get('stddev_fuel_pressure', 0.0),
                    min_fuel_pressure=row.get('min_fuel_pressure', 0.0),
                    max_fuel_pressure=row.get('max_fuel_pressure', 0.0),
                    fuel_pressure_trend=row.get('fuel_pressure_trend', 0.0),
                    avg_fuel_temperature=row.get('avg_fuel_temperature', 0.0),
                    stddev_fuel_temperature=row.get('stddev_fuel_temperature', 0.0),
                    min_fuel_temperature=row.get('min_fuel_temperature', 0.0),
                    max_fuel_temperature=row.get('max_fuel_temperature', 0.0),
                    fuel_temperature_trend=row.get('fuel_temperature_trend', 0.0),
                    avg_fuel_rate=row.get('avg_fuel_rate', 0.0),
                    stddev_fuel_rate=row.get('stddev_fuel_rate', 0.0),
                    min_fuel_rate=row.get('min_fuel_rate', 0.0),
                    max_fuel_rate=row.get('max_fuel_rate', 0.0),
                    fuel_rate_trend=row.get('fuel_rate_trend', 0.0),
                    avg_intake_air_temperature=row.get('avg_intake_air_temperature', 0.0),
                    stddev_intake_air_temperature=row.get('stddev_intake_air_temperature', 0.0),
                    min_intake_air_temperature=row.get('min_intake_air_temperature', 0.0),
                    max_intake_air_temperature=row.get('max_intake_air_temperature', 0.0),
                    intake_air_temperature_trend=row.get('intake_air_temperature_trend', 0.0),
                    avg_intake_air_pressure=row.get('avg_intake_air_pressure', 0.0),
                    stddev_intake_air_pressure=row.get('stddev_intake_air_pressure', 0.0),
                    min_intake_air_pressure=row.get('min_intake_air_pressure', 0.0),
                    max_intake_air_pressure=row.get('max_intake_air_pressure', 0.0),
                    intake_air_pressure_trend=row.get('intake_air_pressure_trend', 0.0),
                    trend_slope=row.get('trend_slope', 0.0),
                    start_time=pd.to_datetime(row.get('_time')).to_pydatetime(),
                    end_time=pd.to_datetime(row.get('_time')).to_pydatetime()
                ))
            return baselines
        except Exception as e:
            self.logger.error(f"Failed to fetch latest baselines: {e}")
            return []

    def get_all_historical_data(self, days_back: int = 30) -> Optional[pd.DataFrame]:
        """Get historical powertrain data for memory bootstrap process.

        Args:
            days_back: Number of days of history to request from InfluxDB.

        Returns:
            DataFrame with historical data, aggregated to 1-minute windows.
        """
        try:
            days_back = max(1, int(days_back))

            query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: -{days_back}d)
              |> filter(fn: (r) => r._measurement == "generator_metrics" and (
                r._field == "Engine_Speed" or
                r._field == "Engine_Run_Speed" or
                r._field == "Engine_Oil_Pressure" or
                r._field == "Generator_Total_Real_Power" or
                r._field == "Engine_Coolant_Temperature" or
                r._field == "Engine_Fuel_Pressure" or
                r._field == "Engine_Fuel_Temperature" or
                r._field == "Engine_Fuel_Rate" or
                r._field == "Intake_Air_Temperature" or
                r._field == "Intake_Air_Pressure" or
                r._field == "Genset_kW_Rating"
              ))
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

            # Pivot in pandas instead of InfluxDB
            result = result.sort_values('_time')
            result['time_group'] = result['_time'].dt.floor('1T')  # Group into 1-minute windows
            result = result.pivot_table(
                index='time_group',
                columns='_field',
                values='_value',
                aggfunc='mean'  # Average values within each minute
            ).reset_index()

            # Fill any missing columns with 0
            required_fields = ['Engine_Speed', 'Generator_Total_Real_Power', 'Engine_Oil_Pressure',
                                'Engine_Run_Speed', 'Engine_Coolant_Temperature', 'Engine_Fuel_Pressure',
                                'Engine_Fuel_Temperature', 'Engine_Fuel_Rate', 'Intake_Air_Temperature',
                                'Intake_Air_Pressure']
            for field in required_fields:
                if field not in result.columns:
                    result[field] = 0

            
            # Add load band classification with engine state awareness
            result['_time'] = result['time_group']  # Use grouped time for load band classification
            result['load_band'] = result.apply(
                lambda row: self._classify_load_band(
                    row['Generator_Total_Real_Power'],
                    row['Engine_Speed']
                ),
                axis=1
            )
            
            self.logger.info(f"Retrieved {len(result)} total historical data points for bootstrap")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get all historical data: {e}")
            return None

    def get_historical_data_for_band(self, load_band: str, days_back: int = 30) -> Optional[pd.DataFrame]:
        """Get historical data filtered to a specific load band."""
        try:
            historical = self.get_all_historical_data(days_back)
            if historical is None or historical.empty:
                self.logger.warning("No historical data available for targeted baseline recalculation")
                return None

            filtered = historical[historical['load_band'] == load_band].copy()
            if filtered.empty:
                self.logger.warning(
                    "No historical samples found for load band %s within last %s days",
                    load_band,
                    days_back
                )
                return None

            self.logger.info(
                "Retrieved %s historical samples for load band %s (last %s days)",
                len(filtered),
                load_band,
                days_back
            )
            return filtered

        except Exception as e:
            self.logger.error(f"Failed to get historical data for load band {load_band}: {e}")
            return None
    
    def _classify_load_band(self, power_percentage: float, engine_speed: float = 0) -> str:
        """Classify load bands with engine state awareness"""
        # First check engine state to separate stopped vs running
        if engine_speed < 100:
            return "0%"  # Engine stopped
        
        # Engine is running - classify by power output  
        if pd.isna(power_percentage) or power_percentage < 0:
            power_percentage = 0
            
        if power_percentage < 20:
            return "0-20%"  # Running but unloaded/lightly loaded
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
                .field("avg_coolant_temperature", baseline.avg_coolant_temperature) \
                .field("oil_pressure_trend", baseline.oil_pressure_trend) \
                .field("coolant_temperature_trend", baseline.coolant_temperature_trend) \
                .field("avg_fuel_pressure", baseline.avg_fuel_pressure) \
                .field("stddev_fuel_pressure", baseline.stddev_fuel_pressure) \
                .field("min_fuel_pressure", baseline.min_fuel_pressure) \
                .field("max_fuel_pressure", baseline.max_fuel_pressure) \
                .field("fuel_pressure_trend", baseline.fuel_pressure_trend) \
                .field("avg_fuel_temperature", baseline.avg_fuel_temperature) \
                .field("stddev_fuel_temperature", baseline.stddev_fuel_temperature) \
                .field("min_fuel_temperature", baseline.min_fuel_temperature) \
                .field("max_fuel_temperature", baseline.max_fuel_temperature) \
                .field("fuel_temperature_trend", baseline.fuel_temperature_trend) \
                .field("avg_fuel_rate", baseline.avg_fuel_rate) \
                .field("stddev_fuel_rate", baseline.stddev_fuel_rate) \
                .field("min_fuel_rate", baseline.min_fuel_rate) \
                .field("max_fuel_rate", baseline.max_fuel_rate) \
                .field("fuel_rate_trend", baseline.fuel_rate_trend) \
                .field("avg_intake_air_temperature", baseline.avg_intake_air_temperature) \
                .field("stddev_intake_air_temperature", baseline.stddev_intake_air_temperature) \
                .field("min_intake_air_temperature", baseline.min_intake_air_temperature) \
                .field("max_intake_air_temperature", baseline.max_intake_air_temperature) \
                .field("intake_air_temperature_trend", baseline.intake_air_temperature_trend) \
                .field("avg_intake_air_pressure", baseline.avg_intake_air_pressure) \
                .field("stddev_intake_air_pressure", baseline.stddev_intake_air_pressure) \
                .field("min_intake_air_pressure", baseline.min_intake_air_pressure) \
                .field("max_intake_air_pressure", baseline.max_intake_air_pressure) \
                .field("intake_air_pressure_trend", baseline.intake_air_pressure_trend) \
                .field("trend_slope", baseline.trend_slope) \
                .time(baseline.end_time)
            
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            self.logger.debug(f"Stored baseline for {baseline.load_band} - {baseline.time_period}")
            
        except Exception as e:
            self.logger.error(f"Failed to store historical baseline: {e}")

    def close(self):
        """Close InfluxDB client connection"""
        if self.client:
            self.client.close()
            self.logger.info("InfluxDB connection closed")
