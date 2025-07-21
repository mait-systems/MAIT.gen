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


load_dotenv()

app = FastAPI()

# Allow your React app to talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your actual domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load secrets
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INFLUXDB_URL = os.getenv("INFLUXDB_URL")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET")

# Initialize clients
openai = OpenAI(api_key=OPENAI_API_KEY)
influx_client = InfluxDBClient(
    url=INFLUXDB_URL,
    token=INFLUXDB_TOKEN,
    org=INFLUXDB_ORG,
    timeout=60_000)


def load_config(config_file='generator_config.yaml'):
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

config = load_config()
    
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
