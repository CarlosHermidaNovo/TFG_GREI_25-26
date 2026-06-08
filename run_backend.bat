@echo off
echo Iniciando Backend TFG...
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause
