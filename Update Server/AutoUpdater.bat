@echo off
echo Deploying Clean Update...
ssh -i "D:\Hereiam.in V5\Update Server\private ssh-key-2026-04-27.key" ubuntu@161.118.191.181 "cd /home/ubuntu/hereiam_portal/hereiam && git fetch --all && git reset --hard origin/master && sudo pkill -9 gunicorn || true && /home/ubuntu/hereiam_portal/venv/bin/python3 -m gunicorn --workers 3 --bind 127.0.0.1:8000 'app:create_app()' --daemon && sudo systemctl restart nginx"
pause