# SHUVAM RECONDITION HOUSE — PRO EDITION v5.0.1

Production-grade desktop management app for a recondition (buy / repair / sell) motorcycle shop.
Built with Python + Tkinter, single-file architecture, offline-first SQLite, optional encrypted Turso cloud sync.

## Highlights
- 5 premium themes (Midnight, Ocean, Emerald, Sunset, Pearl) with smooth transitions
- Bike buy / stock / sell, accessories, number-plate services, repairs
- Billing with banned-word guard (customer-safe bills), overpayment validation
- Ledger + cashbook + audit hash-chain
- Nepal payment methods: Cash, eSewa, Khalti, ConnectIPS, Bank Transfer, Fonepay, IME Pay, Cheque, Other
- Windows Hello / fingerprint / PIN login with password fallback
- DPAPI-encrypted Turso (libSQL) cloud sync, local SQLite fallback
- Auto-update from GitHub Releases
- Soft-delete with audit, owner/staff role gating

## Run
```powershell
python shuvam_glass_pro.py
```
First run creates the owner account.

## Test
```powershell
python shuvam_glass_pro.py --test
```
Current suite: 12 passed, 0 failed.

## Build Windows executable
```powershell
pip install pyinstaller
pyinstaller --noconfirm --windowed --icon assets\shuvam_icon.ico --add-data "assets;assets" shuvam_glass_pro.py
```

## Cloud sync (Turso)
Configure in Settings → Turso Cloud Sync. Auth token is protected with Windows DPAPI.
Database URL: `libsql://shuvam-recondition-house-khemraj73-coder.aws-ap-south-1.turso.io`

## Auto-update
Version is checked against `version.json` on GitHub. Settings → Auto Update.

## License
MIT © Khemraj Bhattarai — KRB STUDIO
```