# MAIT - Modular Analytics & Intelligence Toolkit - Project Memory

## Project Overview
A comprehensive generator monitoring system built with a microservices architecture using Docker containers. MAIT (Modular Analytics & Intelligence Toolkit) monitors generator health metrics via Modbus TCP, stores data in InfluxDB, and provides real-time visualization through a React-based web interface.

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
MAIT/
├── docker_deployment/                      # Production deployment (public)
│   ├── gen_modbus_tcp.py                  # Modbus poller
│   ├── generator_config.yaml.example     # Configuration template
│   ├── docker-compose.yml                # Docker orchestration
│   ├── Dockerfile.poller                 # Poller container definition
│   ├── mait-backend/                     # FastAPI backend service
│   └── mait-front/                       # React frontend application
├── Local code/                            # Private development environment (gitignored)
│   ├── [same structure as docker_deployment]
│   ├── generator_config.yaml             # Real secrets and configuration
│   └── MAIT_Professional_Documentation.md # Source for professional docs
├── LICENSE                                # Custom software license
├── README.md                              # Quick start guide
├── MAIT_Professional_Documentation.md     # Comprehensive installation guide
└── PROJECT_MEMORY.md                      # This file
```

### Key File Details
- **Modbus Poller**: `gen_modbus_tcp.py` is at root level in deployment folders
- **Configuration**: Single `generator_config.yaml` per environment with `.example` templates
- **Logs**: Shared via Docker volumes between containers at `/app/logs`
- **Privacy Protection**: `Local code/` folder is gitignored for development privacy
- **Documentation**: Dual-tier approach with README + Professional Documentation
- **Licensing**: Custom license protecting commercial rights while allowing personal use

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
## Latest Session Update - July 23, 2025

### 🎯 Major Accomplishments
**PROFESSIONAL DOCUMENTATION & REPOSITORY RESTRUCTURE** - Complete overhaul for commercial readiness

### Critical Improvements Completed:
1. **Professional Documentation** - Created comprehensive MAIT_Professional_Documentation.md with hardware setup, installation procedures, and troubleshooting
2. **Repository Privacy** - Removed "Local code" folder from public repository, added to .gitignore for development privacy
3. **UI Enhancement** - Added professional footer, improved Console tab with system info and contact details, removed cluttered About tab
4. **Custom Licensing** - Implemented comprehensive software license protecting commercial rights while allowing personal use
5. **Documentation Hierarchy** - Established clear separation between quick-start README and professional installation guide

### Repository Structure Changes:
- **Public Repository**: Only contains `docker_deployment/`, documentation, and licensing
- **Private Development**: `Local code/` folder gitignored for development privacy
- **Documentation Dual-Tier**: README.md for quick start, Professional Documentation for comprehensive setup
- **Commercial Protection**: Custom license agreement with clear terms and contact information

### UI/UX Improvements:
- **Footer Component**: Professional branding on all pages with copyright notice
- **Console Tab Enhancement**: Added system information and contact details below logs
- **Navigation Cleanup**: Removed About tab to prevent overcrowding, improved button layout
- **Professional Contact**: Clear pathways for commercial licensing and professional support

### Current Operational Status:
- **Generator**: Kohler 150kW, ECM Model 33, stable monitoring via Modbus TCP at 192.168.127.254:502
- **System**: All components operational - data collection, storage, AI analysis, frontend visualization
- **Documentation**: Professional-grade installation guide ready for customer deployment
- **Commercial Ready**: Licensing, documentation, and support structure in place

### Repository Status:
- **Latest Commit**: fcc45cc - "Add comprehensive professional documentation and update README"
- **Privacy**: Development environment protected from public access
- **Documentation**: Complete hardware/software setup guide available
- **Licensing**: Custom agreement protecting commercial interests

### Future Development Path:
- **Single Environment**: Consider transitioning to docker_deployment-only workflow for simplicity
- **Installation Automation**: Potential for automated setup scripts
- **Commercial Deployment**: Ready for professional installations and customer delivery

---
*Last Updated: July 23, 2025 - COMMERCIALLY READY WITH PROFESSIONAL DOCUMENTATION*