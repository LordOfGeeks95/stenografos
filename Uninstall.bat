@echo off
rem Greek Speech To Text (By Nikitas Katsaitis) - uninstaller.
rem Deletes this whole folder and the desktop shortcut. Asks first, and can keep your transcripts.
title Greek Speech To Text - Uninstall
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0app\uninstall.ps1" %*
