@echo off
setlocal
del /s/q *.bak >nul 2>&1

set logfile=install-python-packages.log
del /q %logfile% >nul 2>&1

REM ___________________________________________________________________________
REM Create virtural environment
if not exist ".\.venv" (
echo Creating virtual environment ...
python -m venv ".\.venv"
)
echo Activating virtual environment ...
call .venv\Scripts\activate
python.exe --version

REM ___________________________________________________________________________
REM List Python packages
set cmd=python -m pip list --no-color
echo. | tee.exe -a %logfile%
echo %cmd% | tee.exe -a %logfile%
%cmd% | tee.exe -a %logfile%

REM ___________________________________________________________________________
REM List outdated Python packages
set cmd=python -m pip list --no-color --outdated
echo. | tee.exe -a %logfile%
echo %cmd% | tee.exe -a %logfile%
%cmd% | tee.exe -a %logfile%

REM ___________________________________________________________________________
REM Install/update install Python packages
REM Install/update "pip" first, then "setup", "wheel"
REM Pip "list" output from default Python 3.8.1 install is: "pip", "setuptools"
REM https://packaging.python.org/tutorials/installing-packages/#ensure-pip-setuptools-and-wheel-are-up-to-date
set cmd=python -m pip install --no-color --compile --upgrade pip
echo. | tee.exe -a %logfile%
echo %cmd% | tee.exe -a %logfile%
%cmd% | tee.exe -a %logfile%
set cmd=python -m pip install --no-color --compile --upgrade setuptools wheel
echo. | tee.exe -a %logfile%
echo %cmd% | tee.exe -a %logfile%
%cmd% | tee.exe -a %logfile%

REM ___________________________________________________________________________
REM Install/Update packeages from requirements
if not exist "requirements.txt" (
echo. | tee.exe -a %logfile%
echo "requirements.txt" not found | tee.exe -a %logfile%
goto :eof
)

REM Update using requirements.txt file
set cmd=python -m pip install --no-color --compile --upgrade-strategy eager --upgrade --requirement requirements.txt
echo. | tee.exe -a %logfile%
echo %cmd% | tee.exe -a %logfile%
%cmd% | tee.exe -a %logfile%

REM List Python updated packages
set cmd=python -m pip list --no-color
echo. | tee.exe -a %logfile%
echo %cmd% | tee.exe -a %logfile%
%cmd% | tee.exe -a %logfile%
