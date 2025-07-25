# MAIT - Modular Analytics & Intelligence Toolkit
## Generator Monitoring System, Community Edition

A comprehensive monitoring system for DecisionMaker3500 equipped generators using Modbus TCP communication, real-time data visualization, and AI-powered analytics.

## 📋 Version Information

**Current Branch: `feature/powertrain-ai` (v3.0.0-ai-enhanced)**
- AI-powered PowertrainAgent system with intelligent health monitoring
- Memory-enhanced analysis with historical pattern recognition  
- Advanced anomaly detection and predictive maintenance insights
- Real-time AI analysis with OpenAI GPT-4 integration

**Stable Version: `v2.0.0` (Available via git tag)**
- Core generator monitoring without AI features
- Lighter resource requirements
- Perfect for basic monitoring needs
- Download: `git checkout v2.0.0`

### 🔄 Choosing Your Version
- **For Advanced Users**: Use current `feature/powertrain-ai` branch for AI-enhanced monitoring
- **For Basic Monitoring**: Use `git checkout v2.0.0` for stable, lightweight version
- **For Production**: Recommend v2.0.0 for proven stability, or AI branch for cutting-edge features

## 🚀 Features

### Core Features (All Versions)
- **Real-time Monitoring**: Live dashboard with generator metrics and status
- **Modbus TCP Integration**: Connects to generator controllers via Modbus gateways  
- **Time-series Data Storage**: InfluxDB for efficient data storage and querying
- **Interactive Dashboard**: React-based frontend with real-time updates
- **Docker Deployment**: Complete containerized solution for easy deployment
- **Event Monitoring**: Real-time alerts and event tracking
- **Network Access**: Accessible from multiple devices on the same network

### 🧠 AI-Enhanced Features (v3.0.0-ai-enhanced)
- **PowertrainAgent**: Intelligent health monitoring with persistent memory
- **Predictive Analytics**: AI-powered anomaly detection and trend analysis
- **Memory System**: Multi-layered historical baselines (hourly, daily, weekly, monthly)
- **Load Band Classification**: Intelligent categorization (0%, 0-20%, 20-40%, 40-60%, 60-80%, 80-100%)
- **OpenAI Integration**: GPT-4 powered health assessments and recommendations
- **Pattern Recognition**: Historical trend analysis with learning capabilities
- **Smart Alerts**: Context-aware alert system with severity classification
- **Bootstrap Memory**: Process ALL historical data for comprehensive analysis

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│  Generator      │────│ Modbus TCP   │────│ Modbus      │────│ Docker       │
│  Controller     │    │ Gateway      │    │ Poller      │    │ Stack        │
│  (RS485)        │    │ (NPort)      │    │ (Python)    │    │              │
└─────────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
                                                   │
                                           ┌───────▼───────┐
                                           │   InfluxDB    │
                                           │  (Database)   │
                                           └───────────────┘
                                                   │
                                           ┌───────▼───────┐
                                           │   FastAPI     │
                                           │  (Backend)    │
                                           └───────────────┘
                                                   │
                                           ┌───────▼───────┐
                                           │    React      │
                                           │  (Frontend)   │
                                           └───────────────┘
```

### Quick Dash Preview

![MAIT Live Dashboard](https://github.com/mait-systems/MAIT.gen/blob/main/manuals/screenshots/mait_dash.jpg?raw=true)

*Live dash interface tab with real-time data visualization, system health indicators*

#### Generator Monitoring Tab
![Generator Performance Monitoring](https://github.com/mait-systems/MAIT.gen/blob/main/manuals/screenshots/mait_gen.jpg?raw=true)

*Real-time generator performance metrics including voltage, current, power output, frequency, and engine parameters*

#### Trends Analysis Tab  
![Historical Trends Analysis](https://github.com/mait-systems/MAIT.gen/blob/main/manuals/screenshots/mait_trends.jpg?raw=true)

*Historical data visualization with customizable time ranges for performance analysis and trend identification*

#### AI-Powered Reports Tab
![AI Analysis and Reporting](https://github.com/mait-systems/MAIT.gen/blob/main/manuals/screenshots/mait_ai.jpg?raw=true)

*Intelligent analysis and automated reporting with AI-generated insights, recommendations, and system health assessments*

## 📋 Requirements

### Hardware (Community Edition)
- Generator with DecisionMaker3500  & Modbus RTU interface
- Modbus TCP gateway (e.g., Moxa NPort)
- Computer/server running Docker

### Software
- Docker and Docker Compose
- Git (for cloning repository)

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/mait-systems/MAIT.gen.git
cd MAIT.gen
```

### 2. Configure Your Deployment
```bash
cp generator_config.yaml.example generator_config.yaml
cp .env.example .env
```

### 3. Configure Your System

Edit `generator_config.yaml`:
```yaml
connection:
  host: "YOUR_MODBUS_GATEWAY_IP"  # Replace with your gateway IP, ex. "192.168.127.254"
  port: 502
  unit_id: 1

influxdb:
  token: "YOUR_INFLUXDB_TOKEN"    # Generate a secure token, ex. "ECRbc2byEqKeAMXsgI6YZvMh2g0Dk"
  org: "your-organization"         # Create your organization name, "myorg"
  bucket: "your-bucket-name"       # Create your data bucket name, ex. "generator-metrics"

openai:
  api_key: "your-openai-api-key-here" # You can get your OpenAI API key online
```

Edit `.env` file:

Match your influx configuration from generator_config.yaml. Example:
```yaml
# InfluxDB Configuration (from generator_config.yaml)
INFLUXDB_TOKEN=ECRbc2byEqKeAMXsgI6YZvMh2g0Dk
INFLUXDB_ORG=myorg
INFLUXDB_BUCKET=generator-metric
INFLUXDB_ADMIN_USER=admin # Set admin username for Influx
INFLUXDB_ADMIN_PASSWORD=admin123 # Set admin password for influx

# Generator Configuration (from generator_config.yaml)
MODBUS_HOST=192.168.127.254
MODBUS_PORT=502
MODBUS_UNIT_ID=1
```


### 4. Deploy

```bash
docker compose up --build -d
```

### 5. Access Your Dashboard

- **Local Access**: http://localhost:3000
- **Network Access**: http://YOUR_SERVER_IP:3000
- **InfluxDB UI**: http://localhost:8086
- **Backend API**: http://localhost:8001

## 📱 Network Access Setup

To access from other devices on your network:

1. **Find your server IP**:
   ```bash
   hostname -I  # Linux/Mac
   ipconfig     # Windows
   ```

2. **Update environment** (if needed):
   ```bash
   # In .env file
   REACT_APP_API_URL=http://YOUR_SERVER_IP:3000
   ```

3. **Access from any device**:
   - Dashboard: `http://YOUR_SERVER_IP:3000`
   - From phones, tablets, other computers on same network

## 🔧 Configuration

### Generator Configuration
The `generator_config.yaml` file contains:
- **Connection settings**: Modbus gateway IP, port, unit ID
- **InfluxDB settings**: Database connection and credentials
- **Register mappings**: Generator-specific register definitions
- **Event mappings**: Alarm and event code definitions
- **Logging settings**: Log levels and file locations

### Configuration Management
All configuration is managed through `generator_config.yaml`:
- **Connection settings**: Modbus gateway IP and connection parameters
- **InfluxDB credentials**: Database URL, token, organization, and bucket
- **OpenAI API Key**: For AI-powered analytics and reports
- **Logging settings**: Log levels, file locations, and formatting
- **Register mappings**: Generator-specific Modbus register definitions

## 📊 Dashboard Features

### Real-time Monitoring
- **Engine Status**: Speed, temperature, oil pressure
- **Electrical Metrics**: Voltage, current, power output
- **Fuel System**: Pressure, temperature, consumption rate
- **Environmental**: Intake air temperature and pressure

### Historical Data
- **Trends Tab**: Historical data visualization
- **Reports Tab**: AI-generated daily reports and analysis
- **Maintenance Tab**: Runtime hours and maintenance tracking

### Live Console
- **Console Tab**: Real-time modbus poller logs
- **Connection Status**: Live connection monitoring
- **Error Messages**: Clear diagnostic information

## 🛠️ Development

### Project Structure
```
MAIT.gen/
├── gen_modbus_tcp.py              # Modbus polling script
├── generator_config.yaml.example # Configuration template
├── docker-compose.yml             # Container orchestration
├── mait-backend/                  # FastAPI backend
├── mait-front/                    # React frontend
├── LICENSE                        # Software license agreement
├── README.md                      # Quick start guide
└── MAIT_Professional_Documentation.md # Complete setup guide
```

### Key Components

1. **Modbus Poller** (`gen_modbus_tcp.py`):
   - Connects to generator via Modbus TCP
   - Infinite retry with exponential backoff
   - Text-only logging for compatibility
   - Automatic anomaly detection and correction

2. **Backend** (`mait-backend/main.py`):
   - FastAPI REST API
   - InfluxDB integration
   - OpenAI GPT-4 analytics
   - Real-time log streaming

3. **Frontend** (`mait-front/src/`):
   - React dashboard with emoji UI
   - Real-time data updates
   - Multiple monitoring tabs
   - Network-accessible design

## 🔒 Security

### Secrets Management
- All credentials stored in `generator_config.yaml` files
- Template `.example` files provided for deployment
- Single configuration source per environment for consistency

### Network Security
- CORS configured for legitimate access
- Environment-based API URL configuration
- No hardcoded credentials in source code

## 🐳 Docker Details

### Services
- **InfluxDB**: Time-series database (port 8086)
- **Backend**: FastAPI server (port 8001)
- **Frontend**: React app via Nginx (port 3000)
- **Modbus Poller**: Background polling service

### Volumes
- **Shared Logs**: Container log sharing for console tab
- **InfluxDB Data**: Persistent database storage
- **Configuration**: Mounted config files

## 🔍 Troubleshooting

### Common Issues

1. **Connection Failures**:
   ```
   [FAILED] Failed to connect to Modbus gateway
   ```
   - Check generator_config.yaml host IP
   - Verify network connectivity
   - Confirm Modbus gateway is operational

2. **Empty Console Tab**:
   - Check backend logs: `docker-compose logs backend`
   - Ensure poller is running: `docker-compose logs modbus-poller`

3. **Port Conflicts**:
   ```bash
   # Check what's using ports
   netstat -tulpn | grep :3000
   netstat -tulpn | grep :8001
   netstat -tulpn | grep :8086
   ```

### Debugging Commands

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f

# Individual service logs
docker-compose logs backend
docker-compose logs modbus-poller
docker-compose logs frontend

# Restart services
docker-compose restart

# Rebuild from scratch
docker-compose down
docker-compose up --build -d
```

## 📚 Documentation

### Quick Start Guide
This README provides a streamlined Docker deployment process for getting MAIT.gen running quickly.

### Professional Installation Guide
For comprehensive hardware setup, detailed configuration, troubleshooting, and professional installations:

📖 **[MAIT Professional Documentation](./MAIT_Professional_Documentation.md)**

Includes:
- Complete hardware setup (Raspberry Pi, Moxa Gateway, wiring)
- Step-by-step software installation
- Network configuration and security
- Comprehensive troubleshooting guide
- Development environment setup

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with your generator setup
5. Submit a pull request

## 📄 License

This project is licensed under a custom Software License Agreement that allows personal and internal use while protecting commercial rights. See the LICENSE file for complete terms.

For commercial use or licensing inquiries, contact: yariksychov@pm.me

## 🆘 Support

For issues and questions:
1. **Quick Issues**: Check the troubleshooting section above
2. **Hardware Setup**: See the [Professional Documentation](./MAIT_Professional_Documentation.md)
4. **GitHub Issues**: Open an issue with logs and configuration details (without secrets)
5. **Professional Support**: Contact yariksychov@pm.me for installation assistance

---

**Note**: This system is designed for generators equipped with DecisionMaker3500 with Modbus RTU interfaces. Ensure your generator and network setup match the requirements before deployment.