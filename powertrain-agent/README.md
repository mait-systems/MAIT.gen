# PowertrainAgent - Intelligent Diesel Generator Monitoring

PowertrainAgent is an advanced monitoring system that provides real-time and trend-based analysis of diesel generator powertrain health using AI and persistent memory.

## Features

### 🧠 Persistent Memory System
- **Historical Baselines**: Rolling statistical baselines for different load bands and time periods
- **Event Memory**: Pattern recognition of recurring issues and maintenance events
- **AI Knowledge Store**: Accumulated insights that grow with operational experience
- **Trend Analysis**: Long-term degradation tracking and predictive maintenance

### 📊 Real-time Analysis
- Engine speed stability monitoring
- Oil pressure trend analysis
- Load efficiency assessment
- Coolant temperature tracking
- RPM deviation detection

### 🤖 AI-Powered Insights
- GPT-4 integration for natural language analysis
- Memory-enhanced prompts that include full operational history
- Predictive maintenance recommendations
- Anomaly detection with historical context

### 🚨 Smart Alerting
- Multi-level alert system (OK, WARNING, CRITICAL)
- Context-aware alerts based on historical patterns
- Consecutive alert tracking and escalation
- Load band-specific threshold management

## Architecture

```
Historical Data → Memory Bootstrap → Persistent Baselines
     ↓
Live Metrics → Memory Context → AI Analysis → Results Storage
     ↓
Alerts & Recommendations → API Endpoints → Dashboard
```

## Installation & Usage

### Docker Deployment (Recommended)
```bash
# Add PowertrainAgent to existing docker-compose.yml
docker compose up --build powertrain-agent

# Bootstrap historical memory (first run only)
docker compose exec powertrain-agent python powertrain-agent/agent_powertrain.py --bootstrap

# Check logs
docker compose logs powertrain-agent -f
```

### Standalone Usage
```bash
# Install dependencies
pip install -r requirements.txt

# Bootstrap memory system
python agent_powertrain.py --bootstrap --config generator_config.yaml

# Run continuous monitoring (5-minute intervals)
python agent_powertrain.py --config generator_config.yaml --interval 5

# Single analysis run
python agent_powertrain.py --single-run --config generator_config.yaml
```

## API Endpoints

PowertrainAgent integrates with the existing FastAPI backend:

- `GET /api/powertrain-status` - Current analysis and health status
- `GET /api/powertrain-trends?hours=24` - Historical trend data
- `GET /api/powertrain-alerts?hours=24` - Recent alerts and warnings
- `GET /api/powertrain-baselines?load_band=0-20%` - Historical baselines
- `GET /api/powertrain-memory?knowledge_type=trend` - AI accumulated insights

## Configuration

PowertrainAgent uses the same `generator_config.yaml` as the main system:

```yaml
# InfluxDB configuration
influxdb:
  url: "http://influxdb:8086"
  token: "your-token"
  org: "mlr"
  bucket: "stbd_gen"

# OpenAI configuration  
openai:
  api_key: "your-openai-key"

# Logging configuration
logging:
  filename: "powertrain_agent.log"
  level: "INFO"
```

## Environment Variables

- `POWERTRAIN_INTERVAL`: Analysis interval in minutes (default: 5)
- `POWERTRAIN_BOOTSTRAP`: Set to 'true' to bootstrap on startup
- `INFLUXDB_URL`: InfluxDB connection URL
- `INFLUXDB_TOKEN`: InfluxDB authentication token

## Memory System Details

### Database Schema
PowertrainAgent creates three new InfluxDB measurements:

1. **powertrain_baselines**: Historical statistical baselines
   - Tags: `load_band`, `period_type`
   - Fields: `avg_oil_pressure`, `stddev_oil_pressure`, `trend_slope`, etc.

2. **powertrain_analysis**: Analysis results and metrics
   - Tags: `load_band`, `alert_level`
   - Fields: `engine_speed`, `oil_pressure`, `ai_analysis`, etc.

3. **powertrain_ai_memory**: Accumulated AI insights
   - Tags: `knowledge_type`, `confidence`
   - Fields: `insight_text`, `supporting_metrics`

### Memory Bootstrap Process
1. **Historical Scan**: Process ALL existing data in InfluxDB
2. **Baseline Creation**: Calculate statistical norms for each load band
3. **Pattern Identification**: Find recurring events and seasonal variations
4. **Trend Analysis**: Establish degradation curves and wear patterns
5. **Knowledge Storage**: Create comprehensive baseline datasets

### Incremental Learning
- Each analysis updates memory with new patterns
- Historical baselines evolve with new data
- AI insights accumulate operational knowledge
- Event patterns improve anomaly detection

## Monitoring Metrics

### Key Performance Indicators
- **Oil Pressure Trends**: Early indication of pump wear or viscosity issues
- **RPM Stability**: Engine control system health and load response
- **Load Efficiency**: Power output vs engine performance correlation
- **Temperature Patterns**: Cooling system effectiveness

### Load Band Analysis
PowertrainAgent analyzes performance across different load bands:
- **0%**: Stopped/idle conditions
- **0-20%**: Light load operations
- **20-40%**: Moderate load operations  
- **40-60%**: Normal load operations
- **60-80%**: Heavy load operations
- **80-100%**: Maximum load operations

## Maintenance Integration

PowertrainAgent tracks the generator's 250-hour maintenance schedule:
- **Upcoming Service**: Alerts when approaching 250hr intervals
- **Performance Degradation**: Identifies wear patterns between services
- **Maintenance Effectiveness**: Analyzes performance improvements after service
- **Predictive Scheduling**: Recommends maintenance based on condition trends

## Troubleshooting

### Common Issues
1. **No Historical Data**: Run bootstrap process first
2. **Memory Gaps**: Check InfluxDB retention policies
3. **AI Analysis Failures**: Verify OpenAI API key configuration
4. **Missing Baselines**: Ensure sufficient historical data exists

### Logs and Debugging
```bash
# Check PowertrainAgent logs
docker compose logs powertrain-agent

# Debug memory system
docker compose exec powertrain-agent python -c "
from powertrain-agent.memory_manager import PowertrainMemoryManager
import yaml
config = yaml.safe_load(open('generator_config.yaml'))
memory = PowertrainMemoryManager(config)
print('Memory system status:', memory.memory_bootstrapped)
"
```

## Performance

- **Analysis Cycle**: ~10-30 seconds per run
- **Memory Usage**: ~100-500MB depending on historical data
- **CPU Usage**: Low when idle, moderate during analysis
- **Storage Growth**: ~1-5MB per day for analysis results

## Future Enhancements

- [ ] Machine learning models for failure prediction
- [ ] Integration with external maintenance systems
- [ ] Mobile app notifications for critical alerts
- [ ] Multi-generator fleet monitoring
- [ ] Advanced statistical process control
- [ ] Predictive parts replacement scheduling