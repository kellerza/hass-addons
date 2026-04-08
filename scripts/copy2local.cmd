@echo off
set DEST=\\192.168.1.8\addons

set /a VER=%RANDOM% * 100 / 32768 + 1
CALL :print "Set version to v%VER% for local testing"
sh build_prep.sh hass-addon-control-group %VER%

CALL :copy_addon hass-addon-control-group

@REM rem CALL :copy2 hass-addon-control-group
@REM CALL :copy_addon hass-addon-qsusb64
@REM CALL :copy_lib hass-addon-qsusb64

rem CALL :copy2 hass-addon-esp,\\192.168.1.8\addons\hass-addon-esp\

EXIT /B %ERRORLEVEL%

:copy_addon
CALL :print "Copy '%~1' to '%DEST%\%~1'"
xcopy /Y /S /EXCLUDE:scripts\copyexclude.txt %~1 %DEST%\%~1

set cf=%~1\config.localtest.yaml
cp %~1\config.yaml %cf%
sed -i 's/image:/# image:/' %cf%
sed -i 's/name: /name: A_LOCAL /' %cf%
sed -i "s/version: \"/version: \"v%VER%_/" %cf%
xcopy /Y %cf% %DEST%\%~1\config.yaml*
EXIT /B 0

:print
echo.
echo %~1
echo ===========================================================
echo.
EXIT /B 0
