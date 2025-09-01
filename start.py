#!/usr/bin/env python3
"""
Startup script for HICP deployment
Validates configuration before starting the app
"""
import os
import sys
from configparser import ConfigParser

def validate_config():
    """Validate configuration before starting"""
    print("=== IFX MSD GenAI Tool Startup ===")
    
    # Check for config file
    config_files = ['config.ini', 'config_template.ini']
    config_found = False
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"Found config file: {config_file}")
            config_found = True
            
            # Validate config structure
            config = ConfigParser()
            config.read(config_file)
            
            if config.has_section('gpt4ifxapi'):
                username = config.get('gpt4ifxapi', 'username', fallback='')
                password = config.get('gpt4ifxapi', 'password', fallback='')
                
                if username and password:
                    print(f"✓ Config validated for user: {username[:3]}***")
                    break
                else:
                    print(f"⚠ Config file {config_file} missing credentials")
            else:
                print(f"⚠ Config file {config_file} missing [gpt4ifxapi] section")
    
    # Check environment variables as fallback
    env_username = os.getenv('GPT4IFX_USERNAME')
    env_password = os.getenv('GPT4IFX_PASSWORD')
    
    if env_username and env_password:
        print(f"✓ Environment variables found for user: {env_username[:3]}***")
        config_found = True
    
    if not config_found:
        print("❌ ERROR: No valid configuration found!")
        print("Please either:")
        print("1. Create config.ini with your GPT4IFX credentials")
        print("2. Set environment variables: GPT4IFX_USERNAME, GPT4IFX_PASSWORD")
        sys.exit(1)
    
    print("✓ Configuration validated successfully")
    print("Starting application...")

if __name__ == "__main__":
    validate_config()
    
    # Import and run the app
    from app import app
    app.run(host='0.0.0.0', port=5000, debug=False)