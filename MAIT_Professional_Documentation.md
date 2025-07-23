# MAIT v1.0 - Modular Analytics & Intelligence Toolkit
## Marine Generator Monitoring System - Professional Installation & Operation Guide

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Hardware Requirements](#hardware-requirements)
4. [Hardware Setup](#hardware-setup)
5. [Software Installation](#software-installation)
6. [Configuration](#configuration)
7. [Operation](#operation)
8. [Troubleshooting](#troubleshooting)
9. [Development Notes](#development-notes)
10. [Future Enhancements](#future-enhancements)

---

## 🛠 System Overview

MAIT (Modular Analytics & Intelligence Toolkit) is a comprehensive monitoring solution for marine generators that provides real-time data collection, analysis, and AI-powered insights. The system combines hardware and software components to deliver professional-grade monitoring capabilities.

### Key Features
- **Real-time Data Collection**: Continuous monitoring via Modbus TCP
- **Time-series Data Storage**: InfluxDB for efficient data management
- **AI-Powered Analysis**: OpenAI integration for intelligent reporting
- **Interactive Dashboard**: React-based frontend with live visualization
- **Remote Access**: Network-accessible from multiple devices
- **Professional Reporting**: Automated daily reports with insights

---

## 🏗 Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│  Generator      │────│ Modbus TCP   │────│ Data        │────│ MAIT         │
│  Controller     │    │ Gateway      │    │ Collector   │    │ System       │
│ (DecisionMaker  │    │ (Moxa NPort) │    │ (Python)    │    │ (Docker)     │
│    3500)        │    │              │    │             │    │              │
└─────────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
```

### System Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Data Collector** | Python + pymodbus | Reads Modbus registers, sanitizes data |
| **Database** | InfluxDB | Time-series storage for metrics |
| **Backend API** | FastAPI | REST API, data aggregation, AI analysis |
| **Frontend** | React | Live dashboard, reporting interface |

---

## 💻 Hardware Requirements

### Core Hardware
- **Raspberry Pi 5** with external power supply and case
- **MicroSD Card** (32GB minimum, Class 10)
- **Moxa NPort 5150A** (Modbus TCP Gateway)
- **Network Connection** (Ethernet or WiFi)

### Cables & Connectors
- **DB9 Serial Cable** (Male-to-Female)
- **RS485 Wiring** for generator connection
- **Optional**: Black Box optical isolator for RS232/485 conversion

### Network Configuration
- **Generator Network**: 192.168.127.x subnet
- **Raspberry Pi IP**: 192.168.127.1
- **Moxa Gateway IP**: 192.168.127.254

---

## 🔧 Hardware Setup

### 1. Raspberry Pi Configuration

#### Initial Setup
1. **Download Raspberry Pi Imager**
2. **Select**: Pi 5 → Debian x64
3. **Configure Settings**:

**General Tab:**
```
Hostname: mait.local
Username: [your-username]
Password: [secure-password]
WiFi SSID: [your-network]
WiFi Password: [network-password]
Locale: [your-country]
```

**Services Tab:**
```
✓ Enable SSH (password authentication)
✓ Enable Serial Port
```

#### System Configuration
After first boot, run system configuration:

```bash
sudo raspi-config
```

Configure the following:
```
System Options → S5 Boot → B2 GUI Boot
Interface Options → I3 VNC Enable
Boot Options → Desktop Autologin
```

#### Network Interface Setup
Configure Ethernet for generator network:

```bash
# Set static IP for generator communication
sudo nmcli connection modify "Wired connection 1" \
  ipv4.addresses 192.168.127.1/24 \
  ipv4.method manual

# Restart network interface
sudo ip link set eth0 down
sudo ip link set eth0 up
```

### 2. Moxa Gateway Configuration

#### Access Gateway
1. **Navigate to**: `http://192.168.127.254`
2. **Login**: `admin` / `moxa`

#### Serial Settings
Configure for Kohler DecisionMaker 3500:
```
Baud Rate: 19200
Data Bits: 8
Stop Bits: 1
Parity: None
Flow Control: None
Interface: RS485 (2-wire)
```

### 3. Wiring Connections

#### Moxa to Generator Wiring
**DB9 Cable Pinout** (viewed from connector):
```
Pin 1: Black    →  Not used
Pin 2: Yellow   →  RS485 A+ (Generator Terminal G)
Pin 3: Green    →  RS485 B- (Generator Terminal H)
Pin 4: Orange   →  Not used
Pin 5: Red      →  Not used
Pin 6: Blue     →  Not used
Pin 7: Pink     →  Not used
Pin 8: White    →  Not used
Pin 9: Purple   →  Not used
GND:   Brown    →  Signal Ground
```

⚠️ **Important**: Verify wire colors with multimeter before connection. DB9 pinout is for Moxa connector, not cable.

---

## 📦 Software Installation

### 1. System Prerequisites

#### Update System
```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install git curl ca-certificates -y
```

#### Install Docker
```bash
# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin -y
```

#### Configure Docker (Non-root access)
```bash
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker

# Test installation
docker run hello-world
```

### 2. Optional: Container Management UI

#### Install Portainer
```bash
mkdir ~/portainer
docker pull portainer/portainer-ce:latest

docker run -d -p 8000:8000 -p 9443:9443 \
  --restart always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ~/portainer:/data \
  --name portainer \
  portainer/portainer-ce:latest
```

**Access**: `https://localhost:9443`

### 3. MAIT System Installation

#### Clone Repository
```bash
cd ~
git clone https://github.com/chengmlr/MAIT.git
cd MAIT/docker_deployment
```

#### Configure Environment
```bash
# Copy configuration templates
cp .env.example .env
cp generator_config.yaml.example generator_config.yaml
```

#### Deploy System
```bash
# Automated deployment
./deploy.sh

# OR manual deployment
docker-compose up --build -d
```

---

## ⚙️ Configuration

### 1. Environment Variables (.env)
```bash
# InfluxDB Configuration
INFLUXDB_ADMIN_USER=admin
INFLUXDB_ADMIN_PASSWORD=[secure-password]
INFLUXDB_ORG=your-organization
INFLUXDB_BUCKET=generator-metrics
INFLUXDB_TOKEN=[your-influxdb-token]

# API Configuration
REACT_APP_API_URL=http://localhost:3000
FRONTEND_PORT=3000

# OpenAI Configuration (Optional)
OPENAI_API_KEY=[your-openai-key]
```

### 2. Generator Configuration (generator_config.yaml)

#### Connection Settings
```yaml
connection:
  host: "192.168.127.254"  # Moxa gateway IP
  port: 502
  unit_id: 1
  timeout: 10
  retries: 3
```

#### Database Configuration
```yaml
influxdb:
  url: "http://influxdb:8086"
  token: "[your-influxdb-token]"
  org: "your-organization"
  bucket: "generator-metrics"
```

#### OpenAI Integration
```yaml
openai:
  api_key: "[your-openai-key]"
  model: "gpt-4"
  max_tokens: 2000
```

---

## 🚀 Operation

### 1. System Startup
```bash
cd ~/MAIT/docker_deployment
docker-compose up -d
```

### 2. Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| **Dashboard** | `http://localhost:3000` | Main monitoring interface |
| **API** | `http://localhost:8001` | Backend REST API |
| **InfluxDB** | `http://localhost:8086` | Database management |
| **Portainer** | `https://localhost:9443` | Container management |

### 3. Network Access
For remote access from other devices:

1. **Find Raspberry Pi IP**:
   ```bash
   hostname -I
   ```

2. **Access from network**:
   - Dashboard: `http://[PI-IP]:3000`
   - API: `http://[PI-IP]:8001`

### 4. System Monitoring
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Individual service logs
docker-compose logs modbus-poller
docker-compose logs backend
docker-compose logs frontend
```

---

## 🔍 Troubleshooting

### Common Issues

#### 1. Modbus Connection Failures
**Symptoms**: `[FAILED] Failed to connect to Modbus gateway`

**Solutions**:
```bash
# Check network connectivity
ping 192.168.127.254

# Verify Ethernet configuration
ip addr show eth0

# Check Moxa gateway settings
curl -I http://192.168.127.254
```

#### 2. Container Issues
**High Memory Usage**:
```bash
# Monitor resource usage
htop

# Remove problematic processes
sudo apt remove orca  # If consuming excessive RAM
```

**Container Restart**:
```bash
# Restart specific service
docker-compose restart backend

# Full system restart
docker-compose down && docker-compose up -d
```

#### 3. InfluxDB Storage Issues
**Corrupted Shards**:
```bash
# Locate problematic shard in logs
docker-compose logs influxdb

# Remove corrupted shard (replace XX with shard number)
sudo rm -rf ~/influx_storage/engine/data/[shard-id]
```

#### 4. Port Conflicts
```bash
# Check port usage
netstat -tulpn | grep :3000
netstat -tulpn | grep :8001
netstat -tulpn | grep :8086

# Kill processes if needed
sudo kill -9 [PID]
```

### Diagnostic Commands
```bash
# System health check
docker-compose ps
docker system df
docker system prune -f

# Performance monitoring
docker stats
free -h
df -h
```

---

## 🛠 Development Notes

### Development Environment Setup

#### Node.js Installation
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify installation
node -v && npm -v
```

#### Python Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Development Workflow
```bash
# Frontend development
cd mait-front
npm install
npm start

# Backend development
cd mait-backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Modbus collector testing
python gen_modbus_tcp.py
```

### Migration to New Hardware
1. **Copy project files** to new machine
2. **Create virtual environments** for Python components
3. **Install dependencies**: `pip install -r requirements.txt`
4. **Configure environment** variables and YAML files
5. **Test connectivity** before full deployment

---

## 🚀 Future Enhancements

### Short-term Improvements
- [ ] **Installation Script**: Automated setup.sh for one-command deployment
- [ ] **Web Configuration**: GUI for initial system setup
- [ ] **Mobile Responsive**: Optimize dashboard for mobile devices
- [ ] **Authentication**: Add user login and access control
- [ ] **Health Monitoring**: System status indicators and alerts

### Medium-term Features
- [ ] **Multi-Generator Support**: Monitor multiple generators simultaneously
- [ ] **Advanced Analytics**: Predictive maintenance algorithms
- [ ] **Email Notifications**: Automated alert system
- [ ] **Data Export**: CSV/Excel reporting capabilities
- [ ] **Cloud Integration**: Optional cloud data backup

### Long-term Vision
- [ ] **Commercial Licensing**: White-label solutions
- [ ] **Mobile Application**: Dedicated iOS/Android apps
- [ ] **Edge Computing**: On-device AI processing
- [ ] **Industrial Integration**: SCADA system compatibility
- [ ] **Plug-and-Play Hardware**: Pre-configured hardware packages

---

## 📞 Support & Contact

### Technical Support
- **Developer**: Yarik Sychov
- **Email**: yariksychov@pm.me
- **Response Time**: 24-48 hours
- **Support Type**: Professional installation & maintenance

### Commercial Licensing
For commercial use, white-label solutions, or enterprise deployments, contact the developer for licensing arrangements.

---

## 📄 License

This software is protected under a custom Software License Agreement. See the LICENSE file for complete terms regarding personal use, commercial restrictions, and licensing requirements.

---

**Built with modern technologies for reliable marine generator monitoring**

*Copyright © 2025 Yarik Sychov. All rights reserved.*