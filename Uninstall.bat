@echo off
rem Stenografos (By Nikitas Katsaitis) - uninstaller.
rem Deletes this whole folder and the desktop shortcut. Asks first, and can keep your transcripts.
title Stenografos - Uninstall
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0app\uninstall.ps1" %*
