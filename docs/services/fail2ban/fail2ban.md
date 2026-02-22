# Fail2Ban Service Documentation

Fail2Ban is an intrusion prevention software framework that protects computer servers from brute-force attacks.

## Current Configuration

On Ubuntu 24.04, Fail2Ban is installed as a system service.

### Main Configuration Files

- `/etc/fail2ban/jail.conf`: Default configuration (do not edit directly).
- `/etc/fail2ban/jail.local`: Custom configuration overrides (preferred).
- `/etc/fail2ban/filter.d/`: Directory containing filter definitions.

## Basic SSH Protection

By default, SSH protection is enabled but should be verified in `/etc/fail2ban/jail.local`:

```ini
[sshd]
enabled = true
port    = ssh
logpath = %(sshd_log)s
backend = systemd
maxretry = 5
bantime  = 1h
```

## Commands

### Check Status
To see which jails are active:
```bash
sudo fail2ban-client status
```

### Check Specific Jail
To see banned IPs for SSH:
```bash
sudo fail2ban-client status sshd
```

### Unban an IP
```bash
sudo fail2ban-client set sshd unbanip <IP_ADDRESS>
```

## How-To: Custom Jail

If you add a new service like a custom web app, you can create a jail for it in `jail.local`:

1. Define a filter in `/etc/fail2ban/filter.d/my-app.conf`.
2. Add the jail definition to `/etc/fail2ban/jail.local`.
3. Restart Fail2Ban:
   ```bash
   sudo systemctl restart fail2ban
   ```
