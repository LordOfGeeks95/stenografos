@echo off
rem Greek Speech To Text (By Nikitas Katsaitis) - installer.
rem Everything is installed ONLY inside this folder (app\). Delete the folder to uninstall.
title Greek Speech To Text - Install
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0app\install.ps1" %*
