@echo off
echo Starting Code Testing Agent with Web Interface...
echo.
echo Web dashboard will be available at: http://localhost:5000
echo.
python agent.py --config configs/marketing-agent.yaml --web
