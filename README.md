# MAIT v2.2.0 - Modular Analytics & Intelligence Toolkit
## Generator Monitoring System - Installation & Operation Guide

---

## Table of Contents

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

## System Overview

MAIT (Modular Analytics & Intelligence Toolkit) is a comprehensive monitoring solution for generator controllers that provides real-time data collection, analysis, and AI-powered insights. The system combines hardware and software components to deliver professional-grade monitoring capabilities.

## Features

- **Real-time Monitoring**: Live dashboard with generator metrics and status
- **Modbus TCP Integration**: Connects to generator controllers via Modbus gateways  
- **Time-series Data Storage**: InfluxDB for efficient data storage and querying
- **Interactive Dashboard**: React-based frontend with real-time updates
- **Event Monitoring**: Real-time alerts and event tracking
- **Memory System**: Multi-layered historical baselines 
- **Pattern Recognition**: Historical trend analysis
- **AI / LLM Integration**: AI/LLM-powered health assessments and recommendations
- **Predictive Analytics**: AI/LLM-powered anomaly detection and trend/drift analysis
- **Docker Deployment**: Complete containerized solution for easy deployment
- **Network Access**: Accessible from multiple devices on the same network

## System Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────┐
│  Generator      │────│ Modbus TCP   │────│ Modbus      │
│  Controller     │    │ Gateway      │    │ Poller      │
│                 │    │ (NPort, etc) │    │ (Python)    │
└─────────────────┘    └──────────────┘    └─────────────┘
                                   │
                           ┌───────▼───────┐
                           │   InfluxDB    │
                           │  (Database)   │
                           └───────┬───────┘
                                   │
                ┌──────────────────┼──────────────────┐
                │                  │                  │
        ┌───────▼───────┐  ┌───────▼─────────┐  ┌─────▼─────┐
        │   FastAPI     │  │ PowertrainAgent │  │ React     │
        │   Backend     │  │  (Local / AI)   │  │ Frontend  │
        └───────┬───────┘  └───────┬─────────┘  └─────▲─────┘
                │                  │                  │
                │          ┌───────▼─────────┐        │
                └─────────►│    Gateway      │◄───────┘
                           │  (LLM + Memory) │
                           └─────────────────┘
```

### System Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Data Collector** | Python + pymodbus | Reads Modbus registers, sanitizes data, automatic anomaly detection and correction |
| **Database** | InfluxDB | Time-series storage for metrics |
| **Backend API** | FastAPI REST API | InfluxDB integration, data aggregation, local analysis, real-time log streaming |
| **PowertrainAgent** | REST API |Local Statistical analysis, Baseline refresh / rebuild and bootstrap of historical data |
| **Frontend** | React | Live dashboard, reporting interface |
| **Gateway** | FastAPI | REST API, influx querries, proprietary AI/LLM/memory service, health endpoints for memory, prompt, and server connectivity |

---

### Quick Dash Preview

![MAIT Live Dashboard](https://github.com/mait-systems/MAIT.gen/blob/main/manuals/screenshots/mait_dash.jpg?raw=true)

*Live dash interface tab with real-time data visualization, system health indicators*

#### Generator Monitoring Tab
![Generator Performance Monitoring](https://github.com/mait-systems/MAIT.gen/blob/main/manuals/screenshots/mait_gen.jpg?raw=true)

*Real-time generator performance metrics including voltage, current, power output, frequency, and engine parameters*

#### Trends Analysis Tab  
![Historical Trends Analysis](https://github.com/mait-systems/MAIT.gen/blob/main/manuals/screenshots/mait_trends.jpg?raw=true)

*Historical data visualization with customizable time ranges for performance analysis and trend identification*

#### Local Analysis
![Historical Trends Analysis](https://github.com/mait-systems/MAIT.gen/blob/main/manuals/screenshots/mait_local.jpg?raw=true)

*Local Analysis tab compares live values against memory baselines to flag drift and anomalies.*

#### AI-Powered Analysis 
![AI Analysis and Reporting](https://github.com/mait-systems/MAIT.gen/blob/main/manuals/screenshots/mait_ai.jpg?raw=true)

*Intelligent analysis and automated reporting with LLM-generated insights, recommendations, and system health assessments*


## Requirements

### Core Hardware
- **Linux PC/miniPC** with external power supply
- **SSD / MicroSD Card** (64GB minimum)
- **Modbus TCP Gateway** (Moxa NPort 5150A or other)
- **Network Connection** (Ethernet or WiFi)

### Software
- **Docker and Docker Compose** to run the containers
- **Git** to clone the software
- **Zerotier** for remote access

### Cables & Connectors
- **DB9 Serial Cable, RS485**
- **Eth cable**

### Network Configuration
- **MAIT host eth0 IP**: 192.168.127.1 / 255.255.255.0
- **Modbus Gateway IP**: 192.168.127.254


## Host Setup

### 1. Network Interface Setup
Configure Ethernet for generator network via Debian GUI or:

```bash
# Set static IP for generator communication
sudo nmcli connection modify "Wired connection 1" \
  ipv4.addresses 192.168.127.1/24 \
  ipv4.method manual
```
Use 255.255.255.0 as a gateway

#### Restart network interface
```bash
sudo ip link set eth0 down
sudo ip link set eth0 up
```


### 2. Serial Gateway Configuration, using Moxa NPort as an example

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

#### Example:: DecisionMaker 3500 Controller Wiring
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
Refer to the manual of your Gateway if using another device.

---

## Software Installation

### 1. System Prerequisites (Debian based distros)

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

#### Create Your Deployment Configuration Files
```bash
cp generator_config.yaml.example generator_config.yaml
cp .env.example .env
```

### Configure Your System

Edit `generator_config.yaml`:
```yaml
connection:
  host: "YOUR_MODBUS_GATEWAY_IP"  # Replace with your gateway IP, ex. "192.168.127.254"
  port: 502
  unit_id: 1

influxdb:
  token: "YOUR_INFLUXDB_TOKEN"    # Generate a secure token, ex. "ECRbc2byEqKeAMXsgI6YZvMh2g0Dk"
  org: "your-organization"         # Create your organization name, "myorg"
  bucket: "your-bucket-name"       # Create your data bucket name, ex. "generator1-metrics"

```

Edit `.env` file:

Match your influx configuration from generator_config.yaml. Example:
```yaml
# InfluxDB Configuration (from generator_config.yaml)
INFLUXDB_TOKEN=ECRbc2byEqKedsfgsgI6YZvMh2g0Dk
INFLUXDB_ORG=myorg
INFLUXDB_BUCKET=generator1-metric
INFLUXDB_ADMIN_USER=admin # Set admin username for Influx
INFLUXDB_ADMIN_PASSWORD=admin123 # Set admin password for influx

# Generator Configuration (from generator_config.yaml)
MODBUS_HOST=192.168.127.254
MODBUS_PORT=502
MODBUS_UNIT_ID=1
```

### Join the MAIT ZeroTier Network (Remote Gateway Users only)
To use the Remote Prompt Gateway (recommended for AI powered features), connect your MAIT host to the project's private ZeroTier network so it can reach the remote gateway and InfluxDB. Contact us for more details.

1. **Install ZeroTier** 
   ```bash
   curl -s https://install.zerotier.com | sudo bash
   ```
2. **Join the MAIT network**:
   ```bash
   sudo zerotier-cli join <our_network_address>
   ```
3. **Send your node ID** (`zerotier-cli info`) to the support for approval.
4. **Verify connection** once approved:
   ```bash
   zerotier-cli listnetworks
   ```
   You should see a managed address (10.24x.x.x). **Note this IP address** - you'll need it for the next step.
5. **Configure for remote gateway access**:

   Edit `generator_config_gateway.yaml`:
   ```yaml
   # Gateway configuration
   gateway_url: "http://10.243.212.15:8083"  # Remote gateway endpoint

   # InfluxDB configuration - IMPORTANT: Use your ZeroTier IP, not container name!
   influxdb:
     url: "http://10.243.x.x:8086"  # Replace with YOUR ZeroTier IP from step 4
     token: "YOUR_INFLUXDB_TOKEN"
     org: "your-organization"
     bucket: "your-bucket-name"
   ```

   **Critical**: The `influxdb.url` must use your ZeroTier IP address (e.g., `http://10.243.x.x:8086`), not the Docker container name (`http://influxdb:8086`). The remote gateway needs to access your local InfluxDB from outside your Docker network. Without the correct IP, gateway requests will fail with HTTP 500 errors

### Assign a Unique `site_id`
The PowertrainAgent identifies your installation by `site_id`. Pick something descriptive - for example:

- `site_id: "marina-east-gen01"`
- `site_id: "plantA-standby"`
- `site_id: "fleet-07"`

Update `generator_config_gateway.yaml` accordingly. The default value (`demo-site-001`) is only for documentation and should be replaced before running the stack.


#### Deploy MAIT
```bash
docker compose up --build -d
```

### Access Your Dashboard

| Service | URL | Purpose |
|---------|-----|---------|
| **Dashboard, Local Access** | `http://localhost:3000` | Main monitoring interface |
| **Dashboard, Network Access (see below)** | `http://YOUR_SERVER_IP:3000` | Main monitoring interface |
| **API** | `http://localhost:8001` | Backend REST API |
| **InfluxDB** | `http://localhost:8086` | Database management |
| **Portainer** | `https://localhost:9443` | Container management |


## Network Access Setup

To access from other devices on your network:
1. **Find your server IP**:
   ```bash
   hostname -I  # Linux/Mac
   ipconfig     # Windows
   ```
2. **Update environment** (if needed):
   ```bash
   # In .env or per-stack .env.dev file
   REACT_APP_API_URL=http://YOUR_SERVER_IP:8001
   ```
3. **Access from any device**:
   - Dashboard: `http://YOUR_SERVER_IP:3000`
   - From phones, tablets, other computers on same network


## Troubleshooting

#### Modbus Connection Failures

**Symptoms**: `[FAILED] Failed to connect to Modbus gateway`

- Check generator_config.yaml host IP
- Verify network connectivity
- Confirm Modbus gateway is operational

**Solutions**:
```bash
# Check network connectivity
ping 192.168.127.254

# Verify Ethernet configuration
ip addr show eth0
```
#### High RAM usage

**Symptoms**: `High RAM usage`

- Check for a process that consumes resources

**Solutions**:
```bash
# Monitor resource usage
htop

# Remove problematic processes, potentially orca
sudo apt remove orca  # If consuming excessive RAM
```

#### InfluxDB Storage Issues
**Corrupted Shards**:
```bash
# Locate problematic shard in logs
docker-compose logs influxdb

# Remove corrupted shard (replace XX with shard number)
sudo rm -rf ~/influx_storage/engine/data/[shard-id]
```

#### Port Conflicts
```bash
# Check port usage
netstat -tulpn | grep :3000
netstat -tulpn | grep :8001
netstat -tulpn | grep :8086

# Kill processes if needed
sudo kill -9 [PID]
```

#### Too many files open
```bash
Issue: InfluxDB fails to start with “too many open files” while opening shards (lots of MANIFEST/NATS accept errors) after months
of data; default nofile limit is too low for the number of shards.

- Fix: Raise file descriptor limit for the Influx container. In docker-compose*.yml under influxdb add:

    ulimits:
      nofile:
        soft: 65536
        hard: 65536

Ensure the host/daemon allows it (set the same in /etc/security/limits.conf: set 
* hard/soft nofile 65536
in /etc/security/limits.conf ), 
then recreate the Influx container: ex.  docker compose up -d --force-recreate influxdb
```

### Useful Docker Commands
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


## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with your generator setup
5. Submit a pull request


## Support & Contact

### Technical Support
- **Developer**: Yarik Sychov
- **Email**: ys@mait.tech

### Commercial Licensing
For commercial use, white-label solutions, or enterprise deployments, contact the developer for licensing arrangements.

---

## License

This software is protected under a custom Software License Agreement. See the LICENSE file for complete terms regarding personal use, commercial restrictions, and licensing requirements.

---

*Copyright © 2026 Yarik Sychov. All rights reserved.