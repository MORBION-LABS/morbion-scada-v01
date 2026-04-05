"""
Real-time MORBION Process Monitor
CLI tool using Typer and Rich for beautiful terminal UI.
"""

import socket
import struct
import time
import threading
from datetime import datetime
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

app = typer.Typer(help="MORBION Process Monitor - Real-time Modbus TCP client")
console = Console()


def read_holding_registers(host: str, port: int, start_addr: int, count: int) -> Optional[list]:
    """Read holding registers via Modbus TCP."""
    try:
        transaction_id = 1
        protocol_id = 0
        unit_id = 1
        
        mbap = struct.pack('>HHHB', transaction_id, protocol_id, 6, unit_id)
        fc = 0x03
        pdu = struct.pack('>BHH', fc, start_addr - 1, count)
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((host, port))
        sock.sendall(mbap + pdu)
        
        response = sock.recv(1024)
        sock.close()
        
        byte_count = response[8]
        registers = struct.unpack(f'>{byte_count//2}H', response[9:9+byte_count])
        return list(registers)
    except Exception:
        return None


def get_process_data(host: str, port: int) -> dict:
    """Get process-specific data."""
    regs = read_holding_registers(host, port, 1, 20)
    
    if regs is None:
        return {"status": "OFFLINE"}
    
    if port == 502:  # Pumping Station
        return {
            "status": "ONLINE",
            "tank_level": regs[0] / 10,
            "tank_volume": regs[1] / 10,
            "pump_speed": regs[2],
            "flow": regs[3] / 10,
            "pressure": regs[4] / 100,
            "pump_running": bool(regs[7]),
            "inlet_valve": regs[8] / 10,
            "outlet_valve": regs[9] / 10,
        }
    elif port == 506:  # Heat Exchanger
        return {
            "status": "ONLINE",
            "T_hot_in": regs[0] / 10,
            "T_hot_out": regs[1] / 10,
            "T_cold_in": regs[2] / 10,
            "T_cold_out": regs[3] / 10,
            "flow_hot": regs[4] / 10,
            "flow_cold": regs[5] / 10,
            "efficiency": regs[6] / 10,
            "hot_valve": regs[14] / 10,
            "cold_valve": regs[15] / 10,
        }
    elif port == 507:  # Boiler
        return {
            "status": "ONLINE",
            "drum_pressure": regs[0] / 100,
            "drum_level": regs[1] / 10,
            "steam_flow": regs[2],
            "fuel_flow": regs[4] / 10,
            "flue_temp": regs[5] / 10,
            "burner_state": regs[6],
            "comb_eff": regs[7] / 10,
            "Q_burner": regs[8],
        }
    elif port == 508:  # Pipeline
        return {
            "status": "ONLINE",
            "inlet_pressure": regs[0] / 100,
            "outlet_pressure": regs[1] / 100,
            "flow_rate": regs[2] / 10,
            "flow_velocity": regs[3] / 100,
            "duty_pump_running": bool(regs[5]),
            "duty_pump_speed": regs[6],
            "duty_pump_current": regs[7] / 10,
            "inlet_valve": regs[8] / 10,
            "outlet_valve": regs[9] / 10,
        }
    return {"status": "UNKNOWN"}


def create_table(processes: list, data: dict) -> Table:
    """Create a Rich table with process status."""
    table = Table(title=f"MORBION Processes - {datetime.now().strftime('%H:%M:%S')}", show_header=True, header_style="bold cyan")
    table.add_column("Process", style="cyan", width=18)
    table.add_column("Status", width=10)
    table.add_column("Key Metrics", style="white")
    
    for name, host, port in processes:
        proc_data = data.get(port, {})
        
        if proc_data.get("status") == "OFFLINE":
            table.add_row(
                name,
                "[red]OFFLINE[/red]",
                "[dim]No response[/dim]"
            )
            continue
        
        if port == 502:
            metrics = f"Tank: {proc_data.get('tank_level', 0):.1f}% | Flow: {proc_data.get('flow', 0):.1f} m³/hr | Pump: {'RUN' if proc_data.get('pump_running') else 'STOP'}"
        elif port == 506:
            metrics = f"Hot In: {proc_data.get('T_hot_in', 0):.1f}°C | Cold Out: {proc_data.get('T_cold_out', 0):.1f}°C | Eff: {proc_data.get('efficiency', 0):.1f}%"
        elif port == 507:
            burner_states = {0: "OFF", 1: "LOW", 2: "HIGH"}
            bs = burner_states.get(proc_data.get('burner_state', 0), "UNK")
            metrics = f"Pressure: {proc_data.get('drum_pressure', 0):.2f} bar | Level: {proc_data.get('drum_level', 0):.1f}% | Burner: {bs}"
        elif port == 508:
            metrics = f"Outlet: {proc_data.get('outlet_pressure', 0):.2f} bar | Flow: {proc_data.get('flow_rate', 0):.1f} m³/hr | Pump: {'RUN' if proc_data.get('duty_pump_running') else 'STOP'}"
        else:
            metrics = "-"
        
        table.add_row(name, "[green]ONLINE[/green]", metrics)
    
    return table


@app.command()
def monitor(
    interval: int = typer.Option(2, "--interval", "-i", help="Update interval in seconds"),
    once: bool = typer.Option(False, "--once", "-1", help="Run once and exit"),
):
    """Real-time MORBION process monitor."""
    processes = [
        ("Pumping Station", "127.0.0.1", 502),
        ("Heat Exchanger", "127.0.0.1", 506),
        ("Boiler", "127.0.0.1", 507),
        ("Pipeline", "127.0.0.1", 508),
    ]
    
    console.print(Panel.fit(
        Text("MORBION Process Monitor", justify="center", style="bold cyan"),
        border_style="cyan"
    ))
    console.print(f"[dim]Polling every {interval} seconds. Press Ctrl+C to exit.[/dim]\n")
    
    if once:
        data = {}
        for name, host, port in processes:
            data[port] = get_process_data(host, port)
        table = create_table(processes, data)
        console.print(table)
        return
    
    with Live(console=console, refresh_per_second=1) as live:
        while True:
            data = {}
            for name, host, port in processes:
                data[port] = get_process_data(host, port)
            
            table = create_table(processes, data)
            live.update(table)
            time.sleep(interval)


@app.command()
def status():
    """Show current status of all processes."""
    processes = [
        ("Pumping Station", "127.0.0.1", 502),
        ("Heat Exchanger", "127.0.0.1", 506),
        ("Boiler", "127.0.0.1", 507),
        ("Pipeline", "127.0.0.1", 508),
    ]
    
    console.print("\n[bold cyan]MORBION Process Status[/bold cyan]\n")
    
    for name, host, port in processes:
        data = get_process_data(host, port)
        if data.get("status") == "OFFLINE":
            console.print(f"[red]✗[/red] {name:20} [red]OFFLINE[/red]")
        else:
            console.print(f"[green]✓[/green] {name:20} [green]ONLINE[/green]")
    
    console.print()


@app.command()
def test():
    """Test connectivity to all processes."""
    processes = [
        ("Pumping Station", "127.0.0.1", 502),
        ("Heat Exchanger", "127.0.0.1", 506),
        ("Boiler", "127.0.0.1", 507),
        ("Pipeline", "127.0.0.1", 508),
    ]
    
    console.print("\n[bold cyan]Testing MORBION Process Connectivity[/bold cyan]\n")
    
    all_ok = True
    for name, host, port in processes:
        regs = read_holding_registers(host, port, 1, 5)
        if regs:
            console.print(f"[green]✓[/green] {name:20} Port {port} [green]OK[/green] - Registers read: {len(regs)}")
        else:
            console.print(f"[red]✗[/red] {name:20} Port {port} [red]FAILED[/red]")
            all_ok = False
    
    console.print()
    if all_ok:
        console.print("[green]All processes are reachable![/green]")
    else:
        console.print("[red]Some processes are unreachable![/red]")


if __name__ == "__main__":
    app()
