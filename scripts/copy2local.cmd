@echo off
CALL :copy2 qsusb64-addon,\\192.168.1.8\addons\hass-addon-qsusb64\

EXIT /B %ERRORLEVEL%

:copy2
echo # Modify Config for local testing
set cf=%~1\config.localtest.yaml
cp %~1\config.yaml %cf%
sed -i 's/image:/# image:/' %cf%
sed -i 's/name: /name: LOCAL /' %cf%
xcopy /Y %cf% %~2\config.yaml

echo # Copy '%~1' to '%~2'
xcopy /Y /S /EXCLUDE:scripts\copyexclude.txt %~1 %~2

echo # Copy qsusb package
for %%f in (pyproject.toml,MANIFEST.in,LICENSE,README.md,uv.lock) do xcopy /Y "%%f" %~2\qsusb64\
xcopy /Y /S /EXCLUDE:scripts\copyexclude.txt src %~2\qsusb64\src\

EXIT /B 0
