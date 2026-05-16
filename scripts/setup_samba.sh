#!/bin/bash
# Samba shared folder setup
set -euo pipefail

echo "=== Samba Setup ==="

sudo apt install -y samba

# Create folder structure
sudo mkdir -p /srv/lookbook/{inbox,outbox,processed,brand,bgm}
sudo chown -R lookbook:lookbook /srv/lookbook

# Backup existing config
sudo cp /etc/samba/smb.conf /etc/samba/smb.conf.bak

# Add share config if not already present
if ! grep -q "\[lookbook\]" /etc/samba/smb.conf; then
    cat << 'EOF' | sudo tee -a /etc/samba/smb.conf

[lookbook]
   path = /srv/lookbook
   browseable = yes
   writable = yes
   valid users = lookbook
   create mask = 0664
   directory mask = 0775
   force user = lookbook
   force group = lookbook
EOF
fi

# Set Samba password
echo "Set Samba password for user 'lookbook':"
sudo smbpasswd -a lookbook

sudo systemctl restart smbd

echo ""
echo "=== Samba Ready ==="
echo "Windows mount: \\\\<tailscale-ip>\\lookbook"
echo "PowerShell: New-PSDrive -Name Z -PSProvider FileSystem -Root '\\\\<ip>\\lookbook' -Persist"
