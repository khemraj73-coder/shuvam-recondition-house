SHUVAM Recondition House v9 - Setup & Install
============================================

FILES:
  1) "SHUVAM Recondition House v9 Setup.exe"  (single-file portable installer, ~40 MB)
     -> Double-click to run. Extracts and launches the app. No install needed.

  2) "install.bat"  (proper install to Program Files)
     -> Run as Administrator. Copies the app to:
        C:\Program Files\SHUVAM Recondition House v9\
     -> Creates Desktop + Start Menu shortcuts.
     -> Requires the dist_v9 folder next to install.bat.

  3) dist_v9\  (folder build)
     -> Run "SHUVAM Recondition House v9.exe" directly (no install).

REQUIREMENTS:
  - Windows 10/11 (64-bit)
  - Python NOT required (bundled in EXE)
  - Internet optional (cloud sync + auto-update need internet)

FIRST RUN:
  - Default login: username "admin", password "admin123"
  - You will be forced to change the password on first login.
  - Data stored in: %SHUVAM_HOME% or next to the EXE.
  - Cloud (Turso) auto-syncs when online.

AUTO-UPDATE:
  - App checks GitHub version.json on startup.
  - New version -> popup -> download -> backup -> replace -> restart.

CLOUD SYNC:
  - Silent auto-sync on login + retry every 90s when offline.
  - Settings page: Sync now / Restore / enable-disable.

UNINSTALL:
  - Delete "C:\Program Files\SHUVAM Recondition House v9" folder
  - Remove shortcuts from Desktop / Start Menu.
