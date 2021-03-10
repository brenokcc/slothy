#!/bin/bash
set -e
if [ ! -d ".virtualenv" ]; then
 python -m pip install virtualenv
 python -m virtualenv .virtualenv
 source .virtualenv/bin/activate
 python -m pip install -r requirements.txt
else
 source .virtualenv/bin/activate
fi

mkdir -p logs
python manage.py sync
echo "Starting gunicorn..."
exec gunicorn financeiro.wsgi:application -w 1 -b 127.0.0.1:${1:-8000} --timeout=600 --user=${2:-$(whoami)} --log-level=_debug --log-file=logs/gunicorn.log 2>>logs/gunicorn.log
