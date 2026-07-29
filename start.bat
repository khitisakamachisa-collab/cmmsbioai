@echo off
REM === CMD 1: Backend ===
start cmd /k "cd /d D:\cmmsbioai\backend && python -m venv venv && call venv\Scripts\activate && uvicorn main:app --reload"

REM === CMD 2: Frontend ===
start cmd /k "cd /d D:\cmmsbioai\frontend && npm run dev"

REM === CMD 3: Carpeta principal ===
start cmd /k "cd /d D:\cmmsbioai"
