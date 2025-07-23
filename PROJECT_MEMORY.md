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
**COMPLETE BRAND TRANSFORMATION & GITHUB PROFESSIONAL RESTRUCTURE** - Full commercial rebrand with modular expansion strategy

### Critical Improvements Completed:
1. **Brand Redefinition** - Rebranded from "Marine Asset Intelligence Tool" to "Modular Analytics & Intelligence Toolkit"
2. **GitHub Professional Organization** - Migrated from personal account to professional `mait-systems` organization
3. **Modular Repository Structure** - Renamed repository to `MAIT.gen` supporting future expansion (MAIT.hvac, MAIT.solar, etc.)
4. **UI/UX Refinements** - Streamlined Console tab info, added GitHub links, simplified footer with version display
5. **Documentation Synchronization** - Updated all documentation to reflect new branding and repository structure
6. **Professional Documentation** - Created comprehensive MAIT_Professional_Documentation.md with hardware setup, installation procedures, and troubleshooting
7. **Repository Privacy** - Removed "Local code" folder from public repository, added to .gitignore for development privacy
8. **Custom Licensing** - Implemented comprehensive software license protecting commercial rights while allowing personal use

### Brand Transformation:
- **New Definition**: MAIT = "Modular Analytics & Intelligence Toolkit"
- **Strategic Vision**: Supports expansion into multiple monitoring domains
- **Professional Positioning**: Enterprise-ready branding for B2B sales
- **Scalable Naming**: Perfect foundation for product line growth

### GitHub Professional Restructure:
- **Organization**: Migrated to `mait-systems` for professional credibility
- **Repository**: Renamed to `MAIT.gen` for modular expansion strategy
- **New URL**: https://github.com/mait-systems/MAIT.gen
- **Future Structure**: Ready for MAIT.hvac, MAIT.solar, MAIT.core, etc.

### UI/UX Improvements:
- **Console Tab Streamlined**: Removed database info, added GitHub link, removed support details
- **Footer Simplified**: Version display + copyright only, removed marketing text
- **Professional Links**: Direct access to GitHub repository for users
- **Contact Information**: Clean presentation with email and GitHub access

### Documentation Excellence:
- **Dual-Tier Documentation**: README for quick start, Professional Documentation for comprehensive installation
- **Hardware Setup Guide**: Complete Raspberry Pi, Moxa Gateway, wiring instructions
- **Installation Automation**: Step-by-step Docker deployment procedures
- **Commercial Ready**: Professional-grade documentation for customer delivery

### Current Operational Status:
- **Generator**: Kohler 150kW, ECM Model 33, stable monitoring via Modbus TCP at 192.168.127.254:502
- **System**: All components operational - data collection, storage, AI analysis, frontend visualization
- **Branding**: Fully transformed with professional presentation
- **Repository**: Live at new professional location with modular naming

### Repository Status:
- **New Professional URL**: https://github.com/mait-systems/MAIT.gen
- **All Documentation**: Updated with new branding and repository references
- **UI Changes**: Live with updated GitHub links and professional presentation
- **Commercial Protection**: Custom license with professional contact pathways

### Strategic Expansion Foundation:
```
MAIT - Modular Analytics & Intelligence Toolkit
├── MAIT.gen    ← Generator monitoring (current - LIVE)
├── MAIT.hvac   ← HVAC system monitoring (planned)
├── MAIT.solar  ← Solar installation monitoring (planned)
├── MAIT.fleet  ← Fleet vehicle monitoring (future)
├── MAIT.core   ← Shared libraries & components (future)
└── MAIT.xxx    ← Any monitoring domain (unlimited expansion)
```

### Commercial Readiness:
- **Professional Branding**: Complete transformation from personal to enterprise-ready
- **Modular Strategy**: Framework established for unlimited domain expansion
- **Documentation**: Professional-grade installation and operation guides
- **Licensing**: Commercial rights protected with clear terms
- **Support Structure**: Professional contact pathways established

---
*Last Updated: July 23, 2025 - PROFESSIONALLY REBRANDED & STRATEGICALLY POSITIONED FOR EXPANSION*