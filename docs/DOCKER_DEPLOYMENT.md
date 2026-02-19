# Copilot Quant Docker Deployment Guide

## Overview
This guide covers deploying the Copilot Quant trading system using Docker and Docker Compose.

## Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- Interactive Brokers TWS or Gateway running on host machine
- At least 2GB RAM available for containers
- Disk space for database and logs

## Quick Start

### 1. Configure Environment
Copy the environment template and update with your settings:

```bash
cp .env.docker .env
# Edit .env with your configuration
nano .env
```

Key settings to configure:
- `POSTGRES_PASSWORD`: Set a strong password for the database
- `IB_HOST`: Usually `host.docker.internal` to connect to IBKR on host
- `IB_PORT`: 7497 for paper, 7496 for live (TWS), or gateway ports
- `PAPER_TRADING`: Set to `false` for live trading (use with caution)

### 2. Start Services
Start all services in detached mode:

```bash
docker-compose up -d
```

Start with monitoring (Prometheus + Grafana):

```bash
docker-compose --profile monitoring up -d
```

### 3. Verify Services
Check that all services are running:

```bash
docker-compose ps
```

View logs:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f orchestrator
docker-compose logs -f ui
```

### 4. Access Services
- **Streamlit UI**: http://localhost:8501
- **Prometheus** (if enabled): http://localhost:9090
- **Grafana** (if enabled): http://localhost:3000 (default: admin/admin)

## Service Management

### Stop Services
```bash
docker-compose stop
```

### Restart Services
```bash
docker-compose restart
```

### Rebuild After Code Changes
```bash
docker-compose up -d --build
```

### View Service Status
```bash
docker-compose ps
```

### Execute Commands in Containers
```bash
# Open shell in orchestrator
docker-compose exec orchestrator bash

# Run Python script
docker-compose exec orchestrator python -m copilot_quant.cli status
```

## Data Persistence

Data is persisted in Docker volumes:
- `postgres_data`: Database files
- `prometheus_data`: Prometheus metrics (if enabled)
- `grafana_data`: Grafana dashboards (if enabled)

Host directories mounted as volumes:
- `./data`: Trading data, cache, etc.
- `./logs`: Application logs
- `./config.paper.yaml`: Configuration file

### Backup Database
```bash
docker-compose exec database pg_dump -U copilot copilot_quant > backup.sql
```

### Restore Database
```bash
cat backup.sql | docker-compose exec -T database psql -U copilot copilot_quant
```

## Health Checks

Services include health checks:
- **Database**: PostgreSQL ready check
- **UI**: Streamlit health endpoint
- **Orchestrator**: Python process check

View health status:
```bash
docker-compose ps
```

## Troubleshooting

### Can't Connect to IBKR
1. Ensure TWS/Gateway is running on host machine
2. Check that API connections are enabled in TWS/Gateway
3. Verify `IB_HOST` is set to `host.docker.internal`
4. Check firewall isn't blocking connection
5. Verify port numbers match TWS/Gateway configuration

### Database Connection Issues
1. Wait for database to be healthy: `docker-compose logs database`
2. Check credentials in `.env` match
3. Ensure `DATABASE_URL` is correctly formatted

### Container Won't Start
1. Check logs: `docker-compose logs <service_name>`
2. Verify all required environment variables are set
3. Check for port conflicts: `netstat -an | grep <port>`
4. Ensure sufficient system resources

### Out of Memory
1. Increase Docker memory limit in Docker Desktop settings
2. Reduce number of running services
3. Stop monitoring services if not needed

## Production Deployment

### Security Recommendations
1. **Change default passwords**:
   - Set strong `POSTGRES_PASSWORD`
   - Change `GRAFANA_PASSWORD`

2. **Use secrets management**:
   ```bash
   # Use Docker secrets instead of .env for sensitive data
   echo "my_secret_password" | docker secret create postgres_password -
   ```

3. **Enable TLS/SSL**:
   - Configure PostgreSQL to use SSL
   - Use reverse proxy (nginx) with TLS for UI

4. **Network isolation**:
   - Use custom Docker networks
   - Restrict external access with firewall rules

5. **Regular backups**:
   - Automate database backups
   - Store backups off-site

### Monitoring in Production
Enable monitoring services:
```bash
docker-compose --profile monitoring up -d
```

Configure alerts in Prometheus for:
- Service downtime
- Trading errors
- Connection failures
- Unusual PnL swings

### Resource Limits
Add resource limits to docker-compose.yml:
```yaml
services:
  orchestrator:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### Auto-Restart Policies
All services use `restart: unless-stopped` to ensure:
- Automatic restart after crashes
- Restart after host reboot
- Manual stop prevents restart

To change restart policy:
```yaml
restart: always  # Always restart
restart: on-failure  # Only on error
restart: "no"  # Never restart
```

## Advanced Configuration

### Using External Database
To use an external PostgreSQL instance:

1. Comment out `database` service in docker-compose.yml
2. Update `DATABASE_URL` to point to external DB
3. Ensure database is accessible from Docker network

### Custom Configuration
Mount custom config files:
```yaml
volumes:
  - ./my_config.yaml:/app/config.yaml:ro
```

### Development Mode
For development with live code reloading:
```yaml
volumes:
  - ./copilot_quant:/app/copilot_quant
command: ["python", "-m", "copilot_quant.orchestrator", "--dev"]
```

## Maintenance

### Update Containers
```bash
# Pull latest images
docker-compose pull

# Rebuild and restart
docker-compose up -d --build
```

### Clean Up
```bash
# Remove stopped containers
docker-compose down

# Remove containers and volumes (WARNING: deletes data)
docker-compose down -v

# Remove unused images
docker image prune -a
```

### View Resource Usage
```bash
docker stats
```

## Support
For issues or questions:
1. Check logs: `docker-compose logs`
2. Verify configuration in `.env`
3. Review service health: `docker-compose ps`
4. Consult main README.md for application-specific help
