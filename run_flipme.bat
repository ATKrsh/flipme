@echo off
title Launching FlipMe...
powershell -Command "Unblock-File -Path '%~dp0dist\FlipMe_v3.exe' -ErrorAction SilentlyContinue"
powershell -Command "Unblock-File -Path '%~dp0dist\FlipMe_v2.exe' -ErrorAction SilentlyContinue"
start "" "%~dp0dist\FlipMe_v3.exe"
