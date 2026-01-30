#!/usr/bin/env python3
"""
System Resource Dashboard - Real-time monitoring dashboard
with CPU, memory, and disk metrics displayed in the terminal.
"""

import os
import sys
import time
import signal
import curses
import psutil
from datetime import datetime


class ResourceMonitor:
    """Collects system resource metrics from the OS."""

    def __init__(self):
        self.cpu_count = psutil.cpu_count()
        self.cpu_count_logical = psutil.cpu_count(logical=True)
        self.hostname = os.uname().nodename
        self.boot_time = datetime.fromtimestamp(psutil.boot_time())
        self.history_length = 60
        self.cpu_history = []
        self.memory_history = []
        self.disk_history = []

    def get_cpu_metrics(self):
        """Returns current CPU usage percentage and per-core breakdown."""
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cpu_per_core = psutil.cpu_percent(interval=0, percpu=True)
        load_avg = os.getloadavg()
        self.cpu_history.append(cpu_percent)
        if len(self.cpu_history) > self.history_length:
            self.cpu_history.pop(0)
        return {
            "percent": cpu_percent,
            "per_core": cpu_per_core,
            "load_avg_1": load_avg[0],
            "load_avg_5": load_avg[1],
            "load_avg_15": load_avg[2],
            "cores_physical": self.cpu_count,
            "cores_logical": self.cpu_count_logical,
        }

    def get_memory_metrics(self):
        """Returns memory usage statistics in bytes and percentages."""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        self.memory_history.append(mem.percent)
        if len(self.memory_history) > self.history_length:
            self.memory_history.pop(0)
        return {
            "total": mem.total,
            "available": mem.available,
            "used": mem.used,
            "free": mem.free,
            "percent": mem.percent,
            "swap_total": swap.total,
            "swap_used": swap.used,
            "swap_free": swap.free,
            "swap_percent": swap.percent,
        }

    def get_disk_metrics(self):
        """Returns disk usage for all mounted partitions."""
        partitions = psutil.disk_partitions(all=False)
        disk_data = []
        total_used = 0
        total_free = 0
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                total_used += usage.used
                total_free += usage.free
                disk_data.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent,
                })
            except PermissionError:
                continue
        self.disk_history.append(
            (total_used / (total_used + total_free) * 100) if (total_used + total_free) > 0 else 0
        )
        if len(self.disk_history) > self.history_length:
            self.disk_history.pop(0)
        return {
            "partitions": disk_data,
            "total_used": total_used,
            "total_free": total_free,
            "total_percent": (
                (total_used / (total_used + total_free) * 100)
                if (total_used + total_free) > 0
                else 0
            ),
        }

    def get_network_metrics(self):
        """Returns network I/O counters."""
        net = psutil.net_io_counters()
        return {
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv,
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv,
        }

    @staticmethod
    def format_bytes(nbytes):
        """Format bytes into human-readable units."""
        if nbytes < 1024:
            return f"{nbytes} B"
        elif nbytes < 1024 ** 2:
            return f"{nbytes / 1024:.1f} KB"
        elif nbytes < 1024 ** 3:
            return f"{nbytes / 1024 ** 2:.1f} MB"
        elif nbytes < 1024 ** 4:
            return f"{nbytes / 1024 ** 3:.1f} GB"
        else:
            return f"{nbytes / 1024 ** 4:.2f} TB"

    def get_process_count(self):
        """Returns the total number of running processes."""
        return len(psutil.pids())

    def get_uptime(self):
        """Returns system uptime as a formatted string."""
        uptime_delta = datetime.now() - self.boot_time
        days = uptime_delta.days
        hours, remainder = divmod(uptime_delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{days}d {hours}h {minutes}m {seconds}s"


class DashboardRenderer:
    """Renders the system resource dashboard using curses."""

    COLORS = {
        "default": 0,
        "green": 1,
        "yellow": 2,
        "red": 3,
        "cyan": 4,
        "magenta": 5,
        "white": 6,
    }

    def __init__(self, stdscr, monitor):
        self.stdscr = stdscr
        self.monitor = monitor
        self.running = True
        self._init_colors()
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _init_colors(self):
        """Initialize color pairs for the curses display."""
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        for name, num in self.COLORS.items():
            if num > 0:
                if name == "green":
                    curses.init_pair(num, curses.COLOR_GREEN, -1)
                elif name == "yellow":
                    curses.init_pair(num, curses.COLOR_YELLOW, -1)
                elif name == "red":
                    curses.init_pair(num, curses.COLOR_RED, -1)
                elif name == "cyan":
                    curses.init_pair(num, curses.COLOR_CYAN, -1)
                elif name == "magenta":
                    curses.init_pair(num, curses.COLOR_MAGENTA, -1)
                elif name == "white":
                    curses.init_pair(num, curses.COLOR_WHITE, -1)

    def _signal_handler(self, signum, frame):
        """Handle termination signals gracefully."""
        self.running = False

    def _color_for_percent(self, percent):
        """Return the appropriate color attribute based on usage percentage."""
        if percent >= 90:
            return curses.color_pair(self.COLORS["red"]) | curses.A_BOLD
        elif percent >= 70:
            return curses.color_pair(self.COLORS["yellow"]) | curses.A_BOLD
        else:
            return curses.color_pair(self.COLORS["green"]) | curses.A_BOLD

    def _format_bytes(self, nbytes):
        """Format bytes into human-readable units."""
        return ResourceMonitor.format_bytes(nbytes)

    def _draw_progress_bar(self, win, y, x, width, percent, label=""):
        """Draw a visual progress bar representing usage percentage."""
        filled = int(width * percent / 100.0)
        bar = "█" * filled + "░" * (width - filled)
        color = self._color_for_percent(percent)
        if label:
            win.addstr(y, x, f"{label} ", curses.A_BOLD)
            win.addstr(y, x + len(label) + 1, f"[{bar}] {percent:5.1f}%", color)
        else:
            win.addstr(y, x, f"[{bar}] {percent:5.1f}%", color)

    def _draw_sparkline(self, win, y, x, width, data, label=""):
        """Draw a sparkline chart from a list of percentage values."""
        if not data:
            return
        spark_chars = "▁▂▃▄▅▆▇█"
        win.addstr(y, x, f"{label:<14}", curses.color_pair(self.COLORS["cyan"]) | curses.A_BOLD)
        win.addstr(" ", curses.A_DIM)
        step = max(len(data) // width, 1)
        sampled = data[::step][:width]
        for val in sampled:
            idx = min(int(val / 100.0 * (len(spark_chars) - 1)), len(spark_chars) - 1)
            color = self._color_for_percent(val)
            win.addstr(spark_chars[idx], color)
        if sampled:
            latest = sampled[-1]
            win.addstr(f"  curr: {latest:.1f}%", self._color_for_percent(latest))

    def _draw_header(self, win, max_y):
        """Draw the dashboard header with system info."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        title = f" System Resource Dashboard - {self.monitor.hostname} "
        separator = "═" * (max_y - len(title) - len(now) - 2)
        header = f"╔{title}{separator}{now}╗"
        win.addstr(0, 0, header[:max_y - 1], curses.color_pair(self.COLORS["cyan"]) | curses.A_BOLD)

    def _draw_section(self, win, y, max_y, title, width=60):
        """Draw a section border with a title."""
        line = "─" * (width - len(title) - 4)
        win.addstr(y, 0, f"── {title} {line}", curses.color_pair(self.COLORS["magenta"]) | curses.A_BOLD)
        return y + 1

    def render(self):
        """Main render loop - collects metrics and draws the dashboard."""
        while self.running:
            try:
                self.stdscr.erase()
                max_y, max_x = self.stdscr.getmaxyx()

                if max_y < 20 or max_x < 60:
                    self.stdscr.addstr(0, 0, "Terminal too small. Resize to at least 60x20.")
                    self.stdscr.refresh()
                    time.sleep(0.5)
                    continue

                cpu = self.monitor.get_cpu_metrics()
                memory = self.monitor.get_memory_metrics()
                disk = self.monitor.get_disk_metrics()
                network = self.monitor.get_network_metrics()
                proc_count = self.monitor.get_process_count()
                uptime = self.monitor.get_uptime()

                # Header
                self._draw_header(self.stdscr, max_x)
                row = 2

                # System info line
                self.stdscr.addstr(row, 0, f" Uptime : {uptime}", curses.A_BOLD)
                self.stdscr.addstr(f"  Processes: {proc_count}", curses.color_pair(self.COLORS["cyan"]))
                self.stdscr.addstr(f"  Cores: {cpu['cores_physical']}p/{cpu['cores_logical']}l", curses.color_pair(self.COLORS["cyan"]))
                row += 2

                # CPU Section
                row = self._draw_section(self.stdscr, row, max_x, "CPU", max_x)
                self._draw_progress_bar(self.stdscr, row, 2, min(40, max_x - 25), cpu["percent"], "Overall")
                row += 1
                self.stdscr.addstr(row, 2, f"Load Avg: {cpu['load_avg_1']:.2f} / {cpu['load_avg_5']:.2f} / {cpu['load_avg_15']:.2f}", curses.A_DIM)
                row += 1
                num_cores_to_show = min(len(cpu["per_core"]), max_x - 4)
                if num_cores_to_show > 0:
                    self.stdscr.addstr(row, 2, "Cores: ", curses.A_BOLD)
                    for i in range(num_cores_to_show):
                        color = self._color_for_percent(cpu["per_core"][i])
                        self.stdscr.addstr(f"{cpu['per_core'][i]:5.1f}% ", color)
                    row += 1
                row += 1
                self._draw_sparkline(self.stdscr, row, 0, min(50, max_x - 5), self.monitor.cpu_history, "CPU History")
                row += 2

                # Memory Section
                row = self._draw_section(self.stdscr, row, max_x, "MEMORY", max_x)
                self._draw_progress_bar(self.stdscr, row, 2, min(40, max_x - 25), memory["percent"], "RAM")
                row += 1
                self.stdscr.addstr(row, 4, f"Used: {self._format_bytes(memory['used'])}  /  Free: {self._format_bytes(memory['free'])}  /  Total: {self._format_bytes(memory['total'])}", curses.A_DIM)
                row += 1
                if memory["swap_total"] > 0:
                    self._draw_progress_bar(self.stdscr, row, 2, min(40, max_x - 25), memory["swap_percent"], "Swap")
                    row += 1
                row += 1
                self._draw_sparkline(self.stdscr, row, 0, min(50, max_x - 5), self.monitor.memory_history, "RAM History")
                row += 2

                # Disk Section
                row = self._draw_section(self.stdscr, row, max_x, "DISK", max_x)
                self._draw_progress_bar(self.stdscr, row, 2, min(40, max_x - 25), disk["total_percent"], "Disk")
                row += 1
                self.stdscr.addstr(row, 4, f"Used: {self._format_bytes(disk['total_used'])}  /  Free: {self._format_bytes(disk['total_free'])}", curses.A_DIM)
                row += 1
                for part in disk["partitions"]:
                    if row >= max_y - 4:
                        break
                    self._draw_progress_bar(self.stdscr, row, 4, min(35, max_x - 30), part["percent"], f"{part['mountpoint'][:12]}")
                    row += 1
                row += 1
                self._draw_sparkline(self.stdscr, row, 0, min(50, max_x - 5), self.monitor.disk_history, "Disk History")
                row += 2

                # Network Section
                row = self._draw_section(self.stdscr, row, max_x, "NETWORK", max_x)
                self.stdscr.addstr(row, 2, f"TX: {self._format_bytes(network['bytes_sent'])} ({network['packets_sent']} pkts)", curses.color_pair(self.COLORS["green"]))
                self.stdscr.addstr(f"  RX: {self._format_bytes(network['bytes_recv'])} ({network['packets_recv']} pkts)", curses.color_pair(self.COLORS["cyan"]))
                row += 2

                # Footer
                footer = " Press Ctrl+C to exit "
                footer_x = max(0, (max_x - len(footer)) // 2)
                self.stdscr.addstr(max_y - 1, footer_x, footer, curses.color_pair(self.COLORS["white"]) | curses.A_BOLD | curses.A_REVERSE)

                self.stdscr.refresh()
                time.sleep(1)

            except curses.error:
                continue
            except Exception as e:
                self.running = False
                raise e


def main(stdscr):
    """Entry point for the curses dashboard."""
    monitor = ResourceMonitor()
    dashboard = DashboardRenderer(stdscr, monitor)
    dashboard.render()


if __name__ == "__main__":
    print("Starting System Resource Dashboard...")
    print(f"Hostname: {os.uname().nodename}")
    print(f"CPU Cores: {psutil.cpu_count()}")
    total_mem = psutil.virtual_memory().total
    print(f"Total Memory: {ResourceMonitor.format_bytes(total_mem)}")
    print("-" * 40)
    print("Press Ctrl+C to exit\n")
    curses.wrapper(main)
    print("Dashboard stopped.")
