# PowertrainAgent Deployment Guide

## 🎯 What We Built

PowertrainAgent is a sophisticated AI-powered monitoring system that solves the critical challenge of **persistent memory** in generator health analysis. Unlike traditional monitoring systems that analyze data in isolation, PowertrainAgent **remembers** and **learns** from every data point since day one of operation.

### Key Innovation: Persistent Historical Memory

**The Problem**: Every day adds new data, but most monitoring systems forget the past. How do we ensure current analysis considers ALL historical context?

**Our Solution**: Multi-layered persistent memory system that:

1. **Accumulates Knowledge**: Every analysis builds upon ALL previous data
2. **Remembers Patterns**: Stores recurring events and operational signatures  
3. **Evolves Understanding**: AI insights grow more accurate over time
4. **Contextual Analysis**: Current conditions compared against full operational history

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Historical    │    │   Live Metrics   │    │  Memory-Enhanced│
│   Data Store    │────▶│   Collection     │────▶│   AI Analysis   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Persistent Memory System                       │
├──────────────────┬──────────────────┬──────────────────────────┤
│ Historical       │ Event Memory     │ AI Knowledge Store       │
│ Baselines        │ Pattern Recog.   │ Accumulated Insights     │
└──────────────────┴──────────────────┴──────────────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Layer     │    │    Alerting      │    │   Dashboard     │
│   Integration   │    │    System        │    │   Display       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📦 Components Delivered

### Core PowertrainAgent (`/powertrain-agent/`)
- **`agent_powertrain.py`**: Main orchestration and analysis engine
- **`memory_manager.py`**: Persistent memory system with bootstrap capabilities
- **`influx_query.py`**: Advanced database queries and historical data access
- **`prompt_builder.py`**: Memory-enhanced AI prompt construction
- **`logger.py`**: Results storage and alert management

### Docker Integration
- **`Dockerfile.powertrain`**: Containerized deployment
- **Updated `docker-compose.yml`**: PowertrainAgent service integration
- **Environment variables**: Configuration management

### API Integration
- **5 new FastAPI endpoints** added to existing backend:
  - `/api/powertrain-status` - Current health and analysis
  - `/api/powertrain-trends` - Historical trend data
  - `/api/powertrain-alerts` - Alert management
  - `/api/powertrain-baselines` - Statistical baselines
  - `/api/powertrain-memory` - AI accumulated insights

## 🚀 Deployment Steps

### Step 1: Verify Prerequisites
```bash
# Ensure existing system is running
cd /home/yarik/Code/MAIT
docker compose ps

# Should show: influxdb, backend, frontend, modbus-poller all running
```

### Step 2: Build PowertrainAgent
```bash
# Build the new PowertrainAgent container
docker compose build powertrain-agent

# Verify the build succeeded
docker images | grep powertrain
```

### Step 3: Bootstrap Historical Memory (CRITICAL)
```bash
# Start PowertrainAgent in bootstrap mode to process ALL historical data
docker compose run --rm powertrain-agent python powertrain-agent/agent_powertrain.py --bootstrap

# This processes all existing generator data to create baseline memory
# Expected duration: 5-15 minutes depending on data volume
```

### Step 4: Start Continuous Monitoring
```bash
# Start PowertrainAgent in continuous mode
docker compose up -d powertrain-agent

# Verify it's running
docker compose ps powertrain-agent
```

### Step 5: Verify Operation
```bash
# Check PowertrainAgent logs
docker compose logs powertrain-agent -f

# Test API endpoints
curl http://localhost:8001/api/powertrain-status
curl http://localhost:8001/api/powertrain-memory
```

## 🧠 Memory System Operation

### Bootstrap Process (First Run Only)
When you run `--bootstrap`, PowertrainAgent:

1. **Scans ALL Historical Data**: Processes every data point since logging began
2. **Creates Statistical Baselines**: Calculates normal ranges for each load band
3. **Identifies Patterns**: Finds recurring events and seasonal variations
4. **Builds Knowledge Base**: Creates comprehensive operational memory
5. **Stores Persistent Memory**: Saves baselines in InfluxDB for future use

### Continuous Operation (Every 5 Minutes)
Each analysis cycle:

1. **Collects Live Data**: Gets latest powertrain metrics
2. **Loads Memory Context**: Retrieves relevant historical baselines and patterns
3. **Builds Enhanced Prompt**: Creates AI prompt with full historical context
4. **Generates Analysis**: GPT-4 analyzes with accumulated knowledge
5. **Updates Memory**: Stores new insights and updates baselines
6. **Creates Alerts**: Generates contextual alerts and recommendations

## 📊 Memory Database Schema

PowertrainAgent creates three new InfluxDB measurements:

### `powertrain_baselines`
Historical statistical baselines for trend comparison
```
Tags: load_band, period_type
Fields: avg_oil_pressure, stddev_oil_pressure, trend_slope, confidence_level
```

### `powertrain_analysis` 
Analysis results and current metrics
```
Tags: load_band, alert_level  
Fields: engine_speed, oil_pressure, ai_analysis, analysis_summary
```

### `powertrain_ai_memory`
Accumulated AI insights and patterns
```
Tags: knowledge_type, confidence
Fields: insight_text, supporting_metrics, validation_status
```

## 🎛️ Configuration Options

### Environment Variables
```bash
# Analysis frequency (minutes)
POWERTRAIN_INTERVAL=5

# Bootstrap on startup (true/false)  
POWERTRAIN_BOOTSTRAP=false

# Database connection
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=your-token-here
```

### Command Line Options
```bash
# Bootstrap historical memory
python agent_powertrain.py --bootstrap

# Custom analysis interval
python agent_powertrain.py --interval 10

# Single analysis run
python agent_powertrain.py --single-run

# Custom config file
python agent_powertrain.py --config custom_config.yaml
```

## 🚨 Alert Levels & Thresholds

### Alert Severity Levels
- **OK**: Normal operation within historical parameters
- **INFO**: Notable observations, no action required
- **WARNING**: Deviation from normal patterns, monitor closely
- **CRITICAL**: Significant anomaly, immediate attention required
- **ERROR**: System malfunction, investigate immediately

### Configurable Thresholds
```python
alert_config = {
    'oil_pressure_critical': 150,    # kPa
    'oil_pressure_warning': 250,     # kPa  
    'rpm_deviation_warning': 50,     # RPM
    'rpm_deviation_critical': 100,   # RPM
    'consecutive_warnings': 3,       # Count before escalation
    'consecutive_criticals': 2       # Count before shutdown alert
}
```

## 📈 Expected Performance

### Memory Growth
- **Initial Bootstrap**: 10-50MB depending on historical data volume
- **Daily Growth**: ~1-5MB per day for analysis results and memory updates
- **Long-term**: Self-managing with InfluxDB retention policies

### Analysis Performance
- **Cycle Time**: 10-30 seconds per analysis
- **Memory Usage**: 100-500MB during operation
- **CPU Usage**: Low background load, moderate during analysis

### Data Retention
- **Raw Analysis**: 30 days (high frequency)
- **Hourly Baselines**: 1 year (statistical summaries)
- **Daily Baselines**: 5 years (long-term trends)
- **AI Memory**: Permanent (accumulated knowledge)

## 🔧 Troubleshooting

### Common Issues

**"No recent PowertrainAgent analysis found"**
- Solution: Ensure PowertrainAgent container is running
- Check: `docker compose logs powertrain-agent`

**"No baseline data found for load band"**
- Solution: Run bootstrap process first
- Command: `docker compose run --rm powertrain-agent python powertrain-agent/agent_powertrain.py --bootstrap`

**"Analysis temporarily unavailable"**
- Solution: Check OpenAI API key configuration
- Verify: OpenAI API key in `generator_config.yaml`

**Memory system not learning**
- Solution: Verify InfluxDB write permissions
- Check: Database storage space and retention policies

### Debug Commands
```bash
# Check all containers
docker compose ps

# View PowertrainAgent logs
docker compose logs powertrain-agent --tail 100

# Test database connectivity
docker compose exec powertrain-agent python -c "
from powertrain-agent.influx_query import InfluxQueryManager
import yaml
config = yaml.safe_load(open('generator_config.yaml'))
manager = InfluxQueryManager(config)
print('Database connection:', 'OK' if manager.client else 'FAILED')
"

# Check memory bootstrap status
curl http://localhost:8001/api/powertrain-baselines?load_band=0-20%
```

## 🎯 Success Metrics

### Immediate Indicators (First 24 Hours)
- [ ] PowertrainAgent container running without errors
- [ ] Bootstrap process completed successfully  
- [ ] API endpoints returning data
- [ ] First analysis results stored in InfluxDB

### Short-term Indicators (First Week)
- [ ] Baseline data accumulating for all load bands
- [ ] AI memory insights being stored
- [ ] Alert system detecting anomalies
- [ ] Trend analysis showing historical context

### Long-term Indicators (First Month)
- [ ] Memory system improving analysis accuracy
- [ ] Predictive insights becoming more specific
- [ ] Maintenance recommendations based on trends
- [ ] Seasonal patterns being identified

## 🎉 What This Achieves

PowertrainAgent transforms your generator monitoring from **reactive** to **predictive** by:

1. **Never Forgetting**: Every data point since day one contributes to current analysis
2. **Learning Continuously**: AI insights improve with operational experience
3. **Predicting Issues**: Early warning based on subtle pattern changes
4. **Contextual Alerts**: Alerts that understand historical context, not just current values
5. **Maintenance Optimization**: Data-driven maintenance scheduling

The system now has **institutional memory** like an experienced engineer who remembers every operating condition, every maintenance event, and every subtle change over the generator's entire operational life.

## 🔮 Next Steps

Once PowertrainAgent is operational, consider:

1. **Frontend Integration**: Add PowertrainAgent tab to React dashboard
2. **Mobile Alerts**: Push notifications for critical events
3. **Report Integration**: Include PowertrainAgent insights in daily reports
4. **Fleet Expansion**: Deploy to multiple generators for comparative analysis
5. **ML Enhancement**: Add machine learning models for failure prediction

PowertrainAgent is now ready to provide intelligent, memory-enhanced monitoring of your diesel generator's powertrain health! 🚀