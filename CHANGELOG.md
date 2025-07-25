# Changelog

All notable changes to MAIT (Modular Analytics & Intelligence Toolkit) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0-ai-enhanced] - 2025-07-25 (feature/powertrain-ai branch)

### Added
- **PowertrainAgent**: Complete AI-powered intelligent health monitoring system
- **Persistent Memory System**: Multi-layered historical baselines (hourly, daily, weekly, monthly)
- **OpenAI Integration**: GPT-4 powered health assessments and recommendations
- **Load Band Classification**: Intelligent power output categorization (0%, 0-20%, 20-40%, 40-60%, 60-80%, 80-100%)
- **Pattern Recognition**: Historical trend analysis with learning capabilities
- **Smart Alerts**: Context-aware alert system with severity classification
- **Bootstrap Memory**: Process ALL historical data for comprehensive analysis
- **Frontend AI Dashboard**: PowertrainAgent integration in Reports tab with three-column layout
- **Real-time Status Indicators**: Auto-refresh with 30-second and 5-minute intervals
- **Alert Management Center**: Comprehensive alert tracking with severity levels
- **Historical Intelligence Display**: Memory insights with confidence levels
- **New API Endpoints**: 
  - `/api/powertrain-status` - Current analysis and health status
  - `/api/powertrain-alerts` - Recent alerts and warnings
  - `/api/powertrain-memory` - AI accumulated insights
  - `/api/powertrain-trends` - Historical trend data
  - `/api/powertrain-baselines` - Statistical baselines
- **Enhanced Documentation**: POWERTRAIN_DEPLOYMENT.md and POWERTRAIN_FRONTEND_DEPLOYMENT.md

### Changed
- Enhanced Reports tab with PowertrainAgent control panel
- Improved InfluxDB integration with three new measurements
- Extended Docker architecture with PowertrainAgent microservice
- Updated frontend with PowertrainAgent-specific styling

### Technical Details
- New PowertrainAgent microservice with 5-minute analysis cycles
- Comprehensive logging and performance tracking
- Event-driven alert system with multi-level severity
- Memory-enhanced AI prompts using accumulated operational knowledge
- Real-time anomaly detection with historical context

## [2.0.0] - 2025-07-25 (Stable Release - git tag v2.0.0)

### Features
- Real-time generator monitoring dashboard
- Modbus TCP integration with DecisionMaker3500 controllers
- InfluxDB time-series data storage
- React-based interactive frontend
- Docker containerized deployment
- Event monitoring and alert tracking
- Multi-device network access
- Live data visualization with charts and trends
- Console logging with real-time updates
- Professional documentation with visual guides

### Architecture
- Modbus Poller: Python script for data collection
- FastAPI Backend: Data processing and API services
- React Frontend: Real-time dashboard interface
- InfluxDB: Time-series metrics storage
- nginx: Frontend serving and API proxy
- Docker Compose: Multi-container orchestration

### Deployment
- Complete Docker-based deployment
- Environment variable configuration
- Shared volume logging
- Service health checks
- Port configuration (Frontend: 3000, Backend: 8001, InfluxDB: 8086)

## Version Strategy

- **v2.0.0**: Stable, proven monitoring system without AI features
- **v3.0.0-ai-enhanced**: Advanced AI-powered monitoring with PowertrainAgent
- Users can choose version based on requirements:
  - Basic monitoring: `git checkout v2.0.0`
  - AI-enhanced: `git checkout feature/powertrain-ai`