# Generator Monitoring System - Project Memory

## Project Overview
A comprehensive generator monitoring system built with a microservices architecture using Docker containers. The system monitors generator health metrics via Modbus TCP, stores data in InfluxDB, and provides real-time visualization through a React-based web interface.

## System Architecture

### Core Components
1. **Frontend**: React application with emoji-enhanced UI for user interaction
2. **Backend**: FastAPI service handling API requests and data processing
3. **Database**: InfluxDB for time-series data storage
4. **Modbus Poller**: Python service collecting generator data via Modbus TCP
5. **Docker Orchestration**: Complete containerized deployment

### Data Flow
```
Generator (Modbus TCP) → Modbus Poller → InfluxDB → Backend API → React Frontend
                                    ↓
                               Log Files (shared volume)
```

## File Structure and Key Locations

### Root Directory Structure
```
MAIT-main/
├── Local code/                    # Local development environment
│   ├── gen_modbus_tcp.py         # Modbus poller (moved from backend folder)
│   ├── generator_config.yaml     # Real secrets and configuration
│   ├── docker-compose.yml        # Docker orchestration
│   ├── Dockerfile.poller         # Poller container definition
│   ├── mait-backend/            # FastAPI backend service
│   └── mait-front/              # React frontend application
├── docker_deployment/            # Docker deployment environment
│   ├── gen_modbus_tcp.py         # Synchronized poller
│   ├── generator_config.yaml     # Generic placeholder values
│   ├── docker-compose.yml        # Synchronized compose file
│   └── [same structure as Local code]
└── PROJECT_MEMORY.md             # This file
```

### Key File Details
- **Modbus Poller**: `gen_modbus_tcp.py` is at root level in both folders (moved from backend/)
- **Configuration**: Single `generator_config.yaml` per environment (no more configs/ folder)
- **Logs**: Shared via Docker volumes between containers at `/app/logs`
- **Synchronization**: Local code and docker_deployment folders are kept in sync

## Configuration Management

### Local Development Configuration
- **File**: `C:\Users\RLF Chief Engineer\Documents\Code\MAIT-main\Local code\generator_config.yaml`
- **Contains**: Real production secrets and values
- **InfluxDB**: 
  - Token: `ECRbc2byEqKeAMXsgI6YZvMh2g0DkYtyCP_l26xUgaNGj7-dtOWwSXDuCHZmCrF5L5NUdY_UEg5Z27bwQ9jfew==`
  - Organization: `mlr`
  - Bucket: `stbd_gen`
- **Modbus**: Real IP `192.168.127.254`

### Docker Deployment Configuration
- **File**: `C:\Users\RLF Chief Engineer\Documents\Code\MAIT-main\docker_deployment\generator_config.yaml`
- **Contains**: Generic placeholder values for deployment
- **InfluxDB**: 
  - Token: `changeme-token`
  - Organization: `default-org`
  - Bucket: `generator-metrics`
- **Modbus**: Generic IP `192.168.1.100`

### Configuration Features
- **Comprehensive Register Mapping**: 100+ generator parameters including voltages, currents, power, engine metrics
- **Event Management**: 60+ fault/alarm codes with descriptions
- **Anomaly Detection**: Configurable thresholds for different measurement types
- **Logging**: Structured text-only logging (no emojis for compatibility)

## Recent Major Changes (Resolved Issues)

### 1. Poller Location Standardization
- **Problem**: Confusion about poller location (backend folder vs root)
- **Solution**: Moved `gen_modbus_tcp.py` to root level in both environments
- **Result**: Clear, consistent structure across deployments

### 2. Emoji vs Text-Only Resolution
- **Problem**: Mixed emoji/non-emoji logging causing compatibility issues
- **Solution**: Frontend keeps emoji UI, all logs are text-only
- **Result**: User-friendly interface with compatible backend logging

### 3. Docker Backend Configuration Access
- **Problem**: Backend container couldn't access config file
- **Solution**: Proper volume mounting and file paths in docker-compose
- **Result**: All containers can access shared configuration

### 4. Deployment Synchronization
- **Problem**: Local and Docker folders had inconsistent files
- **Solution**: Synchronized all files between environments
- **Result**: Identical behavior in local and Docker deployments

### 5. Configuration Duplication Cleanup
- **Problem**: Multiple config files causing confusion
- **Solution**: Single config file per environment approach
- **Result**: Clear configuration management

## Current Working State

### Container Status
- **InfluxDB**: Running on port 8086
- **Backend API**: Running on port 8001
- **Frontend**: Running on port 3000
- **Modbus Poller**: Continuously polling and logging

### Functionality Verification
- ✅ Console tab displays real-time logs correctly
- ✅ Frontend has emoji-enhanced UI
- ✅ Logs are text-only for system compatibility
- ✅ All Docker containers start and communicate properly
- ✅ Both Local and Docker versions work identically

### Data Collection
- **Registers**: 100+ parameters monitored every 2 seconds
- **Events**: Real-time fault/alarm monitoring
- **Storage**: Time-series data in InfluxDB with 4-day retention
- **Logging**: Continuous text-based logs shared between containers

## Usage Instructions

### Local Development
```bash
# Navigate to Local code directory
cd "C:\Users\RLF Chief Engineer\Documents\Code\MAIT-main\Local code"

# Run modbus poller directly
python gen_modbus_tcp.py

# Or use Docker
docker-compose up --build -d
```

### Docker Deployment
```bash
# Navigate to docker_deployment directory
cd "C:\Users\RLF Chief Engineer\Documents\Code\MAIT-main\docker_deployment"

# Deploy full stack
docker-compose up --build -d

# View logs
docker-compose logs -f modbus-poller
```

### Configuration Updates
1. **Local Development**: Edit `Local code/generator_config.yaml` with real values
2. **Docker Deployment**: Edit `docker_deployment/generator_config.yaml` with deployment values
3. **Register Changes**: Both files share the same register definitions (synchronize changes)

## Development Notes

### Code Standards
- **Logging**: Text-only format for compatibility
- **UI**: Emoji-enhanced React interface for user experience
- **Configuration**: Environment-specific values in separate config files
- **Documentation**: Comprehensive inline comments in config files

### Architecture Benefits
- **Scalability**: Microservices can be scaled independently
- **Maintainability**: Clear separation of concerns
- **Deployment**: Flexible local/Docker options
- **Monitoring**: Real-time data collection and visualization

### Future Considerations
- Configuration files are environment-specific (keep synchronized for register definitions)
- Log rotation may be needed for long-term deployments
- Consider backup strategies for InfluxDB data
- Monitor container resource usage in production

## Troubleshooting Quick Reference

### Common Issues
1. **Config file not found**: Ensure `generator_config.yaml` is in correct directory
2. **Container communication**: Check Docker network configuration
3. **Log access**: Verify shared volume mounting in docker-compose
4. **UI not updating**: Check backend API connectivity and CORS settings

### File Locations for Debugging
- **Logs**: Docker shared volume `/app/logs`
- **Config**: Root level of each environment folder
- **Poller**: Root level `gen_modbus_tcp.py`
- **Backend**: `mait-backend/main.py`
- **Frontend**: `mait-front/src/`

---
*Last Updated: July 2025 - All systems operational and synchronized*