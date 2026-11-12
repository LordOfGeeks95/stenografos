@echo off
rem Stenografos (By Nikitas Katsaitis) - installer.
rem Everything is installed ONLY inside this folder (app\). Delete the folder to uninstall.
title Stenografos - Install
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0app\install.ps1" %*
