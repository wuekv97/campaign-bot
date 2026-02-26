# 🚀 Deployment guide — Campaign Bot

## Step 1: Connect to the server

```bash
ssh root@YOUR_SERVER_IP
# Use your SSH key or password
```

## Step 2: Prepare the server

```bash
# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx ufw rsync

# Create app directory
mkdir -p /opt/campaign-bot
```

## Step 3: Upload files (from your machine)

In a **new terminal** on your machine:

```bash
cd /path/to/campaign-bot

# Upload project to server
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' --exclude '.git' \
  ./ root@YOUR_SERVER_IP:/opt/campaign-bot/
```

## Step 4: Set up the bot on the server

Back in the SSH session:

```bash
cd /opt/campaign-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
mkdir -p data logs
```

## Step 5: Configure .env

```bash
nano /opt/campaign-bot/.env
```

Set BOT_TOKEN, ADMIN_IDS, DATABASE_URL, WEB_ADMIN_USERNAME, WEB_ADMIN_PASSWORD, etc.

## Step 6: Create systemd services

```bash
# Bot service
cat > /etc/systemd/system/campaign-bot.service << 'EOF'
[Unit]
Description=Campaign Bot (Telegram)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/campaign-bot
Environment=PATH=/opt/campaign-bot/venv/bin
ExecStart=/opt/campaign-bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Web admin panel service
cat > /etc/systemd/system/campaign-bot-web.service << 'EOF'
[Unit]
Description=Campaign Bot Web Admin Panel
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/campaign-bot
Environment=PATH=/opt/campaign-bot/venv/bin
ExecStart=/opt/campaign-bot/venv/bin/python run_web.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

## Step 7: Start services

```bash
systemctl daemon-reload
systemctl enable campaign-bot campaign-bot-web
systemctl start campaign-bot campaign-bot-web

# Check status
systemctl status campaign-bot
systemctl status campaign-bot-web
```

## Step 8: Configure Nginx

```bash
cat > /etc/nginx/sites-available/campaign-bot << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF

ln -sf /etc/nginx/sites-available/campaign-bot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
```

## Step 9: Firewall

```bash
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable
```

## ✅ Done

Admin panel: `http://YOUR_SERVER_IP`

---

## 🌐 Using a domain

1. Point the domain to your server IP (A record).

2. Update Nginx config:
```bash
nano /etc/nginx/sites-available/campaign-bot
# Set server_name yourdomain.xyz;
```

3. Get SSL certificate:
```bash
certbot --nginx -d yourdomain.xyz
```

4. Restart Nginx:
```bash
systemctl restart nginx
```

Panel will be available at: `https://yourdomain.xyz`
