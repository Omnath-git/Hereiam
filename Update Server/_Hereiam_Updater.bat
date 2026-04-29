@echo off
echo Connecting to Oracle Server and Updating Code...
ssh -i "D:\Hereiam.in V5\Update Server\private ssh-key-2026-04-27.key" ubuntu@161.118.191.181 < commands.txt
echo Update Completed Successfully!
pause