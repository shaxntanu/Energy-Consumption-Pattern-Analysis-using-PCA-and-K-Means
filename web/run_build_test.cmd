@echo off
cd /d "%~dp0"
call npm install
echo NPM_INSTALL_DONE
call npm run build
echo NPM_BUILD_DONE