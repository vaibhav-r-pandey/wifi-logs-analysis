#!/usr/bin/env python3
"""
WSGI entry point for HICP deployment
"""
import sys
import os

# Add the application directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import app

if __name__ == "__main__":
    app.run()