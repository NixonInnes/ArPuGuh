for %%I in (.) do set CurrDirName=%%~nxI
set VENV=%USERPROFILE%\.venvs\%CurrDirName%
CMD /k %VENV%\Scripts\activate
