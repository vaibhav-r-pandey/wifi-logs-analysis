# Gunicorn configuration for HICP deployment
bind = "0.0.0.0:5000"
workers = 1
worker_class = "sync"
timeout = 300  # 5 minutes
keepalive = 2
max_requests = 100
max_requests_jitter = 10
preload_app = False