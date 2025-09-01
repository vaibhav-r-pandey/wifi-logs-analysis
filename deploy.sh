#!/bin/bash

# HICP Deployment Script for IFX MSD GenAI Tool

echo "Starting deployment to HICP server..."

# Create necessary directories
mkdir -p uploads logs

# Copy config template if config.ini doesn't exist
if [ ! -f "config.ini" ]; then
    echo "Creating config.ini from template..."
    cp config_template.ini config.ini
    echo "IMPORTANT: Edit config.ini with your GPT4IFX credentials before running!"
    echo "Required fields: username, password"
fi

# Validate config file
if [ -f "config.ini" ]; then
    if ! grep -q "\[gpt4ifxapi\]" config.ini; then
        echo "ERROR: config.ini missing [gpt4ifxapi] section"
        exit 1
    fi
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Set permissions
chmod +x wsgi.py
chmod 755 uploads logs

# Create systemd service file (optional)
cat > ifx-msd-genai.service << EOF
[Unit]
Description=IFX MSD GenAI Tool
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/your/app
Environment=PATH=/usr/bin:/usr/local/bin
ExecStart=/usr/local/bin/gunicorn --bind 0.0.0.0:5000 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "Deployment files prepared!"
echo "Next steps:"
echo "1. Edit config.ini with your GPT4IFX credentials"
echo "2. Install gunicorn: pip3 install gunicorn"
echo "3. Run: gunicorn --bind 0.0.0.0:5000 wsgi:app"