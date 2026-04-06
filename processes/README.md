# MORBION Processes

MORBION Virtual ICS Lab - 4 Industrial Processes with Central Manager

## Processes

| Process | Port | Description |
|---------|------|-------------|
| Pumping Station | 502 | Nairobi Water Municipal Pumping Station |
| Heat Exchanger | 506 | KenGen Olkaria Geothermal Heat Recovery |
| Boiler | 507 | EABL/Bidco Industrial Steam Generation |
| Pipeline | 508 | Kenya Pipeline Co. Petroleum Transfer |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run installer (creates logs dir + config)
python installer.py

# Start all processes
sudo python3 manager.py start    # Linux: sudo required for ports < 1024

# Check status
sudo python3 manager.py status

# View logs
sudo python3 manager.py logs

# Stop all processes
sudo python3 manager.py stop
```

**Linux Note:** Ports 502, 506, 507, 508 are privileged on Linux. You must use `sudo` for all manager commands.

## Installation Options

### Basic Installation (No Service)

```bash
sudo python installer.py    # Linux: sudo required
python installer.py          # Windows (as Admin)
```

Creates:
- `logs/` directory
- `config.yaml` (if not exists)

### With System Services (Optional)

Requires admin/root privileges:

```bash
# Linux
sudo python installer.py --services

# Windows (Run as Administrator)
python installer.py --services
```

This creates systemd services (Linux) or Windows Services for auto-restart and boot.

## Manager Commands

| Command | Description |
|---------|-------------|
| `sudo python3 manager.py start` | Start all 4 processes |
| `sudo python3 manager.py stop` | Stop all 4 processes |
| `sudo python3 manager.py restart` | Restart all 4 processes |
| `sudo python3 manager.py status` | Show status of all processes |
| `sudo python3 manager.py logs` | Show last 50 lines of logs |
| `sudo python3 manager.py logs -f` | Follow logs live (Ctrl+C to exit) |

## Uninstaller

```bash
# Full uninstall (stops processes, removes services, cleans logs + config)
sudo python uninstaller.py

# Selective uninstall
sudo python uninstaller.py --no-services    # Keep services
sudo python uninstaller.py --no-logs         # Keep logs
sudo python uninstaller.py --no-config       # Keep config
```

## Backward Compatibility

Each process folder still has its own `start.sh` and `stop.sh`:

```bash
cd pumping_station
sudo bash start.sh    # Start just pumping station
sudo bash stop.sh     # Stop just pumping station
```

## Configuration

Edit `config.yaml` to change:

- Port numbers
- Enable/disable specific processes
- Log directory location
- Auto-restart settings

## Requirements

- Python 3.8+
- PyYAML
- psutil

```bash
pip install pyyaml psutil
```

## Troubleshooting

### Permission Denied (Linux)
Ports below 1024 require root:
```bash
sudo python3 manager.py start
```

### psutil not found
Install for root:
```bash
sudo pip3 install psutil
```

### Manager says "Not running" but processes are running
Always use sudo for both start and stop:
```bash
sudo python3 manager.py start
sudo python3 manager.py stop
```

### Manual kill if stuck
```bash
sudo pkill -f "python3.*main.py"
```

### Verify processes are running
```bash
sudo ss -tlnp | grep -E ':(502|506|507|508) '
```

## Architecture

```
morbion_processes/
├── pumping_station/       # Process 1
├── heat_exchanger/        # Process 2
├── boiler/                # Process 3
├── pipeline/              # Process 4
├── logs/                  # Created by installer
├── config.yaml            # Central config
├── manager.py             # Central manager (OOP)
├── installer.py           # Installer (OOP)
├── uninstaller.py         # Uninstaller (OOP)
├── test_communication.py  # CLI monitor tool
└── requirements.txt       # Dependencies
```

## License

MORBION Virtual ICS Lab - Industrial Control System Simulation
