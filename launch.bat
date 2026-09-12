@echo off
REM Default to no /generate (skips torch/transformers/CUDA packages).
REM Set USE_GENERATE=true to enable the /generate command.
if "%USE_GENERATE%"=="" set "USE_GENERATE=false"

python -m venv venv

set "GEN=0"
if /i "%USE_GENERATE%"=="true" set "GEN=1"
if /i "%USE_GENERATE%"=="1" set "GEN=1"
if /i "%USE_GENERATE%"=="t" set "GEN=1"

if "%GEN%"=="1" (
    venv\Scripts\pip.exe install -r requirements.txt
    venv\Scripts\python.exe core/setup_generate.py
) else (
    venv\Scripts\pip.exe install -r requirements_no_generate.txt
)

venv\Scripts\python.exe aiya.py
