@echo off
setlocal
del /s/q *.bak >nul 2>&1

REM ___________________________________________________________________________
REM Output Python version outside virtual environment
python.exe --version

REM ___________________________________________________________________________
REM Create virtural environment
if not exist ".\.venv" (
echo Creating virtual environment ...
python -m venv ".\.venv"
)
echo Activating virtual environment ...
call .venv\Scripts\activate

REM Output Python version inside virtual environment
python.exe --version

REM ___________________________________________________________________________
REM List Python packages
set cmd=python -m pip list --no-color
echo.
echo %cmd%
%cmd%

REM ___________________________________________________________________________
REM List outdated Python packages
set cmd=python -m pip list --no-color --outdated
echo.
echo %cmd%
%cmd%

REM ___________________________________________________________________________
REM Install/update install Python packages
REM Install/update "pip" first, then "setup", "wheel"
REM Pip "list" output from default Python 3.8.1 install is: "pip", "setuptools"
REM https://packaging.python.org/tutorials/installing-packages/#ensure-pip-setuptools-and-wheel-are-up-to-date
set cmd=python -m pip install --no-color --compile --upgrade pip
echo.
echo %cmd%
%cmd%
set cmd=python -m pip install --no-color --compile --upgrade setuptools wheel
echo.
echo %cmd%
%cmd%

REM ___________________________________________________________________________
REM Install/Update packeages from requirements
if not exist "requirements.txt" (
echo.
echo "requirements.txt" not found
goto :eof
)

REM Update using requirements.txt file
set cmd=python -m pip install --no-color --compile --upgrade-strategy eager --upgrade --requirement requirements.txt
echo.
echo %cmd%
%cmd%

REM Output Python version inside virtual environment
echo.
python.exe --version

REM List Python (updated) packages
set cmd=python -m pip list --no-color
echo.
echo %cmd%
%cmd%
