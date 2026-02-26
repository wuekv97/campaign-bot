#!/bin/bash
# ===========================================
# Campaign Bot — deployment script
# ===========================================

set -e

echo "🚀 Starting deployment..."

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install dependencies
echo "📦 Installing Python and dependencies..."
apt install -y python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx ufw

# Create app directory
echo "📁 Creating app directory..."
mkdir -p /opt/campaign-bot
cd /opt/campaign-bot

echo "📂 Project directory: /opt/campaign-bot"

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install requirements
echo "📦 Installing Python requirements..."
pip install --upgrade pip
pip install -r requirements.txt

# Create systemd service for bot
echo "⚙️ Creating systemd service for bot..."
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

# Create systemd service for web panel
echo "⚙️ Creating systemd service for web panel..."
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

# Create nginx config
echo "🌐 Creating Nginx configuration..."
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
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF

ln -sf /etc/nginx/sites-available/campaign-bot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Firewall
echo "🔥 Configuring firewall..."
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable

systemctl daemon-reload

echo ""
echo "✅ Server prepared!"
echo ""
echo "📋 Next steps:"
echo "1. Upload project files to /opt/campaign-bot/"
echo "2. Edit /opt/campaign-bot/.env with your settings"
echo "3. Run: systemctl enable --now campaign-bot campaign-bot-web"
echo "4. Run: systemctl restart nginx"
echo ""
echo "With a domain:"
echo "5. Update /etc/nginx/sites-available/campaign-bot with your domain"
echo "6. Run: certbot --nginx -d yourdomain.xyz"
