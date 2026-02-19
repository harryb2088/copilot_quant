# Copilot Quant Platform - Complete Bootstrapping Guide

**Complete setup guide for development teams and operations. Get the entire platform running from scratch.**

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start Decision Tree](#quick-start-decision-tree)
- [Option 1: Local Development Setup](#option-1-local-development-setup)
- [Option 2: Docker Compose Setup](#option-2-docker-compose-setup)
- [Option 3: Cloud Deployment (Vercel)](#option-3-cloud-deployment-vercel)
- [Service Verification](#service-verification)
- [Configuration Guide](#configuration-guide)
- [Common Issues and Troubleshooting](#common-issues-and-troubleshooting)
- [Next Steps](#next-steps)

---

## Overview

The Copilot Quant Platform consists of three main services:

1. **PostgreSQL Database** - Persistent data storage
2. **Trading Orchestrator** - Automated trading engine with market hours management
3. **Streamlit UI** - Web-based user interface and analytics dashboard

Optional monitoring services:
- **Prometheus** - Metrics collection
- **Grafana** - Visualization dashboards

This guide covers three deployment approaches:
- **Local Development**: Python environment, ideal for development and testing
- **Docker Compose**: Containerized, ideal for production and consistent environments
- **Cloud (Vercel)**: Serverless UI deployment for remote access

---

## Prerequisites

### All Deployments
- Git installed
- GitHub account with repository access
- Text editor (VS Code, Sublime, etc.)

### Local Development
- **Python 3.8+** (3.12 recommended)
- **PostgreSQL 16** installed locally
- **pip** package manager
- 4GB+ RAM
- 10GB+ disk space

### Docker Compose Deployment
- **Docker Engine 20.10+**
- **Docker Compose 2.0+**
- 4GB+ RAM available for containers
- 20GB+ disk space for images and volumes

### Cloud Deployment (Vercel)
- **Node.js and npm** (for Vercel CLI)
- Vercel account (free tier works)
- Internet connection

### For Live Trading (Optional)
- **Interactive Brokers** account (paper or live)
- **TWS** (Trader Workstation) or **IB Gateway** installed
- See [IBKR Comprehensive Guide](IBKR_COMPREHENSIVE_GUIDE.md) for details

---

## Quick Start Decision Tree

**Choose your deployment path:**

```
┌─────────────────────────────────────────────────────┐
│  What's your primary use case?                      │
└─────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
   Development    Production     Remote Access
   & Testing       Deployment       Only
        │               │               │
        ▼               ▼               ▼
    Option 1        Option 2        Option 3
    Local Dev    Docker Compose   Vercel Cloud
```

- **Option 1 (Local)**: Best for active development, debugging, and rapid iteration
- **Option 2 (Docker)**: Best for production, consistent environments, and team collaboration
- **Option 3 (Cloud)**: Best for UI-only access, demos, and remote monitoring

---

## Option 1: Local Development Setup

**Time to complete: 15-30 minutes**

### 1.1 Clone Repository

```bash
# Clone the repository
git clone https://github.com/harryb2088/copilot_quant.git
cd copilot_quant
```

### 1.2 Setup Python Environment

#### Option A: Using venv (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

#### Option B: Using conda

```bash
# Create conda environment
conda create -n copilot_quant python=3.12
conda activate copilot_quant
```

### 1.3 Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

**Verify installation:**
```bash
python -c "import copilot_quant; print('Installation successful!')"
```

### 1.4 Setup PostgreSQL Database

#### Install PostgreSQL

**macOS (using Homebrew):**
```bash
brew install postgresql@16
brew services start postgresql@16
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql-16
sudo systemctl start postgresql
```

**Windows:**
Download and install from [postgresql.org](https://www.postgresql.org/download/windows/)

#### Create Database and User

```bash
# Access PostgreSQL
psql postgres

# Create database and user
CREATE DATABASE copilot_quant;
CREATE USER copilot WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE copilot_quant TO copilot;
\q
```

#### Initialize Database Schema

```bash
# Run initialization script
psql -U copilot -d copilot_quant -f scripts/init_db.sql
```

### 1.5 Configure Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
nano .env  # or use your preferred editor
```

**Minimum required settings:**
```bash
# Database
POSTGRES_USER=copilot
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=copilot_quant
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql://copilot:your_secure_password@localhost:5432/copilot_quant

# Trading Mode (paper by default)
PAPER_TRADING=true

# Interactive Brokers (if using)
IB_PAPER_HOST=127.0.0.1
IB_PAPER_PORT=7497
IB_PAPER_CLIENT_ID=1
IB_PAPER_ACCOUNT=YOUR_PAPER_ACCOUNT
```

### 1.6 Launch Services

#### Start Database (if not already running)
```bash
# macOS (Homebrew)
brew services start postgresql@16

# Linux
sudo systemctl start postgresql

# Windows - use pgAdmin or Services panel
```

#### Start Streamlit UI
```bash
streamlit run copilot_quant/ui/app.py
```

The UI will open automatically at `http://localhost:8501`

#### Start Trading Orchestrator (Optional)
```bash
# In a new terminal (activate venv first)
python -m copilot_quant.orchestrator
```

#### Start REST API (Optional)
```bash
# In a new terminal (activate venv first)
python scripts/run_api.py
```

API will be available at `http://localhost:8000`

### 1.7 Verify Local Setup

**Check Database Connection:**
```bash
psql -U copilot -d copilot_quant -c "SELECT version();"
```

**Check Python Environment:**
```bash
python -c "import copilot_quant, streamlit, pandas; print('All imports successful')"
```

**Access Services:**
- UI: http://localhost:8501
- API: http://localhost:8000/docs (Swagger UI)
- Database: localhost:5432

✅ **Local setup complete!** Continue to [Service Verification](#service-verification)

---

## Option 2: Docker Compose Setup

**Time to complete: 10-20 minutes**

Perfect for production deployments and consistent environments across teams.

### 2.1 Prerequisites Check

```bash
# Verify Docker installation
docker --version
# Expected: Docker version 20.10.0 or higher

# Verify Docker Compose
docker compose version
# Expected: Docker Compose version v2.0.0 or higher

# Check Docker is running
docker ps
# Should show running containers (may be empty)
```

### 2.2 Clone Repository

```bash
git clone https://github.com/harryb2088/copilot_quant.git
cd copilot_quant
```

### 2.3 Configure Environment

```bash
# Copy Docker environment template
cp .env.docker .env

# Edit configuration
nano .env  # or use your preferred editor
```

**Critical settings to configure:**

```bash
# Database password (REQUIRED - set a strong password)
POSTGRES_PASSWORD=your_very_secure_password_here

# Interactive Brokers connection
IB_HOST=host.docker.internal  # Connects to IBKR on host machine
IB_PORT=7497                   # 7497 = paper, 7496 = live (TWS)
IB_CLIENT_ID=1

# Paper trading (recommended for initial setup)
PAPER_TRADING=true

# Optional: Ports (defaults shown)
POSTGRES_PORT=5432
STREAMLIT_PORT=8501
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

### 2.4 Build and Start Services

#### Development Mode (Basic Services)

```bash
# Build and start database, orchestrator, and UI
docker compose up -d

# View logs
docker compose logs -f
```

#### Production Mode (with Monitoring)

```bash
# Start all services including Prometheus and Grafana
docker compose --profile monitoring up -d

# View logs
docker compose logs -f
```

### 2.5 Verify Services are Running

```bash
# Check service status
docker compose ps

# Expected output:
# NAME                        STATUS              PORTS
# copilot_quant_db           Up (healthy)        0.0.0.0:5432->5432/tcp
# copilot_quant_orchestrator Up                  
# copilot_quant_ui           Up (healthy)        0.0.0.0:8501->8501/tcp
```

### 2.6 Access Services

- **Streamlit UI**: http://localhost:8501
- **PostgreSQL**: localhost:5432
- **Prometheus** (if enabled): http://localhost:9090
- **Grafana** (if enabled): http://localhost:3000 (admin/admin)

### 2.7 Docker Service Management

**View logs:**
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f ui
docker compose logs -f orchestrator
docker compose logs -f database
```

**Restart services:**
```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart ui
```

**Stop services:**
```bash
# Stop all (keeps data)
docker compose stop

# Stop and remove containers (keeps data volumes)
docker compose down

# Stop and remove everything including volumes (DELETES DATA)
docker compose down -v
```

**Rebuild after code changes:**
```bash
docker compose up -d --build
```

**Execute commands in containers:**
```bash
# Access database
docker compose exec database psql -U copilot copilot_quant

# Access orchestrator shell
docker compose exec orchestrator bash

# Run Python command
docker compose exec orchestrator python -c "import copilot_quant; print('OK')"
```

### 2.8 Data Persistence

Docker volumes persist data across container restarts:

- `postgres_data`: Database files
- `./data`: Trading data, cache (mounted from host)
- `./logs`: Application logs (mounted from host)

**Backup database:**
```bash
docker compose exec database pg_dump -U copilot copilot_quant > backup_$(date +%Y%m%d).sql
```

**Restore database:**
```bash
cat backup_20260219.sql | docker compose exec -T database psql -U copilot copilot_quant
```

✅ **Docker setup complete!** Continue to [Service Verification](#service-verification)

---

## Option 3: Cloud Deployment (Vercel)

**Time to complete: 10-15 minutes**

Deploy the Streamlit UI to Vercel for remote access. Note: This deploys UI only - database and orchestrator remain local/on-prem.

### 3.1 Prerequisites

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login
```

### 3.2 Clone Repository (if not already done)

```bash
git clone https://github.com/harryb2088/copilot_quant.git
cd copilot_quant
```

### 3.3 Deploy to Vercel

```bash
# Deploy to Vercel
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? [Select your account]
# - Link to existing project? No
# - Project name? copilot-quant (or your choice)
# - Directory? ./ (current directory)
# - Override settings? No
```

### 3.4 Configure Authentication

```bash
# Add environment variables for authentication
vercel env add AUTH_EMAIL
# Enter: admin@example.com (your login email)

vercel env add AUTH_PASSWORD
# Enter: your_secure_password

vercel env add AUTH_NAME
# Enter: Admin User (display name)

# For each variable, select:
# - Production: Yes
# - Preview: Yes
# - Development: Yes
```

### 3.5 Deploy to Production

```bash
# Deploy with environment variables
vercel --prod
```

After deployment completes, you'll get a URL like: `https://copilot-quant-xyz123.vercel.app`

### 3.6 Update README (Optional)

```bash
# Edit README.md to update deployment URL
nano README.md

# Replace YOUR-DEPLOYMENT-URL with your actual URL
# Commit changes
git add README.md
git commit -m "Update deployment URL"
git push
```

### 3.7 Access Deployed Application

1. Navigate to your Vercel URL
2. Login with credentials you configured (AUTH_EMAIL and AUTH_PASSWORD)
3. Verify all pages load correctly

### 3.8 Managing Vercel Deployment

**View deployments:**
```bash
vercel ls
```

**View logs:**
```bash
vercel logs <deployment-url> --follow
```

**Update environment variables:**
```bash
# Remove old variable
vercel env rm AUTH_PASSWORD

# Add new variable
vercel env add AUTH_PASSWORD

# Redeploy
vercel --prod
```

**Add custom domain (optional):**
```bash
vercel domains add yourdomain.com
```

**Remove deployment:**
```bash
vercel rm copilot-quant
```

### 3.9 Important Notes

⚠️ **Vercel Limitations:**
- Only deploys the Streamlit UI
- Database and orchestrator must run elsewhere (local/VPS)
- No persistent storage on Vercel
- For full functionality, use Docker deployment

✅ **Cloud deployment complete!** See [Vercel-specific verification](#vercel-deployment) below.

---

## Service Verification

### Database Verification

**Check database is running:**

**Local PostgreSQL:**
```bash
psql -U copilot -d copilot_quant -c "SELECT version();"
```

**Docker:**
```bash
docker compose exec database psql -U copilot -d copilot_quant -c "SELECT version();"
```

**Check tables exist:**
```bash
# Local
psql -U copilot -d copilot_quant -c "\dt"

# Docker
docker compose exec database psql -U copilot -d copilot_quant -c "\dt"
```

Expected tables: `strategies`, `backtests`, `positions`, `trades`, etc.

### UI Verification

1. **Open UI**: http://localhost:8501
2. **Check pages load**:
   - Dashboard
   - Strategies
   - Backtests
   - Live Trading
   - Settings
3. **Test functionality**:
   - Create a strategy
   - Run a backtest
   - View performance charts

**UI Health Check:**
```bash
# Should return 200 OK
curl http://localhost:8501/_stcore/health
```

### Orchestrator Verification

**Check orchestrator is running:**

**Local:**
```bash
# Should show python process
ps aux | grep orchestrator
```

**Docker:**
```bash
docker compose logs orchestrator | tail -20
# Look for "Orchestrator started" message
```

**Check orchestrator logs:**
```bash
# Local
tail -f logs/orchestrator.log

# Docker
docker compose logs -f orchestrator
```

Expected log messages:
- `[INFO] Orchestrator initialized`
- `[INFO] Market status: CLOSED` (or TRADING during market hours)
- `[INFO] Heartbeat` (periodic)

### API Verification (if running)

```bash
# Health check
curl http://localhost:8000/health/

# Portfolio endpoint
curl http://localhost:8000/api/v1/portfolio/

# API documentation
# Open: http://localhost:8000/docs
```

### Vercel Deployment

1. Navigate to your Vercel URL
2. Login with configured credentials
3. Verify all pages accessible
4. Check Vercel dashboard for deployment status: https://vercel.com/dashboard

### Full System Check Script

Create this script to verify all services:

```bash
#!/bin/bash
# save as: verify_services.sh

echo "🔍 Copilot Quant Service Verification"
echo "======================================"

# Database
echo -n "📊 Database: "
if docker compose exec -T database psql -U copilot -d copilot_quant -c "SELECT 1" > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not running"
fi

# UI
echo -n "🖥️  UI: "
if curl -s http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    echo "✅ Running on http://localhost:8501"
else
    echo "❌ Not running"
fi

# Orchestrator
echo -n "🤖 Orchestrator: "
if docker compose ps orchestrator | grep -q "Up"; then
    echo "✅ Running"
else
    echo "❌ Not running"
fi

echo ""
echo "Run 'docker compose ps' for detailed status"
```

```bash
chmod +x verify_services.sh
./verify_services.sh
```

---

## Configuration Guide

### Environment Variables Reference

**Database Configuration:**
```bash
POSTGRES_USER=copilot              # Database username
POSTGRES_PASSWORD=secure_password  # Database password (CHANGE THIS)
POSTGRES_DB=copilot_quant          # Database name
POSTGRES_HOST=localhost            # localhost or database (Docker)
POSTGRES_PORT=5432                 # PostgreSQL port
DATABASE_URL=postgresql://copilot:password@localhost:5432/copilot_quant
```

**Trading Configuration:**
```bash
PAPER_TRADING=true                 # true = paper, false = live (CAUTION)
```

**Interactive Brokers (Paper Trading):**
```bash
IB_PAPER_HOST=127.0.0.1           # localhost or host.docker.internal
IB_PAPER_PORT=7497                # TWS paper port
IB_PAPER_CLIENT_ID=1              # Unique client ID
IB_PAPER_ACCOUNT=DUB267514        # Your paper account number
IB_PAPER_USE_GATEWAY=false        # false = TWS, true = IB Gateway
```

**Interactive Brokers (Live Trading - USE WITH CAUTION):**
```bash
IB_LIVE_HOST=127.0.0.1
IB_LIVE_PORT=7496                 # TWS live port
IB_LIVE_CLIENT_ID=2               # Different from paper
IB_LIVE_ACCOUNT=                  # Your live account number
IB_LIVE_USE_GATEWAY=false
```

**API & UI Ports:**
```bash
STREAMLIT_PORT=8501               # Streamlit UI port
API_PORT=8000                     # FastAPI REST API port
```

**Monitoring (Optional):**
```bash
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_PASSWORD=admin            # Change for production
```

**Authentication (Vercel/Cloud only):**
```bash
AUTH_EMAIL=admin@example.com      # Login email
AUTH_PASSWORD=secure_password     # Login password
AUTH_NAME=Admin User              # Display name
```

### Trading Configuration File (config.paper.yaml)

The orchestrator uses `config.paper.yaml` for strategy and risk settings:

```yaml
version: "1.0.0"
mode: paper  # or 'live' (USE WITH CAUTION)

schedule:
  timezone: "America/New_York"
  enable_pre_market: false
  enable_post_market: false
  auto_start: true
  auto_stop: true

strategy:
  symbols:
    - AAPL
    - MSFT
    - GOOGL
  max_positions: 10
  position_size_pct: 0.10

risk:
  max_portfolio_drawdown: 0.12
  min_cash_buffer: 0.20
  enable_circuit_breaker: true
  circuit_breaker_threshold: 0.10
```

See full example in `config.paper.yaml`.

### Port Reference

| Service | Default Port | Notes |
|---------|-------------|-------|
| PostgreSQL | 5432 | Database |
| Streamlit UI | 8501 | Web interface |
| FastAPI | 8000 | REST API |
| Prometheus | 9090 | Metrics (optional) |
| Grafana | 3000 | Dashboards (optional) |
| TWS Paper | 7497 | Interactive Brokers |
| TWS Live | 7496 | Interactive Brokers |
| IB Gateway Paper | 4002 | Interactive Brokers |
| IB Gateway Live | 4001 | Interactive Brokers |

---

## Common Issues and Troubleshooting

### Database Connection Issues

**Problem:** `could not connect to database`

**Solutions:**
```bash
# Check PostgreSQL is running
# Local:
sudo systemctl status postgresql  # Linux
brew services list                # macOS

# Docker:
docker compose ps database

# Check credentials in .env match database
# Verify DATABASE_URL format:
# postgresql://USERNAME:PASSWORD@HOST:PORT/DATABASE

# Test connection
psql -U copilot -h localhost -d copilot_quant
```

### Docker Container Won't Start

**Problem:** Container exits immediately or fails health check

**Solutions:**
```bash
# View detailed logs
docker compose logs <service_name>

# Check for port conflicts
sudo lsof -i :5432  # Database
sudo lsof -i :8501  # UI

# Rebuild containers
docker compose down
docker compose up -d --build

# Check disk space
docker system df
```

### Cannot Connect to Interactive Brokers

**Problem:** `Connection refused` or `Failed to connect to IBKR`

**Solutions:**
1. **Ensure TWS/Gateway is running on host machine**
2. **Enable API connections in TWS/Gateway**:
   - File → Global Configuration → API → Settings
   - ✓ Enable ActiveX and Socket Clients
   - ✓ Read-Only API: Unchecked (for trading)
   - Socket Port: 7497 (paper) or 7496 (live)
3. **Check host configuration**:
   - Docker: Use `IB_HOST=host.docker.internal`
   - Local: Use `IB_HOST=127.0.0.1`
4. **Verify port numbers**:
   - TWS Paper: 7497
   - TWS Live: 7496
   - Gateway Paper: 4002
   - Gateway Live: 4001
5. **Check firewall**:
   ```bash
   # Allow port through firewall
   sudo ufw allow 7497  # Linux
   ```

See [IBKR Connection Troubleshooting](IBKR_CONNECTION_TROUBLESHOOTING.md) for detailed help.

### Streamlit UI Won't Load

**Problem:** Cannot access http://localhost:8501

**Solutions:**
```bash
# Check Streamlit is running
ps aux | grep streamlit  # Local
docker compose logs ui   # Docker

# Check port isn't blocked
curl http://localhost:8501/_stcore/health

# Restart UI
# Docker:
docker compose restart ui

# Local:
# Kill existing process
pkill -f streamlit
# Restart
streamlit run copilot_quant/ui/app.py
```

### Permission Denied Errors

**Problem:** `Permission denied` when accessing files or sockets

**Solutions:**
```bash
# Docker: Fix volume permissions
sudo chown -R $USER:$USER ./data ./logs

# PostgreSQL: Fix data directory
sudo chown -R postgres:postgres /var/lib/postgresql/data

# Script files: Add execute permission
chmod +x scripts/*.py
```

### Out of Memory

**Problem:** Container or process killed due to OOM

**Solutions:**
```bash
# Docker: Increase memory limit
# Edit Docker Desktop → Settings → Resources → Memory
# Or add to docker-compose.yml:
services:
  orchestrator:
    deploy:
      resources:
        limits:
          memory: 2G

# System: Check available memory
free -h  # Linux
vm_stat  # macOS

# Reduce services if needed
docker compose stop prometheus grafana
```

### Module Import Errors

**Problem:** `ModuleNotFoundError: No module named 'copilot_quant'`

**Solutions:**
```bash
# Ensure package is installed
pip install -e .

# Verify installation
python -c "import copilot_quant; print(copilot_quant.__file__)"

# Check virtual environment is activated
which python  # Should show venv/bin/python

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Vercel Deployment Fails

**Problem:** Deployment fails or authentication doesn't work

**Solutions:**
```bash
# Check environment variables are set
vercel env ls

# Verify variable names (exact match required):
# - AUTH_EMAIL
# - AUTH_PASSWORD
# - AUTH_NAME

# View deployment logs
vercel logs <deployment-url>

# Redeploy after fixing
vercel --prod

# Check Vercel dashboard for errors
# https://vercel.com/dashboard
```

### Database Migration Errors

**Problem:** Schema mismatch or migration failures

**Solutions:**
```bash
# Reinitialize database (CAUTION: deletes data)
# Local:
dropdb -U postgres copilot_quant
createdb -U postgres copilot_quant
psql -U copilot -d copilot_quant -f scripts/init_db.sql

# Docker:
docker compose down -v  # Removes volumes
docker compose up -d    # Recreates with fresh DB
```

---

## Next Steps

### After Successful Bootstrap

1. **Configure Trading**:
   - Review `config.paper.yaml`
   - Set up Interactive Brokers (see [IBKR Comprehensive Guide](IBKR_COMPREHENSIVE_GUIDE.md))
   - Configure notification channels (Slack, Discord, Email)

2. **Explore Features**:
   - Create your first strategy (UI → Strategies → New Strategy)
   - Run a backtest (UI → Backtests)
   - Monitor live data (UI → Live Trading)
   - Explore API endpoints (http://localhost:8000/docs)

3. **Set Up Monitoring** (Production):
   - Enable Prometheus and Grafana
   - Configure alerts
   - Set up log aggregation
   - See [MONITORING.md](MONITORING.md)

4. **Production Hardening**:
   - Change default passwords
   - Enable SSL/TLS
   - Configure backups
   - Set up systemd service
   - Review security best practices

5. **Team Collaboration**:
   - Share `.env.example` (never `.env`)
   - Document custom configurations
   - Set up CI/CD pipelines
   - Configure team access

### Recommended Reading

- **[IBKR Comprehensive Guide](IBKR_COMPREHENSIVE_GUIDE.md)** - Complete Interactive Brokers setup
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Vercel cloud deployment guide
- **[DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)** - Advanced Docker configuration
- **[ORCHESTRATOR.md](ORCHESTRATOR.md)** - Trading orchestrator details
- **[MONITORING.md](MONITORING.md)** - Observability and logging
- **[API.md](API.md)** - REST API reference
- **[Quick Reference](quick_reference.md)** - Common commands and patterns

### Getting Help

- **Documentation**: [docs/README.md](README.md)
- **Issues**: [GitHub Issues](https://github.com/harryb2088/copilot_quant/issues)
- **Contributing**: [CONTRIBUTING.md](../CONTRIBUTING.md)

---

## Quick Reference Commands

### Docker Compose

```bash
# Start all services
docker compose up -d

# Start with monitoring
docker compose --profile monitoring up -d

# View logs
docker compose logs -f

# Stop services
docker compose stop

# Restart services
docker compose restart

# Rebuild and restart
docker compose up -d --build

# Remove everything (INCLUDING DATA)
docker compose down -v
```

### Local Development

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Start UI
streamlit run copilot_quant/ui/app.py

# Start orchestrator
python -m copilot_quant.orchestrator

# Start API
python scripts/run_api.py

# Database access
psql -U copilot -d copilot_quant
```

### Vercel

```bash
# Deploy
vercel --prod

# View logs
vercel logs <deployment-url> --follow

# Manage environment variables
vercel env ls
vercel env add <VAR_NAME>
vercel env rm <VAR_NAME>
```

---

**🎉 You're all set! The Copilot Quant Platform is ready to use.**

For questions or issues, consult the troubleshooting section above or review the comprehensive documentation in the `docs/` directory.
