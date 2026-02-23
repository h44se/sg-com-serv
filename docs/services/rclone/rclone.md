# Rclone Cloud Backup Service

Rclone is a command-line program to manage files on cloud storage. It is used here to synchronize local backups (created by `tools.py`) to external providers like Google Drive, AWS S3, or Dropbox.

## Overview

Unlike other services, Rclone runs directly on the host system (not in Docker) to allow easier access to the host's filesystem and cron scheduling.

## Installation

Rclone must be installed on the host system.

```bash
sudo -v && curl https://rclone.org/install.sh | sudo bash
```

## Configuration

### 1. Initialize Rclone

Run the following command on the host to configure your cloud remote:

```bash
rclone config
```

Follow the interactive prompts to add a new remote (e.g., named `gdrive`).

### 2. Move Config to Project

By default, rclone stores its config in `~/.config/rclone/rclone.conf`. To use it with our project-specific tools, either copy it or symlink it:

```bash
mkdir -p services/rclone
cp ~/.config/rclone/rclone.conf services/rclone/rclone.conf
```

### 3. Optional: Encryption

It is highly recommended to use rclone's **Crypt** remote type to encrypt your backups before they reach the cloud provider.

1. Run `rclone config`.
2. Create a new remote of type `crypt`.
3. Point it to your cloud remote (e.g., `gdrive:backups`).
4. Name it something like `backup-crypt`.

## Usage

### Manual Upload

```bash
uv run tools.py backup-upload --remote backup-crypt:backups
```

### Manual Download

```bash
uv run tools.py backup-download --remote backup-crypt:backups
```

## Automated Backups (Cron)

You can automate the process of creating a local backup and uploading it to the cloud daily:

```bash
uv run tools.py setup-backup-cron
```

This adds a entry to your crontab that runs at 02:00 AM every night.

## Retention Policy

The `backup-upload` command automatically deletes files from the remote that are older than **14 days**.
