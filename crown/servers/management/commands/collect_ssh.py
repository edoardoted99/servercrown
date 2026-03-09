"""Collect metrics from servers via SSH (pull mode).

Usage:
  python manage.py collect_ssh              # one-shot, all SSH servers
  python manage.py collect_ssh --loop 10    # continuous, every 10 seconds
  python manage.py collect_ssh --server 3   # single server by ID
"""
import json
import subprocess
import time

from django.core.management.base import BaseCommand
from django.utils import timezone

from servers.models import Server, Metric

# Inline Python script executed on the remote host via SSH.
# Only depends on psutil (must be installed on the target).
REMOTE_SCRIPT = r"""
import json, os, time, platform, psutil
cpu = psutil.cpu_percent(interval=1)
mem = psutil.virtual_memory()
disk = psutil.disk_usage('/')
l1, l5, l15 = os.getloadavg()
print(json.dumps({
    'cpu_percent': cpu,
    'memory_percent': mem.percent,
    'memory_used_mb': round(mem.used/1024/1024, 1),
    'memory_total_mb': round(mem.total/1024/1024, 1),
    'disk_percent': disk.percent,
    'disk_used_gb': round(disk.used/1024/1024/1024, 2),
    'disk_total_gb': round(disk.total/1024/1024/1024, 2),
    'load_1m': round(l1, 2),
    'load_5m': round(l5, 2),
    'load_15m': round(l15, 2),
    'uptime_seconds': int(time.time() - psutil.boot_time()),
    'os': f"{platform.system()} {platform.release()} ({platform.machine()})",
}))
"""


def collect_from(server):
    """SSH into a server, run the metrics script, return parsed dict or None."""
    cmd = [
        'sshpass', '-p', server.ssh_password,
        'ssh',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=10',
        '-p', str(server.ssh_port),
        f'{server.ssh_user}@{server.ssh_host}',
        'python3', '-c', REMOTE_SCRIPT,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return None, result.stderr.strip()
        return json.loads(result.stdout), None
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
        return None, str(e)


def save_metrics(server, payload):
    """Save collected metrics and update server status."""
    Metric.objects.create(
        server=server,
        cpu_percent=payload.get('cpu_percent', 0),
        memory_percent=payload.get('memory_percent', 0),
        memory_used_mb=payload.get('memory_used_mb', 0),
        memory_total_mb=payload.get('memory_total_mb', 0),
        disk_percent=payload.get('disk_percent', 0),
        disk_used_gb=payload.get('disk_used_gb', 0),
        disk_total_gb=payload.get('disk_total_gb', 0),
        load_1m=payload.get('load_1m', 0),
        load_5m=payload.get('load_5m', 0),
        load_15m=payload.get('load_15m', 0),
        uptime_seconds=payload.get('uptime_seconds', 0),
    )
    server.status = Server.Status.ONLINE
    server.last_seen = timezone.now()
    if not server.enrolled_at:
        server.enrolled_at = timezone.now()
    if payload.get('os'):
        server.os_info = payload['os']
    server.save()


class Command(BaseCommand):
    help = 'Collect metrics from servers via SSH'

    def add_arguments(self, parser):
        parser.add_argument('--loop', type=int, default=0,
                            help='Run continuously with this interval (seconds)')
        parser.add_argument('--server', type=int, default=0,
                            help='Collect from a single server ID')

    def handle(self, **options):
        interval = options['loop']
        server_id = options['server']

        while True:
            if server_id:
                servers = Server.objects.filter(pk=server_id, ssh_host__gt='')
            else:
                servers = Server.objects.filter(ssh_host__gt='')

            if not servers.exists():
                self.stderr.write('No servers with SSH configured.')
                return

            for srv in servers:
                self.stdout.write(f'[ssh] Collecting from {srv.name} ({srv.ssh_user}@{srv.ssh_host}:{srv.ssh_port}) ...')
                payload, err = collect_from(srv)
                if payload:
                    save_metrics(srv, payload)
                    self.stdout.write(self.style.SUCCESS(
                        f'  CPU {payload["cpu_percent"]}% | '
                        f'RAM {payload["memory_percent"]}% | '
                        f'Disk {payload["disk_percent"]}%'
                    ))
                else:
                    self.stderr.write(self.style.ERROR(f'  Failed: {err}'))
                    srv.status = Server.Status.OFFLINE
                    srv.save(update_fields=['status'])

            if not interval:
                break
            time.sleep(interval)
