#!/usr/bin/env python3
"""
Baseline Calculator for PowertrainAgent
Handles statistical baseline calculations locally on customer side
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from influx_query import HistoricalSummary
from dataclasses import replace
from influxdb_client import Point
from influxdb_client.client.write_api import SYNCHRONOUS


class BaselineCalculator:
    """Calculate statistical baselines for powertrain metrics by load band"""
    
    def __init__(self, config: dict):
        """Initialize baseline calculator with configuration"""
        self.config = config
        self.logger = logging.getLogger('BaselineCalculator')
        self.min_samples = 10  # Minimum samples required for reliable baseline
        self.logger.info("BaselineCalculator initialized")

    # Write memory bootstrap status into influx
    def _write_bootstrap_status(self, baseline_count: int, influx_client): 
        """Write bootstrap completion status to InfluxDB"""
        try:
            point = Point("powertrain_system_status") \
                .field("bootstrap_completed", True) \
                .field("bootstrap_progress", 100) \
                .field("baseline_count", baseline_count) \
                .field("bootstrap_timestamp", datetime.now().isoformat()) \
                .field("calculation_method", "30day_statistical") \
                .time(datetime.now())
            
            influx_client.write_api.write(
                bucket=influx_client.bucket,
                org=influx_client.org, 
                record=point,
            )

            self.logger.info(f"Bootstrap status written: {baseline_count} baselines completed")
        
        except Exception as e:
            self.logger.error(f"Failed to write bootstrap status: {e}")


    
    def calculate_load_band_baselines(
        self,
        historical_data: pd.DataFrame,
        influx_client,
        days_back: int = 30,
        preserve_existing: bool = True
    ) -> List[HistoricalSummary]:
        """
        Calculate avg_engine_speed baselines for each load band
        
        Args:
            historical_data: Pre-filtered DataFrame from InfluxQueryManager with load_band classification
            influx_client: InfluxDB client for writing bootstrap status
            days_back: Number of days the data covers (for metadata only)
            preserve_existing: When True, re-store baselines for bands not present in the dataframe
            
        Returns:
            List of HistoricalSummary objects with avg_engine_speed calculated
        """
        try:
            # Basic validation
            if historical_data is None or historical_data.empty:
                self.logger.warning("No historical data provided for baseline calculation")
                return []
            
            # Check required columns
            required_columns = ['load_band', 'Engine_Speed', 'Engine_Oil_Pressure', 'Generator_Total_Real_Power', 'Engine_Coolant_Temperature', 'Engine_Fuel_Pressure', 'Engine_Fuel_Temperature', 'Engine_Fuel_Rate', 'Intake_Air_Temperature', 'Intake_Air_Pressure'] # What we are analyzing
            missing_columns = [col for col in required_columns if col not in historical_data.columns]
            if missing_columns:
                self.logger.error(f"Missing required columns: {missing_columns}")
                return []
            
            self.logger.info(f"Calculating baselines from {len(historical_data)} historical data points")
            
            # Group by load band and calculate statistics
            baselines = []
            preserved_baselines = []
            processed_bands = set()
            current_time = datetime.now()
            start_time = current_time - timedelta(days=days_back)
            existing = {b.load_band: b for b in influx_client.get_latest_baselines()}

            for load_band, group in historical_data.groupby('load_band'):
                processed_bands.add(load_band)
                self.logger.debug(f"Processing load band: {load_band} with {len(group)} samples")

                # Validate minimum sample size for reliability
                if len(group) < self.min_samples:
                    self.logger.warning(f"Insufficient samples for load band {load_band}: {len(group)} < {self.min_samples}")
                    previous = existing.get(load_band)
                    if previous:
                        refreshed = replace(previous, start_time=current_time, end_time=current_time)
                        influx_client.store_historical_baseline(refreshed)
                        preserved_baselines.append(refreshed)
                        self.logger.info(f"Reusing existing baseline for {load_band}; no fresh samples found")
                        continue

                    # Allow provisional baseline creation when we have a handful of samples
                    provisional_threshold = max(3, self.min_samples // 2)
                    if len(group) < provisional_threshold:
                        self.logger.warning(
                            f"Not enough samples to create provisional baseline for {load_band}: {len(group)} < {provisional_threshold}"
                        )
                        continue

                    self.logger.info(
                        f"Creating provisional baseline for {load_band} with {len(group)} samples"
                    )

                # ENGINE SPEED: Calculate avg_engine_speed for this load band
                avg_engine_speed = float(group['Engine_Speed'].dropna().mean())
                
                # ENGINE SPEED: Calculate stddev_engine_speed for this load band
                stddev_engine_speed = float(group['Engine_Speed'].dropna().std())
                
                # OIL PRESSURE: Calculate avg_oil_pressure for this load band
                avg_oil_pressure = float(group['Engine_Oil_Pressure'].dropna().mean())

                # OIL PRESSURE: Calculate stddev_oil_pressure for this load band
                stddev_oil_pressure = float(group['Engine_Oil_Pressure'].dropna().std())

                # OIL PRESSURE: Calculate min/max oil pressure for this load band
                min_oil_pressure = float(group['Engine_Oil_Pressure'].dropna().min())
                max_oil_pressure = float(group['Engine_Oil_Pressure'].dropna().max())

                # POWER OUTPUT: Calculate average power output for this load band
                avg_power_output = float(group['Generator_Total_Real_Power'].dropna().mean())

                # COOLANT TEMPERATURE: Calculate average coolant temperature for this load band
                avg_coolant_temperature = float(group['Engine_Coolant_Temperature'].dropna().mean())

                # FUEL PRESSURE: Calculate avg_fuel_pressure for this load band
                avg_fuel_pressure = float(group['Engine_Fuel_Pressure'].dropna().mean())

                # FUEL PRESSURE: Calculate stddev_fuel_pressure for this load band
                stddev_fuel_pressure = float(group['Engine_Fuel_Pressure'].dropna().std())

                # FUEL PRESSURE: Calculate min/max fuel pressure for this load band
                min_fuel_pressure = float(group['Engine_Fuel_Pressure'].dropna().min())
                max_fuel_pressure = float(group['Engine_Fuel_Pressure'].dropna().max())

                # FUEL TEMPERATURE: Calculate avg_fuel_temperature for this load band
                avg_fuel_temperature = float(group['Engine_Fuel_Temperature'].dropna().mean())

                # FUEL TEMPERATURE: Calculate stddev_fuel_temperature for this load band
                stddev_fuel_temperature = float(group['Engine_Fuel_Temperature'].dropna().std())

                # FUEL TEMPERATURE: Calculate min/max fuel temperature for this load band
                min_fuel_temperature = float(group['Engine_Fuel_Temperature'].dropna().min())
                max_fuel_temperature = float(group['Engine_Fuel_Temperature'].dropna().max())

                # FUEL RATE: Calculate avg_fuel_rate for this load band
                avg_fuel_rate = float(group['Engine_Fuel_Rate'].dropna().mean())

                # FUEL RATE: Calculate stddev_fuel_rate for this load band
                stddev_fuel_rate = float(group['Engine_Fuel_Rate'].dropna().std())

                # FUEL RATE: Calculate min/max fuel rate for this load band
                min_fuel_rate = float(group['Engine_Fuel_Rate'].dropna().min())
                max_fuel_rate = float(group['Engine_Fuel_Rate'].dropna().max())

                # INTAKE AIR TEMPERATURE: Calculate avg_intake_air_temperature for this load band
                avg_intake_air_temperature = float(group['Intake_Air_Temperature'].dropna().mean())

                # INTAKE AIR TEMPERATURE: Calculate stddev_intake_air_temperature for this load band
                stddev_intake_air_temperature = float(group['Intake_Air_Temperature'].dropna().std())

                # INTAKE AIR TEMPERATURE: Calculate min/max intake air temperature for this load band
                min_intake_air_temperature = float(group['Intake_Air_Temperature'].dropna().min())
                max_intake_air_temperature = float(group['Intake_Air_Temperature'].dropna().max())

                # INTAKE AIR PRESSURE: Calculate avg_intake_air_pressure for this load band
                avg_intake_air_pressure = float(group['Intake_Air_Pressure'].dropna().mean())

                # INTAKE AIR PRESSURE: Calculate stddev_intake_air_pressure for this load band
                stddev_intake_air_pressure = float(group['Intake_Air_Pressure'].dropna().std())

                # INTAKE AIR PRESSURE: Calculate min/max intake air pressure for this load band
                min_intake_air_pressure = float(group['Intake_Air_Pressure'].dropna().min())
                max_intake_air_pressure = float(group['Intake_Air_Pressure'].dropna().max())

                # TREND ANALYSIS: Calculate linear regression slopes over time 
                time_seconds = (group['_time'] - group['_time'].min()).dt.total_seconds()

                # Trend calc below use notna for:
                # Proper alignment - Both X and Y arrays have same length
                # Cleaner syntax - notna() is more explicit than dropna()
                # Consistent indexing - Uses boolean mask on both arrays

                # TREND ANALYSIS: OIL PRESSURE trend (kPa per day)
                running_mask = (group['Engine_Speed'] > 100) & group['Engine_Oil_Pressure'].notna() 

                if running_mask.sum() > 2:  # Need minimum points
                    time_running = time_seconds[running_mask]
                    oil_running = group['Engine_Oil_Pressure'][running_mask]
                    oil_pressure_trend = np.polyfit(time_running, oil_running, 1)[0] * 86400
                else:
                    oil_pressure_trend = 0.0


                # TREND ANALYSIS: COOLANT TEMPERATURE trend (°C per day)
                running_mask = (group['Engine_Speed'] > 100) & group['Engine_Coolant_Temperature'].notna() 

                if running_mask.sum() > 2:  # Need minimum points
                    time_running = time_seconds[running_mask]
                    coolant_running = group['Engine_Coolant_Temperature'][running_mask]
                    coolant_temperature_trend = np.polyfit(time_running, coolant_running, 1)[0] * 86400
                else:
                    coolant_temperature_trend = 0.0

                # TREND ANALYSIS: FUEL PRESSURE trend (kPa per day)
                running_mask = (group['Engine_Speed'] > 100) & group['Engine_Fuel_Pressure'].notna() 

                if running_mask.sum() > 2:  # Need minimum points
                    time_running = time_seconds[running_mask]
                    fuel_running = group['Engine_Fuel_Pressure'][running_mask]
                    fuel_pressure_trend = np.polyfit(time_running, fuel_running, 1)[0] * 86400
                else:
                    fuel_pressure_trend = 0.0

                # TREND ANALYSIS: FUEL TEMPERATURE trend (°C per day)
                running_mask = (group['Engine_Speed'] > 100) & group['Engine_Fuel_Temperature'].notna() 

                if running_mask.sum() > 2:  # Need minimum points
                    time_running = time_seconds[running_mask]
                    fuel_temp_running = group['Engine_Fuel_Temperature'][running_mask]
                    fuel_temperature_trend = np.polyfit(time_running, fuel_temp_running, 1)[0] * 86400
                else:
                    fuel_temperature_trend = 0.0

                # TREND ANALYSIS: FUEL RATE trend (L/h per day)
                running_mask = (group['Engine_Speed'] > 100) & group['Engine_Fuel_Rate'].notna() 

                if running_mask.sum() > 2:  # Need minimum points
                    time_running = time_seconds[running_mask]
                    fuel_rate_running = group['Engine_Fuel_Rate'][running_mask]
                    fuel_rate_trend = np.polyfit(time_running, fuel_rate_running, 1)[0] * 86400
                else:
                    fuel_rate_trend = 0.0

                # TREND ANALYSIS: INTAKE AIR TEMPERATURE trend (°C per day)
                running_mask = (group['Engine_Speed'] > 100) & group['Intake_Air_Temperature'].notna() 

                if running_mask.sum() > 2:  # Need minimum points
                    time_running = time_seconds[running_mask]
                    intake_air_temp_running = group['Intake_Air_Temperature'][running_mask]
                    intake_air_temperature_trend = np.polyfit(time_running, intake_air_temp_running, 1)[0] * 86400
                else:
                    intake_air_temperature_trend = 0.0

                # TREND ANALYSIS: INTAKE AIR PRESSURE trend (kPa per day)
                running_mask = (group['Engine_Speed'] > 100) & group['Intake_Air_Pressure'].notna() 

                if running_mask.sum() > 2:  # Need minimum points
                    time_running = time_seconds[running_mask]
                    intake_air_press_running = group['Intake_Air_Pressure'][running_mask]
                    intake_air_pressure_trend = np.polyfit(time_running, intake_air_press_running, 1)[0] * 86400
                else:
                    intake_air_pressure_trend = 0.0

                # TREND ANALYSIS: ENGINE SPEED trend (RPM per day)
                mask = group['Engine_Speed'].notna()
                if mask.sum() > 1:
                    trend_slope = np.polyfit(
                        time_seconds[mask],
                        group['Engine_Speed'][mask],
                        1
                    )[0] * 86400
                else:
                    trend_slope = 0.0

                
                # Create HistoricalSummary with calculated values
                baseline = HistoricalSummary(
                    load_band=load_band,
                    time_period="daily",
                    avg_engine_speed=avg_engine_speed, # Average engine speed
                    avg_run_speed=1800.0,  # Nominal generator run speed
                    avg_oil_pressure=avg_oil_pressure, # Average oil pressure
                    avg_power_output=avg_power_output, # Average power output
                    stddev_engine_speed=stddev_engine_speed, # Standard deviation, engine speed
                    stddev_oil_pressure=stddev_oil_pressure, # Standard deviation, oil pressure
                    sample_count=len(group),
                    min_oil_pressure=min_oil_pressure, # Minimum oil pressure
                    max_oil_pressure=max_oil_pressure, # Maximum oil pressure
                    avg_coolant_temperature=avg_coolant_temperature, # Average coolant temperature
                    oil_pressure_trend=oil_pressure_trend, # Trend slope, oil pressure
                    coolant_temperature_trend=coolant_temperature_trend, # Trend slope, coolant T
                    avg_fuel_pressure=avg_fuel_pressure, # Average fuel pressure
                    stddev_fuel_pressure=stddev_fuel_pressure, # Standard deviation, fuel pressure
                    min_fuel_pressure=min_fuel_pressure, # Minimum fuel pressure
                    max_fuel_pressure=max_fuel_pressure, # Maximum fuel pressure
                    fuel_pressure_trend=fuel_pressure_trend, # Trend slope, fuel pressure
                    avg_fuel_temperature=avg_fuel_temperature, # Average fuel temperature
                    stddev_fuel_temperature=stddev_fuel_temperature, # Standard deviation, fuel temperature
                    min_fuel_temperature=min_fuel_temperature, # Minimum fuel temperature
                    max_fuel_temperature=max_fuel_temperature, # Maximum fuel temperature
                    fuel_temperature_trend=fuel_temperature_trend, # Trend slope, fuel temperature
                    avg_fuel_rate=avg_fuel_rate, # Average fuel rate
                    stddev_fuel_rate=stddev_fuel_rate, # Standard deviation, fuel rate
                    min_fuel_rate=min_fuel_rate, # Minimum fuel rate
                    max_fuel_rate=max_fuel_rate, # Maximum fuel rate
                    fuel_rate_trend=fuel_rate_trend, # Trend slope, fuel rate
                    avg_intake_air_temperature=avg_intake_air_temperature, # Average intake air temperature
                    stddev_intake_air_temperature=stddev_intake_air_temperature, # Standard deviation, intake air temperature
                    min_intake_air_temperature=min_intake_air_temperature, # Minimum intake air temperature
                    max_intake_air_temperature=max_intake_air_temperature, # Maximum intake air temperature
                    intake_air_temperature_trend=intake_air_temperature_trend, # Trend slope, intake air temperature
                    avg_intake_air_pressure=avg_intake_air_pressure, # Average intake air pressure
                    stddev_intake_air_pressure=stddev_intake_air_pressure, # Standard deviation, intake air pressure
                    min_intake_air_pressure=min_intake_air_pressure, # Minimum intake air pressure
                    max_intake_air_pressure=max_intake_air_pressure, # Maximum intake air pressure
                    intake_air_pressure_trend=intake_air_pressure_trend, # Trend slope, intake air pressure
                    trend_slope=trend_slope,  # Trend slope, RPMs
                    start_time=start_time,
                    end_time=current_time
                )
                
                baselines.append(baseline)
                self.logger.info(f"Created baseline for {load_band}: avg_engine_speed={avg_engine_speed:.1f} ± {stddev_engine_speed:.1f} RPM (trend: {trend_slope:.3f}/day), avg_oil_pressure={avg_oil_pressure:.1f} ± {stddev_oil_pressure:.1f} kPa; ({min_oil_pressure:.0f}-{max_oil_pressure:.0f} r, trend: {oil_pressure_trend:.3f}/day); avg_power_output={avg_power_output:.1f} kW, avg_coolant_temperature={avg_coolant_temperature:.1f}°C, (trend:{coolant_temperature_trend:.3f}/day); avg_fuel_pressure={avg_fuel_pressure:.1f} ± {stddev_fuel_pressure:.1f} kPa; ({min_fuel_pressure:.0f}-{max_fuel_pressure:.0f} r, trend: {fuel_pressure_trend:.3f}/day); avg_fuel_temperature={avg_fuel_temperature:.1f} ± {stddev_fuel_temperature:.1f}°C; ({min_fuel_temperature:.0f}-{max_fuel_temperature:.0f} r, trend: {fuel_temperature_trend:.3f}/day); avg_fuel_rate={avg_fuel_rate:.1f} ± {stddev_fuel_rate:.1f} L/h; ({min_fuel_rate:.0f}-{max_fuel_rate:.0f} r, trend: {fuel_rate_trend:.3f}/day); avg_intake_air_temperature={avg_intake_air_temperature:.1f} ± {stddev_intake_air_temperature:.1f}°C; ({min_intake_air_temperature:.0f}-{max_intake_air_temperature:.0f} r, trend: {intake_air_temperature_trend:.3f}/day); avg_intake_air_pressure={avg_intake_air_pressure:.1f} ± {stddev_intake_air_pressure:.1f} kPa; ({min_intake_air_pressure:.0f}-{max_intake_air_pressure:.0f} r, trend: {intake_air_pressure_trend:.3f}/day); ({len(group)} samples)")
            
            self.logger.info(f"Successfully calculated {len(baselines)} load band baselines")

            # Also refresh baselines for load bands we didn't see this run (optional)
            if preserve_existing:
                for load_band, previous in existing.items():
                    if load_band in processed_bands or any(b.load_band == load_band for b in baselines):
                        continue
                    refreshed = replace(previous, start_time=current_time, end_time=current_time)
                    influx_client.store_historical_baseline(refreshed)
                    preserved_baselines.append(refreshed)
                    self.logger.info(f"Preserving existing baseline for {load_band}; no data in recent window")

            # Write all calculated baselines to InfluxDB
            for baseline in baselines:
                try:
                    influx_client.store_historical_baseline(baseline)
                    self.logger.debug(f"Stored baseline for {baseline.load_band}")
                except Exception as e:
                    self.logger.error(f"Failed to store baseline for {baseline.load_band}: {e}")

            total_baselines = len(baselines) + len(preserved_baselines)
            if total_baselines > 0:
                self._write_bootstrap_status(total_baselines, influx_client)

            return baselines + preserved_baselines
            
        except Exception as e:
            self.logger.error(f"Failed to calculate load band baselines: {e}")
            return []
