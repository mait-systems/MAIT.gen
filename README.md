# MAIT - Marine Generator Monitoring System

A comprehensive Docker-based monitoring system for marine generators using Modbus TCP communication, real-time data visualization, and AI-powered analytics.

## 🚀 Features

- **Real-time Monitoring**: Live dashboard with generator metrics and status
- **Modbus TCP Integration**: Connects to generator controllers via Modbus gateways
- **Time-series Data Storage**: InfluxDB for efficient data storage and querying
- **Interactive Dashboard**: React-based frontend with real-time updates
- **AI-Powered Analytics**: OpenAI integration for intelligent health analysis
- **Docker Deployment**: Complete containerized solution for easy deployment
- **Event Monitoring**: Real-time alerts and event tracking
- **Network Access**: Accessible from multiple devices on the same network

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

## 📋 Requirements

### Hardware
- Generator with Modbus RTU interface
- Modbus TCP gateway (e.g., Moxa NPort)
- Computer/server running Docker

### Software
- Docker and Docker Compose
- Git (for cloning repository)

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/chengmlr/MAIT.git
cd MAIT
```

### 2. Configure Your Deployment
```bash
cd docker_deployment
cp .env.example .env
cp generator_config.yaml.example generator_config.yaml
```

### 3. Configure Your System

Edit `generator_config.yaml`:
```yaml
connection:
  host: "YOUR_MODBUS_GATEWAY_IP"  # Replace with your gateway IP
  port: 502
  unit_id: 1

influxdb:
  token: "YOUR_INFLUXDB_TOKEN"    # Generate a secure token
  org: "your-organization"         # Your organization name
  bucket: "your-bucket-name"       # Your data bucket name
```

Edit `generator_config.yaml` with your real credentials:
```yaml
influxdb:
  token: "your-influxdb-token-here"
  org: "your-organization"
  bucket: "generator-metrics"
  
openai:
  api_key: "your-openai-api-key-here"
```

### 4. Deploy

```bash
cd docker_deployment
./deploy.sh  # Automated deployment script
# OR manually:
docker-compose up --build -d
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
MAIT/
├── docker_deployment/      # Production deployment
│   ├── gen_modbus_tcp.py   # Modbus polling script
│   ├── generator_config.yaml.example # Configuration template
│   ├── docker-compose.yml  # Container orchestration
│   ├── deploy.sh           # Automated deployment
│   ├── mait-backend/       # FastAPI backend
│   └── mait-front/         # React frontend
├── LICENSE                 # Software license agreement
└── PROJECT_MEMORY.md       # Detailed technical documentation
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
- `.gitignore` protects sensitive YAML files from being committed
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
   - Verify shared volume configuration
   - Ensure poller is running: `docker-compose logs modbus-poller`

3. **Permission Errors**:
   ```bash
   # Fix file permissions
   chmod +x deploy.sh
   ```

4. **Port Conflicts**:
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
This README provides a streamlined Docker deployment process for getting MAIT running quickly.

### Professional Installation Guide
For comprehensive hardware setup, detailed configuration, troubleshooting, and professional installations:

📖 **[MAIT Professional Documentation](./MAIT_Professional_Documentation.md)**

Includes:
- Complete hardware setup (Raspberry Pi, Moxa Gateway, wiring)
- Step-by-step software installation
- Network configuration and security
- Comprehensive troubleshooting guide
- Development environment setup
- Future enhancement roadmap

### Additional Resources
- **Technical Documentation**: See `PROJECT_MEMORY.md`
- **Configuration Examples**: Check `.example` files in `docker_deployment/`

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
3. **Technical Details**: Review `PROJECT_MEMORY.md` for detailed technical info
4. **GitHub Issues**: Open an issue with logs and configuration details (without secrets)
5. **Professional Support**: Contact yariksychov@pm.me for installation assistance

---

**Note**: This system is designed for marine generators with Modbus RTU interfaces. Ensure your generator and network setup match the requirements before deployment.