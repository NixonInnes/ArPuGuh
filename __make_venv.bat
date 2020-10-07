for %%I in (.) do set CurrDirName=%%~nxI
set VENV=%USERPROFILE%\.venvs\%CurrDirName%
python -m venv %VENV%
CALL %VENV%\Scripts\activate
python -m pip install -U pip
