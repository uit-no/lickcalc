@echo off
REM Script to compile paper for bioRxiv using Pandoc
REM Creates a clean PDF without JOSS branding
REM
REM Prerequisites: Pandoc and a LaTeX distribution (e.g., MiKTeX or TeX Live)
REM Pandoc: https://pandoc.org/installing.html
REM MiKTeX: https://miktex.org/download

echo ============================================
echo   bioRxiv Paper Compilation Script
echo ============================================
echo.

REM Check if Pandoc is available
pandoc --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Pandoc is not installed or not in PATH
    echo.
    echo Please install Pandoc from:
    echo https://pandoc.org/installing.html
    echo.
    pause
    exit /b 1
)

echo Pandoc found. Compiling paper...
echo.

REM Navigate to the paper directory
cd /d "%~dp0"

REM Compile using Pandoc with a clean academic template
pandoc paper.md ^
    --metadata-file=paper_biorxiv.yaml ^
    --bibliography=paper.bib ^
    --citeproc ^
    --pdf-engine=xelatex ^
    --variable geometry:margin=1in ^
    --variable fontsize=11pt ^
    --variable documentclass=article ^
    --variable papersize=letter ^
    --number-sections ^
    -o paper_biorxiv.pdf

if errorlevel 1 (
    echo.
    echo ============================================
    echo   Compilation FAILED - see errors above
    echo ============================================
    echo.
    echo Common issues:
    echo   - LaTeX not installed (install MiKTeX or TeX Live)
    echo   - Missing LaTeX packages (MiKTeX will prompt to install)
    echo   - Citation formatting errors in paper.md
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Compilation SUCCESSFUL!
echo ============================================
echo.
echo Output: paper_biorxiv.pdf
echo Location: %cd%
echo.
pause
