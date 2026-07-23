@echo off
title CG e-Procurement - Government Re-Ingestion
echo =======================================================
echo   Government PDF Re-Ingestion (govt role only)
echo =======================================================
echo.
echo Prerequisites:
echo   1. Ollama running with bge-m3 pulled
echo   2. LLAMA_CLOUD_API_KEY set in this session
echo   3. Backend server STOPPED (Qdrant lock)
echo   4. PDFs in backend\data\govt_rules\
echo.
if "%LLAMA_CLOUD_API_KEY%"=="" (
    echo WARNING: LLAMA_CLOUD_API_KEY is not set.
    echo Hindi PDFs will fall back to local OCR only.
    echo.
)
cd /d "%~dp0"
venv\Scripts\python.exe scripts\ingest_documents.py --role govt --reindex --force %*
echo.
pause
