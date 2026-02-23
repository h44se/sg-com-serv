import os
from typing import List
import typer
from .runner import CommandRunner

class SystemManager:
    """Manages base system setup and security hardening."""
    
    def update(self):
        typer.echo("Updating system packages...")
        CommandRunner.run("sudo apt update && sudo apt upgrade -y")
        CommandRunner.run("sudo apt install apache2-utils -y")

    def harden_ssh(self):
        typer.echo("Hardening SSH configuration...")
        configs = [
            ("PermitRootLogin", "no"),
            ("PasswordAuthentication", "no"),
            ("PermitEmptyPasswords", "no"),
            ("PubkeyAuthentication", "yes"),
            ("MaxAuthTries", "3"),
            ("X11Forwarding", "no")
        ]
        for key, value in configs:
            CommandRunner.run(f"sudo sed -i 's/^#*{key}.*/{key} {value}/' /etc/ssh/sshd_config")
        
        CommandRunner.run("sudo sshd -t && sudo systemctl restart ssh")

    def setup_firewall(self, ports: List[str]):
        typer.echo("Setting up UFW firewall...")
        CommandRunner.run("sudo ufw default deny incoming")
        CommandRunner.run("sudo ufw default allow outgoing")
        CommandRunner.run("sudo ufw allow ssh")
        for port in ports:
            CommandRunner.run(f"sudo ufw allow {port}")
        CommandRunner.run("sudo ufw --force enable")

    def setup_auto_updates(self):
        typer.echo("Configuring unattended-upgrades...")
        CommandRunner.run("sudo apt install unattended-upgrades -y")
        CommandRunner.run("echo 'unattended-upgrades unattended-upgrades/enable_auto_updates boolean true' | sudo debconf-set-selections")
        CommandRunner.run("sudo dpkg-reconfigure -f noninteractive unattended-upgrades")

    def setup_fail2ban(self):
        typer.echo("Setting up Fail2Ban...")
        CommandRunner.run("sudo apt install fail2ban -y")
        self._setup_teamspeak_fail2ban()
        CommandRunner.run("sudo systemctl enable fail2ban")
        CommandRunner.run("sudo systemctl restart fail2ban")

    def _setup_teamspeak_fail2ban(self):
        typer.echo("Configuring TeamSpeak 3 Jail for Fail2Ban...")
        filter_content = "[Definition]\\nfailregex = query from .*:<HOST>:[0-9]+ .* failed .*\\nignoreregex ="
        CommandRunner.run(f"echo -e '{filter_content}' | sudo tee /etc/fail2ban/filter.d/teamspeak.conf > /dev/null")
        
        base_path = os.path.expanduser("~/server-config")
        log_dir = os.path.join(base_path, "services/teamspeak/data/logs")
        CommandRunner.run(f"mkdir -p {log_dir}")
        
        log_path = os.path.join(log_dir, "ts3server_*.log")
        jail_content = f"\\n[teamspeak]\\nenabled  = true\\nport     = 10011\\nfilter   = teamspeak\\nlogpath  = {log_path}\\nmaxretry = 5\\nbantime  = 1h"
        
        CommandRunner.run(f"if ! sudo grep -q '\\[teamspeak\\]' /etc/fail2ban/jail.local 2>/dev/null; then echo -e '{jail_content}' | sudo tee -a /etc/fail2ban/jail.local > /dev/null; fi")

    def setup_docker(self):
        typer.echo("Installing Docker...")
        CommandRunner.run("curl -fsSL https://get.docker.com -o get-docker.sh")
        CommandRunner.run("sudo sh get-docker.sh")
        user = os.getenv("USER") or os.getlogin()
        CommandRunner.run(f"sudo usermod -aG docker {user}")
        typer.echo(f"Added {user} to docker group. You may need to log out and back in.")
