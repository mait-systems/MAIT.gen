#!/usr/bin/env python3
"""
Simple test script for BaselineCalculator
Run with: python test_baseline_calc.py
"""

import yaml
import logging
from influx_query import InfluxQueryManager
from baseline_calculator import BaselineCalculator

import warnings
from influxdb_client.client.warnings import MissingPivotFunction

warnings.simplefilter("ignore", MissingPivotFunction)

def main():
    # Set up logging to see detailed output
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Load config
        print("Loading configuration...")
        with open('../generator_config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Get historical data
        print("\nFetching historical data...")
        influx = InfluxQueryManager(config)

        data = influx.get_all_historical_data()
        
        if data is None or data.empty:
            print("No historical data found!")
            return
        
        # Quick data inspection
        print(f"\n=== DATA INSPECTION ===")
        print(f"Data shape: {data.shape}")
        print(f"Columns: {data.columns.tolist()}")
        print(f"Date range: {data['_time'].min()} to {data['_time'].max()}")
        print(f"\nLoad band distribution:")
        print(data['load_band'].value_counts().sort_index())
        
        # ENGINE SPEED general data inspection
        print(f"\nEngine Speed data quality:")
        engine_speed_data = data['Engine_Speed'].dropna()
        print(f"  Mean: {engine_speed_data.mean():.1f} RPM")
        print(f"  Std Dev: {engine_speed_data.std():.1f} RPM") 
        print(f"  Range: {engine_speed_data.min():.0f} - {engine_speed_data.max():.0f} RPM")

        # OIL PRESSURE general data inspection
        print(f"\nEngine Oil Pressure data quality:")
        oil_pressure_data = data['Engine_Oil_Pressure'].dropna() 
        print(f"  Mean: {oil_pressure_data.mean():.1f} kPa")
        print(f"  Std Dev: {oil_pressure_data.std():.1f} kPa")
        print(f"  Range: {oil_pressure_data.min():.0f} - {oil_pressure_data.max():.0f} kPa")

        # POWER OUTPUT general data inspection
        print(f"\nGenerator Power Output data quality:")
        power_output_data = data['Generator_Total_Real_Power'].dropna()
        print(f"  Mean: {power_output_data.mean():.1f} kW")
        print(f"  Std Dev: {power_output_data.std():.1f} kW")
        print(f"  Range: {power_output_data.min():.0f} - {power_output_data.max():.0f} kW")

        # COOLANT TEMPERATURE general data inpsection
        print(f"\nEngine Coolant Temperature data quality:")
        coolant_temp_data = data['Engine_Coolant_Temperature'].dropna()
        print(f"  Mean: {coolant_temp_data.mean():.1f}°C")
        print(f"  Std Dev: {coolant_temp_data.std():.1f}°C")
        print(f"  Range: {coolant_temp_data.min():.0f} - {coolant_temp_data.max():.0f}°C")

        # FUEL PRESSURE general data inspection
        print(f"\nEngine Fuel Pressure data quality:")
        fuel_pressure_data = data['Engine_Fuel_Pressure'].dropna()
        print(f"  Mean: {fuel_pressure_data.mean():.1f} kPa")
        print(f"  Std Dev: {fuel_pressure_data.std():.1f} kPa")
        print(f"  Range: {fuel_pressure_data.min():.0f} - {fuel_pressure_data.max():.0f} kPa")

        # FUEL TEMPERATURE general data inspection
        print(f"\nEngine Fuel Temperature data quality:")
        fuel_temp_data = data['Engine_Fuel_Temperature'].dropna()
        print(f"  Mean: {fuel_temp_data.mean():.1f}°C")
        print(f"  Std Dev: {fuel_temp_data.std():.1f}°C")
        print(f"  Range: {fuel_temp_data.min():.0f} - {fuel_temp_data.max():.0f}°C")

        # FUEL RATE general data inspection
        print(f"\nEngine Fuel Rate data quality:")
        fuel_rate_data = data['Engine_Fuel_Rate'].dropna()
        print(f"  Mean: {fuel_rate_data.mean():.1f} L/h")
        print(f"  Std Dev: {fuel_rate_data.std():.1f} L/h")
        print(f"  Range: {fuel_rate_data.min():.0f} - {fuel_rate_data.max():.0f} L/h")

        # INTAKE AIR TEMPERATURE general data inspection
        print(f"\nIntake Air Temperature data quality:")
        intake_air_temp_data = data['Intake_Air_Temperature'].dropna()
        print(f"  Mean: {intake_air_temp_data.mean():.1f}°C")
        print(f"  Std Dev: {intake_air_temp_data.std():.1f}°C")
        print(f"  Range: {intake_air_temp_data.min():.0f} - {intake_air_temp_data.max():.0f}°C")

        # INTAKE AIR PRESSURE general data inspection
        print(f"\nIntake Air Pressure data quality:")
        intake_air_pressure_data = data['Intake_Air_Pressure'].dropna()
        print(f"  Mean: {intake_air_pressure_data.mean():.1f} kPa")
        print(f"  Std Dev: {intake_air_pressure_data.std():.1f} kPa")
        print(f"  Range: {intake_air_pressure_data.min():.0f} - {intake_air_pressure_data.max():.0f} kPa")
                
        print(f"\nSample data (first 5 rows):")
        print(data[['_time', 'Engine_Speed', 'Engine_Oil_Pressure', 'Generator_Total_Real_Power', 'Engine_Coolant_Temperature', 'Engine_Fuel_Pressure', 'Engine_Fuel_Temperature', 'Engine_Fuel_Rate', 'Intake_Air_Temperature', 'Intake_Air_Pressure', 'load_band']].head())
        
        # Test calculator
        print(f"\n=== BASELINE CALCULATION ===")
        calc = BaselineCalculator(config)
        baselines = calc.calculate_load_band_baselines(data, influx)
        
        # Show results
        if baselines:
            print(f"Successfully calculated {len(baselines)} baselines:")
            for b in baselines:
                print(f"\n  === {b.load_band} Load Band ({b.sample_count} samples) ===")
                print(f"    Engine Speed: {b.avg_engine_speed:.1f} ± {b.stddev_engine_speed:.1f} RPM (trend: {b.trend_slope:.3f}/day)")
                print(f"    Oil Pressure: {b.avg_oil_pressure:.1f} ± {b.stddev_oil_pressure:.1f} kPa ({b.min_oil_pressure:.0f}-{b.max_oil_pressure:.0f} range, trend: {b.oil_pressure_trend:.3f}/day)")
                print(f"    Power Output: {b.avg_power_output:.1f} kW")
                print(f"    Coolant Temp: {b.avg_coolant_temperature:.1f}°C (trend: {b.coolant_temperature_trend:.3f}/day)")
                print(f"    Fuel Pressure: {b.avg_fuel_pressure:.1f} ± {b.stddev_fuel_pressure:.1f} kPa ({b.min_fuel_pressure:.0f}-{b.max_fuel_pressure:.0f} range, trend: {b.fuel_pressure_trend:.3f}/day)")
                print(f"    Fuel Temperature: {b.avg_fuel_temperature:.1f} ± {b.stddev_fuel_temperature:.1f}°C ({b.min_fuel_temperature:.0f}-{b.max_fuel_temperature:.0f} range, trend: {b.fuel_temperature_trend:.3f}/day)")
                print(f"    Fuel Rate: {b.avg_fuel_rate:.1f} ± {b.stddev_fuel_rate:.1f} L/h ({b.min_fuel_rate:.0f}-{b.max_fuel_rate:.0f} range, trend: {b.fuel_rate_trend:.3f}/day)")
                print(f"    Intake Air Temp: {b.avg_intake_air_temperature:.1f} ± {b.stddev_intake_air_temperature:.1f}°C ({b.min_intake_air_temperature:.0f}-{b.max_intake_air_temperature:.0f} range, trend: {b.intake_air_temperature_trend:.3f}/day)")
                print(f"    Intake Air Pressure: {b.avg_intake_air_pressure:.1f} ± {b.stddev_intake_air_pressure:.1f} kPa ({b.min_intake_air_pressure:.0f}-{b.max_intake_air_pressure:.0f} range, trend: {b.intake_air_pressure_trend:.3f}/day)")
        else:
            print("No baselines calculated!")

        # Verify writes to InfluxDB
        print("\n=== INFLUXDB WRITE VERIFICATION ===")

        # Check bootstrap status
        print("Checking bootstrap status...")
        try:
            bootstrap_query = f"""
            from(bucket: "{config['influxdb']['bucket']}")
            |> range(start: -1h)
            |> filter(fn: (r) => r._measurement == "powertrain_system_status")
            |> last()
            """

            status_result = influx.client.query_api().query_data_frame(
                query=bootstrap_query,
                org=config['influxdb']['org']
            )

            # Handle list result from Influx
            if isinstance(status_result, list):
                if status_result:
                    import pandas as pd
                    status_result = pd.concat(status_result, ignore_index=True)
                else:
                    status_result = pd.DataFrame()

            if not status_result.empty:
                print("✅ Bootstrap status written:")
                for _, row in status_result.iterrows():
                    print(f"  {row['_field']}: {row['_value']}")
            else:
                print("❌ No bootstrap status found")

        except Exception as e:
            print(f"❌ Bootstrap status check failed: {e}")

        # Check baseline data
        print("\nChecking stored baselines...")
        try:
            baseline_query = f"""
            from(bucket: "{config['influxdb']['bucket']}")
            |> range(start: -1h)
            |> filter(fn: (r) => r._measurement == "powertrain_baselines")
            |> group(columns: ["load_band"])
            |> count()
            """

            baseline_result = influx.client.query_api().query_data_frame(
                query=baseline_query,
                org=config['influxdb']['org']
            )

            if not baseline_result.empty:
                print("✅ Baseline data written:")
                for _, row in baseline_result.iterrows():
                    print(f"  Load band {row['load_band']}: {row['_value']} records")
            else:
                print("❌ No baseline data found")

        except Exception as e:
            print(f"❌ Baseline data check failed: {e}")

            
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()