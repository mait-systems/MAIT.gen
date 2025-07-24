# MAIT v2.1 - Modular Analytics & Intelligence Toolkit
## Generator Monitoring System - Professional Installation & Operation Guide

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
9. [Support and Contact](#support)

---

## 🛠 System Overview

MAIT (Modular Analytics & Intelligence Toolkit) is a comprehensive monitoring solution for DecisionMaker3500 generator controllers made by Kohler that provides real-time data collection, analysis, and AI-powered insights. The system combines hardware and software components to deliver professional-grade monitoring capabilities.

### Key Features
- **Real-time Data Collection**: Continuous monitoring via Modbus TCP
- **Time-series Data Storage**: InfluxDB for efficient data management
- **AI-Powered Analysis**: Agentic AI integration for reporting
- **Interactive Dashboard**: React-based frontend with live visualization
- **Remote Access**: Network-accessible from multiple devices
- **Professional Reporting**: Automated daily reports with insights

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

## 💻 Hardware Requirements (Community Edition)


### Core Hardware
- **Raspberry Pi 5** with external power supply and case
- **MicroSD Card** (64GB minimum, Class 10)
- **Moxa NPort 5150A** (Modbus TCP Gateway)
- **Network Connection** (Ethernet or WiFi)

### Cables & Connectors
- **DB9 Serial Cable** (Male-to-Female) or
- **Terminal Block**
- **RS485 Wiring** for generator connection

### Network Configuration
- **Generator Network**: 192.168.127.x subnet
- **Raspberry Pi IP**: 192.168.127.1
- **Moxa Gateway IP**: 192.168.127.254

---

## 🔧 Hardware Setup (Community Edition)

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
Configure Ethernet for generator network via Debian GUI or:

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

![Moxa NPort 5150A Setup](https://github.com/mait-systems/MAIT.gen/blob/main/manuals/Nport5150A.png?raw=true)

#### Access Gateway
1. **Navigate to**: `http://192.168.127.254`
2. **Login**: `admin` / `moxa`

#### Serial Settings
Configure for Kohler DecisionMaker 3500:

![Moxa Serial Settings](https://github.com/mait-systems/MAIT.gen/blob/main/manuals/Nport5150A_serial_settings.png?raw=true)

```
Baud Rate: 19200
Data Bits: 8
Stop Bits: 1
Parity: None
Flow Control: None
Interface: RS485 (2-wire)
```

#### TCP Settings
Configure the TCP settings for Modbus communication:

![Moxa TCP Settings](https://github.com/mait-systems/MAIT.gen/blob/main/manuals/Nport5150A_tcp_settings.png?raw=true)

### 3. Wiring Connections

#### DecisionMaker 3500 Controller Wiring
![DecisionMaker 3500 Wiring Diagram](https://github.com/mait-systems/MAIT.gen/blob/main/manuals/DM3500wiring.png?raw=true)

#### Moxa to Generator Wiring
![Moxa NPort Wiring Diagram](https://github.com/mait-systems/MAIT.gen/blob/main/manuals/Nport5150Awiring.png?raw=true)

**DB9 Cable Pinout** (viewed from connector):
```
Pin 1: Black    →  Not used
Pin 2: Yellow   →  A- (RS485)
Pin 3: Green    →  B+ (RS485)
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

The Docker daemon binds to a Unix socket, not a TCP port. By default it's the root user that owns the Unix socket, and other users can only access it using sudo. The Docker daemon always runs as the root user.

If you don't want to preface the docker command with sudo, create a Unix group called docker and add users to it. When the Docker daemon starts, it creates a Unix socket accessible by members of the docker group. On some Linux distributions, the system automatically creates this group when installing Docker Engine using a package manager. In that case, there is no need for you to manually create the group.

```bash
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker

# Test installation
docker run hello-world
```
This command downloads a test image and runs it in a container. When the container runs, it prints a message and exits.

### 2. Optional: Container Management UI

There is no official “Docker Desktop” equivalent UI for Linux (like what macOS/Windows users get with Docker Desktop), one of the ways to observe the containers is to install Portainer that provides a web GUI access.

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
git clone https://github.com/mait-systems/MAIT.gen.git
cd MAIT.gen
```

#### Configure Environment
```bash
# Copy configuration templates
cp generator_config.yaml.example generator_config.yaml
```


#### Deploy System
```bash
docker compose up --build -d
```

---

## ⚙️ Configuration

The system uses a single YAML configuration file for all settings. Docker Compose requires `.env` for basic operation.

### Create yaml and .env files:
```bash
cp generator_config.yaml.example generator_config.yaml
cp .env.example .env
```

### First, edit you Generator Configuration (generator_config.yaml)

#### Connection Configuration
```yaml

connection:
  host: "YOUR_MODBUS_GATEWAY_IP"  # Replace with your Moxa gateway IP, ex. "192.168.127.254"
  port: 502
  unit_id: 1
```

#### Database Configuration
```yaml
influxdb:
  token: "YOUR_INFLUXDB_TOKEN"    # Generate a secure token, ex. "ECRbc2byEqKeAMXsgI6YZvMh2g0Dk"
  org: "your-organization"         # Create your organization name, "myorg"
  bucket: "your-bucket-name"       # Create your data bucket name, ex. "generator-metrics"

openai:
  api_key: "your-openai-api-key-here" # You can get your OpenAI API key online
```

#### OpenAI Integration (Optional)
```yaml
openai:
  api_key: "[your-openai-key]"
  model: "gpt-4"
  max_tokens: 2000
```

### Edit Environment Variables (.env file)

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
---

## 🚀 Operation

### 1. System Startup
```bash
cd ~/MAIT.gen
docker compose up -d
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
   /api/live-stats
   /api/active-events
   /api/live-analysis
   /api/trend
   /api/load-trend
   /api/logs
   /api/generate-daily-report

### 4. Useful Docker Commands
```bash
# Look up images
docker images

# Remove an image
docker rmi image_id (rmi -f for forced deletion)

# Check active containers
docker container ps
docker-compose ps

# Stop a container
docker stop container_id

# Stop all and delete all containers
docker rm -f $(docker ps -aq)

# Delete all the images and volumes
docker rmi -f $(docker images -aq)

# Prune, delete junk
docker system prune -af

# Restart specific service
docker-compose restart backend

# Full system restart
docker-compose down && docker-compose up -d

# View logs
docker-compose logs -f

# Individual service logs
docker-compose logs modbus-poller
docker-compose logs backend
docker-compose logs frontend
```

# Performance monitoring
docker stats
free -h
df -h


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


#### 2. Container Issues
**High Memory Usage**:
```bash
# Monitor resource usage
htop

# Remove problematic processes
sudo apt remove orca  # If consuming excessive RAM, observed on Pi5
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

## 📞 Support & Contact

### Technical Support
- **Developer**: Yarik Sychov
- **Email**: yariksychov@pm.me

### Commercial Licensing
For commercial use, white-label solutions, or enterprise deployments, contact the developer for licensing arrangements.

---

## 📄 License

This software is protected under a custom Software License Agreement. See the LICENSE file for complete terms regarding personal use, commercial restrictions, and licensing requirements.

---

*Copyright © 2025 Yarik Sychov. All rights reserved.*