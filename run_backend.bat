@echo off
title CG e-Procurement Chatbot Backend
echo =======================================================
echo   Starting CG e-Procurement Chatbot Backend API Server
echo =======================================================
cd backend
..\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
pause
