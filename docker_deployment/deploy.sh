#!/bin/bash
# Generator Monitoring System - Docker Deployment Script

echo "[START] Starting Generator Monitoring System Deployment..."

# Get server IP automatically
SERVER_IP=$(hostname -I | awk '{print $1}')
echo "[INFO] Detected server IP: $SERVER_IP"

# Create .env file from template if it doesn't exist
if [ ! -f .env ]; then
    echo "[INFO] Creating .env file from template..."
    cp .env.example .env
    
    # Update SERVER_IP in .env file
    sed -i "s/SERVER_IP=192.168.1.100/SERVER_IP=$SERVER_IP/g" .env
    
    echo "[WARNING] Please edit .env file with your specific settings:"
    echo "   - OPENAI_API_KEY (if using AI features)"
    echo "   - MODBUS_HOST (your Modbus gateway IP)"
    echo "   - INFLUXDB_TOKEN (generate a secure token)"
    echo ""
    echo "[INFO] For network access from other devices, uncomment and set:"
    echo "   REACT_APP_API_URL=http://$SERVER_IP:3000"
    echo ""
fi

# Build and start containers
echo "[INFO] Building and starting Docker containers..."
docker-compose up --build -d

echo ""
echo "[SUCCESS] Deployment complete!"
echo ""
echo "[INFO] Access URLs:"
echo "   Dashboard:    http://localhost:3000"
echo "   InfluxDB UI:  http://localhost:8086"
echo "   Backend API:  http://localhost:8001"
echo ""
echo "[INFO] Network Access URLs (from other devices):"
echo "   Dashboard:    http://$SERVER_IP:3000"
echo "   InfluxDB UI:  http://$SERVER_IP:8086"
echo "   Backend API:  http://$SERVER_IP:8001"
echo ""
echo "[INFO] To view logs: docker-compose logs -f"
echo "[INFO] To stop: docker-compose down"