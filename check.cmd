@echo off
rem Windows equivalent of `make check` (no make on this host).
setlocal
set PY=.venv\Scripts\python.exe
%PY% -m pytest || exit /b 1
%PY% .claude\skills\hwde\scripts\check_env.py --quiet >NUL || exit /b 1
echo check: OK
