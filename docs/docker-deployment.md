# Docker Deployment Guide

This guide covers deploying the Bitaxe Monitor using Docker and Docker Compose.

## Quick Start

1. **Clone and Configure**
   ```bash
   git clone https://github.com/mtab3000/bitaxe-monitor.git
   cd bitaxe-monitor
   cp docker-compose.yml docker-compose.yml.backup
   nano docker-compose.yml  # Edit your miner configuration
   ```

2. **Start the Monitor**
   ```bash
   docker-compose up -d
   ```

3. **Access Web Interface**
   - Open http://localhost:8080 in your browser
   - Toggle between Desktop and Mobile views
   - Monitor all charts simultaneously

## Configuration

### Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `MINER_NAMES` | Comma-separated miner names | `Gamma-1,Gamma-2,Gamma-3` | `Supra-1,Ultra-2,Max-3` |
| `MINER_IPS` | Comma-separated IP addresses | `192.168.1.45,192.168.1.46,192.168.1.47` | `10.0.1.100,10.0.1.101` |
| `MINER_PORTS` | Comma-separated ports | `80,80,80` | `80,8080,80` |
| `POLL_INTERVAL` | Seconds between polls | `60` | `30` |
| `WEB_PORT` | Web interface port | `8080` | `3000` |
| `DATA_FILE` | CSV file path | `/app/data/bitaxe_monitor_data.csv` | `/data/mining.csv` |
| `EXPECTED_HASHRATES` | Manual hashrate overrides | _(empty)_ | `Gamma-1:1200,Gamma-2:1150` |
| `SHOW_DETAILED` | Enable detailed console output | `false` | `true` |

### Example Configurations

#### Single Miner
```yaml
environment:
  - MINER_NAMES=MyBitaxe
  - MINER_IPS=192.168.1.100
  - MINER_PORTS=80
```

#### Mixed Miners with Custom Ports
```yaml
environment:
  - MINER_NAMES=Gamma-1,Supra-2,Ultra-3
  - MINER_IPS=192.168.1.45,192.168.1.46,192.168.1.47
  - MINER_PORTS=80,8080,80
  - EXPECTED_HASHRATES=Gamma-1:1200,Supra-2:700
```

#### Development Setup
```yaml
environment:
  - MINER_NAMES=TestMiner
  - MINER_IPS=192.168.1.45
  - POLL_INTERVAL=30
  - SHOW_DETAILED=true
```

## Docker Commands

### Basic Operations
```bash
# Start in background
docker-compose up -d

# Start with logs visible
docker-compose up

# Stop the monitor
docker-compose down

# Restart the monitor
docker-compose restart

# View logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# Check status
docker-compose ps
```

### Maintenance
```bash
# Update to latest image
docker-compose pull
docker-compose up -d

# Rebuild from source
docker-compose build
docker-compose up -d

# Access container shell
docker-compose exec bitaxe-monitor sh

# View container resource usage
docker stats bitaxe-monitor
```

### Data Management
```bash
# Backup data
cp ./data/bitaxe_monitor_data.csv ./data/backup_$(date +%Y%m%d_%H%M%S).csv

# View data file
tail -f ./data/bitaxe_monitor_data.csv

# Clear old data (be careful!)
rm ./data/bitaxe_monitor_data.csv
docker-compose restart
```

## Volumes and Data Persistence

### Default Volume Mounts
- `./data:/app/data` - CSV data files
- `./config:/app/config` - Configuration files (future use)

### Custom Data Location
```yaml
volumes:
  - /my/custom/path:/app/data
  - ./config:/app/config
```

### Backup Strategy
```bash
# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp ./data/bitaxe_monitor_data.csv ./backups/bitaxe_backup_$DATE.csv
find ./backups -name "bitaxe_backup_*.csv" -mtime +7 -delete
```

## Web Interface

### Features
- **Real-time Monitoring**: Updates every 5 seconds
- **Multi-Chart View**: All metrics visible simultaneously
- **Mobile Optimized**: Responsive design for all devices
- **Persistent Charts**: Never disappear or reset
- **Efficiency Alerts**: Visual warnings for low performance
- **Variance Tracking**: Hashrate stability analysis

### Access Options
- **Local**: http://localhost:8080
- **Network**: http://YOUR_DOCKER_HOST_IP:8080
- **Custom Port**: Change `WEB_PORT` environment variable

### View Modes
- **Desktop View**: Optimized for large screens
- **Mobile View**: Compact layout for phones/tablets

## Network Configuration

### Port Mapping
```yaml
ports:
  - "8080:8080"  # Standard mapping
  - "3000:8080"  # Custom external port
```

### Multiple Instances
```yaml
# Instance 1
ports:
  - "8080:8080"

# Instance 2  
ports:
  - "8081:8080"
```

### Reverse Proxy (Nginx)
```nginx
server {
    listen 80;
    server_name bitaxe.local;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
docker-compose logs

# Common causes:
# - Invalid miner IP addresses
# - Port conflicts
# - Permission issues with data directory
```

#### No Data in Charts
```bash
# Check miner connectivity
docker-compose exec bitaxe-monitor sh
# Inside container:
curl http://MINER_IP/api/system/info

# Check logs for errors
docker-compose logs | grep -i error
```

#### Web Interface Not Accessible
```bash
# Check if container is running
docker-compose ps

# Check port conflicts
netstat -tulpn | grep 8080

# Try different port
# Edit docker-compose.yml: "8081:8080"
```

#### Permission Denied on Data Directory
```bash
# Fix permissions
sudo chown -R $USER:$USER ./data
chmod 755 ./data
```

### Debug Mode
```yaml
environment:
  - SHOW_DETAILED=true
  # Enable debug logging
```

### Performance Issues
```bash
# Check resource usage
docker stats bitaxe-monitor

# Increase poll interval if needed
# POLL_INTERVAL=90
```

## Security Considerations

### Network Security
- Only expose necessary ports
- Use firewall rules to restrict access
- Consider VPN for remote access

### Data Security
- Regular backups of CSV data
- Secure file permissions on data directory
- Monitor container logs for unauthorized access

### Container Security
```yaml
# Run as non-root user (future enhancement)
user: "1000:1000"

# Read-only filesystem (config only)
read_only: true
tmpfs:
  - /tmp
```

## Monitoring and Alerts

### Health Checks
The container includes built-in health checks:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/api/metrics"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### External Monitoring
```bash
# Check if service is healthy
curl -f http://localhost:8080/api/metrics

# Monitor with external tools
# - Prometheus
# - Grafana
# - Uptime Robot
```

### Log Monitoring
```bash
# Monitor for errors
docker-compose logs | grep -i "error\|warning\|fail"

# Export logs to external system
docker-compose logs --json | your-log-aggregator
```

## Production Deployment

### Resource Limits
```yaml
deploy:
  resources:
    limits:
      cpus: '0.5'
      memory: 256M
    reservations:
      cpus: '0.1'
      memory: 128M
```

### Restart Policies
```yaml
restart: unless-stopped
# Options: no, always, on-failure, unless-stopped
```

### Environment-Specific Configs
```bash
# Production
cp docker-compose.yml docker-compose.prod.yml
# Edit for production settings

# Development
cp docker-compose.yml docker-compose.dev.yml
# Edit for development settings

# Use specific config
docker-compose -f docker-compose.prod.yml up -d
```

## Updates and Maintenance

### Regular Updates
```bash
#!/bin/bash
# update_bitaxe_monitor.sh

echo "Stopping monitor..."
docker-compose down

echo "Backing up data..."
cp ./data/bitaxe_monitor_data.csv ./data/backup_$(date +%Y%m%d_%H%M%S).csv

echo "Pulling latest image..."
docker-compose pull

echo "Starting monitor..."
docker-compose up -d

echo "Update complete!"
```

### Migration Between Hosts
```bash
# Export configuration and data
tar -czf bitaxe_backup.tar.gz docker-compose.yml data/

# On new host
tar -xzf bitaxe_backup.tar.gz
docker-compose up -d
```

This completes the Docker deployment guide for the Bitaxe Monitor!
