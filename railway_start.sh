#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f "manage.py" ]]; then
  echo "ERROR: manage.py not found. Set Railway Root Directory to the folder containing manage.py."
  exit 1
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec gunicorn STYRIVA.wsgi:application --bind "0.0.0.0:${PORT:-8000}"
