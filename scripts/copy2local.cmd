@echo off
set DEST=\\192.168.1.8\addons

CALL :copy_addon hass-addon-control-group
CALL :copy_lib hass-addon-control-group

rem CALL :copy2 hass-addon-control-group
CALL :copy_addon hass-addon-qsusb64
CALL :copy_lib hass-addon-qsusb64

rem CALL :copy2 hass-addon-esp,\\192.168.1.8\addons\hass-addon-esp\

EXIT /B %ERRORLEVEL%

:copy_lib
CALL :print "Copy ha_addon package for '%~1'"
for %%f in (pyproject.toml,MANIFEST.in,LICENSE,README.md,uv.lock) do xcopy /Y "%%f" %DEST%\%~1\ha_addon\
xcopy /Y /S /EXCLUDE:scripts\copyexclude.txt src %DEST%\%~1\ha_addon\src\
EXIT /B 0

:copy_addon
CALL :print "Copy '%~1' to '%DEST%\%~1'"
set /a num=%RANDOM% * 100 / 32768 + 1
CALL :print "Set version to v%num% for local testing"
xcopy /Y /S /EXCLUDE:scripts\copyexclude.txt %~1 %DEST%\%~1

set cf=%~1\config.localtest.yaml
cp %~1\config.yaml %cf%
sed -i 's/image:/# image:/' %cf%
sed -i 's/name: /name: A_LOCAL /' %cf%
sed -i "s/version: \"/version: \"v%num%_/" %cf%
xcopy /Y %cf% %DEST%\%~1\config.yaml*
EXIT /B 0

:print
echo.
echo %~1
echo ===========================================================
echo.
EXIT /B 0
