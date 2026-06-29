@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ================================================================
echo   REDROB HACKATHON PROJECT
echo ================================================================

echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python is not available on PATH.
  echo Install Python 3.10+ and re-run this file.
  exit /b 1
)

echo [2/6] Installing/updating required packages...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo ERROR: Failed to install requirements.
  exit /b 1
)

echo [3/6] Ensuring output folder exists...
if not exist output mkdir output

echo [4/6] Running full ranker on candidates.jsonl...
if exist data\candidates.jsonl (
  set "CANDIDATE_FILE=data\candidates.jsonl"
) else if exist candidates.jsonl (
  set "CANDIDATE_FILE=candidates.jsonl"
) else (
  echo ERROR: Could not find candidates.jsonl in project root or data\ folder.
  exit /b 1
)

python src\ranker.py --candidates "%CANDIDATE_FILE%" --out .\output\submission.xlsx
if errorlevel 1 (
  echo ERROR: Ranking failed.
  exit /b 1
)

echo [5/6] Validating generated submission...
python validate_submission.py .\output\submission.xlsx
if errorlevel 1 (
  echo ERROR: Submission validation failed.
  exit /b 1
)


echo [6/6] Cleaning non-essential local artifacts...
if exist src\__pycache__ rmdir /s /q src\__pycache__
if exist __pycache__ rmdir /s /q __pycache__
if exist .pytest_cache rmdir /s /q .pytest_cache
if exist .mypy_cache rmdir /s /q .mypy_cache
if exist .ruff_cache rmdir /s /q .ruff_cache
if exist .streamlit rmdir /s /q .streamlit
if exist clean-dist rmdir /s /q clean-dist
if exist _archive rmdir /s /q _archive

del /q *.log 2>nul
del /q *.tmp 2>nul
del /q *.bak 2>nul

echo.
echo ================================================================
echo SUCCESS: Project run completed.
echo Final XLSX: %cd%\output\submission.xlsx
echo ================================================================
endlocal
exit /b 0
