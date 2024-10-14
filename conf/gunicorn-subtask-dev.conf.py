from os import environ


bind = "localhost:5003"
worker_class = "h.subtask.Worker"
graceful_timeout = 0
workers = 2
worker_connections = 8


if 'H_GUNICORN_CERTFILE' in environ:
    certfile = environ['H_GUNICORN_CERTFILE']

if 'H_GUNICORN_KEYFILE' in environ:
    keyfile = environ['H_GUNICORN_KEYFILE']
