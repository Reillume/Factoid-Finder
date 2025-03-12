@echo off

type Setup\Logo.txt
timeout /t 5 >nul

REM This next line is very important. It specifies where the Python 3.12 installation is located. Change this if the default path is not correct.
set "python_location= C:\Program Files\Python312\python.exe"
echo %python_location%

REM Check Python version
%python_location% --version

REM Check if virtual environment directory exists
if not exist FFenv (
    REM Create virtual environment
    echo Creating virtual environment...
    @echo on
    %python_location% -m venv FFenv
    @echo off
    echo Virtual environment created.
)

REM Activate virtual environment
echo Activating virtual environment...
@echo on
call FFenv\Scripts\activate
@echo off
echo Virtual environment activated.

REM Install dependencies
echo Installing required packages...
@echo on
FFenv\Scripts\python.exe -m pip install -r Setup\requirements.txt
@echo off
echo Required packages are installed.

echo Setup complete. Virtual environment is activated.
@echo on
FFenv\Scripts\python.exe Scripts\Interface.py

pause