@echo off
title CG e-Procurement Ingestion Tool
echo =======================================================
echo   CG e-Procurement Chatbot - Document Ingestion
echo =======================================================
echo This will scan:
echo   - backend\data\vendor_manuals (for Vendor PDFs)
echo   - backend\data\govt_rules     (for Government PDFs)
echo and ingest them into the Chroma vector databases.
echo.
venv\Scripts\python.exe scripts\ingest_documents.py %*
echo.
pause
