# PowertrainAgent - Intelligent Monitoring

PowertrainAgent is an advanced monitoring system that provides real-time and trend-based analysis of powertrain health using persistent memory.

## Features

### Persistent Memory System
- **Historical Baselines**: Rolling statistical baselines for different load bands and time periods
- **Event Memory**: Pattern recognition of recurring issues and maintenance events

### Real-time Analysis
- Engine speed stability monitoring
- Oil pressure trend analysis
- Load efficiency assessment
- Coolant temperature tracking
- RPM deviation detection

#### Statistical Analysis (Tagged as "STAT:" in frontend)  
- **Mathematical trend detection** using linear regression on historical data
- **Load band-specific analysis** for different operating conditions (0%, 0-20%, 20-40%, etc.)
- **P-value statistical testing** to ensure trends are not random (p < 0.05 required)
- **Pattern recognition** for hourly and daily operational cycles

### Smart Alerting
   
- **Statistical Anomaly Detection** - Pattern-based monitoring
- 2-sigma deviation from historical baselines triggers WARNING
- 3-sigma deviation triggers CRITICAL alerts
- Load band-specific threshold management


## Architecture

```
Historical Data → Memory Bootstrap → Persistent Baselines
     ↓
Live Metrics → Memory Context → Results Storage
     ↓
Alerts & Recommendations → API Endpoints → Dashboard
```
## API Endpoints

PowertrainAgent integrates with the existing FastAPI backend:

- `GET /api/powertrain-status` - Current analysis and health status
- `GET /api/powertrain-trends?hours=24` - Historical trend data
- `GET /api/powertrain-alerts?hours=24` - Recent alerts and warnings
- `GET /api/powertrain-baselines?load_band=0-20%` - Historical baselines
- `GET /api/powertrain-memory?knowledge_type=trend` - AI accumulated insights, if enabled
- `GET /api/powertrain-local-analysis` - Local-only analysis.

## Memory System Details

### Database Schema
PowertrainAgent writes the following InfluxDB measurements:

1. **powertrain_baselines**: Historical statistical baselines
   - Tags: `load_band`, `period_type`
   - Fields: `avg_oil_pressure`, `stddev_oil_pressure`, `trend_slope`, etc.

2. **powertrain_analysis**: Analysis results and metrics (alerts are stored here)
   - Tags: `load_band`, `alert_level`, `mode`, `analysis_type`
   - Fields: `engine_speed`, `oil_pressure`, `ai_analysis`, `analysis_summary`, etc.

3. **powertrain_ai_memory**: Accumulated AI insights, if enabled
   - Tags: `knowledge_type`, `confidence`
   - Fields: `insight_text`, `supporting_metrics`

4. **powertrain_system_status**: Bootstrap and system state
   - Fields: `bootstrap_completed`, `baseline_count`, `bootstrap_timestamp`, etc.

5. **powertrain_system_events**: System events and lifecycle logs
   - Tags: `event_type`, `severity`
   - Fields: `message`, `system_status`

6. **powertrain_recommendations**: Recommendations persisted from AI runs, if enabled
   - Tags: `alert_level`, `priority`
   - Fields: `recommendation`, `status`

### Memory Bootstrap Process
1. **Historical Scan**: Process ALL existing data in InfluxDB (default last 30 days)
2. **Baseline Creation**: Calculate statistical norms for each load band; Baselines are refreshed (age > 7 days or missing load band).
4. **Trend Analysis**: Establish degradation curves and wear patterns
5. **Knowledge Storage**: Create comprehensive baseline datasets

### Local Statistical Analysis Process (STAT: Tags)

**Data Sources:**
- Raw time-series data from InfluxDB (minimum 10 data points required)
- Historical measurements grouped by load bands (0%, 0-20%, 20-40%, etc.)
- Mathematical calculations using scipy.stats.linregress

**Processing Steps:**
1. **Data Grouping**: Separates measurements by generator load levels
2. **Time Series Analysis**: Sorts data chronologically for trend detection
3. **Linear Regression**: Calculates slope, R-squared, and p-values for each metric
4. **Significance Testing**: Only reports trends with p < 0.05 AND |slope| > 0.01

**Output Examples:**
```
 Engine_Oil_Pressure showing declining trend in 20-40% load band (R²=0.850)
 Generator_Total_Real_Power showing stable trend in 0-20% load band (R²=0.652)
 Engine_Speed showing increasing trend in 40-60% load band (R²=0.923)
```
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
1. **No Historical Data**: Wait for the bootstrap process to complete
4. **Missing Baselines**: Ensure sufficient historical data exists

### Logs and Debugging
```bash
# Check PowertrainAgent logs
docker logs powertrain-agent