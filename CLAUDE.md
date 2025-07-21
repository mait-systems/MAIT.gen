# Generator Monitoring System - Claude Development Notes

## Project Overview
This is a comprehensive generator monitoring system with Docker deployment capabilities. The system consists of:
- **Modbus Poller**: Python script that reads generator data via Modbus TCP
- **FastAPI Backend**: Processes data, stores to InfluxDB, provides AI analysis via OpenAI
- **React Frontend**: Real-time dashboard with multiple tabs (Live, Trends, Console, Reports)
- **InfluxDB**: Time-series database for metrics storage

## Architecture
```
Generator (Modbus RTU) → Moxa NPort (RS485→TCP) → Modbus Poller → InfluxDB
                                                        ↓
React Frontend ← nginx proxy ← FastAPI Backend ← InfluxDB
```

## Recent Development Progress

### ✅ Completed Tasks
1. **Docker Deployment Setup** - Created complete containerized deployment
2. **Configuration Generalization** - Made system deployable across different environments
3. **Enhanced Modbus Poller** - Added infinite retry logic with exponential backoff and emoji status messages
4. **Console Tab Logging** - Fixed real-time log display in frontend

### 🔧 Key Technical Improvements

#### Modbus Poller Enhancements (`gen_modbus_tcp.py`)
- **Infinite Retry Logic**: Never exits, continuously attempts reconnection
- **No Emoji Version**: Compatible with systems having limited Unicode support
- **Dual Console/File Logging**: Both console output for manual runs AND file logging
- **Smart Environment Detection**: Automatically detects Docker vs local environments
- **Connection Health Monitoring**: Periodic checks with automatic reconnection
- **Enhanced Status Messages**: Clear text-based indicators (`[CONNECT]`, `[SUCCESS]`, etc.)
- **Shared Volume Logging**: Logs to `/app/logs/modbus_poller.log` for frontend access
- **Unbuffered Output**: Added `-u` flag for real-time Docker logs

#### Docker Infrastructure
- **Shared Volumes**: Added `shared_logs` volume for log sharing between containers
- **Environment Variables**: Comprehensive .env configuration
- **Service Dependencies**: Proper startup order and health checks
- **Port Configuration**: Frontend on 3001, backend on 8001, InfluxDB on 8086

#### Frontend Fixes
- **Console Tab**: Fixed to display real-time modbus poller logs with 2-second refresh
- **API URLs**: Changed from hardcoded `127.0.0.1` to relative URLs for Docker networking
- **Nginx Proxy**: Configured to route `/api/*` requests to backend

### 🐛 Known Issues Fixed
1. **Console Tab Empty** - Fixed by implementing shared volume logging
2. **Docker Networking** - Resolved hardcoded localhost URLs
3. **Connection Failures** - Enhanced retry logic prevents poller exit
4. **Port Conflicts** - Moved frontend from 3000 to 3001

### 📁 Key Files & Locations

#### Docker Deployment (`docker_deployment/`)
- `docker-compose.yml` - Multi-container orchestration with shared volumes
- `.env.example` - Complete environment variable template
- `generator_config.yaml` - Full Modbus register configuration

#### Backend (`mait-backend/`)
- `main.py` - FastAPI application with InfluxDB integration and OpenAI analysis
- `gen_modbus_tcp.py` - Enhanced modbus poller with retry logic
- `Dockerfile.poller` - Dedicated container for modbus polling

#### Frontend (`mait-front/`)
- `src/tabs/ConsoleTab.js` - Real-time log display (fixed API calls)
- `nginx.conf` - Proxy configuration for API routing

### 🚀 Deployment Commands
```bash
cd docker_deployment
docker-compose up --build -d    # Start all services
docker-compose logs -f          # View all logs
docker-compose down             # Stop all services
```

### 🔍 Debugging & Monitoring
- **Container Logs**: `docker logs docker_deployment-modbus-poller-1`
- **API Endpoints**: 
  - `http://localhost:8001/api/logs` - Direct backend access
  - `http://localhost:3001/api/logs` - Through frontend proxy
- **Frontend**: `http://localhost:3001`
- **InfluxDB**: `http://localhost:8086`

### 📋 Configuration Notes
- **Modbus Connection**: Currently configured for `192.168.1.100:502`
- **Register Mapping**: 50+ generator parameters with proper scaling
- **Event Handling**: Active event monitoring with persistence
- **Anomaly Detection**: Built-in threshold checking for data validation

### 🔧 Development Environment
- **Python**: 3.11-slim containers
- **Node.js**: 18 for React build
- **InfluxDB**: 2.1.1
- **nginx**: Alpine for frontend serving

### 💡 Future Development Ideas
1. **Authentication**: Add user management and JWT tokens
2. **Mobile App**: React Native companion app
3. **Email Alerts**: SMTP integration for critical events
4. **Data Export**: CSV/Excel report generation
5. **Multi-Generator**: Support for multiple generator monitoring
6. **Predictive Analytics**: ML-based failure prediction

### 🏗️ Commands for Claude
```bash
# Build and test
cd "C:\Users\RLF Chief Engineer\Documents\Code\MAIT-main\docker_deployment"
docker-compose up --build

# Check logs
docker-compose logs modbus-poller -f

# Test API endpoints
curl http://localhost:8001/api/logs
curl http://localhost:3001/api/live-stats
```

## Project Status: ✅ FULLY FUNCTIONAL
- All containers running successfully
- Frontend displaying real-time data
- Console tab showing modbus poller logs with emoji status
- Ready for production deployment or further development