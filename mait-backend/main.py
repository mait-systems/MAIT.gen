from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import pandas as pd
from influxdb_client import InfluxDBClient
from openai import OpenAI
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse
from fastapi import Request
import numpy as np
from fastapi import Query
import yaml


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
openai_config = config.get('openai', {})

OPENAI_API_KEY = openai_config.get('api_key', '')
INFLUXDB_URL = influxdb_config.get('url', 'http://localhost:8086')
INFLUXDB_TOKEN = influxdb_config.get('token', '')
INFLUXDB_ORG = influxdb_config.get('org', 'mlr')
INFLUXDB_BUCKET = influxdb_config.get('bucket', 'generator-metrics')

# Initialize clients
openai = OpenAI(api_key=OPENAI_API_KEY)
influx_client = InfluxDBClient(
    url=INFLUXDB_URL,
    token=INFLUXDB_TOKEN,
    org=INFLUXDB_ORG,
    timeout=60_000)
    
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

    # Extend time range to allow for long-lasting events
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -1h)
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


@app.get("/api/live-analysis")
async def live_analysis(request: Request):
    # Reuse your live stats function
    live_data = await get_live_stats()

    prompt = (
        "You are a generator technician reviewing real-time sensor data from a diesel generator.\n"
        "Please give a short and clear health summary. Just mention if the engine is running normally or not.\n"
        "Flag any values that look suspicious or out of range. Use bullet points and emojis if helpful.\n\n"
        "Ignore: Bus_Frequency, RMS_Bus_Voltage_Average_Line_to_Line, RMS_Bus_Voltage_L1-L2, RMS_Bus_Voltage_L2-L3, RMS_Bus_Voltage_L3-L1, Total_Bus_Reactive_Power, and Total_Bus_Real_Power"
        "If ECM_Fault_Codes equals to 65472, then it's just that modbus register is not supported in the given application so ignore it. Unless there is another value"
        f"Here is the current data:\n{live_data}"
    )

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    return {"analysis": response.choices[0].message.content}

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
      |> keep(columns: ["_time", "_value"])
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

@app.get("/api/generate-daily-report")
async def generate_daily_report():
    query_api = influx_client.query_api()

    
    query = f'''
    excludedFields = ["Rated_Current", "System_Voltage", "System_Frequency", "Genset_kW_Rating", "ECM_Model"]

    engineOnTimes = from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -2d)
      |> filter(fn: (r) => r._measurement == "generator_metrics" and r._field == "Engine_Speed")
      |> aggregateWindow(every: 3h, fn: last, createEmpty: false)
      |> map(fn: (r) => ({{ r with _value: float(v: r._value) }}))
      |> filter(fn: (r) => r._value > 0)
      |> keep(columns: ["_time"])

    allMetrics = from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -2d)
      |> filter(fn: (r) =>
    	r._measurement == "generator_metrics" and
    	not contains(value: r._field, set: excludedFields)
      )
      |> aggregateWindow(every: 3h, fn: last, createEmpty: false)
      |> map(fn: (r) => ({{ r with _value: float(v: r._value) }}))

    join(
      tables: {{a: allMetrics, b: engineOnTimes}},
      on: ["_time"]
    )
      |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
    '''
    
    
    result = query_api.query_data_frame(org=INFLUXDB_ORG, query=query)
	
	# Combine list of DataFrames if needed
    if isinstance(result, list):    
        result = pd.concat(result, ignore_index=True)
    if result.empty:
        return {"report": "No data found in the last 1 day."}

    # Convert DataFrame to simplified summary
    summary = result.describe().to_string()

    # Ask GPT to generate a natural language report
    prompt = (
    "You are an engineer monitoring Kohler Diesel Generator. It is a 6 cylinder diesel engine, with nominal power of 150kW at 1800rpm"
    "Nominal frequency is 60Hz. Based on the following generator data, generate a short report on the generator's health, trends."
    "See if you can spot any possible issues."
    "Format the response using nice markdown, with sections, emojis or whatever you think is good for readability."
    "Point out the important latest operational ranges, like the pressures (in kPa), load (%), power (kW), the latest data you got."
    "We service generators at every 250hours, so 250-500-1000-1250 etc. Keep it in  mind when giving hours value and see if we are approaching a service."
    
    f"{summary}"
    )

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    report = response.choices[0].message.content
    return {"report": report}

@app.get("/api/powertrain-status")
async def get_powertrain_status():
    """Get current PowertrainAgent status and latest analysis"""
    query_api = influx_client.query_api()
    
    # Get latest powertrain analysis
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -1h)
      |> filter(fn: (r) => r._measurement == "powertrain_analysis")
      |> last()
    '''
    
    try:
        result = query_api.query_data_frame(org=INFLUXDB_ORG, query=query)
        
        if isinstance(result, list):
            result = pd.concat(result, ignore_index=True)
        
        if result.empty:
            return {"status": "No recent PowertrainAgent analysis found"}
        
        # Convert to dictionary - handle InfluxDB data structure with tags and fields
        latest_data = {}
        
        for _, row in result.iterrows():
            field_name = row.get('_field')
            field_value = row.get('_value')
            
            # Store field values
            if field_name and field_value is not None:
                latest_data[field_name] = field_value
            
            # Store tags (they appear in every row)
            latest_data['alert_level'] = row.get('alert_level', 'UNKNOWN')
            latest_data['load_band'] = row.get('load_band', 'unknown')
            latest_data['_time'] = row.get('_time')
        
        # Handle timestamp conversion safely
        timestamp_value = latest_data.get("_time", "")
        if hasattr(timestamp_value, 'isoformat'):
            timestamp_str = timestamp_value.isoformat().replace("T", " ").replace("Z", "")
        else:
            timestamp_str = str(timestamp_value).replace("T", " ").replace("Z", "")
        
        return {
            "timestamp": timestamp_str,
            "alert_level": latest_data.get("alert_level", "UNKNOWN"),
            "load_band": latest_data.get("load_band", "unknown"),
            "engine_speed": latest_data.get("engine_speed", 0),
            "engine_oil_pressure": latest_data.get("engine_oil_pressure", 0),
            "generator_power": latest_data.get("generator_power", 0),
            "coolant_temperature": latest_data.get("coolant_temperature", 0),
            "analysis_summary": latest_data.get("analysis_summary", "No summary available"),
            "ai_analysis": latest_data.get("ai_analysis", "")
        }
        
    except Exception as e:
        return {"error": f"Failed to get powertrain status: {str(e)}"}

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
      |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
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
      |> filter(fn: (r) => r._measurement == "powertrain_alerts")
      |> sort(columns: ["_time"], desc: true)
      |> limit(n: 50)
    '''
    
    try:
        result = query_api.query_data_frame(org=INFLUXDB_ORG, query=query)
        
        if isinstance(result, list):
            result = pd.concat(result, ignore_index=True)
        
        if result.empty:
            return []
        
        alerts = []
        for _, row in result.iterrows():
            alert = {
                "timestamp": str(row.get("_time", "")),
                "severity": row.get("severity", "INFO"),
                "description": row.get("description", ""),
                "load_band": row.get("load_band", "unknown"),
                "oil_pressure": row.get("oil_pressure", 0),
                "engine_speed": row.get("engine_speed", 0),
                "resolved": row.get("resolved", False)
            }
            alerts.append(alert)
        
        return alerts
        
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
        
        if isinstance(result, list):
            result = pd.concat(result, ignore_index=True)
        
        if result.empty:
            return {"message": f"No baseline data found for load band {load_band}"}
        
        baselines = []
        for _, row in result.iterrows():
            baseline = {
                "timestamp": str(row.get("_time", "")),
                "load_band": row.get("load_band", load_band),
                "period_type": row.get("period_type", "hourly"),
                "avg_oil_pressure": row.get("avg_oil_pressure", 0),
                "avg_engine_speed": row.get("avg_engine_speed", 0),
                "avg_power_output": row.get("avg_power_output", 0),
                "sample_count": row.get("sample_count", 0),
                "confidence_level": row.get("confidence_level", 0)
            }
            baselines.append(baseline)
        
        return baselines
        
    except Exception as e:
        return {"error": f"Failed to get powertrain baselines: {str(e)}"}

@app.get("/api/powertrain-memory")
async def get_powertrain_memory(knowledge_type: str = "all", days: int = 7):
    """Get PowertrainAgent accumulated memory/insights"""
    query_api = influx_client.query_api()
    
    if knowledge_type == "all":
        filter_clause = 'r._measurement == "powertrain_ai_memory"'
    else:
        filter_clause = f'r._measurement == "powertrain_ai_memory" and r.knowledge_type == "{knowledge_type}"'
    
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -{days}d)
      |> filter(fn: (r) => {filter_clause})
      |> sort(columns: ["_time"], desc: true)
      |> limit(n: 20)
    '''
    
    try:
        result = query_api.query_data_frame(org=INFLUXDB_ORG, query=query)
        
        if isinstance(result, list):
            result = pd.concat(result, ignore_index=True)
        
        if result.empty:
            return {"message": "No memory data found", "insights": []}
        
        insights = []
        for _, row in result.iterrows():
            insight = {
                "timestamp": str(row.get("_time", "")),
                "knowledge_type": row.get("knowledge_type", "unknown"),
                "confidence": row.get("confidence", "medium"),
                "insight_text": row.get("insight_text", ""),
                "validation_status": row.get("validation_status", "pending")
            }
            insights.append(insight)
        
        return {"insights": insights, "total_count": len(insights)}
        
    except Exception as e:
        return {"error": f"Failed to get powertrain memory: {str(e)}"}
