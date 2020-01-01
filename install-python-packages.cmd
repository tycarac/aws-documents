@echo off
setlocal
del /s/q *.bak >nul 2>&1

set logfile=install-python-packages.log
del /q %logfile%

echo on

if not exist [.\.env] (
python -m venv ".\.env"
)
call .env\Scripts\activate.bat

set cmd=python -m pip list --outdated
echo. | tee.exe -a %logfile%
echo %cmd% | tee.exe -a %logfile%
%cmd% | tee.exe -a %logfile%

set cmd=python -m pip install --upgrade pip setuptools wheel virtualenv certifi
echo. | tee.exe -a %logfile%
echo %cmd% | tee.exe -a %logfile%
%cmd% | tee.exe -a %logfile%

if not exist "requirements.txt" goto :eof

set cmd=pip.exe install -U --upgrade-strategy eager -r requirements.txt --compile
echo cmd %cmd%
echo. | tee.exe -a %logfile%
echo %cmd% | tee.exe -a %logfile%
%cmd% | tee.exe -a %logfile%

