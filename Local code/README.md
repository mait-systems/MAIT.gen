# Generator Monitoring System (MAIT)

A comprehensive Docker-based monitoring solution for diesel generators with Modbus TCP communication, real-time data visualization, and AI-powered health analysis.

## 🏗️ Architecture

The system consists of four containerized services:
- **InfluxDB**: Time-series database for sensor data storage
- **Modbus Poller**: Python service that reads generator data via Modbus TCP
- **Backend API**: FastAPI service providing data access and AI analysis
- **Frontend Dashboard**: React web interface for monitoring and visualization

## 📋 Prerequisites

- Docker and Docker Compose installed
- Modbus TCP gateway (e.g., Moxa NPort) connected to generator RS485 port
- Network connectivity between deployment host and Modbus gateway
- Optional: OpenAI API key for AI-powered health analysis

## 🚀 Quick Start

1. **Clone and Navigate**
   ```bash
   git clone <repository-url>
   cd docker_deployment
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your specific settings and add your OpenAI key to .env
   ```

3. **Update Generator Configuration**
   - Edit `generator_config.yaml` to match your generator's Modbus register map, if needed.
   - Update the `connection.host` to your Modbus gateway IP address


4. **Deploy**
   ```bash
   docker-compose up -d
   ```

5. **Access**
   - Frontend Dashboard: http://localhost:3000
   - Backend API: http://localhost:8001
   - InfluxDB UI: http://localhost:8086

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# InfluxDB Configuration
INFLUXDB_TOKEN=your-secure-token-here
INFLUXDB_ORG=your-organization
INFLUXDB_BUCKET=generator-data

# OpenAI Configuration (Optional)
OPENAI_API_KEY=your-openai-api-key

# Network Configuration
MODBUS_HOST=192.168.127.254
MODBUS_PORT=502
MODBUS_UNIT_ID=1
```

### Generator Configuration (generator_config.yaml)

The configuration file defines:
- **Connection settings**: Modbus TCP gateway details
- **Register mappings**: Generator sensor addresses and scaling
- **Event definitions**: Alarm and fault code mappings
- **Thresholds**: Anomaly detection parameters

Key sections to customize:
```yaml
connection:
  host: "192.168.127.254"  # Your Modbus gateway IP
  port: 502
  unit_id: 1

registers:
  "Engine Speed":
    address: 61
    type: "UINT"
    units: "RPM"
```

## 🔧 Hardware Setup

### Typical Connection Diagram
```
Generator Controller (RS485) → Moxa NPort → Network → Docker Host
```

### Modbus Gateway Configuration
1. Configure Moxa NPort for:
   - RS485 to Modbus TCP conversion
   - Baud rate: 9600/19200 (check generator manual)
   - Parity: None/Even (check generator manual)
   - Stop bits: 1
   - Data bits: 8

2. Set static IP address accessible from Docker host

## 📊 Features

### Real-time Monitoring
- Live engine parameters (RPM, temperatures, pressures)
- Electrical measurements (voltage, current, power, frequency)
- Maintenance tracking (runtime hours, starts, service intervals)

### Data Visualization
- **Dashboard**: Key metrics and status overview
- **Trends**: Historical data charts and analysis
- **Events**: Active alarms and fault history
- **Reports**: AI-generated daily health summaries

### AI Analysis
- Automated health assessments using OpenAI GPT-4
- Anomaly detection and predictive insights
- Natural language report generation

## 🛠️ Development

### Local Development Setup
```bash
# Backend development
cd mait-backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend development  
cd mait-front
npm install
npm start

# Run modbus poller locally
python gen_modbus_tcp.py --config generator_config.yaml
```

### Adding New Registers
1. Update `generator_config.yaml` with new register definitions
2. Restart the modbus-poller service:
   ```bash
   docker-compose restart modbus-poller
   ```

### Customizing the Dashboard
- Frontend components are in `mait-front/src/`
- Add new tabs in `mait-front/src/tabs/`
- Update API endpoints in `mait-backend/main.py`

## 🔒 Security Considerations

- Change default InfluxDB credentials in production
- Use strong, unique tokens for InfluxDB access
- Consider network segmentation for Modbus communication
- Regularly update container images for security patches

## 📋 Troubleshooting

### Common Issues

**Modbus Connection Failed**
- Verify network connectivity to Modbus gateway
- Check gateway IP address in `generator_config.yaml`
- Confirm generator controller is responding
- Review Modbus gateway configuration

**No Data in Dashboard**
- Check modbus-poller logs: `docker-compose logs modbus-poller`
- Verify InfluxDB connectivity: `docker-compose logs backend`
- Confirm register addresses match your generator model

**Frontend Not Loading**
- Check if all services are running: `docker-compose ps`
- Verify backend API is accessible: `curl http://localhost:8001/api/live-stats`

### Log Access
```bash
# View all service logs
docker-compose logs

# View specific service logs
docker-compose logs modbus-poller
docker-compose logs backend
docker-compose logs frontend
```

### Data Verification
```bash
# Check InfluxDB data
docker-compose exec influxdb influx query 'from(bucket:"default-bucket") |> range(start:-1h)'
```

## 🔧 Maintenance

### Backup Strategy
- InfluxDB data is stored in Docker volumes
- Backup volumes regularly for data persistence
- Export configuration files to version control

### Updates
```bash
# Pull latest images
docker-compose pull

# Restart with new images
docker-compose up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test your changes thoroughly
4. Submit a pull request with clear description

## 📄 License

[Add your license information here]

## 🆘 Support

For technical support or questions:
- Check the troubleshooting section above
- Review Docker and application logs
- Consult your generator's Modbus documentation for register mappings

---

**Note**: This system is designed for monitoring purposes. Always follow proper safety procedures when working with generator equipment.