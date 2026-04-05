# MORBION Processes

MORBION Virtual ICS Lab - 4 Industrial Processes with Central Manager

## Processes

| Process | Port | Description |
|--------|------|-------------|
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
python manager.py start

# Check status
python manager.py status

# View logs
python manager.py logs

# Stop all processes
python manager.py stop
```

## Installation Options

### Basic Installation (No Service)

```bash
python installer.py
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
| `python manager.py start` | Start all 4 processes |
| `python manager.py stop` | Stop all 4 processes |
| `python manager.py restart` | Restart all 4 processes |
| `python manager.py status` | Show status of all processes |
| `python manager.py logs` | Show last 50 lines of logs |
| `python manager.py logs -f` | Follow logs live (Ctrl+C to exit) |

## Uninstaller

```bash
# Full uninstall (stops processes, removes services, cleans logs + config)
python uninstaller.py

# Selective uninstall
python uninstaller.py --no-services    # Keep services
python uninstaller.py --no-logs         # Keep logs
python uninstaller.py --no-config       # Keep config
```

## Backward Compatibility

Each process folder still has its own `start.sh` and `stop.sh`:

```bash
cd pumping_station
./start.sh    # Start just pumping station
./stop.sh     # Stop just pumping station
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

```bash
pip install pyyaml
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
└── requirements.txt       # Dependencies
```

## License

MORBION Virtual ICS Lab - Industrial Control System Simulation
