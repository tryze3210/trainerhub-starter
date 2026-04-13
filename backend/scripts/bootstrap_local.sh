#!/usr/bin/env bash
set -euo pipefail

python manage.py migrate
python manage.py seed_platform_settings
python manage.py seed_categories
python manage.py create_demo_users

echo "Bootstrap complete."
