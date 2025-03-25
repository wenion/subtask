from os import environ


bind = "unix:/tmp/gunicorn-subtask.sock"
worker_class = "h.subtask.Worker"
graceful_timeout = 0
workers = environ["SUBTASK_NUM_WORKERS"]
worker_connections = 8192
