@echo off
REM Script to compile JOSS paper locally using Docker
REM This replicates what the GitHub Actions workflow does
REM
REM Prerequisites: Docker Desktop must be installed and running
REM Download from: https://www.docker.com/products/docker-desktop

echo ============================================
echo   JOSS Paper Local Compilation Script
echo ============================================
echo.

REM Check if Docker is available
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not in PATH
    echo.
    echo Please install Docker Desktop from:
    echo https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

echo Docker found. Compiling paper...
echo.

REM Navigate to the paper directory
cd /d "%~dp0"

REM Run the OpenJournals Docker container
REM This uses the same Docker image as the GitHub Actions workflow
docker run --rm ^
    -v "%cd%:/data" ^
    openjournals/inara ^
    -o pdf,crossref ^
    /data/paper.md

if errorlevel 1 (
    echo.
    echo ============================================
    echo   Compilation FAILED - see errors above
    echo ============================================
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Compilation SUCCESSFUL!
echo ============================================
echo.
echo Output: paper.pdf
echo Location: %cd%
echo.
pause
