# System Resource Dashboard

Real-time terminal-based dashboard for monitoring CPU, memory, disk, and network metrics with visual progress bars and sparkline history charts.

## Features

- **CPU Monitoring**: Overall usage, per-core breakdown, load averages
- **Memory Monitoring**: RAM and swap usage with detailed byte counts
- **Disk Monitoring**: Per-partition usage with mount point details
- **Network Monitoring**: TX/RX byte counts and packet statistics
- **Visual Indicators**: Color-coded progress bars (green/yellow/red based on thresholds)
- **Sparkline History**: 60-second rolling history charts for CPU, memory, and disk
- **System Info**: Uptime, process count, core count

## Requirements

- Python 3.6+
- Linux, macOS, or Windows (curses support required)
- `psutil` library

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python dashboard.py
```

Press `Ctrl+C` to exit the dashboard.

## Screenshot Layout

```
╔══ System Resource Dashboard - myhost ═══════ 2026-04-14 10:30:00╗
 Uptime: 5d 3h 22m 15s  Processes: 234  Cores: 4p/8l

── CPU ─────────────────────────────────────────────────────────────
  Overall [████████████████░░░░░░░░░░░░░░░░░░░░]  42.3%
  Load Avg: 1.23 / 0.98 / 0.75
  Cores:  35.2%  48.1%  52.0%  31.5%  44.7%  39.8%  50.2%  41.1%
CPU History   ▂▃▄▅▄▃▂▁▂▃▄▅▆▇▆▅▄▃  curr: 42.3%

── MEMORY ──────────────────────────────────────────────────────────
  RAM     [██████████░░░░░░░░░░░░░░░░░░░░░░░░░░]  25.8%
    Used: 4.1 GB  /  Free: 11.8 GB  /  Total: 15.9 GB
  Swap    [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]   0.0%
RAM History   ▁▁▂▁▂▃▂▁▁▂▂▃▂▁▁▁▁▁  curr: 25.8%

── DISK ────────────────────────────────────────────────────────────
  Disk    [██████████████████████░░░░░░░░░░░░░░]  55.2%
    Used: 120.5 GB  /  Free: 97.8 GB
  /             [██████████████████████░░░░░░░░░░]  55.2%
  /boot/efi     [█████░░░░░░░░░░░░░░░░░░░░░░░░░░░]  12.3%
Disk History    ▄▄▄▄▄▄▅▅▅▅▅▅▅▅▅▅▅▅  curr: 55.2%

── NETWORK ─────────────────────────────────────────────────────────
  TX: 1.2 GB (456789 pkts)  RX: 3.4 GB (789012 pkts)

                        Press Ctrl+C to exit
```

## Color Coding

| Color   | Threshold | Meaning          |
|---------|-----------|------------------|
| Green   | < 70%     | Normal usage     |
| Yellow  | 70-89%    | Elevated usage   |
| Red     | >= 90%    | Critical usage   |

## Architecture

- **`ResourceMonitor`**: Collects metrics from the OS using `psutil`
- **`DashboardRenderer`**: Renders the terminal UI using Python's built-in `curses` module
- Metrics are collected every second with a 60-sample rolling history

## License

MIT
