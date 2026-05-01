@echo off
set "KEY_PATH=D:\Hereiam.in V5\Update Server\private ssh-key-2026-04-27.key"
set "SERVER=ubuntu@161.118.191.181"

echo ------------------------------------------
echo Step 1: Connecting and Cleaning Server...
echo ------------------------------------------

:: सभी कमांड्स को एक ही लाइन में बिना किसी विशेष युनिकोड के भेजा गया है
ssh -i "%KEY_PATH%" %SERVER% "cd /home/ubuntu/hereiam_portal/hereiam && git fetch --all && git reset --hard origin/master && find . -name '__pycache__' -delete && sudo pkill -9 gunicorn || true && sudo lsof -t -i:8000 | xargs -r sudo kill -9 && sleep 2 && /home/ubuntu/hereiam_portal/venv/bin/python3 -m gunicorn --workers 3 --bind 127.0.0.1:8000 'app:create_app()' --daemon && sudo systemctl restart nginx"

echo ------------------------------------------
echo Step 2: Deployment Finished!
echo ------------------------------------------
pause