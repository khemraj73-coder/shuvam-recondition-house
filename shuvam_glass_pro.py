"""
SHUVAM RECONDITION HOUSE — PRO EDITION v4.0
File: shuvam_glass_pro.py
Design & Developed by Khemraj Bhattarai | KRB STUDIO | khemraj73@gmail.com

Production-grade recondition-house management:
 • 5 premium themes (Midnight / Ocean / Emerald / Sunset / Pearl)
 • Animated aurora-glass interface, smooth page transitions
 • Bike buy/sell/stock, accessories, plate, repair, billing, ledger, cashbook
 • Payment methods: Cash, eSewa, Khalti, ConnectIPS, Bank Transfer, Fonepay, IME Pay, Cheque
 • Security: PBKDF2, Windows Hello / fingerprint login, DPAPI secret vault, audit hash-chain
 • Cloud: optional Turso (libSQL) encrypted-token sync
 • Auto-update from GitHub

Run:  python shuvam_glass_pro.py
Test: python shuvam_glass_pro.py --test
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import math
import os
import secrets
import sqlite3
import struct
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import zlib
from contextlib import contextmanager, closing
from dataclasses import dataclass
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Optional, Iterator, Callable

if os.name == "nt":
    import ctypes
    from ctypes import wintypes

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog, font as tkfont
    HAS_TK = True
except ImportError:
    tk = ttk = messagebox = filedialog = tkfont = None
    HAS_TK = False

# ================= CONSTANTS =================
DEV_NAME = "Khemraj Bhattarai"
STUDIO_NAME = "KRB STUDIO"
DEV_EMAIL = "khemraj73@gmail.com"
BRAND_LINE = f"Design & Developed by {DEV_NAME}  •  {STUDIO_NAME}  •  {DEV_EMAIL}"
APP_NAME = "SHUVAM RECONDITION HOUSE"
APP_VERSION = "5.0.0"
APP_BUILD = "2026.11"
APP_TITLE = APP_NAME
APP_VERSION_LABEL = f"{APP_NAME}   •   v{APP_VERSION}"
CURRENCY = "Rs."
KAR_VALID_DAYS = 365
KAR_ALERT_DAYS = 30
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 30
PASSWORD_MIN_LEN = 8
PHONE_MIN_LEN = 10
PBKDF2_ROUNDS = 600_000
BILL_RETRY = 5
LIST_LIMIT = 200
DEFAULT_SHOP_NAME = "SHUVAM RECONDITION HOUSE"
DEFAULT_ADDRESS = "Hatti Chowk, Tulsipur, Dang"
DEFAULT_THEME = "midnight"
DEFAULT_LANG = "ne"
CURRENT_LANG = DEFAULT_LANG
LANGS = {
  "ne": {
    "app": "SHUVAM RECONDITION HOUSE",
    "login": "लगइन", "username": "प्रयोगकर्ता नाम", "password": "पासवर्ड",
    "dashboard": "ड्यासबोर्ड", "bike": "बाइक", "saman": "सामान", "hisab": "हिसाब",
    "bills": "बिल", "settings": "सेटिङ",
    "theme": "थिम", "language": "भाषा", "save": "सेभ", "cancel": "रद्द",
    "welcome": "स्वागत छ", "today_sales": "आजको बिक्री", "month_sales": "यो महिना",
    "pending_due": "बाँकी उधारो", "stock_bikes": "स्टक बाइक",
    "buy": "खरिद", "sell": "बिक्री", "stock": "स्टक",
    "customer": "ग्राहक", "phone": "फोन", "price": "मूल्य", "paid": "पैसा पाइयो",
    "payment": "भुक्तानी", "due": "बाँकी", "total": "जम्मा",
  },
  "en": {
    "app": "SHUVAM RECONDITION HOUSE",
    "login": "Login", "username": "Username", "password": "Password",
    "dashboard": "Dashboard", "bike": "Bike", "saman": "Goods", "hisab": "Accounts",
    "bills": "Bills", "settings": "Settings",
    "theme": "Theme", "language": "Language", "save": "Save", "cancel": "Cancel",
    "welcome": "Welcome", "today_sales": "Today's Sales", "month_sales": "This Month",
    "pending_due": "Pending Due", "stock_bikes": "Stock Bikes",
    "buy": "Buy", "sell": "Sell", "stock": "Stock",
    "customer": "Customer", "phone": "Phone", "price": "Price", "paid": "Paid",
    "payment": "Payment", "due": "Due", "total": "Total",
  },
}
def t(key):
    return LANGS.get(CURRENT_LANG, LANGS["ne"]).get(key, key)
def set_lang(lang):
    global CURRENT_LANG
    if lang in LANGS: CURRENT_LANG = lang
GENESIS = "GENESIS"
PAYMENT_METHODS = ("Cash", "eSewa", "Khalti", "Connect IPS", "Bank Transfer",
                   "Fonepay", "IME Pay", "Cheque", "Other")
GITHUB_REPO = "https://github.com/khemraj73-coder/shuvam-recondition-house"
GITHUB_RAW = "https://raw.githubusercontent.com/khemraj73-coder/shuvam-recondition-house/main"
UPDATE_VERSION_URL = f"{GITHUB_RAW}/version.json"
TURSO_URL_DEFAULT = "libsql://shuvam-recondition-house-khemraj73-coder.aws-ap-south-1.turso.io"
TURSO_URL_BUILTIN = "libsql://shuvam-recondition-house-khemraj73-coder.aws-ap-south-1.turso.io"
TURSO_TOKEN_BUILTIN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3OTUyMTM3NzgsImlkIjoiMDFhMWZhYTItYzUwMS03ZjNlLWEwMjctZmY0YWQ4YTBlOWVmIiwia2lkIjoiTUFONElfcXVPMVBzLXZMNm9SY3BnVjRIMlV4cG4tWm9mNHJ4NnNvN2lpYyIsInJpZCI6ImE3Mjc1MWUyLTQ3NTEtNGZmNC1iMTFiLTI4Zjg4MGUwMzhmMSJ9.OuI33n3uQL_1XrydzTK-yqpYcR3TJpbG81t0jyGhClQfh5RpfNZP_5ThxY8_e4-j3mOjjBvV2U9hZUEUJgNWAA"
TURSO_VAULT_TABLE = "shuvam_vault"
CLOUD_FILE = None  # BASE पछि तोकिन्छ
UPDATES_FILE = None
BANNED_BILL_WORDS = ("profit", "faida", "lagat", "cost", "internal",
                     "dekhidaina", "dekhiyeko", "नाफा", "फाइदा", "लागत", "भित्री")

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("shuvam")

# ================= COLOR UTILITIES (liquid glass) =================
def hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

def rgb_hex(c: tuple[int, int, int]) -> str:
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(v))) for v in c)

def blend(a: str, b: str, t: float) -> str:
    """a र b लाई t अनुसार मिश्रण गर्छ (0=a, 1=b) — glass translucency को लागि।"""
    ar, ag, ab = hex_rgb(a); br, bg, bb = hex_rgb(b)
    return rgb_hex((ar + (br-ar)*t, ag + (bg-ag)*t, ab + (bb-ab)*t))

def lighten(c: str, t: float) -> str:
    return blend(c, "#FFFFFF", t)

def darken(c: str, t: float) -> str:
    return blend(c, "#000000", t)

# ================= CONFIG / DATA =================
BASE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
CONFIG_FILE = BASE / "shuvam_config.json"          # FIX 7: script-relative
LANG_FILE = BASE / "shuvam_lang.json"
ASSET_DIR = BASE / "assets"
CLOUD_FILE = BASE / "shuvam_cloud.json"
UPDATES_FILE = BASE / "shuvam_updates.json"
ICON_PNG = ASSET_DIR / "shuvam_icon.png"
ICON_ICO = ASSET_DIR / "shuvam_icon.ico"

def get_default_data_dir() -> Path:
    p = Path(r"C:\ShuvamReconditionHouse\Data")
    try:
        p.mkdir(parents=True, exist_ok=True)
        probe = p / ".probe"; probe.write_text("ok", encoding="utf-8"); probe.unlink()
        return p
    except Exception as exc:
        log.warning("C: writable छैन, local Data प्रयोग: %s", exc)
        local = BASE / "Data"; local.mkdir(parents=True, exist_ok=True)
        return local

def load_data_dir() -> Path:
    if CONFIG_FILE.exists():
        try:
            saved = json.loads(CONFIG_FILE.read_text(encoding="utf-8")).get("data_dir")
            if saved and Path(saved).exists():
                return Path(saved)
        except Exception as exc:
            log.warning("config पढ्न सकिएन: %s", exc)
    d = get_default_data_dir()
    try:
        CONFIG_FILE.write_text(json.dumps({"data_dir": str(d)}, ensure_ascii=False),
                               encoding="utf-8")
    except Exception as exc:
        log.warning("config लेख्न सकिएन: %s", exc)
    return d

def load_lang() -> str:
    global CURRENT_LANG
    try:
        if LANG_FILE.exists():
            CURRENT_LANG = json.loads(LANG_FILE.read_text(encoding="utf-8")).get("lang", DEFAULT_LANG)
    except Exception: pass
    if CURRENT_LANG not in LANGS: CURRENT_LANG = DEFAULT_LANG
    return CURRENT_LANG
def save_lang(lang: str) -> None:
    global CURRENT_LANG
    if lang in LANGS:
        CURRENT_LANG = lang
        try: LANG_FILE.write_text(json.dumps({"lang": lang}), encoding="utf-8")
        except Exception: pass
DATA_DIR = load_data_dir()
load_lang()
DB_FILE = DATA_DIR / "shuvam.db"
BILL_FOLDER = DATA_DIR / "Bills"
BILL_FOLDER.mkdir(parents=True, exist_ok=True)

# ================= DATABASE =================
class Database:
    """हरेक अपरेशनमा नयाँ connection; read/transaction context; SQLite backup API।"""

    def __init__(self, db_file: Path):
        self.db_file = Path(db_file)
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(str(self.db_file), timeout=30.0, isolation_level=None)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA busy_timeout=30000")
        return con

    @contextmanager
    def read(self) -> Iterator[sqlite3.Connection]:
        con = self.connect()
        try:
            yield con
        finally:
            con.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        con = self.connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            yield con
            con.execute("COMMIT")
        except Exception:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            con.close()

    def _init_schema(self) -> None:
        with self.read() as con:
            con.executescript("""
            CREATE TABLE IF NOT EXISTS settings(id INTEGER PRIMARY KEY, shop_name TEXT, address TEXT,
                mobile TEXT, pan TEXT, owner TEXT, bill_note TEXT, theme TEXT DEFAULT 'midnight',
                hello_login INTEGER DEFAULT 0, hello_user TEXT DEFAULT '', auto_update INTEGER DEFAULT 1,
                auto_cloud INTEGER DEFAULT 1);
            CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, password_hash TEXT NOT NULL,
                salt TEXT NOT NULL, role TEXT DEFAULT 'owner', created_at TEXT);
            CREATE TABLE IF NOT EXISTS bikes(id INTEGER PRIMARY KEY AUTOINCREMENT, brand TEXT, model TEXT,
                color TEXT, year TEXT, engine_no TEXT, chassis_no TEXT, bike_no TEXT UNIQUE,
                seller_name TEXT, seller_phone TEXT, buy_price REAL DEFAULT 0, repair_cost REAL DEFAULT 0,
                naam_sari REAL DEFAULT 0, kar_cost REAL DEFAULT 0, kar_paid INTEGER DEFAULT 0,
                total_cost REAL DEFAULT 0, sell_price REAL DEFAULT 0, status TEXT DEFAULT 'Stock Ma',
                buy_date TEXT, sell_date TEXT, buyer_name TEXT, buyer_phone TEXT, buyer_address TEXT,
                profit REAL DEFAULT 0, is_deleted INTEGER DEFAULT 0, updated_at TEXT);
            CREATE TABLE IF NOT EXISTS bills(id INTEGER PRIMARY KEY AUTOINCREMENT, bill_no TEXT UNIQUE NOT NULL,
                bill_type TEXT, ref_id INTEGER, customer TEXT, phone TEXT, detail TEXT, total REAL DEFAULT 0,
                paid REAL DEFAULT 0, due REAL DEFAULT 0, payment TEXT, created_at TEXT,
                is_deleted INTEGER DEFAULT 0, updated_at TEXT);
            CREATE TABLE IF NOT EXISTS bill_counter(id INTEGER PRIMARY KEY CHECK(id=1), next_no INTEGER NOT NULL DEFAULT 1);
            CREATE TABLE IF NOT EXISTS accessories(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE,
                category TEXT, stock INTEGER DEFAULT 0, buy_price REAL DEFAULT 0, sell_price REAL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS accessory_sales(id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, qty INTEGER,
                price REAL, total REAL, customer TEXT, phone TEXT, payment TEXT, date TEXT,
                bill_no TEXT, is_deleted INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS plates(id INTEGER PRIMARY KEY AUTOINCREMENT, customer TEXT, phone TEXT,
                bike_no TEXT, plate_type TEXT, charge REAL DEFAULT 0, paid REAL DEFAULT 0, due REAL DEFAULT 0,
                status TEXT, date TEXT, bill_no TEXT, is_deleted INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS repairs(id INTEGER PRIMARY KEY AUTOINCREMENT, customer TEXT, phone TEXT,
                bike_no TEXT, bike_model TEXT, problem TEXT, parts_cost REAL DEFAULT 0, labour REAL DEFAULT 0,
                total REAL DEFAULT 0, paid REAL DEFAULT 0, due REAL DEFAULT 0, status TEXT, date TEXT,
                bill_no TEXT, is_deleted INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS ledger(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT,
                type TEXT, description TEXT, udharo REAL DEFAULT 0, tiryo REAL DEFAULT 0,
                balance REAL DEFAULT 0, date TEXT, bill_no TEXT);
            CREATE TABLE IF NOT EXISTS cashbook(id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT,
                description TEXT, income REAL DEFAULT 0, expense REAL DEFAULT 0, category TEXT);
            CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY AUTOINCREMENT, actor TEXT,
                action TEXT, detail TEXT, prev_hash TEXT, hash TEXT, created_at TEXT);
            CREATE INDEX IF NOT EXISTS idx_bikes_no ON bikes(bike_no);
            CREATE INDEX IF NOT EXISTS idx_bikes_status ON bikes(status);
            CREATE INDEX IF NOT EXISTS idx_ledger_name ON ledger(name);
            CREATE INDEX IF NOT EXISTS idx_cashbook_date ON cashbook(date);
            CREATE INDEX IF NOT EXISTS idx_bills_no ON bills(bill_no);
            CREATE INDEX IF NOT EXISTS idx_bills_type ON bills(bill_type);
            """)
            # पुरानो schema लाई नयाँ columns मा migrate
            for table, cols in (("bikes", {"is_deleted": "INTEGER DEFAULT 0", "updated_at": "TEXT"}),
                                ("bills", {"is_deleted": "INTEGER DEFAULT 0", "updated_at": "TEXT",
                                           "ref_id": "INTEGER"}),
                                ("accessory_sales", {"is_deleted": "INTEGER DEFAULT 0", "bill_no": "TEXT"}),
                                ("plates", {"is_deleted": "INTEGER DEFAULT 0", "bill_no": "TEXT"}),
                                ("repairs", {"is_deleted": "INTEGER DEFAULT 0", "bill_no": "TEXT"}),
                                ("ledger", {"bill_no": "TEXT"})):
                have = {r[1] for r in con.execute(f"PRAGMA table_info({table})").fetchall()}
                for c, typ in cols.items():
                    if c not in have:
                        con.execute(f"ALTER TABLE {table} ADD COLUMN {c} {typ}")
            for col, typ in (("theme", "TEXT DEFAULT 'midnight'"),
                             ("hello_login", "INTEGER DEFAULT 0"),
                             ("hello_user", "TEXT DEFAULT ''"),
                             ("auto_update", "INTEGER DEFAULT 1"),
                             ("auto_cloud", "INTEGER DEFAULT 1")):
                try:
                    con.execute(f"ALTER TABLE settings ADD COLUMN {col} {typ}")
                except sqlite3.OperationalError:
                    pass
            con.execute("INSERT OR IGNORE INTO bill_counter(id,next_no) VALUES(1,1)")
            con.execute("INSERT OR IGNORE INTO settings(id,shop_name,address,mobile,pan,owner,bill_note,theme) "
                        "VALUES(1,?,?,?,?,?,?,?)",
                        (DEFAULT_SHOP_NAME, DEFAULT_ADDRESS, "", "", "Shuvam",
                         "7 din bhitra kunai samasya bhaye samparka garnuhola. Dhanyabad!", DEFAULT_THEME))
            con.execute("UPDATE settings SET theme='midnight' WHERE theme IS NULL OR theme='dark'")
            con.execute("UPDATE settings SET theme='pearl' WHERE theme='light'")
            con.execute("UPDATE settings SET theme='midnight' WHERE theme NOT IN "
                        "('midnight','ocean','emerald','sunset','pearl')")
            con.execute("UPDATE settings SET auto_cloud=1 WHERE auto_cloud IS NULL")
            con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_acc_name ON accessories(name)")
            seeds = [("Helmet - Full Face", "Helmet", 10, 1200, 1800),
                     ("Helmet - Half", "Helmet", 10, 700, 1100),
                     ("Bike Cover", "Accessories", 10, 400, 650),
                     ("Mobile Holder", "Accessories", 10, 300, 550),
                     ("Engine Oil", "Accessories", 15, 650, 850),
                     ("Mirror Set", "Accessories", 10, 250, 450)]
            for n, c, s, b, sp in seeds:
                con.execute("INSERT OR IGNORE INTO accessories(name,category,stock,buy_price,sell_price) "
                            "VALUES(?,?,?,?,?)", (n, c, s, b, sp))

    def backup(self, dest: Path) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with self.read() as src, closing(sqlite3.connect(str(dest))) as dst:
            src.backup(dst)
        log.info("Backup सम्पन्न: %s", dest)
        return dest

DB = Database(DB_FILE)

# ================= WINDOWS SECURITY / CLOUD / UPDATE / ICON =================
# सबै optional service — fail भए पनि app चल्नुपर्छ।
ASSET_DIR.mkdir(parents=True, exist_ok=True)

if os.name == "nt":
    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    _crypt32 = ctypes.windll.crypt32
    _kernel32 = ctypes.windll.kernel32
    _crypt32.CryptProtectData.argtypes = [
        ctypes.POINTER(DATA_BLOB), wintypes.LPCWSTR, ctypes.POINTER(DATA_BLOB),
        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(DATA_BLOB)]
    _crypt32.CryptProtectData.restype = wintypes.BOOL
    _crypt32.CryptUnprotectData.argtypes = [
        ctypes.POINTER(DATA_BLOB), ctypes.POINTER(wintypes.LPWSTR), ctypes.POINTER(DATA_BLOB),
        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(DATA_BLOB)]
    _crypt32.CryptUnprotectData.restype = wintypes.BOOL
    _kernel32.LocalFree.argtypes = [ctypes.c_void_p]

def _blob(data: bytes):
    buf = ctypes.create_string_buffer(data, len(data))
    return DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))), buf

def dpapi_available() -> bool:
    return os.name == "nt"

def dpapi_protect_bytes(data: bytes, entropy: bytes = b"SHUVAM.RH.v4") -> str:
    """Windows DPAPI — यही Windows user मात्र decrypt गर्न सक्छ।"""
    if os.name != "nt":
        raise RuntimeError("DPAPI केवल Windows मा उपलब्ध छ")
    in_blob, _keep1 = _blob(data)
    ent_blob, _keep2 = _blob(entropy)
    out = DATA_BLOB()
    ok = _crypt32.CryptProtectData(ctypes.byref(in_blob), "SHUVAM Secure Vault",
                                   ctypes.byref(ent_blob), None, None, 0x1, ctypes.byref(out))
    if not ok:
        raise OSError(f"DPAPI encrypt असफल (code {ctypes.GetLastError()})")
    try:
        raw = ctypes.string_at(out.pbData, out.cbData)
    finally:
        _kernel32.LocalFree(ctypes.cast(out.pbData, ctypes.c_void_p))
    return base64.b64encode(raw).decode("ascii")

def dpapi_unprotect_bytes(token: str, entropy: bytes = b"SHUVAM.RH.v4") -> bytes:
    if os.name != "nt":
        raise RuntimeError("DPAPI केवल Windows मा उपलब्ध छ")
    raw = base64.b64decode(token.encode("ascii"))
    in_blob, _keep1 = _blob(raw)
    ent_blob, _keep2 = _blob(entropy)
    out = DATA_BLOB(); desc = wintypes.LPWSTR()
    ok = _crypt32.CryptUnprotectData(ctypes.byref(in_blob), ctypes.byref(desc),
                                     ctypes.byref(ent_blob), None, None, 0x1, ctypes.byref(out))
    if not ok:
        raise OSError(f"DPAPI decrypt असफल (code {ctypes.GetLastError()})")
    try:
        return ctypes.string_at(out.pbData, out.cbData)
    finally:
        _kernel32.LocalFree(ctypes.cast(out.pbData, ctypes.c_void_p))

def dpapi_protect_text(text: str) -> str:
    return dpapi_protect_bytes(text.encode("utf-8"))

def dpapi_unprotect_text(token: str) -> str:
    return dpapi_unprotect_bytes(token).decode("utf-8")

# ---------- Windows Hello / fingerprint ----------
HELLO_PS = r'''
$ErrorActionPreference = 'Stop'
try {
    Add-Type -AssemblyName System.Runtime.WindowsRuntime | Out-Null
    [Windows.Security.Credentials.UI.UserConsentVerifier,Windows.Security.Credentials.UI,ContentType=WindowsRuntime] | Out-Null
    $asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
        $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
        $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
    })[0]
    $op = [Windows.Security.Credentials.UI.UserConsentVerifier]::RequestVerificationAsync($env:SHUVAM_HELLO_MSG)
    $task = $asTask.MakeGenericMethod([Windows.Security.Credentials.UI.UserConsentVerificationResult]).Invoke($null, @($op))
    if (-not $task.Wait(65000)) { Write-Output 'RESULT:Timeout'; exit 2 }
    Write-Output ('RESULT:' + $task.Result)
} catch {
    Write-Output ('ERROR:' + $_.Exception.Message)
    exit 1
}
'''

def windows_hello_verify(message: str = "Login to SHUVAM Recondition House") -> tuple[bool, str]:
    """Windows Hello / fingerprint / PIN को system dialog देखाउँछ।"""
    if os.name != "nt":
        return False, "Windows Hello केवल Windows मा उपलब्ध छ"
    path = None
    try:
        fd, path = tempfile.mkstemp(prefix="shuvam_hello_", suffix=".ps1")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(HELLO_PS)
        env = dict(os.environ, SHUVAM_HELLO_MSG=message[:120])
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        p = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-STA",
                            "-ExecutionPolicy", "Bypass", "-File", path],
                           capture_output=True, text=True, timeout=75,
                           creationflags=flags, env=env)
        out = (p.stdout or "").strip()
        log.info("Windows Hello output: %s", out[-300:])
        if "RESULT:Verified" in out:
            return True, "Verified"
        if "RESULT:Canceled" in out:
            return False, "रद्द गरियो"
        if "RESULT:Timeout" in out:
            return False, "समय सकियो"
        if "ERROR:" in out:
            return False, out.split("ERROR:", 1)[1].strip()[:160]
        tail = out.splitlines()[-1] if out else (p.stderr or "").strip()[:160]
        return False, f"Windows Hello उपलब्ध/स्वीकृत भएन — {tail or 'No device'}"
    except Exception as exc:
        log.warning("Windows Hello failed: %s", exc)
        return False, str(exc)[:160]
    finally:
        try:
            if path: os.unlink(path)
        except OSError:
            pass

# ---------- Turso (libSQL) encrypted sync ----------
class TursoError(RuntimeError):
    pass

class TursoClient:
    """Turso HTTP pipeline — थप package चाहिँदैन।"""
    def __init__(self, url: str, token: str, timeout: int = 25):
        u = (url or "").strip().rstrip("/")
        if u.startswith("libsql://"):
            u = "https://" + u[len("libsql://"):]
        if not u.startswith(("https://", "http://")):
            raise TursoError("Turso URL गलत छ (libsql:// वा https://)")
        if not u.endswith("/v2/pipeline"):
            u += "/v2/pipeline"
        self.url = u
        self.token = (token or "").strip()
        if not self.token:
            raise TursoError("Turso auth token खाली छ")
        self.timeout = timeout

    @staticmethod
    def _arg(v):
        if v is None:
            return {"type": "null"}
        if isinstance(v, bool):
            return {"type": "integer", "value": "1" if v else "0"}
        if isinstance(v, int):
            return {"type": "integer", "value": str(v)}
        if isinstance(v, float):
            return {"type": "float", "value": repr(v)}
        if isinstance(v, (bytes, bytearray)):
            return {"type": "blob", "value": base64.b64encode(bytes(v)).decode("ascii")}
        return {"type": "text", "value": str(v)}

    def _post(self, payload: dict) -> dict:
        req = urllib.request.Request(
            self.url, data=json.dumps(payload).encode("utf-8"), method="POST",
            headers={"Authorization": f"Bearer {self.token}",
                     "Content-Type": "application/json",
                     "User-Agent": f"SHUVAM/{APP_VERSION}"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            raise TursoError(f"Turso HTTP {exc.code}: {detail}") from exc
        except Exception as exc:
            raise TursoError(f"Turso connection असफल: {exc}") from exc
        try:
            return json.loads(body)
        except Exception as exc:
            raise TursoError("Turso ले अमान्य JSON फर्कायो") from exc

    def execute(self, sql: str, args=()) -> dict:
        payload = {"requests": [{"type": "execute", "stmt": {
            "sql": sql, "args": [self._arg(a) for a in args]}}]}
        data = self._post(payload)
        results = data.get("results") or []
        if not results:
            raise TursoError("Turso बाट कुनै परिणाम आएन")
        item = results[0]
        if item.get("type") == "error":
            raise TursoError(item.get("error", {}).get("message", "Turso query error"))
        return (item.get("response") or {}).get("result") or {}

    def query(self, sql: str, args=()) -> list[list]:
        res = self.execute(sql, args)
        rows = []
        for row in res.get("rows", []) or []:
            rows.append([(cell or {}).get("value") for cell in row])
        return rows

    def ping(self) -> None:
        self.query("SELECT 1")

SNAPSHOT_TABLES = ("settings", "users", "bikes", "bills", "bill_counter", "accessories",
                   "accessory_sales", "plates", "repairs", "ledger", "cashbook", "audit_log")

def export_snapshot(db: Optional[Database] = None) -> dict:
    db = db or DB
    tables = {}
    with db.read() as con:
        for t in SNAPSHOT_TABLES:
            try:
                tables[t] = [dict(r) for r in con.execute(f"SELECT * FROM {t}").fetchall()]
            except sqlite3.Error:
                tables[t] = []
    return {"format": 1, "app": APP_NAME, "version": APP_VERSION,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "tables": tables}

def restore_snapshot(data: dict, db: Optional[Database] = None, actor: str = "cloud") -> int:
    db = db or DB
    if not isinstance(data, dict) or data.get("format") != 1 or not isinstance(data.get("tables"), dict):
        raise ValueError("Snapshot format मान्य छैन")
    tables = data["tables"]
    backup = DATA_DIR / "Backups" / f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    db.backup(backup)
    count = 0
    with db.transaction() as con:
        for t in SNAPSHOT_TABLES:
            rows = tables.get(t)
            if not isinstance(rows, list):
                continue
            con.execute(f"DELETE FROM {t}")
            for row in rows:
                if not isinstance(row, dict) or not row:
                    continue
                cols = [c for c in row.keys()
                        if all(ch.isalnum() or ch == "_" for ch in str(c))]
                if not cols:
                    continue
                con.execute(f"INSERT INTO {t}({','.join(cols)}) VALUES({','.join('?'*len(cols))})",
                            tuple(row[c] for c in cols))
                count += 1
        _audit(con, actor, "RESTORE_CLOUD", f"{count} rows | {backup.name}")
    log.info("Cloud restore सम्पन्न: %s rows", count)
    return count

def load_cloud_config() -> dict:
    cfg = {"url": TURSO_URL_BUILTIN, "token": TURSO_TOKEN_BUILTIN,
           "enabled": True, "last_sync": ""}
    try:
        if CLOUD_FILE.exists():
            raw = json.loads(CLOUD_FILE.read_text(encoding="utf-8"))
            cfg.update({k: raw.get(k, cfg[k]) for k in ("url", "enabled", "last_sync")})
            if raw.get("token_enc"):
                try:
                    cfg["token"] = dpapi_unprotect_text(raw["token_enc"])
                except Exception as exc:
                    log.warning("Turso token decrypt असफल: %s", exc)
            # if no token_enc, keep built-in
            if not cfg.get("token"):
                cfg["token"] = TURSO_TOKEN_BUILTIN
            if not cfg.get("url"):
                cfg["url"] = TURSO_URL_BUILTIN
    except Exception as exc:
        log.warning("Cloud config पढ्न सकिएन: %s", exc)
    # built-in fallback
    if not cfg.get("token"): cfg["token"] = TURSO_TOKEN_BUILTIN
    if not cfg.get("url"): cfg["url"] = TURSO_URL_BUILTIN
    return cfg

def save_cloud_config(cfg: dict) -> None:
    out = {"url": cfg.get("url") or TURSO_URL_DEFAULT,
           "enabled": bool(cfg.get("enabled")),
           "last_sync": cfg.get("last_sync") or ""}
    token = (cfg.get("token") or "").strip()
    if token:
        out["token_enc"] = dpapi_protect_text(token)
    elif CLOUD_FILE.exists():
        try:
            old = json.loads(CLOUD_FILE.read_text(encoding="utf-8"))
            if old.get("token_enc"):
                out["token_enc"] = old["token_enc"]
        except Exception:
            pass
    CLOUD_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

def cloud_push(cfg: Optional[dict] = None) -> str:
    cfg = cfg or load_cloud_config()
    client = TursoClient(cfg.get("url") or TURSO_URL_DEFAULT, cfg.get("token") or "")
    client.ping()
    plain = json.dumps(export_snapshot(), ensure_ascii=False).encode("utf-8")
    checksum = hashlib.sha256(plain).hexdigest()
    encrypted = dpapi_protect_bytes(plain)
    now = datetime.now().isoformat(timespec="seconds")
    client.execute(
        f"CREATE TABLE IF NOT EXISTS {TURSO_VAULT_TABLE}("
        "id INTEGER PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT, "
        "app_version TEXT, checksum TEXT)")
    client.execute(
        f"INSERT INTO {TURSO_VAULT_TABLE}(id,payload,updated_at,app_version,checksum) "
        "VALUES(1,?,?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload, "
        "updated_at=excluded.updated_at, app_version=excluded.app_version, checksum=excluded.checksum",
        (encrypted, now, APP_VERSION, checksum))
    cfg["last_sync"] = now
    save_cloud_config(cfg)
    return now

def cloud_pull(cfg: Optional[dict] = None, db: Optional[Database] = None) -> tuple[int, str]:
    cfg = cfg or load_cloud_config()
    client = TursoClient(cfg.get("url") or TURSO_URL_DEFAULT, cfg.get("token") or "")
    rows = client.query(f"SELECT payload,checksum,updated_at FROM {TURSO_VAULT_TABLE} WHERE id=1")
    if not rows:
        raise TursoError("Turso मा कुनै backup भेटिएन")
    payload, checksum, updated = rows[0][0], rows[0][1], rows[0][2]
    if not payload:
        raise TursoError("Turso payload खाली छ")
    plain = dpapi_unprotect_bytes(payload)
    if checksum and hashlib.sha256(plain).hexdigest() != checksum:
        raise TursoError("Snapshot checksum मिलेन — data बिग्रिएको हुनसक्छ")
    data = json.loads(plain.decode("utf-8"))
    count = restore_snapshot(data, db=db, actor="cloud-restore")
    return count, str(updated or "")

# ---------- Auto update ----------
def version_tuple(v: str) -> tuple:
    out = []
    for part in str(v or "0").split("."):
        try: out.append(int("".join(ch for ch in part if ch.isdigit()) or 0))
        except ValueError: out.append(0)
    return tuple((out + [0, 0, 0])[:4])

def _http_get(url: str, timeout: int = 15) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": f"SHUVAM/{APP_VERSION}",
                                              "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()

def check_for_update(timeout: int = 12) -> Optional[dict]:
    try:
        raw = json.loads(_http_get(UPDATE_VERSION_URL, timeout=timeout).decode("utf-8"))
        remote = str(raw.get("version") or "")
        if remote and version_tuple(remote) > version_tuple(APP_VERSION):
            raw["version"] = remote
            return raw
    except Exception as exc:
        log.info("Update check असफल: %s", exc)
    return None

def install_update(info: dict) -> tuple[bool, str]:
    url = (info or {}).get("url") or f"{GITHUB_RAW}/shuvam_glass_pro.py"
    expected = ((info or {}).get("sha256") or "").strip().lower()
    try:
        data = _http_get(url, timeout=60)
        if expected and hashlib.sha256(data).hexdigest() != expected:
            return False, "Download checksum मिलेन — update रोकियो"
        if getattr(sys, "frozen", False):
            target = Path(sys.executable)
            new_file = target.with_suffix(".new.exe")
            new_file.write_bytes(data)
            bat = Path(tempfile.gettempdir()) / f"shuvam_update_{int(time.time())}.bat"
            bat.write_text(
                "@echo off\r\n"
                "timeout /t 2 /nobreak >nul\r\n"
                f'copy /y "{new_file}" "{target}" >nul\r\n'
                f'start "" "{target}"\r\n'
                'del "%~f0"\r\n', encoding="ascii", errors="ignore")
            subprocess.Popen(["cmd", "/c", str(bat)], creationflags=0x08000008, close_fds=True)
            return True, "Update download भयो — app restart हुँदैछ"
        target = Path(__file__).resolve()
        backup = target.with_suffix(f".bak-{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
        backup.write_bytes(target.read_bytes())
        tmp = target.with_suffix(".update.tmp")
        tmp.write_bytes(data)
        os.replace(tmp, target)
        return True, f"v{info.get('version', '?')} install भयो — app पुनः सुरु गर्नुस्"
    except Exception as exc:
        log.warning("Update install असफल: %s", exc)
        return False, f"Update असफल: {exc}"

# ---------- Programmatic SHUVAM icon (stdlib मात्र, PIL चाहिँदैन) ----------
def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return (struct.pack(">I", len(data)) + kind + data +
            struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))

def _png_bytes(w: int, h: int, rgba: bytearray) -> bytes:
    raw = bytearray()
    stride = w * 4
    for y in range(h):
        raw.append(0)
        raw.extend(rgba[y * stride:(y + 1) * stride])
    return (b"\x89PNG\r\n\x1a\n" +
            _png_chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) +
            _png_chunk(b"IDAT", zlib.compress(bytes(raw), 9)) +
            _png_chunk(b"IEND", b""))

def _blend_px(buf: bytearray, i: int, r: float, g: float, b: float, a: float) -> None:
    if a <= 0:
        return
    a = min(1.0, a)
    da = buf[i + 3] / 255.0
    oa = a + da * (1 - a)
    if oa <= 0:
        return
    for k, v in enumerate((r, g, b)):
        buf[i + k] = int(max(0, min(255, (v * a + buf[i + k] * da * (1 - a)) / oa)))
    buf[i + 3] = int(oa * 255)

def _stamp_circle(buf: bytearray, w: int, h: int, cx: float, cy: float, rad: float,
                  color, alpha: float = 1.0) -> None:
    x0, x1 = max(0, int(cx - rad - 1)), min(w - 1, int(cx + rad + 1))
    y0, y1 = max(0, int(cy - rad - 1)), min(h - 1, int(cy + rad + 1))
    rr = rad * rad
    for y in range(y0, y1 + 1):
        dy = y + .5 - cy
        for x in range(x0, x1 + 1):
            dx = x + .5 - cx
            if dx * dx + dy * dy <= rr:
                _blend_px(buf, (y * w + x) * 4, color[0], color[1], color[2], alpha)

def _bezier_points(p0, p1, p2, p3, n=90):
    for i in range(n + 1):
        t = i / n; u = 1 - t
        x = u*u*u*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t*t*t*p3[0]
        y = u*u*u*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t*t*t*p3[1]
        yield x, y

def _icon_rgba(size: int = 512) -> bytearray:
    w = h = size
    buf = bytearray(w * h * 4)
    dark = hex_rgb("#060814"); mid = hex_rgb("#141039"); deep = hex_rgb("#241356")
    violet = hex_rgb("#7C5CFF"); cyan = hex_rgb("#22D3EE"); pink = hex_rgb("#F472B6")
    margin = size * 0.055; radius = size * 0.225
    left = top = margin; right = bottom = size - margin
    hw, hh = (right - left) / 2, (bottom - top) / 2
    cx0, cy0 = left + hw, top + hh
    for y in range(h):
        for x in range(w):
            qx = abs((x + .5) - cx0) - (hw - radius)
            qy = abs((y + .5) - cy0) - (hh - radius)
            dist = math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - radius
            if dist > 0.7:
                continue
            cov = 1.0 if dist < -0.7 else max(0.0, 0.7 - dist) / 1.4
            t = (x / w) * 0.55 + (y / h) * 0.45
            if t < 0.5:
                c = blend(rgb_hex(dark), rgb_hex(mid), t * 2)
            else:
                c = blend(rgb_hex(mid), rgb_hex(deep), (t - .5) * 2)
            r, g, b = hex_rgb(c)
            # floating aurora glows
            for gx, gy, gr, gc, amt in ((.22, .18, .42, violet, .55),
                                         (.86, .78, .40, cyan, .30),
                                         (.80, .18, .30, pink, .20)):
                d2 = ((x/w - gx) ** 2 + (y/h - gy) ** 2) / (gr * gr)
                a = math.exp(-d2 * 2.6) * amt
                r += (gc[0] - r) * a; g += (gc[1] - g) * a; b += (gc[2] - b) * a
            # rim light
            if dist > -5.0:
                rim = (1 + dist / 5.0) * 0.55
                r += (violet[0] - r) * rim * .5 + 60 * rim
                g += (cyan[1] - g) * rim * .3 + 60 * rim
                b += (cyan[2] - b) * rim * .4 + 70 * rim
            _blend_px(buf, (y * w + x) * 4, r, g, b, cov)
    # metallic S — shadow first, then two smooth strokes
    sw = size * 0.074
    p0 = (size*.625, size*.305); p1 = (size*.535, size*.205)
    p2 = (size*.375, size*.225); p3 = (size*.360, size*.355)
    p4 = (size*.350, size*.455); p5 = (size*.500, size*.485)
    p6 = (size*.615, size*.565); p7 = (size*.625, size*.675)
    p8 = (size*.635, size*.775); p9 = (size*.455, size*.785)
    p10 = (size*.365, size*.795); p11 = (size*.300, size*.735)
    pts = list(_bezier_points(p0, p1, p2, p3)) + list(_bezier_points(p3, p4, p5, p6)) + \
          list(_bezier_points(p6, p7, p8, p9)) + list(_bezier_points(p9, p10, p11, (size*.278, size*.682)))
    for x, y in pts:
        _stamp_circle(buf, w, h, x, y + size*.012, sw*.56, (0, 0, 0), .32)
    for i, (x, y) in enumerate(pts):
        t = i / max(1, len(pts) - 1)
        col = blend("#FFFFFF", "#BFD4FF", t * .65)
        col = blend(col, "#8CF4FF", max(0, t - .75) * .55)
        rgbt = hex_rgb(col)
        _stamp_circle(buf, w, h, x, y, sw*.52, rgbt, 1.0)
    for x, y in pts[::7]:
        _stamp_circle(buf, w, h, x - sw*.16, y - sw*.18, sw*.16, (255, 255, 255), .20)
    return buf

def _resize_rgba(buf: bytearray, sw: int, sh: int, dw: int, dh: int) -> bytearray:
    out = bytearray(dw * dh * 4)
    xmap = [min(sw - 1, int(x * sw / dw)) for x in range(dw)]
    ymap = [min(sh - 1, int(y * sh / dh)) for y in range(dh)]
    for y in range(dh):
        sy = ymap[y]
        for x in range(dw):
            sx = xmap[x]
            si = (sy * sw + sx) * 4; di = (y * dw + x) * 4
            out[di:di + 4] = buf[si:si + 4]
    return out

def ensure_icon_assets(force: bool = False) -> tuple[Path, Path]:
    if ICON_PNG.exists() and ICON_ICO.exists() and not force:
        return ICON_PNG, ICON_ICO
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    master = _icon_rgba(512)
    png256 = _resize_rgba(master, 512, 512, 256, 256)
    ICON_PNG.write_bytes(_png_bytes(256, 256, png256))
    sizes = (16, 24, 32, 48, 64, 128, 256)
    blobs = []
    for s in sizes:
        img = png256 if s == 256 else _resize_rgba(png256, 256, 256, s, s)
        blobs.append((s, _png_bytes(s, s, img)))
    header = struct.pack("<HHH", 0, 1, len(blobs))
    entries, data, offset = b"", b"", 6 + 16 * len(blobs)
    for s, blob in blobs:
        entries += struct.pack("<BBBBHHII", s if s < 256 else 0, s if s < 256 else 0,
                               0, 0, 1, 32, len(blob), offset)
        data += blob; offset += len(blob)
    ICON_ICO.write_bytes(header + entries + data)
    log.info("SHUVAM icon generated: %s / %s", ICON_PNG, ICON_ICO)
    return ICON_PNG, ICON_ICO

BIKE_DATA = {"Honda":["Shine 125","Unicorn 160","Hornet 2.0","SP 125","Dio 110","Activa 125","X-Blade 160","CB200X","Livo 110","CD 110 Dream","CBR 150R"],
 "Yamaha":["FZ-S V3","FZ-S V4","MT-15 V2","R15 V4","R15M","FZ-X","Ray ZR 125","Fascino 125","Aerox 155"],
 "Bajaj":["Pulsar 150","Pulsar NS 160","Pulsar NS 200","Pulsar N160","Pulsar N250","Pulsar 220F","Dominar 250","Dominar 400","Platina 110","CT 100","Avenger 160 Street"],
 "TVS":["Apache RTR 160 4V","Apache RTR 200 4V","Apache RTR 310","Raider 125","NTorq 125","Jupiter 125","Jupiter 110","Sport 110","Radeon 110"],
 "Hero":["Splendor Plus","Splendor Xtec","Xtreme 160R","Glamour 125","Passion Pro","XPulse 200 4V","Destini 125","Pleasure Plus"],
 "Suzuki":["Gixxer 150","Gixxer SF 150","Gixxer 250","Access 125","Burgman Street 125","V-Strom SX 250","Avenis 125"],
 "KTM":["Duke 200","Duke 250","Duke 390","RC 200","RC 390","Adventure 250","Adventure 390","Duke 125"],
 "Royal Enfield":["Classic 350","Hunter 350","Meteor 350","Bullet 350","Himalayan 450","Scram 411","Super Meteor 650"],
 "CFMoto":["300NK","250SR","450MT","300SR","450SR"], "Benelli":["TNT 150","Leoncino 250","TRK 251"],
 "Vespa / Aprilia":["Vespa VXL 125","Vespa SXL 150","Aprilia SR 160","Aprilia SXR 160"],
 "Electric":["Yadea G5","NIU NQi","Pure EV EPluto","Segway E125","Atum Vader","Super Soco"],
 "Other":["Other - Manual Type Garnus"]}
COLOR_LIST = ["Black (कालो)","White (सेतो)","Red (रातो)","Blue (निलो)","Grey (खैरो)","Silver (चाँदी)","Green (हरियो)","Yellow (पहेंलो)","Orange (सुन्तला)","Maroon (मेरुन)","Matt Black (म्याट कालो)","Matt Blue (म्याट निलो)","Matt Green (म्याट हरियो)","Brown (खैरो-रातो)"]
YEAR_LIST = [str(y) for y in range(date.today().year + 1, 2009, -1)]

# ================= PURE BUSINESS LOGIC =================
def calc_total_cost(buy=0, repair=0, naam_sari=0, kar_cost=0, kar_paid=False) -> float:
    return (float(buy or 0) + float(repair or 0) + float(naam_sari or 0)
            + (float(kar_cost or 0) if kar_paid else 0))

def calc_profit(sell, total_cost) -> float:
    return float(sell or 0) - float(total_cost or 0)

def calc_due(total, paid) -> float:
    return max(0.0, float(total or 0) - float(paid or 0))

def validate_payment(total, paid, label="Paid") -> None:
    """FIX 2: clamp गर्नु अघि validation — overpayment रोक्छ।"""
    if not is_valid_amount(paid) or not is_valid_amount(total):
        raise ValueError(f"{label} र Total Number मा हाल्नुस्")
    if float(paid) > float(total):
        raise ValueError(f"{label} 0 देखि {float(total):,.0f} सम्म मात्र हुनुपर्छ")

def calc_kar_due_date(buy_date: str) -> str:
    try:
        d = datetime.strptime(buy_date, "%Y-%m-%d").date()
    except Exception:
        d = date.today()
    return (d + timedelta(days=KAR_VALID_DAYS)).isoformat()

def kar_status(buy_date: str, today: Optional[date] = None) -> Optional[tuple[str, int]]:
    """FIX 3: overdue पनि समेट्छ। Returns (status, days) or None."""
    today = today or date.today()
    try:
        due = datetime.strptime(buy_date, "%Y-%m-%d").date() + timedelta(days=KAR_VALID_DAYS)
    except Exception:
        return None
    days = (due - today).days
    if days <= KAR_ALERT_DAYS:
        return ("म्याद नाघिसकेको ⚠" if days < 0 else ("आज नै ⚠" if days == 0 else f"{days} दिन बाँकी")), days
    return None

def calc_repair_total(parts, labour) -> float:
    return float(parts or 0) + float(labour or 0)

def format_svm(n: int) -> str:
    return f"SVM{n:05d}" if n < 100000 else f"SVM{n}"

def is_valid_phone(phone: str) -> bool:
    p = str(phone or "").strip().replace("+", "").replace(" ", "")
    return len(p) >= PHONE_MIN_LEN and p.isdigit()

def is_valid_amount(x) -> bool:
    try:
        return float(x) >= 0
    except Exception:
        return False

def growth_pct(cur: float, prev: float) -> Optional[float]:
    return ((cur - prev) / prev * 100.0) if prev > 0 else None

def fmt_compact(v: float) -> str:
    v = float(v or 0)
    if abs(v) >= 1e7: return f"{v/1e7:.2f}Cr"
    if abs(v) >= 1e5: return f"{v/1e5:.2f}L"
    if abs(v) >= 1e3: return f"{v/1e3:.1f}K"
    return f"{v:.0f}"

# ================= AUTH =================
def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
    if salt is None:
        salt = secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ROUNDS)
    return h.hex(), salt.hex()

def verify_password(password: str, stored_hash: str, salt_hex: str) -> bool:
    try:
        h, _ = hash_password(password, bytes.fromhex(salt_hex))
        return hmac.compare_digest(h, stored_hash)
    except Exception as exc:
        log.warning("password verify असफल: %s", exc)
        return False

def create_user(username: str, password: str, role: str = "owner", db: Optional[Database] = None) -> bool:
    db = db or DB
    if not username.strip():
        raise ValueError("Username खाली हुन सक्दैन")
    if len(password) < PASSWORD_MIN_LEN:
        raise ValueError(f"Password कम्तीमा {PASSWORD_MIN_LEN} अक्षर चाहिन्छ")
    h, s = hash_password(password)
    try:
        with db.transaction() as con:
            con.execute("INSERT INTO users(username,password_hash,salt,role,created_at) VALUES(?,?,?,?,?)",
                        (username.strip(), h, s, role, datetime.now().isoformat()))
        return True
    except sqlite3.IntegrityError:
        return False

def check_login(username: str, password: str, db: Optional[Database] = None) -> Optional[str]:
    db = db or DB
    with db.read() as con:
        row = con.execute("SELECT password_hash,salt,role FROM users WHERE username=?",
                          (username,)).fetchone()
    if row and verify_password(password, row["password_hash"], row["salt"]):
        return row["role"]
    return None

def has_any_user(db: Optional[Database] = None) -> bool:
    db = db or DB
    with db.read() as con:
        return con.execute("SELECT COUNT(*) c FROM users").fetchone()["c"] > 0

# ================= AUDIT (hash chain) =================
def _audit(con: sqlite3.Connection, actor: str, action: str, detail: str) -> None:
    prev = con.execute("SELECT hash FROM audit_log ORDER BY id DESC LIMIT 1").fetchone()
    prev_h = prev["hash"] if prev else GENESIS
    ts = datetime.now().isoformat(timespec="seconds")
    payload = f"{prev_h}|{actor}|{action}|{detail}|{ts}"
    h = hashlib.sha256(payload.encode()).hexdigest()
    con.execute("INSERT INTO audit_log(actor,action,detail,prev_hash,hash,created_at) VALUES(?,?,?,?,?,?)",
                (actor, action, detail, prev_h, h, ts))

def audit(actor: str, action: str, detail: str, db: Optional[Database] = None) -> None:
    db = db or DB
    with db.transaction() as con:
        _audit(con, actor, action, detail)

def verify_audit_chain(db: Optional[Database] = None) -> tuple[bool, int]:
    db = db or DB
    with db.read() as con:
        rows = con.execute("SELECT * FROM audit_log ORDER BY id").fetchall()
    prev = GENESIS
    for r in rows:
        if r["prev_hash"] != prev:
            return False, r["id"]
        payload = f"{r['prev_hash']}|{r['actor']}|{r['action']}|{r['detail']}|{r['created_at']}"
        if hashlib.sha256(payload.encode()).hexdigest() != r["hash"]:
            return False, r["id"]
        prev = r["hash"]
    return True, len(rows)

# ================= BILLING =================
def _alloc_bill_no(con: sqlite3.Connection) -> str:
    if sqlite3.sqlite_version_info >= (3, 35, 0):
        row = con.execute("UPDATE bill_counter SET next_no=next_no+1 WHERE id=1 "
                          "RETURNING next_no-1 AS n").fetchone()
        return format_svm(int(row["n"]))
    for _ in range(BILL_RETRY):
        n = con.execute("SELECT next_no FROM bill_counter WHERE id=1").fetchone()["next_no"]
        cur = con.execute("UPDATE bill_counter SET next_no=? WHERE id=1 AND next_no=?", (n+1, n))
        if cur.rowcount == 1:
            return format_svm(int(n))
    raise RuntimeError("Bill number allocate गर्न सकिएन")

def _create_bill(con: sqlite3.Connection, bill_type: str, customer: str, phone: str,
                 detail: str, total: float, paid: float, due: float, payment: str,
                 created_at: Optional[str] = None, ref_id: Optional[int] = None) -> str:
    bill_no = _alloc_bill_no(con)
    con.execute("INSERT INTO bills(bill_no,bill_type,ref_id,customer,phone,detail,total,paid,due,payment,created_at) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (bill_no, bill_type, ref_id, customer, phone, detail, float(total), float(paid),
                 float(due), payment, created_at or datetime.now().isoformat(timespec="seconds")))
    return bill_no

def save_bill(bill_type, customer, phone, detail, total, paid, due, payment, db=None) -> str:
    db = db or DB
    for _ in range(BILL_RETRY):
        try:
            with db.transaction() as con:
                return _create_bill(con, bill_type, customer, phone, detail, total, paid, due, payment)
        except sqlite3.IntegrityError:
            continue
    raise RuntimeError("Bill save गर्न सकिएन")

# ================= BILL TEXT (FIX 1) =================
def assert_customer_safe(*texts) -> None:
    for t in texts:
        low = str(t or "").lower()
        for w in BANNED_BILL_WORDS:
            if w in low:
                raise ValueError(f"Bill मा भित्री शब्द राख्न मिल्दैन: '{w}' — '{t}'")

def make_bill_text(title: str, lines: list, customer: str = "", phone: str = "",
                   address: str = "", total: float = 0, paid: float = 0, due: float = 0,
                   payment: str = "Cash", bill_no: str = "", bill_date: str = "") -> str:
    shop, addr, mob, pan, owner, note, _theme, *_extra = get_settings()
    dt = bill_date or datetime.now().strftime("%Y-%m-%d %H:%M")
    assert_customer_safe(title, *lines, note, shop, addr, owner)
    b = ["=" * 56, f"              {shop}", f"              {addr}",
         f"        Mobile: {mob}  |  PAN: {pan}", "=" * 56,
         f"{title}  |  Bill: {bill_no}  |  Date: {dt}",
         f"Customer: {customer}   Phone: {phone}"]
    if address:
        b.append(f"Address: {address}")
    b.append("-" * 56); b.extend(lines); b.append("-" * 56)
    b.append(f"TOTAL: Rs. {total:,.0f}   PAID: Rs. {paid:,.0f}   DUE: Rs. {due:,.0f}")
    b.append(f"Payment: {payment}")
    b.append("-" * 56); b.append(note or "Dhanyabad! Feri pani palnuhola.")
    b.append("-" * 56); b.append(BRAND_LINE); b.append("=" * 56)
    return "\n".join(b)

# ================= SETTINGS / CASH / LEDGER SERVICES =================
def get_settings(db: Optional[Database] = None) -> tuple:
    db = db or DB
    with db.read() as con:
        r = con.execute("SELECT shop_name,address,mobile,pan,owner,bill_note,theme,"
                        "hello_login,hello_user,auto_update,auto_cloud "
                        "FROM settings WHERE id=1").fetchone()
    if not r:
        return (DEFAULT_SHOP_NAME, DEFAULT_ADDRESS, "", "", "Shuvam", "", DEFAULT_THEME, 0, "", 1, 1)
    row = list(tuple(r))
    while len(row) < 11:
        row.append(0 if len(row) in (7, 9) else "")
    row[6] = {"dark": "midnight", "light": "pearl"}.get(row[6], row[6] or DEFAULT_THEME)
    row[7] = int(row[7] or 0)
    row[8] = row[8] or ""
    row[9] = int(row[9] if row[9] is not None else 1)
    row[10] = int(row[10] or 0)
    return tuple(row[:11])

def _cash(con: sqlite3.Connection, desc: str, income: float = 0,
          expense: float = 0, category: str = "General") -> None:
    con.execute("INSERT INTO cashbook(date,description,income,expense,category) VALUES(?,?,?,?,?)",
                (datetime.now().strftime("%Y-%m-%d %H:%M"), desc,
                 float(income or 0), float(expense or 0), category))

def add_cash(desc: str, income: float = 0, expense: float = 0, category: str = "General",
             db: Optional[Database] = None) -> None:
    db = db or DB
    with db.transaction() as con:
        _cash(con, desc, income, expense, category)

def _ledger_entry(con: sqlite3.Connection, name: str, phone: str, ltype: str,
                  desc: str, udharo: float, tiryo: float, bill_no: str = "") -> float:
    """FIX 5:_running balance सही; 'दिन बाँकी' लाई अलग type मा राख्छ।"""
    prev = con.execute("SELECT COALESCE(SUM(udharo-tiryo),0) s FROM ledger WHERE name=?",
                       (name,)).fetchone()["s"] or 0
    bal = float(prev) + float(udharo) - float(tiryo)
    con.execute("INSERT INTO ledger(name,phone,type,description,udharo,tiryo,balance,date,bill_no) "
                "VALUES(?,?,?,?,?,?,?,?,?)",
                (name, phone, ltype, desc, float(udharo), float(tiryo), bal,
                 datetime.now().strftime("%Y-%m-%d"), bill_no or None))
    return bal

def _ledger_due(con, name, phone, ltype, desc, due, bill_no="") -> float:
    return _ledger_entry(con, name, phone, ltype, desc, due, 0, bill_no)

def receive_payment(bill_no: str, amount: float, actor: str, note: str = "",
                    db: Optional[Database] = None, payment: str = "Cash") -> float:
    """FIX 5: एउटै txn मा bills.due घटाउँछ + ledger + cashbook + audit।"""
    db = db or DB
    payment = (payment or "Cash").strip()
    if payment not in PAYMENT_METHODS:
        raise ValueError("भुक्तानी विधि मान्य छैन")
    if not is_valid_amount(amount) or amount <= 0:
        raise ValueError("रकम 0 भन्दा माथि हाल्नुहोस्")
    with db.transaction() as con:
        r = con.execute("SELECT * FROM bills WHERE bill_no=? AND is_deleted=0", (bill_no,)).fetchone()
        if not r:
            raise ValueError("बिल भेटिएन")
        amt = min(float(amount), float(r["due"]))
        if amt <= 0:
            raise ValueError("यो बिलको बाँकी रकम 0 छ")
        new_paid = float(r["paid"]) + amt
        new_due = calc_due(r["total"], new_paid)
        con.execute("UPDATE bills SET paid=?,due=?,updated_at=? WHERE bill_no=?",
                    (new_paid, new_due, datetime.now().isoformat(timespec="seconds"), bill_no))
        _ledger_entry(con, r["customer"], r["phone"] or "", "उधारो असुल",
                      f"{note or 'बिल असुल'} [{payment}]: {bill_no}", 0, amt, bill_no)
        _cash(con, f"उधारो असुल [{payment}]: {bill_no} — {r['customer']}", amt, 0,
              f"Udharo Recovery - {payment}")
        _audit(con, actor, "RECEIVE_PAYMENT", f"{bill_no} {amt:,.0f} via {payment}")
        return new_due

def restock_accessory(name: str, qty: int, buy_price: float, sell_price: float,
                      actor: str, db: Optional[Database] = None) -> None:
    """FIX 4: ON CONFLICT DO UPDATE — पुरानो सामानको स्टक बढ्छ, मूल्य 0 हुँदैन।"""
    db = db or DB
    if qty <= 0:
        raise ValueError("Qty 1 भन्दा माथि हाल्नुस्")
    with db.transaction() as con:
        con.execute("""INSERT INTO accessories(name,category,stock,buy_price,sell_price)
            VALUES(?,?,?,?,?)
            ON CONFLICT(name) DO UPDATE SET
              stock=accessories.stock+excluded.stock,
              buy_price=CASE WHEN excluded.buy_price>0 THEN excluded.buy_price ELSE accessories.buy_price END,
              sell_price=CASE WHEN excluded.sell_price>0 THEN excluded.sell_price ELSE accessories.sell_price END""",
                    (name, "Accessories", qty, buy_price, sell_price))
        _cash(con, f"Saman Kinyo/Restock: {name} x{qty}", 0, buy_price*qty, "Accessories Purchase")
        _audit(con, actor, "RESTOCK_ACC", f"{name} x{qty}")

def edit_bike(bike_id: int, fields: dict, actor: str, db: Optional[Database] = None) -> None:
    """FIX 6: कर Paid भएपछि total_cost र sold profit दुवै अपडेट।"""
    db = db or DB
    with db.transaction() as con:
        r = con.execute("SELECT * FROM bikes WHERE id=? AND is_deleted=0", (bike_id,)).fetchone()
        if not r:
            raise ValueError("Bike भेटिएन")
        tc = calc_total_cost(fields["buy_price"], fields["repair_cost"], fields["naam_sari"],
                             fields["kar_cost"], bool(fields["kar_paid"]))
        profit = calc_profit(r["sell_price"], tc) if r["status"] == "Bechiyo" else 0
        con.execute("""UPDATE bikes SET brand=?,model=?,color=?,year=?,bike_no=?,buy_price=?,
            repair_cost=?,naam_sari=?,kar_cost=?,kar_paid=?,total_cost=?,profit=?,updated_at=?
            WHERE id=?""",
                    (fields["brand"], fields["model"], fields["color"], fields["year"],
                     fields["bike_no"], fields["buy_price"], fields["repair_cost"],
                     fields["naam_sari"], fields["kar_cost"], int(fields["kar_paid"]),
                     tc, profit, datetime.now().isoformat(timespec="seconds"), bike_id))
        _audit(con, actor, "EDIT_BIKE", f"ID {bike_id} Total {tc:,.0f}")

def edit_bill(bill_no: str, customer: str, phone: str, total: float, paid: float,
              actor: str, db: Optional[Database] = None) -> str:
    """FIX 6: same bill_no, स्रोत table को paid/due/profit पनि अपडेट; bill text date जोगाउँछ।"""
    db = db or DB
    validate_payment(total, paid)
    with db.transaction() as con:
        r = con.execute("SELECT * FROM bills WHERE bill_no=? AND is_deleted=0", (bill_no,)).fetchone()
        if not r:
            raise ValueError("बिल भेटिएन")
        due = calc_due(total, paid)
        con.execute("UPDATE bills SET customer=?,phone=?,total=?,paid=?,due=?,updated_at=? WHERE bill_no=?",
                    (customer, phone, total, paid, due, datetime.now().isoformat(timespec="seconds"), bill_no))
        if r["bill_type"] == "BIKE" and r["ref_id"]:
            b = con.execute("SELECT total_cost FROM bikes WHERE id=?", (r["ref_id"],)).fetchone()
            if b:
                con.execute("UPDATE bikes SET buyer_name=?,buyer_phone=?,sell_price=?,profit=?,updated_at=? WHERE id=?",
                            (customer, phone, total, calc_profit(total, b["total_cost"]),
                             datetime.now().isoformat(timespec="seconds"), r["ref_id"]))
        con.execute("UPDATE accessory_sales SET customer=?,phone=?,total=? WHERE bill_no=?",
                    (customer, phone, total, bill_no))
        con.execute("UPDATE plates SET customer=?,phone=?,charge=?,paid=?,due=? WHERE bill_no=?",
                    (customer, phone, total, paid, due, bill_no))
        con.execute("UPDATE repairs SET customer=?,phone=?,total=?,paid=?,due=? WHERE bill_no=?",
                    (customer, phone, total, paid, due, bill_no))
        _audit(con, actor, "EDIT_BILL", f"{bill_no} Total {total:,.0f}")
        return r["created_at"]

def soft_delete(table: str, row_id: int, actor: str, db: Optional[Database] = None) -> None:
    """FIX 6: safe delete — hard delete होइन, audit सहित।"""
    allowed = {"bikes", "bills", "accessory_sales", "plates", "repairs"}
    if table not in allowed:
        raise ValueError("Delete नगर्न मिल्ने table")
    db = db or DB
    with db.transaction() as con:
        con.execute(f"UPDATE {table} SET is_deleted=1 WHERE id=?", (row_id,))
        _audit(con, actor, "SOFT_DELETE", f"{table}#{row_id}")

# ================= PREMIUM THEMES (5) =================
@dataclass(frozen=True)
class Theme:
    name: str
    BG0: str; BG1: str; BG2: str
    CARD: str; CARD2: str; EDGE: str; HI: str; SHADOW: str
    SIDE: str; SIDE_TXT: str; SIDE_ACT: str
    BORDER: str; TEXT: str; MUTED: str; INPUT: str
    ACCENT: str; ACCENT2: str; ACCENT3: str
    GREEN: str; RED: str; BLUE: str; PURPLE: str; GOLD: str
    GLOW1: str; GLOW2: str; GLOW3: str
    CHART: tuple
    PG_BG: str; PG_FG: str; PR_BG: str; PR_FG: str
    PN_BG: str; PN_FG: str; PB_BG: str; PB_FG: str; PP_BG: str; PP_FG: str

THEMES = {
    "midnight": Theme("midnight",
        "#060814", "#0C1028", "#171A3A",
        "#131A35", "#1A2244", "#303B70", "#E9EEFF", "#03050C",
        "#080C1E", "#98A3C7", "#6D5DF6",
        "#2A3460", "#F4F7FF", "#8B95B8", "#0F1630",
        "#7C5CFF", "#22D3EE", "#F472B6",
        "#34D399", "#FB7185", "#38BDF8", "#A78BFA", "#FBBF24",
        "#6D5DF6", "#22D3EE", "#EC4899",
        ("#7C5CFF", "#22D3EE"),
        "#10362A", "#6EE7B7", "#3B1822", "#FDA4AF",
        "#1C2444", "#A9B4D0", "#0F2F44", "#7DD3FC", "#2A1F4E", "#C4B5FD"),
    "ocean": Theme("ocean",
        "#04121C", "#08273A", "#0B3B54",
        "#0C2B3E", "#12384F", "#1E5A78", "#E7FBFF", "#020A10",
        "#061826", "#8FB6C9", "#0284C7",
        "#1B4A63", "#EFFBFF", "#7FA6B8", "#0A2537",
        "#0EA5E9", "#22D3EE", "#2DD4BF",
        "#34D399", "#FB7185", "#60A5FA", "#818CF8", "#FBBF24",
        "#0EA5E9", "#22D3EE", "#2DD4BF",
        ("#0EA5E9", "#22D3EE"),
        "#0B3328", "#6EE7B7", "#3A1824", "#FDA4AF",
        "#15384C", "#A9C4D2", "#0D3145", "#7DD3FC", "#1E2A55", "#A5B4FC"),
    "emerald": Theme("emerald",
        "#06130F", "#0A241C", "#0F3228",
        "#0E2A21", "#14382C", "#256B52", "#E9FFF6", "#030B08",
        "#071B15", "#8FBFAE", "#10B981",
        "#1E5340", "#EFFFF8", "#82A99A", "#0B241C",
        "#10B981", "#2DD4BF", "#A3E635",
        "#34D399", "#FB7185", "#38BDF8", "#A78BFA", "#FBBF24",
        "#10B981", "#2DD4BF", "#84CC16",
        ("#10B981", "#2DD4BF"),
        "#0E3B2E", "#6EE7B7", "#3C1D24", "#FDA4AF",
        "#123B2F", "#9DC4B5", "#0B3328", "#7DD3FC", "#1D3448", "#93C5FD"),
    "sunset": Theme("sunset",
        "#140711", "#2A0D1E", "#3B1424",
        "#2A1220", "#38182A", "#6E2B43", "#FFEAF2", "#0B0308",
        "#1B0813", "#C79AAE", "#F43F5E",
        "#59243A", "#FFF1F6", "#B98A9D", "#2A1020",
        "#F43F5E", "#FB923C", "#FBBF24",
        "#34D399", "#FB7185", "#38BDF8", "#C084FC", "#FBBF24",
        "#F43F5E", "#FB923C", "#A855F7",
        ("#F43F5E", "#FB923C"),
        "#123A2B", "#6EE7B7", "#44141F", "#FDA4AF",
        "#3A1526", "#C9A0B1", "#431B2B", "#FDBA74", "#2F1A4A", "#C4B5FD"),
    "pearl": Theme("pearl",
        "#EEF2FB", "#F8FAFF", "#E6ECF9",
        "#FFFFFF", "#F4F7FE", "#D7E0F2", "#FFFFFF", "#C3CEE4",
        "#17203A", "#AEB8D4", "#5A5FE0",
        "#DCE4F3", "#1A2340", "#74809A", "#F2F6FD",
        "#5A5FE0", "#0EA5E9", "#EC4899",
        "#16A34A", "#DC2626", "#0284C7", "#7C3AED", "#D4A017",
        "#6366F1", "#06B6D4", "#F472B6",
        ("#5A5FE0", "#0EA5E9"),
        "#DCFCE7", "#15803D", "#FEE2E2", "#B91C1C",
        "#E8EDF8", "#475569", "#E0F2FE", "#0369A1", "#EDE9FE", "#6D28D9"),
}
THEME_ORDER = ["midnight", "ocean", "emerald", "sunset", "pearl"]
THEME_LABELS = {"midnight": "Midnight", "ocean": "Ocean", "emerald": "Emerald",
                "sunset": "Sunset", "pearl": "Pearl"}
DARK = THEMES["midnight"]
LIGHT = THEMES["pearl"]
T = DARK

def apply_theme(name: str) -> None:
    global T
    key = {"dark": "midnight", "light": "pearl"}.get(str(name or "").strip().lower(), name)
    T = THEMES.get(key, THEMES[DEFAULT_THEME])

def glass_fill() -> str:
    """card र background को blend — पारदर्शी जस्तो देखिन्छ।"""
    return blend(T.BG1, T.CARD, 0.86)

# ================= ANIMATION ENGINE =================
def ease(p: float) -> float:
    return 1 - (1 - p) ** 3

class Anim:
    @staticmethod
    def run(widget, key: str, dur: int, steps: int, fn, done=None):
        if not widget.winfo_exists():
            return
        st = widget.__dict__.setdefault("_anim", {})
        gen = st.get(key, 0) + 1
        st[key] = gen
        def step(i: int):
            if st.get(key) != gen or not widget.winfo_exists():
                return
            fn(ease(i / steps))
            if i < steps:
                widget.after(max(8, dur // steps), lambda: step(i + 1))
            elif done:
                done()
        step(0)

# ================= GLASS WIDGETS (Tkinter मात्र) =================
if HAS_TK:
    FONT_FAMILY = "Segoe UI"

    def pick_font(root) -> str:
        try:
            fams = set(tkfont.families(root))
            for f in ("Segoe UI", "Nirmala UI", "DejaVu Sans", "Arial"):
                if f in fams:
                    return f
        except Exception:
            pass
        return "TkDefaultFont"

    def fnt(size: int, bold: bool = False):
        return (FONT_FAMILY, size, "bold" if bold else "normal")

    def round_rect(cv, x1, y1, x2, y2, r, **kw):
        r = max(0, min(r, (x2-x1)/2, (y2-y1)/2))
        pts = [x1+r,y1, x2-r,y1, x2,y1+r, x2,y2-r, x2-r,y2,
               x1+r,y2, x1,y2-r, x1,y1+r]
        return cv.create_polygon(pts, smooth=True, **kw)

    class GradientCanvas(tk.Canvas):
        """Root/page पछाडिको soft gradient + floating glow blobs."""
        def __init__(self, parent):
            super().__init__(parent, highlightthickness=0, bd=0)
            self.bind("<Configure>", lambda e=None: self.redraw())
            self.blobs = []

        def redraw(self):
            # केवल background shapes मेट्छ — canvas भित्रका embedded windows (sidebar/topbar/content) सुरक्षित रहन्छन्
            self.delete("bg")
            w, h = self.winfo_width(), self.winfo_height()
            if w < 2 or h < 2:
                return
            bands = 26
            for i in range(bands):
                t = i / (bands-1)
                self.create_rectangle(0, h*t/bands, w, h*(t+1)/bands+1,
                                      fill=blend(T.BG0, T.BG1, t), outline="", tags="bg")
            for x, y, r, col in self.blobs:
                cx, cy = x*w, y*h
                self.create_oval(cx-r, cy-r, cx+r, cy+r,
                                 fill=blend(glass_fill(), col, 0.20), outline="", tags="bg")
            self.tag_lower("bg")

    class GlassCard(tk.Canvas):
        """Animated rounded glass card: shadow + translucent fill + glow + sheen."""
        def __init__(self, parent, pad=14, r=18, glow=0.0, animate=True, stretch=True):
            super().__init__(parent, bg=glass_fill(), highlightthickness=0, bd=0)
            self.pad, self.r, self.stretch = pad, r, stretch
            self.glow = glow; self.sheen = -0.4
            self.body = tk.Frame(self, bg=glass_fill())
            self.win = self.create_window(pad, pad, anchor="nw", window=self.body)
            self.body.bind("<Configure>", self._fit_body)
            self.bind("<Configure>", self._fit_canvas)
            self.bind("<Enter>", lambda e: self._hover(1.0))
            self.bind("<Leave>", lambda e: self._hover(0.0))
            self._draw()
            if animate:
                def intro(p):
                    self.coords(self.win, pad, pad + (1-p)*14)
                    self._draw(alpha=p)
                Anim.run(self, "intro", 480, 20, intro)

        def _hover(self, target):
            start = self.glow
            Anim.run(self, "hover", 260, 12, lambda p: self._set_glow(start+(target-start)*p))
        def tilt(self, e):
            try:
                w,h=self.winfo_width(),self.winfo_height()
                if w<10 or h<10: return
                rx=(e.x/w-0.5)*6; ry=(e.y/h-0.5)*6
                self.place_configure(x=int(self.winfo_x()+rx),y=int(self.winfo_y()+ry))
            except Exception: pass

        def _set_glow(self, v):
            self.glow = v; self._draw()

        def _fit_body(self, e):
            self.configure(height=e.height + 2*self.pad)
            if not self.stretch:
                self.configure(width=e.width + 2*self.pad)
            else:
                self.itemconfigure(self.win, width=max(10, self.winfo_width()-2*self.pad))
            self._draw()

        def _fit_canvas(self, e):
            if self.stretch:
                self.itemconfigure(self.win, width=max(10, e.width-2*self.pad))
            self._draw()

        def _draw(self, alpha=1.0):
            self.delete("glass")
            w, h = self.winfo_width(), self.winfo_height()
            if w <= 6 or h <= 6:
                return
            base = blend(T.BG1, T.CARD, 0.88*alpha)
            edge = blend(T.EDGE, T.ACCENT, self.glow*0.75)
            round_rect(self, 4, 6, w-2, h-2, self.r, fill=T.SHADOW, outline="", tags="glass")
            round_rect(self, 1, 1, w-3, h-5, self.r, fill=base, outline=edge,
                       width=1 if self.glow < .1 else 2, tags="glass")
            # glass sheen (diagonal light sweep)
            sx = int((w+160)*self.sheen - 80)
            if -160 < sx < w+80:
                self.create_polygon(sx, 0, sx+55, 0, sx-45, h, sx-100, h,
                                    fill=lighten(base, 0.055), outline="", tags="glass")
            # top-left highlight stroke
            self.create_line(14, 3, w*0.42, 3, fill=blend(T.HI, edge, 0.45), tags="glass")
            self.tag_lower("glass")

        def sweep(self):
            start = -0.4
            def step(p):
                self.sheen = start + p*1.8
                self._draw()
            Anim.run(self, "sheen", 900, 24, step)

    class Pill(tk.Canvas):
        KINDS = {"g": ("PG_BG","PG_FG"), "r": ("PR_BG","PR_FG"), "n": ("PN_BG","PN_FG"),
                 "b": ("PB_BG","PB_FG"), "p": ("PP_BG","PP_FG")}
        def __init__(self, parent, text="—", kind="n"):
            super().__init__(parent, bg=glass_fill(), highlightthickness=0, height=22)
            self._font = tkfont.Font(font=fnt(8, True))
            self.set(text, kind)
        def set(self, text, kind="n"):
            bg, fg = self.KINDS.get(kind, self.KINDS["n"])
            w = self._font.measure(str(text)) + 18
            self.configure(width=w)
            self.delete("all")
            round_rect(self, 1, 1, w-1, 21, 10, fill=getattr(T,bg), outline=getattr(T,bg))
            self.create_text(w/2, 11, text=str(text), fill=getattr(T,fg), font=fnt(8, True))

    class NavItem(tk.Canvas):
        def __init__(self, parent, icon, text, cmd, width=208):
            super().__init__(parent, bg=T.SIDE, highlightthickness=0, height=44,
                             width=width, cursor="hand2")
            self.icon, self.text, self.cmd = icon, text, cmd
            self.active = False; self.hover = False; self.w = width; self.g = 0.0
            self.bind("<Button-1>", lambda e: self.cmd())
            self.bind("<Enter>", lambda e: self._hover(True))
            self.bind("<Leave>", lambda e: self._hover(False))
            self.redraw()
        def _hover(self, v):
            self.hover = v
            start = self.g
            target = 1.0 if (v or self.active) else 0.0
            Anim.run(self, "g", 220, 10, lambda p: self._set(start+(target-start)*p))
        def _set(self, v):
            self.g = v; self.redraw()
        def set_active(self, v):
            was = self.active; self.active = v
            if was != v:
                start = self.g
                Anim.run(self, "a", 300, 12, lambda p: self._set(start+((1.0 if v else 0.0)-start)*p))
            else:
                self.redraw()
        def redraw(self):
            self.delete("all")
            fill = blend(T.SIDE, T.SIDE_ACT, self.g)
            round_rect(self, 2, 2, self.w-2, 42, 12, fill=fill, outline=fill)
            fg = "#FFFFFF" if self.g > .35 else T.SIDE_TXT
            self.create_text(20, 22, text=self.icon, fill=fg, font=fnt(12, True), anchor="w")
            self.create_text(48, 22, text=self.text, fill=fg, font=fnt(10, True), anchor="w")
            if self.active:
                self.create_oval(6, 19, 11, 24, fill=T.ACCENT2, outline="")

    class Seg(tk.Canvas):
        """Sliding liquid-glass segmented control."""
        def __init__(self, parent, options, cmd, height=38):
            total_w = 0
            f = tkfont.Font(font=fnt(10, True))
            widths = [f.measure(t)+34 for t, _ in options]
            total_w = sum(widths) + 8
            super().__init__(parent, bg=glass_fill(), highlightthickness=0,
                             width=total_w, height=height)
            self.options = options; self.cmd = cmd; self.widths = widths
            self.keys = [k for _, k in options]
            self.cur = self.keys[0]; self.pos = 0.0; self.px = 4; self.pw = widths[0]
            self.bind("<Button-1>", self._click)
            self.bind("<Configure>", lambda e: self._draw())
            self._draw()
        def _click(self, e):
            x = 4; idx = 0
            for i, w in enumerate(self.widths):
                if x <= e.x <= x+w:
                    idx = i; break
                x += w + 4
            self.set(self.keys[idx], True)
        def set(self, key, fire=True):
            idx = self.keys.index(key) if key in self.keys else 0
            self.cur = self.keys[idx]
            x = 4 + sum(self.widths[:idx]) + idx*4
            w = self.widths[idx]
            start_x, start_w = self.px, self.pw
            def step(p):
                self.px = start_x+(x-start_x)*p
                self.pw = start_w+(w-start_w)*p
                self._draw()
            Anim.run(self, "seg", 320, 16, step)
            if fire:
                self.cmd(self.cur)
        def _draw(self):
            self.delete("all")
            round_rect(self, 1, 1, self.winfo_width()-2, self.winfo_height()-2, 12,
                       fill=blend(glass_fill(), T.BG0, .25), outline=T.BORDER)
            round_rect(self, self.px, 2, self.px+self.pw, self.winfo_height()-3, 10,
                       fill=blend(T.ACCENT, T.ACCENT2, .18), outline=T.ACCENT)
            x = 4
            for (t, k), w in zip(self.options, self.widths):
                self.create_text(x+w/2, self.winfo_height()/2, text=t,
                                 fill="#FFFFFF" if k == self.cur else T.MUTED, font=fnt(10, True))
                x += w+4

    class BarChart(tk.Canvas):
        def __init__(self, parent, height=210):
            super().__init__(parent, bg=glass_fill(), highlightthickness=0, height=height)
            self.data = []; self.anim = []
            self.bind("<Configure>", lambda e: self.redraw())
        def set_data(self, data, animate=True):
            self.data = data
            self.anim = [0.0]*len(data) if animate else [1.0]*len(data)
            self.redraw()
            if animate:
                def step(p):
                    self.anim = [p]*len(self.data); self.redraw()
                Anim.run(self, "bar", 700, 24, step)
        def redraw(self):
            self.delete("all")
            w, h = self.winfo_width(), self.winfo_height()
            if w < 80: return
            pl, pr, pt, pb = 48, 12, 22, 26
            pw, ph = w-pl-pr, h-pt-pb
            maxv = max([max(i,e) for _,i,e in self.data]+[1])
            for g in range(5):
                y = pt+ph*g/4
                self.create_line(pl,y,w-pr,y,fill=T.BORDER,dash=(2,4))
                self.create_text(pl-6,y,text=fmt_compact(maxv*(1-g/4)),anchor="e",
                                 fill=T.MUTED,font=fnt(8))
            n = max(1,len(self.data)); slot = pw/n; bw = max(6,min(16,slot/3.2))
            for idx,(lab,inc,exp) in enumerate(self.data):
                cx = pl+slot*idx+slot/2
                for off,val,col in ((-bw*.65,inc,T.CHART[0]),(bw*.65,exp,T.CHART[1])):
                    bh = ph*(val/maxv)*self.anim[idx]
                    if bh >= 1.5:
                        round_rect(self,cx+off-bw/2,pt+ph-bh,cx+off+bw/2,pt+ph,
                                   min(4,bh/2),fill=col,outline="")
                self.create_text(cx,h-9,text=lab,fill=T.MUTED,font=fnt(8))
            for j,(lab,col) in enumerate((("आयो",T.CHART[0]),("गयो",T.CHART[1]))):
                x = w-pr-90+j*52
                self.create_oval(x,6,x+8,14,fill=col,outline=col)
                self.create_text(x+12,10,text=lab,anchor="w",fill=T.MUTED,font=fnt(8))
            if not self.data or sum(i+e for _,i,e in self.data)==0:
                self.create_text(w/2,h/2,text="तथ्याङ्क छैन — पहिलो हिसाब प्रविष्ट गर्नुस्",
                                 fill=T.MUTED,font=fnt(10))

    class Donut(tk.Canvas):
        def __init__(self, parent, size=168):
            super().__init__(parent, bg=glass_fill(), highlightthickness=0, width=size,height=size)
            self.size=size; self.segs=[]; self.p=1.0
            self.redraw()
        def set_data(self, segs, animate=True):
            self.segs=segs; self.p=0.0 if animate else 1.0; self.redraw()
            if animate:
                def step(p): self.p=p; self.redraw()
                Anim.run(self,"donut",700,24,step)
        def redraw(self):
            self.delete("all"); s=self.size; m=14
            total=sum(v for _,v,_ in self.segs)
            if total<=0:
                self.create_oval(m,m,s-m,s-m,outline=T.BORDER,width=20)
                self.create_text(s/2,s/2,text="तथ्याङ्क छैन",fill=T.MUTED,font=fnt(9)); return
            acc=0.0
            for _,v,col in self.segs:
                deg=v/total*360.0*self.p
                self.create_arc(m,m,s-m,s-m,start=90-acc,extent=-min(deg,359.99),
                                style="arc",outline=col,width=20)
                acc+=deg
            self.create_text(s/2,s/2-8,text=f"{CURRENCY} {fmt_compact(total*self.p)}",
                             fill=T.TEXT,font=fnt(12,True))
            self.create_text(s/2,s/2+12,text="जम्मा बिक्री",fill=T.MUTED,font=fnt(8))

    class Spark(tk.Canvas):
        def __init__(self,parent,height=64):
            super().__init__(parent,bg=glass_fill(),highlightthickness=0,height=height)
            self.vals=[]; self.p=1.0; self.bind("<Configure>",lambda e:self.redraw())
        def set_data(self,vals,animate=True):
            self.vals=vals; self.p=0.0 if animate else 1.0; self.redraw()
            if animate:
                def step(p): self.p=p; self.redraw()
                Anim.run(self,"spark",650,22,step)
        def redraw(self):
            self.delete("all"); w,h=self.winfo_width(),self.winfo_height()
            if w<40 or not self.vals: return
            vals=self.vals if len(self.vals)>=2 else self.vals*2
            mx=max(vals+[1]); pad=8; pts=[]
            count=max(2,int(len(vals)*self.p))
            for i in range(count):
                v=vals[i]; x=pad+(w-2*pad)*i/(len(vals)-1)
                y=h-pad-(h-2*pad)*v/mx; pts.extend([x,y])
            if len(pts)>=4:
                self.create_line(*pts,fill=T.ACCENT2,width=2,smooth=True)
                self.create_oval(pts[-2]-3,pts[-1]-3,pts[-2]+3,pts[-1]+3,
                                 fill=T.ACCENT2,outline=glass_fill())

    class Ring(tk.Canvas):
        def __init__(self,parent,label,color):
            super().__init__(parent,bg=glass_fill(),highlightthickness=0,width=92,height=104)
            self.label=label; self.color=color; self.pct=0.0; self.p=0.0
            self.redraw()
        def set(self,pct,animate=True):
            self.pct=max(0.0,min(100.0,float(pct or 0)))
            self.p=0.0 if animate else 1.0; self.redraw()
            if animate:
                def step(p): self.p=p; self.redraw()
                Anim.run(self,"ring",600,20,step)
        def redraw(self):
            self.delete("all"); m=12; s=76
            self.create_oval(m,m,m+s,m+s,outline=T.BORDER,width=8)
            shown=self.pct*self.p
            if shown>0:
                self.create_arc(m,m,m+s,m+s,start=90,extent=-max(.01,shown*3.6),
                                style="arc",outline=self.color,width=8)
            self.create_text(m+s/2,m+s/2,text=f"{shown:.0f}%",fill=T.TEXT,font=fnt(10,True))
            self.create_text(46,96,text=self.label,fill=T.MUTED,font=fnt(8))

    class ScrollFrame(tk.Frame):
        """सधैं पूरा content देखिने scroll — visible slim scrollbar सहित।"""
        def __init__(self,parent):
            super().__init__(parent,bg=T.BG0)
            self.cv=tk.Canvas(self,bg=T.BG0,highlightthickness=0)
            self.sb=ttk.Scrollbar(self,orient="vertical",command=self.cv.yview,
                                  style="Shuvam.Vertical.TScrollbar")
            self.cv.configure(yscrollcommand=self.sb.set)
            self.cv.pack(side="left",fill="both",expand=True)
            self.sb.pack(side="right",fill="y",padx=(0,2))
            self.body=tk.Frame(self.cv,bg=T.BG0)
            self.win=self.cv.create_window(0,0,anchor="nw",window=self.body)
            self.body.bind("<Configure>",self._on_body)
            self.cv.bind("<Configure>",self._on_canvas)
            self.cv.bind("<Enter>",lambda e:self.cv.focus_set())
            self.cv.bind("<Prior>",lambda e:self.cv.yview_scroll(-1,"pages"))
            self.cv.bind("<Next>",lambda e:self.cv.yview_scroll(1,"pages"))
        def _on_body(self,e=None):
            self.cv.configure(scrollregion=self.cv.bbox("all"))
            self._autohide()
        def _on_canvas(self,e=None):
            self.cv.itemconfigure(self.win,width=max(20,e.width))
            self._autohide()
        def _autohide(self):
            try:
                first,last=self.cv.yview()
                if first<=0.0 and last>=1.0: self.sb.pack_forget()
                elif not self.sb.winfo_ismapped(): self.sb.pack(side="right",fill="y",padx=(0,2))
            except Exception:
                pass
        def wheel(self,delta): self.cv.yview_scroll(delta,"units")

    class Toast:
        """Glass toast — alpha + slide animated."""
        @staticmethod
        def show(root,text,color=None,dur=2600):
            if not HAS_TK: return
            col=color or T.ACCENT
            win=tk.Toplevel(root); win.overrideredirect(True)
            win.attributes("-alpha",0.0)
            win.configure(bg=col)
            inner=tk.Frame(win,bg=glass_fill(),padx=18,pady=10)
            inner.pack(fill="both",expand=True,padx=2,pady=2)
            tk.Label(inner,text=text,bg=glass_fill(),fg=T.TEXT,font=fnt(10,True)).pack()
            win.update_idletasks()
            w=win.winfo_width(); h=win.winfo_height()
            sw=root.winfo_screenwidth()
            x=sw-w-24; y0=30
            win.geometry(f"{w}x{h}+{x}+{y0-24}")
            def fade(up):
                steps=14
                def step(i):
                    if not win.winfo_exists(): return
                    p=i/steps
                    if up:
                        win.attributes("-alpha",0.95*p)
                        win.geometry(f"{w}x{h}+{x}+{y0-24+int(24*p)}")
                    else:
                        win.attributes("-alpha",0.95*(1-p))
                        win.geometry(f"{w}x{h}+{x}+{y0-int(10*p)}")
                    if i<steps: win.after(18,lambda:step(i+1))
                    elif not up: win.destroy()
                step(0)
            fade(True)
            win.after(dur,lambda:fade(False))

    def style_trees():
        st=ttk.Style(); st.theme_use("clam")
        st.configure("Treeview",background=glass_fill(),fieldbackground=glass_fill(),
                     foreground=T.TEXT,rowheight=30,borderwidth=0,font=fnt(9))
        st.configure("Treeview.Heading",background=glass_fill(),foreground=T.MUTED,
                     font=fnt(9,True),relief="flat",borderwidth=0)
        st.map("Treeview",background=[("selected",T.ACCENT)],foreground=[("selected","#FFFFFF")])
        st.configure("TCombobox",fieldbackground=T.INPUT,background=glass_fill(),
                     foreground=T.TEXT,arrowcolor=T.TEXT,borderwidth=0)
        st.map("TCombobox",fieldbackground=[("readonly",T.INPUT)])
        st.configure("Shuvam.Vertical.TScrollbar",background=T.EDGE,troughcolor=glass_fill(),
                     bordercolor=glass_fill(),arrowcolor=T.MUTED,width=10,arrows=False,
                     gripcount=0,relief="flat")
        st.map("Shuvam.Vertical.TScrollbar",background=[("active",T.ACCENT)])
        st.configure("Vertical.TScrollbar",background=T.EDGE,troughcolor=glass_fill(),
                     bordercolor=glass_fill(),arrowcolor=T.MUTED,arrows=False)
        for o,v in (("*TCombobox*Listbox.background",T.CARD),
                    ("*TCombobox*Listbox.foreground",T.TEXT),
                    ("*TCombobox*Listbox.selectBackground",T.ACCENT),
                    ("*TCombobox*Listbox.selectForeground","#FFFFFF")):
            st.master.option_add(o,v)

    def make_tree(parent,cols,height=10):
        tree=ttk.Treeview(parent,columns=[c for c,_ in cols],show="headings",height=height)
        for c,w in cols:
            tree.heading(c,text=c.replace("_"," ").title()); tree.column(c,width=w,anchor="w",minwidth=60)
        tree.tag_configure("due",foreground=T.RED)
        tree.tag_configure("ok",foreground=T.GREEN)
        return tree

    def mk_btn(parent,text,cmd,bg=None,width=None):
        bg=bg or T.ACCENT
        b=tk.Button(parent,text=text,command=cmd,bg=bg,fg="#FFFFFF",
                    activebackground=blend(bg,"#FFFFFF",.16),activeforeground="#FFFFFF",
                    font=fnt(10,True),bd=0,relief="flat",padx=16,pady=9,cursor="hand2",
                    width=width)
        b.bind("<Enter>",lambda e:b.config(bg=blend(bg,"#FFFFFF",.16)))
        b.bind("<Leave>",lambda e:b.config(bg=bg))
        return b

    def field(parent,label,row,col=0,width=16):
        width=max(8,min(int(width),16))          # संकीर्ण column मा पनि फिट हुने
        tk.Label(parent,text=label,bg=glass_fill(),fg=T.TEXT,font=fnt(9,True)).grid(
            row=row,column=col*2,sticky="w",padx=4,pady=4)
        e=tk.Entry(parent,width=width,font=fnt(10),bg=T.INPUT,fg=T.TEXT,relief="flat",
                   insertbackground=T.TEXT)
        e.grid(row=row,column=col*2+1,sticky="ew",padx=4,pady=4,ipady=5)
        return e

    def combo(parent,label,values,row,col=0,width=16):
        width=max(8,min(int(width),18))
        tk.Label(parent,text=label,bg=glass_fill(),fg=T.TEXT,font=fnt(9,True)).grid(
            row=row,column=col*2,sticky="w",padx=4,pady=4)
        c=ttk.Combobox(parent,values=values,width=width,font=fnt(10))
        c.grid(row=row,column=col*2+1,sticky="ew",padx=4,pady=4)
        return c

    def card_title(body,text,sub=""):
        tk.Label(body,text=text,bg=glass_fill(),fg=T.TEXT,font=fnt(12,True)).pack(
            anchor="w",padx=4,pady=(2,0))
        if sub:
            tk.Label(body,text=sub,bg=glass_fill(),fg=T.MUTED,font=fnt(8)).pack(
                anchor="w",padx=4,pady=(0,6))

    def parse_money(entry,label):
        raw=entry.get().strip() or "0"
        if not is_valid_amount(raw):
            raise ValueError(f"{label} मा 0 वा सोभन्दा माथिको Number मात्र हाल्नुस्")
        return float(raw)

    def show_bill(bill_text,filename="bill"):
        win=tk.Toplevel(); win.title("Bill Print — SHUVAM")
        win.geometry("620x720"); win.configure(bg=T.BG0)
        card=GlassCard(win,pad=12); card.pack(fill="both",expand=True,padx=14,pady=14)
        txt=tk.Text(card.body,font=("Courier New",10),wrap="word",bg=T.INPUT,fg=T.TEXT,
                    bd=0,insertbackground=T.TEXT)
        txt.pack(fill="both",expand=True,padx=4,pady=4); txt.insert("1.0",bill_text)
        def do_print():
            path=BILL_FOLDER/f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            path.write_text(bill_text,encoding="utf-8")
            try: os.startfile(str(path))
            except Exception as exc: log.info("startfile unavailable: %s",exc)
            messagebox.showinfo("Bill Saved",
                                f"Bill Save भयो:\n{path}\nNotepad बाट Ctrl+P गरेर Print गर्नुस्।",
                                parent=win)
        bf=tk.Frame(card.body,bg=glass_fill()); bf.pack(pady=8)
        mk_btn(bf,"🖨 PRINT / SAVE",do_print,T.ACCENT).pack(side="left",padx=5)
        mk_btn(bf,"Close",win.destroy,T.SIDE).pack(side="left",padx=5)
        card.sweep()

# ================= MAIN APPLICATION =================
if HAS_TK:
    class App:
        NAV = [("dash","⌂","Dashboard"),("bike","🏍","Bike"),("saman","📦","Saman"),
               ("hisab","📊","Hisab"),("bills","🧾","Bill Center"),
               ("settings","⚙","Settings")]

        def __init__(self, root, role="owner", username=""):
            self.root=root; self.role=role; self.username=username or role
            self.is_owner=(role=="owner")
            self.current=""; self.pages={}; self.nav={}; self.dash_range="7"
            apply_theme(get_settings()[6] or DEFAULT_THEME)
            self._shell()
            for key,_,_ in self.NAV:
                getattr(self,"build_"+key)()
            self.switch_page("dash")
            try: Anim.run(root,"boot",420,14,lambda p: root.attributes("-alpha",0.92+0.08*p))
            except Exception: pass

        # ---- db helpers ----
        def q(self,sql,params=()):
            with DB.read() as con: return con.execute(sql,params).fetchall()
        def q1(self,sql,params=()):
            with DB.read() as con: return con.execute(sql,params).fetchone()
        def val(self,sql,params=(),default=0):
            r=self.q1(sql,params)
            return r[0] if r and r[0] is not None else default

        def _shell(self):
            root=self.root
            root.title(APP_VERSION_LABEL)
            root.geometry("1400x900"); root.minsize(1180,760)
            root.configure(bg=T.BG0)
            try:
                ensure_icon_assets()
                root.iconbitmap(default=str(ICON_ICO))
            except Exception as exc:
                log.info("iconbitmap unavailable: %s", exc)
            try:
                if not hasattr(root, "_icon_photo"):
                    root._icon_photo = tk.PhotoImage(file=str(ICON_PNG))
                root.iconphoto(True, root._icon_photo)
            except Exception as exc:
                log.info("iconphoto unavailable: %s", exc)
            try: root.attributes("-alpha",0.0)
            except Exception: pass
            style_trees()
            self.cv=GradientCanvas(root); self.cv.pack(fill="both",expand=True)
            self.cv.blobs=[(0.05,0.05,260,T.PURPLE),(0.95,0.1,200,T.BLUE),
                           (0.8,0.9,240,T.ACCENT3),(0.15,0.9,200,T.GOLD)]
            self.side=tk.Frame(self.cv,bg=T.SIDE)
            self.top=tk.Frame(self.cv,bg=blend(T.BG0,T.CARD,0.85))
            self.content=tk.Frame(self.cv,bg=blend(T.BG0,T.BG1,0.5))
            self.ws=self.cv.create_window(0,0,anchor="nw",window=self.side,width=236)
            self.wt=self.cv.create_window(0,0,anchor="nw",window=self.top,height=70)
            self.wc=self.cv.create_window(0,0,anchor="nw",window=self.content)
            def layout(e=None):
                w,h=self.cv.winfo_width(),self.cv.winfo_height()
                if w<20 or h<20: return
                self.cv.itemconfigure(self.ws,height=h)
                self.cv.coords(self.wt,236,0); self.cv.itemconfigure(self.wt,width=w-236)
                self.cv.coords(self.wc,236,70)
                self.cv.itemconfigure(self.wc,width=max(20,w-236),height=max(20,h-70))
            self.cv.bind("<Configure>",layout,add="+")
            self.cv.redraw()
            self._build_side(); self._build_top()
            root.bind_all("<MouseWheel>",self._wheel)

        def _wheel(self,e):
            pg=self.pages.get(self.current)
            if pg is not None and hasattr(pg,"wheel"):
                pg.wheel(-1 if getattr(e,"delta",0)>0 else 1)

        def _build_side(self):
            s=self.side
            brand=tk.Frame(s,bg=T.SIDE); brand.pack(fill="x",padx=18,pady=(20,8))
            try:
                self.brand_img=tk.PhotoImage(file=str(ICON_PNG)).subsample(4)
                tk.Label(brand,image=self.brand_img,bg=T.SIDE).pack(side="left",padx=(0,10))
            except Exception:
                pass
            bt=tk.Frame(brand,bg=T.SIDE); bt.pack(side="left",fill="x")
            tk.Label(bt,text="SHUVAM",bg=T.SIDE,fg=T.TEXT,font=fnt(14,True)).pack(anchor="w")
            tk.Label(bt,text="RECONDITION HOUSE",bg=T.SIDE,fg=T.SIDE_TXT,font=fnt(7,True)).pack(anchor="w")
            tk.Frame(s,bg=T.EDGE,height=1).pack(fill="x",padx=16,pady=10)
            for key,icon,text in self.NAV:
                if key in ("hisab","settings") and not self.is_owner: continue
                nav=NavItem(s,icon,text,lambda k=key:self.switch_page(k))
                nav.pack(fill="x",padx=8,pady=3); self.nav[key]=nav
            tk.Frame(s,bg=T.EDGE,height=1).pack(fill="x",padx=18,pady=14)
            role_txt="OWNER" if self.is_owner else "STAFF"
            tk.Label(s,text=f"👤 {self.username}  •  {role_txt}",bg=T.SIDE,fg=T.SIDE_TXT,
                     font=fnt(8,True),wraplength=190,justify="left").pack(anchor="w",padx=18)
            tk.Label(s,text=BRAND_LINE,bg=T.SIDE,fg=darken(T.SIDE_TXT,0.30),
                     font=fnt(7),wraplength=190,justify="left").pack(anchor="sw",padx=18,pady=(0,16),side="bottom")

        def _build_top(self):
            tp=self.top
            self.title_lab=tk.Label(tp,text="Dashboard",bg=tp["bg"],fg=T.TEXT,font=fnt(18,True))
            self.title_lab.pack(side="left",padx=24)
            self.sub_lab=tk.Label(tp,text="",bg=tp["bg"],fg=T.MUTED,font=fnt(9))
            self.sub_lab.pack(side="left",padx=4)
            # search box
            sf=tk.Frame(tp,bg=T.INPUT,highlightthickness=1,highlightbackground=T.BORDER)
            sf.pack(side="left",padx=24,ipady=2)
            tk.Label(sf,text="🔍",bg=T.INPUT,fg=T.MUTED,font=fnt(10)).pack(side="left",padx=(8,4))
            self.search_entry=tk.Entry(sf,width=28,font=fnt(10),bg=T.INPUT,fg=T.TEXT,bd=0,relief="flat",insertbackground=T.TEXT)
            self.search_entry.pack(side="left",ipady=6,padx=(0,8))
            self.clock=tk.Label(tp,text="",bg=tp["bg"],fg=T.MUTED,font=fnt(9))
            self.clock.pack(side="right",padx=18)
            mk_btn(tp,"◐",self._theme_menu,T.PURPLE).pack(side="right",padx=4,pady=14)
            mk_btn(tp,"🌐",self._toggle_lang,T.SIDE).pack(side="right",padx=4,pady=14)
            # avatar
            av=tk.Label(tp,text="👤",bg=T.ACCENT,fg="#FFFFFF",font=fnt(11,True),width=2,padx=6)
            av.pack(side="right",padx=(4,12),pady=14)
            self._tick()

        def _tick(self):
            self.clock.config(text=datetime.now().strftime("%a, %d %b %Y  %I:%M %p"))
            self.root.after(1000,self._tick)

        def _toggle_theme(self):
            cur=get_settings()[6] or DEFAULT_THEME
            nxt=THEME_ORDER[(THEME_ORDER.index(cur)+1) % len(THEME_ORDER)] if cur in THEME_ORDER else THEME_ORDER[0]
            self.set_theme(nxt)

        def _toggle_lang(self):
            new="en" if CURRENT_LANG=="ne" else "ne"
            save_lang(new)
            # rebuild UI to apply language (like theme)
            prev=self.current or "dash"
            for w in self.root.winfo_children(): w.destroy()
            new_app=App(self.root,self.role,self.username)
            new_app.switch_page(prev)
            Toast.show(self.root,("Language: English" if new=="en" else "भाषा: नेपाली"),T.ACCENT)

        def _theme_menu(self):
            cur=get_settings()[6] or DEFAULT_THEME
            m=tk.Menu(self.root,tearoff=0,bg=T.CARD,fg=T.TEXT,activebackground=T.ACCENT,
                      activeforeground="#FFFFFF",bd=0,font=fnt(10))
            for key in THEME_ORDER:
                m.add_command(label=("● " if key==cur else "○ ")+THEME_LABELS[key],
                              command=lambda k=key:self.set_theme(k))
            try:
                m.tk_popup(self.root.winfo_pointerx(),self.root.winfo_pointery())
            finally:
                m.grab_release()

        def set_theme(self,key):
            """तुरुन्तै theme बदल्छ — UI पुनः build गरेर उही पेजमा फर्कन्छ।"""
            if key not in THEMES: return
            with DB.transaction() as con:
                con.execute("UPDATE settings SET theme=? WHERE id=1",(key,))
            prev=self.current or "dash"
            for w in self.root.winfo_children(): w.destroy()
            new_app=App(self.root,self.role,self.username)
            new_app.switch_page(prev)
            Toast.show(self.root,f"🎨 {THEME_LABELS[key]} theme लागू भयो",T.ACCENT)

        def switch_page(self,key):
            if key not in self.pages: return
            if key in ("hisab","settings") and not self.is_owner:
                Toast.show(self.root,"⛔ यो पेज Owner का लागि मात्र हो",T.RED)
                return
            for w in self.content.winfo_children(): w.pack_forget()
            self.current=key
            self.pages[key].pack(fill="both",expand=True)
            for k,nav in self.nav.items(): nav.set_active(k==key)
            names=dict((k,t) for k,_,t in self.NAV)
            self.title_lab.config(text=names.get(key,key))
            self.sub_lab.config(text={"dash":"आजको झलक","bike":"खरिद • बिक्री • स्टक",
                "saman":"हेल्मेट • नम्बर प्लेट • मर्मत","hisab":"लेजर • क्यासबुक",
                "bills":"प्रिन्ट • सम्पादन • सुरक्षित डिलिट",
                "settings":"दुकान • प्रयोगकर्ता • ब्याकअप"}.get(key,""))
            getattr(self,"refresh_"+key,lambda:None)()
            try:
                Anim.run(self.cv,"page_slide",200,9,
                         lambda p:self.cv.coords(self.wc,224+(1-p)*18,66))
            except Exception:
                pass

        # ---------------- DASHBOARD ----------------
        def build_dash(self):
            pg=tk.Frame(self.content,bg=blend(T.BG0,T.BG1,0.65)); self.pages["dash"]=pg
            sf=ScrollFrame(pg); sf.pack(fill="both",expand=True); pg.wheel=sf.wheel
            b=sf.body
            # 3D hero banner
            hero=GlassCard(b,pad=20,glow=.5); hero.pack(fill="x",padx=12,pady=(12,6))
            hb=tk.Frame(hero.body,bg=glass_fill()); hb.pack(fill="x")
            hl=tk.Frame(hb,bg=glass_fill()); hl.pack(side="left")
            tk.Label(hl,text="नमस्ते 👋",bg=glass_fill(),fg=T.TEXT,font=fnt(26,True)).pack(anchor="w")
            tk.Label(hl,text=f"{APP_TITLE} — {datetime.now().strftime('%A, %d %B %Y')}",
                     bg=glass_fill(),fg=T.MUTED,font=fnt(11)).pack(anchor="w")
            tk.Label(hl,text="Real-time business intelligence",bg=glass_fill(),fg=T.ACCENT2,font=fnt(10,True)).pack(anchor="w",pady=(6,0))
            hr=tk.Frame(hb,bg=glass_fill()); hr.pack(side="right")
            self.dash_seg=Seg(hr,[("७ दिन","7"),("३० दिन","30")],self._set_dash_range)
            self.dash_seg.pack(pady=4)
            try:
                if getattr(self,"_dash_icon",None) is None:
                    self._dash_icon=tk.PhotoImage(file=str(ICON_PNG)).subsample(3)
                tk.Label(hr,image=self._dash_icon,bg=glass_fill()).pack(pady=(6,0))
            except Exception: pass

            krow=tk.Frame(b,bg=b["bg"]); krow.pack(fill="x",padx=12,pady=6)
            self.kpis={}
            for key,title,icon,col in (("today","आजको बिक्री","💰",T.GREEN),
                    ("month","यो महिना","📈",T.ACCENT),("due","बाँकी उधारो","⏳",T.RED),
                    ("stock","स्टक Bike","🏍",T.BLUE)):
                c=GlassCard(krow,pad=14,r=18,glow=.25); c.pack(side="left",fill="both",expand=True,padx=6,pady=6)
                top=tk.Frame(c.body,bg=glass_fill()); top.pack(fill="x")
                badge=tk.Label(top,text=icon,font=fnt(20),bg=col,fg="#FFFFFF",width=2,padx=4)
                badge.pack(side="left")
                tk.Label(top,text=title,font=fnt(9,True),bg=glass_fill(),fg=T.MUTED).pack(side="left",padx=8)
                lab=tk.Label(c.body,text=f"{CURRENCY} 0",font=fnt(22,True),bg=glass_fill(),fg=T.TEXT)
                lab.pack(anchor="w",pady=(8,0))
                sub=tk.Label(c.body,text="",font=fnt(9),bg=glass_fill(),fg=T.MUTED); sub.pack(anchor="w")
                self.kpis[key]=(lab,sub)

            crow=tk.Frame(b,bg=b["bg"]); crow.pack(fill="x",padx=12,pady=6)
            c1=GlassCard(crow,pad=14,glow=.16); c1.pack(side="left",fill="both",expand=True,padx=6,pady=6)
            card_title(c1.body,"आय / व्यय","प्रत्येक दिन अनुसार")
            self.bar=BarChart(c1.body); self.bar.pack(fill="both",expand=True,padx=4,pady=6)
            c2=GlassCard(crow,pad=14,stretch=False); c2.pack(side="left",fill="y",padx=6,pady=6)
            card_title(c2.body,"बिक्री विभाजन")
            self.donut=Donut(c2.body); self.donut.pack(padx=8,pady=6)
            self.donut_legend=tk.Frame(c2.body,bg=glass_fill()); self.donut_legend.pack(fill="x",padx=8,pady=(0,8))

            rrow=tk.Frame(b,bg=b["bg"]); rrow.pack(fill="x",padx=12,pady=(6,18))
            c3=GlassCard(rrow,pad=14,stretch=False); c3.pack(side="left",fill="y",padx=6,pady=6)
            card_title(c3.body,"व्यवसाय स्वास्थ्य")
            rr=tk.Frame(c3.body,bg=glass_fill()); rr.pack()
            self.ring_collect=Ring(rr,"असुल",T.GREEN); self.ring_collect.pack(side="left",padx=6)
            self.ring_stock=Ring(rr,"स्टक",T.ACCENT2); self.ring_stock.pack(side="left",padx=6)
            c4=GlassCard(rrow,pad=14); c4.pack(side="left",fill="both",expand=True,padx=6,pady=6)
            card_title(c4.body,"बिक्री ट्रेन्ड","आय + व्यय")
            self.spark=Spark(c4.body); self.spark.pack(fill="x",padx=6,pady=10)
            c5=GlassCard(rrow,pad=14,glow=.30); c5.pack(side="left",fill="both",expand=True,padx=6,pady=6)
            card_title(c5.body,"⚠ अलर्ट","कर म्याद र बाँकी बिल")
            self.alert_box=tk.Frame(c5.body,bg=glass_fill()); self.alert_box.pack(fill="both",expand=True,padx=4,pady=4)

        def _set_dash_range(self,k):
            self.dash_range=k; self.refresh_dash()

        def refresh_dash(self):
            if not hasattr(self,"kpis"): return
            today=date.today().isoformat(); month=today[:7]
            t_sale=self.val("SELECT COALESCE(SUM(total),0) FROM bills WHERE date(created_at)=? AND is_deleted=0",(today,))
            m_sale=self.val("SELECT COALESCE(SUM(total),0) FROM bills WHERE substr(created_at,1,7)=? AND is_deleted=0",(month,))
            due=self.val("SELECT COALESCE(SUM(due),0) FROM bills WHERE is_deleted=0")
            stock=self.val("SELECT COUNT(*) FROM bikes WHERE status='Stock Ma' AND is_deleted=0")
            prev=self.val("SELECT COALESCE(SUM(total),0) FROM bills WHERE substr(created_at,1,7)=strftime('%Y-%m',date('now','-1 month')) AND is_deleted=0")
            g=growth_pct(m_sale,prev)
            t_count=self.val("SELECT COUNT(*) FROM bills WHERE date(created_at)=? AND is_deleted=0",(today,))
            d_count=self.val("SELECT COUNT(*) FROM bills WHERE due>0 AND is_deleted=0")
            sold=self.val("SELECT COUNT(*) FROM bikes WHERE status='Bechiyo' AND is_deleted=0")
            self.kpis["today"][0].config(text=f"{CURRENCY} {t_sale:,.0f}")
            self.kpis["today"][1].config(text=f"{t_count} बिल आज")
            self.kpis["month"][0].config(text=f"{CURRENCY} {m_sale:,.0f}")
            self.kpis["month"][1].config(text=(f"{g:+.1f}% गत महिना भन्दा" if g is not None else "गत महिना तथ्याङ्क छैन"))
            self.kpis["due"][0].config(text=f"{CURRENCY} {due:,.0f}")
            self.kpis["due"][1].config(text=f"{d_count} ग्राहक बाँकी")
            self.kpis["stock"][0].config(text=str(stock))
            self.kpis["stock"][1].config(text=f"{sold} बिकिभयो")

            days=int(self.dash_range); data=[]
            for i in range(days-1,-1,-1):
                d=(date.today()-timedelta(days=i)).isoformat()
                inc=self.val("SELECT COALESCE(SUM(income),0) FROM cashbook WHERE date(date)=?",(d,))
                exp=self.val("SELECT COALESCE(SUM(expense),0) FROM cashbook WHERE date(date)=?",(d,))
                data.append((d[5:],inc,exp))
            self.bar.set_data(data); self.spark.set_data([i+e for _,i,e in data])
            segs=[("Bike",self.val("SELECT COALESCE(SUM(total),0) FROM bills WHERE bill_type='BIKE' AND is_deleted=0"),T.ACCENT),
                  ("Helmet",self.val("SELECT COALESCE(SUM(total),0) FROM bills WHERE bill_type='HELMET' AND is_deleted=0"),T.ACCENT2),
                  ("Plate",self.val("SELECT COALESCE(SUM(total),0) FROM bills WHERE bill_type='PLATE' AND is_deleted=0"),T.GREEN),
                  ("Repair",self.val("SELECT COALESCE(SUM(total),0) FROM bills WHERE bill_type='REPAIR' AND is_deleted=0"),T.GOLD)]
            self.donut.set_data([(n,v,c) for n,v,c in segs if v>0] or [("तथ्याङ्क छैन",0,T.BORDER)])
            for w in self.donut_legend.winfo_children(): w.destroy()
            for n,v,c in segs:
                row=tk.Frame(self.donut_legend,bg=glass_fill()); row.pack(fill="x",pady=1)
                tk.Label(row,text="●",fg=c,bg=glass_fill(),font=fnt(8)).pack(side="left")
                tk.Label(row,text=n,bg=glass_fill(),fg=T.MUTED,font=fnt(8)).pack(side="left")
                tk.Label(row,text=f"{CURRENCY}{v:,.0f}",bg=glass_fill(),fg=T.TEXT,font=fnt(8,True)).pack(side="right")

            recv=self.val("SELECT COALESCE(SUM(tiryo),0) FROM ledger")
            udh=self.val("SELECT COALESCE(SUM(udharo),0) FROM ledger")
            self.ring_collect.set(100*recv/(recv+udh) if (recv+udh)>0 else 0)
            low=self.val("SELECT COUNT(*) FROM accessories WHERE stock<=2")
            self.ring_stock.set(max(0,100-low*12))

            for w in self.alert_box.winfo_children(): w.destroy()
            alerts=[]
            for r in self.q("SELECT bike_no,brand,model,buy_date FROM bikes WHERE kar_paid=0 AND status='Stock Ma' AND is_deleted=0"):
                st=kar_status(r["buy_date"])
                if st: alerts.append((st[0],f"{r['brand']} {r['model']} • {r['bike_no']}",T.GOLD))
            for r in self.q("SELECT bill_no,customer,due FROM bills WHERE due>0 AND is_deleted=0 ORDER BY due DESC LIMIT 5"):
                alerts.append((f"{CURRENCY}{r['due']:,.0f} बाँकी",f"{r['bill_no']} • {r['customer']}",T.RED))
            if not alerts:
                tk.Label(self.alert_box,text="✅ सबै ठीक छ — कुनै अलर्ट छैन",bg=glass_fill(),fg=T.GREEN,
                         font=fnt(10,True)).pack(pady=18)
            else:
                for title,sub,col in alerts[:7]:
                    row=tk.Frame(self.alert_box,bg=glass_fill()); row.pack(fill="x",pady=3,padx=4)
                    tk.Label(row,text="●",fg=col,bg=glass_fill(),font=fnt(8)).pack(side="left")
                    tk.Label(row,text=title,bg=glass_fill(),fg=col,font=fnt(9,True)).pack(side="left",padx=4)
                    tk.Label(row,text=sub,bg=glass_fill(),fg=T.MUTED,font=fnt(8),wraplength=250,
                             justify="left").pack(side="left",padx=4)
            self.cv.redraw()

        # ---------------- BIKE ----------------
        def build_bike(self):
            pg=tk.Frame(self.content,bg=blend(T.BG0,T.BG1,0.65)); self.pages["bike"]=pg
            sf=ScrollFrame(pg); sf.pack(fill="both",expand=True); pg.wheel=sf.wheel
            b=sf.body
            head=tk.Frame(b,bg=b["bg"]); head.pack(fill="x",padx=12,pady=(14,6))
            self.bike_seg=Seg(head,[("स्टक","Stock Ma"),("बिकिभयो","Bechiyo"),("सबै","all")],self._bike_tab)
            self.bike_seg.pack(side="left")
            self.bike_tab="Stock Ma"
            tk.Label(head,text="खरिद → मर्मत → नामसारी → कर → बिक्री",bg=b["bg"],fg=T.MUTED,
                     font=fnt(9)).pack(side="left",padx=16)
            main=tk.Frame(b,bg=b["bg"]); main.pack(fill="both",expand=True,padx=12,pady=6)
            col=tk.Frame(main,bg=b["bg"]); col.pack(fill="both",expand=True)

            bc=GlassCard(col,pad=12,glow=.18); bc.pack(fill="x",padx=6,pady=6)
            card_title(bc.body,"🛒 नयाँ Bike खरिद","लागतका सबै खर्च एकै ठाउँमा")
            form=tk.Frame(bc.body,bg=glass_fill()); form.pack(fill="x",padx=4,pady=6)
            for i in range(4): form.columnconfigure(i,weight=1)
            self.bf={}
            self.bf["brand"]=combo(form,"Brand",list(BIKE_DATA),0,0)
            self.bf["model"]=combo(form,"Model",BIKE_DATA["Honda"],0,1)
            self.bf["color"]=combo(form,"Color",COLOR_LIST,1,0)
            self.bf["year"]=combo(form,"Year",YEAR_LIST,1,1)
            self.bf["engine"]=field(form,"Engine No",2,0,22)
            self.bf["chassis"]=field(form,"Chassis No",2,1,22)
            self.bf["bike_no"]=field(form,"Bike No *",3,0,22)
            self.bf["buy_date"]=field(form,"खरिद मिति",3,1,22)
            self.bf["seller"]=field(form,"बिक्रेता नाम",4,0,22)
            self.bf["seller_phone"]=field(form,"बिक्रेता फोन",4,1,22)
            self.bf["buy_price"]=field(form,"खरिद मूल्य",5,0,22)
            self.bf["repair_cost"]=field(form,"मर्मत खर्च",5,1,22)
            self.bf["naam_sari"]=field(form,"नामसारी खर्च",6,0,22)
            self.bf["kar_cost"]=field(form,"कर रकम",6,1,22)
            self.kar_var=tk.IntVar()
            tk.Checkbutton(form,text="✓ कर तिरिसकेको (Paid)",variable=self.kar_var,
                           bg=glass_fill(),fg=T.TEXT,selectcolor=T.INPUT,activebackground=glass_fill(),
                           font=fnt(9,True)).grid(row=7,column=2,columnspan=2,sticky="w",padx=8,pady=6)
            bfbtn=tk.Frame(bc.body,bg=glass_fill()); bfbtn.pack(fill="x",padx=4,pady=(2,8))
            mk_btn(bfbtn,"💾 खरिद सेभ",self._buy_bike,T.GREEN).pack(side="left",padx=4)
            mk_btn(bfbtn,"🧹 क्लियर",self._clear_bike_form,T.SIDE).pack(side="left",padx=4)
            def brand_changed(e=None):
                self.bf["model"]["values"]=BIKE_DATA.get(self.bf["brand"].get(),["Other - Manual Type Garnus"])
                self.bf["model"].current(0)
            self.bf["brand"].bind("<<ComboboxSelected>>",brand_changed)
            self._clear_bike_form()

            sc=GlassCard(col,pad=12,glow=.28); sc.pack(fill="x",padx=6,pady=6)
            card_title(sc.body,"💰 बिक्री गर्नुहोस्","बिल स्वतः बन्छ — profit कहिले देखिँदैन")
            sf2=tk.Frame(sc.body,bg=glass_fill()); sf2.pack(fill="x",padx=4,pady=6)
            for i in range(4): sf2.columnconfigure(i,weight=1)
            self.sf={}
            self.sf["bike"]=combo(sf2,"स्टक Bike",[],0,0)
            self.sf2_width_fix=sf2
            self.sf["buyer"]=field(sf2,"ग्राहक नाम",0,1,22)
            self.sf["phone"]=field(sf2,"ग्राहक फोन",1,0,22)
            self.sf["address"]=field(sf2,"ठेगाना",1,1,22)
            self.sf["price"]=field(sf2,"बिक्री मूल्य",2,0,22)
            self.sf["paid"]=field(sf2,"पैसा पाइयो",2,1,22)
            self.sf["payment"]=combo(sf2,"भुक्तानी",list(PAYMENT_METHODS),3,0)
            self.sf["payment"].current(0); self.sf["payment"].config(state="readonly")
            self.due_lab=tk.Label(sf2,text="बाँकी: Rs. 0",bg=glass_fill(),fg=T.RED,font=fnt(9,True))
            self.due_lab.grid(row=3,column=2,columnspan=2,sticky="w",padx=8,pady=6)
            for key in ("price","paid"):
                self.sf[key].bind("<KeyRelease>",lambda e:self._preview_sell_due())
            mk_btn(sc.body,"🧾 बिल बनाउ र बिक्री गर",self._sell_bike,T.ACCENT).pack(fill="x",padx=8,pady=(2,10))

            rc=GlassCard(col,pad=12,glow=.10); rc.pack(fill="x",padx=6,pady=6)
            card_title(rc.body,"🏍 Bike सूची","डबल-क्लिक गरेर सम्पादन गर्नुस्")
            bar=tk.Frame(rc.body,bg=glass_fill()); bar.pack(fill="x",padx=4,pady=4)
            mk_btn(bar,"✏ सम्पादन",self._edit_bike,T.ACCENT).pack(side="left",padx=4)
            mk_btn(bar,"🗑 डिलिट",self._del_bike,T.RED).pack(side="left",padx=4)
            mk_btn(bar,"🔄 रिफ्रेस",self.refresh_bike,T.SIDE).pack(side="left",padx=4)
            cols=[("bike_no",110),("brand",100),("model",140),("status",90),
                  ("total",100),("sell",100)]
            if self.is_owner: cols.append(("profit",95))
            cols.append(("kar",125))
            self.bike_tree=make_tree(rc.body,cols,height=14)
            self.bike_tree.pack(fill="both",expand=True,padx=4,pady=4)
            self.bike_tree.bind("<Double-1>",lambda e:self._edit_bike())

        def _bike_tab(self,key):
            self.bike_tab=key; self.refresh_bike()

        def _clear_bike_form(self):
            if not hasattr(self,"bf"): return
            for e in self.bf.values():
                try: e.delete(0,"end")
                except Exception: e.set("")
            self.bf["brand"].current(0)
            self.bf["model"]["values"]=BIKE_DATA["Honda"]; self.bf["model"].current(0)
            self.bf["color"].current(0); self.bf["year"].current(0)
            self.bf["buy_date"].insert(0,date.today().isoformat())
            self.kar_var.set(0)

        def _preview_sell_due(self):
            try:
                total=parse_money(self.sf["price"],"बिक्री मूल्य")
                paid=parse_money(self.sf["paid"],"पैसा पाइयो")
                d=calc_due(total,paid)
                self.due_lab.config(text=f"बाँकी: {CURRENCY} {d:,.0f}",fg=T.RED if d>0 else T.GREEN)
            except Exception:
                self.due_lab.config(text="बाँकी: Rs. 0",fg=T.MUTED)

        def _buy_bike(self):
            try:
                f=self.bf
                bike_no=f["bike_no"].get().strip()
                if not bike_no: raise ValueError("Bike नम्बर हाल्नुस्")
                if not is_valid_phone(f["seller_phone"].get()): raise ValueError("बिक्रेता फोन १० अंकको हुनुपर्छ")
                buy=parse_money(f["buy_price"],"खरिद मूल्य")
                rep=parse_money(f["repair_cost"],"मर्मत खर्च")
                ns=parse_money(f["naam_sari"],"नामसारी खर्च")
                kc=parse_money(f["kar_cost"],"कर रकम")
                kp=bool(self.kar_var.get())
                tc=calc_total_cost(buy,rep,ns,kc,kp)
                bdate=f["buy_date"].get().strip() or date.today().isoformat()
                with DB.transaction() as con:
                    try:
                        cur=con.execute("""INSERT INTO bikes(brand,model,color,year,engine_no,chassis_no,bike_no,
                            seller_name,seller_phone,buy_price,repair_cost,naam_sari,kar_cost,kar_paid,
                            total_cost,buy_date,status,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (f["brand"].get(),f["model"].get(),f["color"].get(),f["year"].get(),
                             f["engine"].get().strip(),f["chassis"].get().strip(),bike_no,
                             f["seller"].get().strip(),f["seller_phone"].get().strip(),
                             buy,rep,ns,kc,int(kp),tc,bdate,"Stock Ma",datetime.now().isoformat(timespec="seconds")))
                    except sqlite3.IntegrityError:
                        raise ValueError(f"Bike नम्बर '{bike_no}' पहिले नै छ")
                    bid=cur.lastrowid
                    _cash(con,f"Bike खरिद: {bike_no}",0,buy,"Bike Purchase")
                    if rep: _cash(con,f"मर्मत खर्च: {bike_no}",0,rep,"Repair")
                    if ns: _cash(con,f"नामसारी: {bike_no}",0,ns,"Name Transfer")
                    if kp and kc: _cash(con,f"कर तिर्यो: {bike_no}",0,kc,"Tax")
                    _audit(con,self.username,"BUY_BIKE",f"{bike_no} Total {tc:,.0f}")
                Toast.show(self.root,f"✅ Bike {bike_no} खरिद भयो",T.GREEN)
                self._clear_bike_form(); self.refresh_bike(); self.refresh_dash()
            except Exception as exc:
                messagebox.showerror("खरिद त्रुटि",str(exc),parent=self.root)

        def _sell_bike(self):
            try:
                raw=self.sf["bike"].get().strip()
                if not raw: raise ValueError("स्टक बाइक छान्नुस्")
                bike_no=raw.split(" | ")[0].strip()
                r=self.q1("SELECT * FROM bikes WHERE bike_no=? AND status='Stock Ma' AND is_deleted=0",(bike_no,))
                if not r: raise ValueError("उक्त Bike स्टकमा छैन")
                buyer=self.sf["buyer"].get().strip(); phone=self.sf["phone"].get().strip()
                if not buyer: raise ValueError("ग्राहक नाम हाल्नुस्")
                if not is_valid_phone(phone): raise ValueError("ग्राहक फोन १० अंकको हुनुपर्छ")
                total=parse_money(self.sf["price"],"बिक्री मूल्य")
                paid=parse_money(self.sf["paid"],"पैसा पाइयो")
                validate_payment(total,paid,"Paid")          # FIX 2
                due=calc_due(total,paid)
                payment=self.sf["payment"].get() or "Cash"
                addr=self.sf["address"].get().strip()
                profit=calc_profit(total,r["total_cost"])     # internal only — bill मा कहिले जाँदैन
                lines=[f"Bike No: {r['bike_no']}",f"Brand/Model: {r['brand']} {r['model']}",
                       f"Color/Year: {r['color']}  |  {r['year']}",f"Engine: {r['engine_no'] or '-'}",
                       f"Chassis: {r['chassis_no'] or '-'}"]
                with DB.transaction() as con:
                    bno=_create_bill(con,"BIKE",buyer,phone,f"{r['brand']} {r['model']} | {r['bike_no']}",
                                     total,paid,due,payment,ref_id=r["id"])
                    con.execute("""UPDATE bikes SET status='Bechiyo',sell_date=?,sell_price=?,buyer_name=?,
                        buyer_phone=?,buyer_address=?,profit=?,updated_at=? WHERE id=?""",
                        (datetime.now().strftime("%Y-%m-%d"),total,buyer,phone,addr,profit,
                         datetime.now().isoformat(timespec="seconds"),r["id"]))
                    if due>0: _ledger_due(con,buyer,phone,"उधारो",f"Bike बिक्री {bno}",due,bno)
                    _cash(con,f"Bike बिक्री: {r['bike_no']} ({bno})",paid,0,"Bike Sale")
                    _audit(con,self.username,"SELL_BIKE",f"{bno} {bike_no} {total:,.0f}")
                txt=make_bill_text("बाइक बिक्री बिल",lines,customer=buyer,phone=phone,address=addr,
                                   total=total,paid=paid,due=due,payment=payment,bill_no=bno)
                show_bill(txt,bno)
                for k in ("bike","buyer","phone","address","price","paid"): self.sf[k].delete(0,"end")
                self._preview_sell_due(); self.refresh_bike(); self.refresh_dash(); self.refresh_bills()
            except Exception as exc:
                messagebox.showerror("बिक्री त्रुटि",str(exc),parent=self.root)

        def refresh_bike(self):
            if not hasattr(self,"bike_tree"): return
            tab=getattr(self,"bike_tab","Stock Ma")
            sql="SELECT * FROM bikes WHERE is_deleted=0"; params=()
            if tab!="all": sql+=" AND status=?"; params=(tab,)
            sql+=" ORDER BY id DESC LIMIT 200"
            rows=self.q(sql,params)
            for i in self.bike_tree.get_children(): self.bike_tree.delete(i)
            for r in rows:
                st=kar_status(r["buy_date"]) if (not r["kar_paid"] and r["status"]=="Stock Ma") else None
                kar=st[0] if st else ("तिर्यो ✓" if r["kar_paid"] else "—")
                vals=[r["bike_no"],r["brand"],r["model"],r["status"],
                      f"{r['total_cost'] or 0:,.0f}",f"{r['sell_price'] or 0:,.0f}"]
                if self.is_owner: vals.append(f"{r['profit'] or 0:,.0f}")
                vals.append(kar)
                tag=("due",) if (st and st[1]<0) else (("ok",) if r["status"]=="Bechiyo" else ())
                self.bike_tree.insert("","end",values=vals,tags=tag,iid=str(r["id"]))
            stock=self.q("SELECT bike_no,brand,model FROM bikes WHERE status='Stock Ma' AND is_deleted=0 ORDER BY id DESC")
            opts=[f"{x['bike_no']} | {x['brand']} {x['model']}" for x in stock]
            self.sf["bike"]["values"]=opts
            if opts: self.sf["bike"].current(0)
            elif hasattr(self.sf["bike"],"set"): self.sf["bike"].set("")

        def _edit_bike(self):
            sel=self.bike_tree.selection()
            if not sel:
                messagebox.showwarning(" सम्पादन","पहिले Bike छान्नुस्",parent=self.root); return
            bid=int(sel[0]); r=self.q1("SELECT * FROM bikes WHERE id=?",(bid,))
            if not r: return
            win=tk.Toplevel(self.root); win.title(f"Bike सम्पादन — {r['bike_no']}")
            win.geometry("600x640"); win.configure(bg=T.BG0)
            c=GlassCard(win,pad=14,glow=.22); c.pack(fill="both",expand=True,padx=14,pady=14)
            card_title(c.body,f"✏ {r['bike_no']} सम्पादन","कर Paid गरेपछि Total Cost र Profit स्वतः अपडेट हुन्छ")
            form=tk.Frame(c.body,bg=glass_fill()); form.pack(fill="x",padx=4,pady=8)
            for i in range(4): form.columnconfigure(i,weight=1)
            ef={}
            ef["brand"]=combo(form,"Brand",list(BIKE_DATA),0,0); ef["brand"].set(r["brand"] or "")
            def mchanged(e=None):
                ef["model"]["values"]=BIKE_DATA.get(ef["brand"].get(),["Other - Manual Type Garnus"])
            ef["model"]=combo(form,"Model",BIKE_DATA.get(r["brand"],[]),0,1); ef["model"].set(r["model"] or "")
            ef["brand"].bind("<<ComboboxSelected>>",mchanged)
            ef["color"]=combo(form,"Color",COLOR_LIST,1,0); ef["color"].set(r["color"] or "")
            ef["year"]=combo(form,"Year",YEAR_LIST,1,1); ef["year"].set(r["year"] or "")
            ef["bike_no"]=field(form,"Bike No",2,0,22); ef["bike_no"].insert(0,r["bike_no"] or "")
            ef["buy_price"]=field(form,"खरिद मूल्य",2,1,22); ef["buy_price"].insert(0,str(r["buy_price"] or 0))
            ef["repair_cost"]=field(form,"मर्मत खर्च",3,0,22); ef["repair_cost"].insert(0,str(r["repair_cost"] or 0))
            ef["naam_sari"]=field(form,"नामसारी",3,1,22); ef["naam_sari"].insert(0,str(r["naam_sari"] or 0))
            ef["kar_cost"]=field(form,"कर रकम",4,0,22); ef["kar_cost"].insert(0,str(r["kar_cost"] or 0))
            kv=tk.IntVar(value=r["kar_paid"] or 0)
            tk.Checkbutton(form,text="✓ कर तिरिसकेको (Paid)",variable=kv,bg=glass_fill(),fg=T.TEXT,
                           selectcolor=T.INPUT,activebackground=glass_fill(),font=fnt(9,True)).grid(
                           row=4,column=2,columnspan=2,sticky="w",padx=8,pady=6)
            preview=tk.Label(c.body,text="",bg=glass_fill(),fg=T.GOLD,font=fnt(10,True))
            preview.pack(anchor="w",padx=8)
            def upd(e=None):
                try:
                    tc=calc_total_cost(parse_money(ef["buy_price"],"Buy"),parse_money(ef["repair_cost"],"Repair"),
                                       parse_money(ef["naam_sari"],"Naam"),parse_money(ef["kar_cost"],"Kar"),bool(kv.get()))
                    preview.config(text=f"नयाँ Total Cost: {CURRENCY} {tc:,.0f}")
                except Exception: preview.config(text="")
            for e in (ef["buy_price"],ef["repair_cost"],ef["naam_sari"],ef["kar_cost"]):
                e.bind("<KeyRelease>",upd)
            kv.trace_add("write",lambda *a:upd()); upd()
            def save():
                try:
                    fields={"brand":ef["brand"].get(),"model":ef["model"].get(),"color":ef["color"].get(),
                            "year":ef["year"].get(),"bike_no":ef["bike_no"].get().strip(),
                            "buy_price":parse_money(ef["buy_price"],"खरिद मूल्य"),
                            "repair_cost":parse_money(ef["repair_cost"],"मर्मत"),
                            "naam_sari":parse_money(ef["naam_sari"],"नामसारी"),
                            "kar_cost":parse_money(ef["kar_cost"],"कर"),"kar_paid":int(kv.get())}
                    if not fields["bike_no"]: raise ValueError("Bike नम्बर खाली हुन सक्दैन")
                    edit_bike(bid,fields,self.username)
                    Toast.show(self.root,"✅ Bike अपडेट भयो",T.GREEN)
                    win.destroy(); self.refresh_bike(); self.refresh_dash(); self.refresh_bills()
                except Exception as exc:
                    messagebox.showerror("सम्पादन त्रुटि",str(exc),parent=win)
            bfr=tk.Frame(c.body,bg=glass_fill()); bfr.pack(fill="x",pady=8)
            mk_btn(bfr,"💾 सेभ गर्नुहोस्",save,T.GREEN).pack(side="left",padx=6)
            mk_btn(bfr,"रद्द गर्नुहोस्",win.destroy,T.SIDE).pack(side="left",padx=6)
            c.sweep()

        def _del_bike(self):
            sel=self.bike_tree.selection()
            if not sel:
                messagebox.showwarning("डिलिट","पहिले Bike छान्नुस्",parent=self.root); return
            bid=int(sel[0]); r=self.q1("SELECT * FROM bikes WHERE id=?",(bid,))
            if not r: return
            extra="\n⚠ यो Bike बिकिभयो — सम्बन्धित बिल रहन्छ।" if r["status"]=="Bechiyo" else ""
            if messagebox.askyesno("सुरक्षित डिलिट",
                    f"'{r['bike_no']}' लाई हटाउने हो? डाटा स्थायी रूपमा मेटिँदैन (audit मा रहन्छ)।{extra}",
                    parent=self.root):
                try:
                    soft_delete("bikes",bid,self.username)
                    Toast.show(self.root,"🗑 Bike सूचीबाट हटाइयो (audit सहित)",T.RED)
                    self.refresh_bike(); self.refresh_dash()
                except Exception as exc:
                    messagebox.showerror("डिलिट त्रुटि",str(exc),parent=self.root)

        # ---------------- SAMAN / PLATE / REPAIR ----------------
        def build_saman(self):
            pg=tk.Frame(self.content,bg=blend(T.BG0,T.BG1,0.65)); self.pages["saman"]=pg
            sf=ScrollFrame(pg); sf.pack(fill="both",expand=True); pg.wheel=sf.wheel
            b=sf.body
            head=tk.Frame(b,bg=b["bg"]); head.pack(fill="x",padx=12,pady=(14,6))
            self.saman_seg=Seg(head,[("🛡 सामान","acc"),("🚗 नम्बर प्लेट","plate"),("🔧 मर्मत","repair")],
                               self._saman_tab)
            self.saman_seg.pack(side="left")
            self.saman_pages={}
            for key in ("acc","plate","repair"):
                f=tk.Frame(b,bg=b["bg"]); self.saman_pages[key]=f
            self._build_acc(); self._build_plate(); self._build_repair()
            for f in self.saman_pages.values(): f.pack_forget()
            self.saman_pages["acc"].pack(fill="both",expand=True)

        def _saman_tab(self,key):
            self.saman_key=key
            for k,f in self.saman_pages.items():
                if k==key: f.pack(fill="both",expand=True)
                else: f.pack_forget()
            getattr(self,"refresh_"+("acc" if key=="acc" else key),lambda:None)()

        def _build_acc(self):
            b=self.saman_pages["acc"]
            main=tk.Frame(b,bg=b["bg"]); main.pack(fill="both",expand=True,padx=12,pady=6)
            lf=tk.Frame(main,bg=b["bg"]); lf.configure(width=480); lf.pack(side="left",fill="y"); lf.pack_propagate(False)
            rf=tk.Frame(main,bg=b["bg"]); rf.pack(side="left",fill="both",expand=True)
            c=GlassCard(lf,pad=12,glow=.20); c.pack(fill="x",padx=6,pady=6)
            card_title(c.body,"🛡 हेल्मेट / सामान बिक्री","स्टक स्वतः घट्छ — बिल स्वतः बन्छ")
            f=tk.Frame(c.body,bg=glass_fill()); f.pack(fill="x",padx=4,pady=6)
            for i in range(4): f.columnconfigure(i,weight=1)
            self.acc={}
            self.acc["item"]=combo(f,"सामान",[],0,0)
            self.acc["qty"]=field(f,"संख्या",0,1,20); self.acc["qty"].insert(0,"1")
            self.acc["price"]=field(f,"मूल्य / पिस",1,0,20)
            self.acc["customer"]=field(f,"ग्राहक",1,1,20)
            self.acc["phone"]=field(f,"फोन",2,0,20)
            self.acc["payment"]=combo(f,"भुक्तानी",list(PAYMENT_METHODS),2,1)
            self.acc["payment"].current(0); self.acc["payment"].config(state="readonly")
            self.acc["paid"]=field(f,"पैसा पाइयो",3,0,20)
            self.acc_total=tk.Label(c.body,text="जम्मा: Rs. 0",bg=glass_fill(),fg=T.GOLD,font=fnt(10,True))
            self.acc_total.pack(anchor="w",padx=8)
            def prev(e=None):
                try:
                    q=int(self.acc["qty"].get() or 1); p=parse_money(self.acc["price"],"मूल्य")
                    self.acc_total.config(text=f"जम्मा: {CURRENCY} {q*p:,.0f}")
                except Exception: self.acc_total.config(text="जम्मा: Rs. 0")
            for w in (self.acc["qty"],self.acc["price"]): w.bind("<KeyRelease>",prev)
            self._acc_prev=prev
            self.acc["item"].bind("<<ComboboxSelected>>",lambda e:self._acc_price())
            mk_btn(c.body,"🧾 बिक्री गर",self._sell_accessory,T.ACCENT).pack(fill="x",padx=8,pady=(2,10))

            r=GlassCard(lf,pad=12,glow=.32); r.pack(fill="x",padx=6,pady=6)
            card_title(r.body,"📦 Restock / नयाँ सामान","ON CONFLICT DO UPDATE — पुरानो स्टक बढ्छ")
            f2=tk.Frame(r.body,bg=glass_fill()); f2.pack(fill="x",padx=4,pady=6)
            for i in range(4): f2.columnconfigure(i,weight=1)
            self.rst={}
            self.rst["name"]=combo(f2,"सामान नाम",[],0,0)
            self.rst["qty"]=field(f2,"थप मात्रा",0,1,20); self.rst["qty"].insert(0,"10")
            self.rst["buy"]=field(f2,"खरिद मूल्य",1,0,20)
            self.rst["sell"]=field(f2,"बिक्री मूल्य",1,1,20)
            mk_btn(r.body,"➕ Restock गर्नुहोस्",self._do_restock,T.GREEN).pack(fill="x",padx=8,pady=(2,10))

            rc=GlassCard(rf,pad=12,glow=.10); rc.pack(fill="both",expand=True,padx=6,pady=6)
            card_title(rc.body,"📋 स्टक र बिक्री","कम स्टक भएको सामान रातो देखिन्छ")
            bar=tk.Frame(rc.body,bg=glass_fill()); bar.pack(fill="x",padx=4,pady=4)
            mk_btn(bar,"🔄 रिफ्रेस",self.refresh_acc,T.SIDE).pack(side="left",padx=4)
            self.stock_tree=make_tree(rc.body,[("name",190),("category",110),("stock",80),("buy",100),("sell",100)],height=6)
            self.stock_tree.pack(fill="x",padx=4,pady=4)
            tk.Label(rc.body,text="— हालैको बिक्री —",bg=glass_fill(),fg=T.MUTED,font=fnt(9,True)).pack(anchor="w",padx=8,pady=(8,0))
            self.acc_tree=make_tree(rc.body,[("bill",100),("item",180),("qty",60),("total",100),
                                             ("customer",120),("payment",90)],height=8)
            self.acc_tree.pack(fill="both",expand=True,padx=4,pady=4)

        def _acc_price(self):
            raw=self.acc["item"].get().split(" (स्टक")[0].strip()
            r=self.q1("SELECT sell_price FROM accessories WHERE name=?",(raw,))
            if r:
                self.acc["price"].delete(0,"end"); self.acc["price"].insert(0,str(r["sell_price"]))
                if hasattr(self,"_acc_prev"): self._acc_prev()

        def refresh_acc(self):
            if not hasattr(self,"stock_tree"): return
            for i in self.stock_tree.get_children(): self.stock_tree.delete(i)
            for r in self.q("SELECT * FROM accessories ORDER BY stock ASC,name"):
                tag=("due",) if r["stock"]<=2 else (("ok",) if r["stock"]>10 else ())
                self.stock_tree.insert("","end",values=(r["name"],r["category"],r["stock"],
                    f"{r['buy_price']:,.0f}",f"{r['sell_price']:,.0f}"),tags=tag)
            opts=[f"{r['name']} (स्टक {r['stock']})" for r in self.q("SELECT name,stock FROM accessories WHERE stock>0 ORDER BY name")]
            self.acc["item"]["values"]=opts
            if opts: self.acc["item"].current(0); self._acc_price()
            for i in self.acc_tree.get_children(): self.acc_tree.delete(i)
            for r in self.q("SELECT * FROM accessory_sales WHERE is_deleted=0 ORDER BY id DESC LIMIT 200"):
                self.acc_tree.insert("","end",values=(r["bill_no"],r["item"],r["qty"],
                    f"{r['total']:,.0f}",r["customer"],r["payment"]),iid=str(r["id"]))
            names=[r["name"] for r in self.q("SELECT name FROM accessories ORDER BY name")]
            self.rst["name"]["values"]=names

        def _sell_accessory(self):
            try:
                raw=self.acc["item"].get().strip()
                name=raw.split(" (स्टक")[0].strip()
                if not name: raise ValueError("सामान छान्नुस्")
                qty=int(self.acc["qty"].get() or 0)
                if qty<=0: raise ValueError("संख्या १ भन्दा माथि हाल्नुस्")
                price=parse_money(self.acc["price"],"मूल्य")
                customer=self.acc["customer"].get().strip(); phone=self.acc["phone"].get().strip()
                if not customer: raise ValueError("ग्राहक नाम हाल्नुस्")
                if not is_valid_phone(phone): raise ValueError("फोन १० अंकको हुनुपर्छ")
                total=qty*price; paid=parse_money(self.acc["paid"],"पैसा पाइयो")
                validate_payment(total,paid,"Paid")           # FIX 2 (accessory पनि सुरक्षित)
                due=calc_due(total,paid); payment=self.acc["payment"].get() or "Cash"
                with DB.transaction() as con:
                    a=con.execute("SELECT * FROM accessories WHERE name=?",(name,)).fetchone()
                    if not a: raise ValueError("सामान भेटिएन")
                    if a["stock"]<qty: raise ValueError(f"स्टक अपर्याप्त — मात्र {a['stock']} छ")
                    con.execute("UPDATE accessories SET stock=stock-? WHERE name=?",(qty,name))
                    bno=_create_bill(con,"HELMET",customer,phone,f"{name} x {qty}",total,paid,due,payment)
                    con.execute("INSERT INTO accessory_sales(item,qty,price,total,customer,phone,payment,date,bill_no) "
                                "VALUES(?,?,?,?,?,?,?,?,?)",(name,qty,price,total,customer,phone,payment,
                                datetime.now().strftime("%Y-%m-%d"),bno))
                    if due>0: _ledger_due(con,customer,phone,"उधारो",f"सामान बिक्री {bno}",due,bno)
                    _cash(con,f"सामान बिक्री: {name} x{qty} ({bno})",paid,0,"Accessory Sale")
                    _audit(con,self.username,"SELL_ACC",f"{bno} {name} x{qty}")
                txt=make_bill_text("सामान बिक्री बिल",[f"सामान: {name}",f"मात्रा: {qty}  |  दर: {CURRENCY}{price:,.0f}"],
                                   customer=customer,phone=phone,total=total,paid=paid,due=due,
                                   payment=payment,bill_no=bno)
                show_bill(txt,bno)
                Toast.show(self.root,"✅ सामान बिक्री भयो",T.GREEN)
                self.refresh_acc(); self.refresh_dash(); self.refresh_bills()
            except Exception as exc:
                messagebox.showerror("बिक्री त्रुटि",str(exc),parent=self.root)

        def _do_restock(self):
            try:
                name=self.rst["name"].get().strip()
                if not name: raise ValueError("सामान नाम हाल्नुस्")
                qty=int(self.rst["qty"].get() or 0)
                buy=parse_money(self.rst["buy"],"खरिद मूल्य")
                sell=parse_money(self.rst["sell"],"बिक्री मूल्य")
                restock_accessory(name,qty,buy,sell,self.username)   # FIX 4
                Toast.show(self.root,f"✅ {name} मा {qty} थपियो",T.GREEN)
                self.refresh_acc(); self.refresh_dash()
            except Exception as exc:
                messagebox.showerror("Restock त्रुटि",str(exc),parent=self.root)

        def refresh_saman(self):
            key=getattr(self,"saman_key","acc")
            getattr(self,"refresh_"+key,lambda:None)()

        def _build_plate(self):
            b=self.saman_pages["plate"]
            main=tk.Frame(b,bg=b["bg"]); main.pack(fill="both",expand=True,padx=12,pady=6)
            lf=tk.Frame(main,bg=b["bg"]); lf.configure(width=480); lf.pack(side="left",fill="y"); lf.pack_propagate(False)
            rf=tk.Frame(main,bg=b["bg"]); rf.pack(side="left",fill="both",expand=True)
            c=GlassCard(lf,pad=12,glow=.22); c.pack(fill="x",padx=6,pady=6)
            card_title(c.body,"🚗 नम्बर प्लेट आवेदन","पैसा बढी लिएमा रोकिन्छ")
            f=tk.Frame(c.body,bg=glass_fill()); f.pack(fill="x",padx=4,pady=6)
            for i in range(4): f.columnconfigure(i,weight=1)
            self.plt={}
            self.plt["customer"]=field(f,"ग्राहक नाम",0,0,20)
            self.plt["phone"]=field(f,"फोन",0,1,20)
            self.plt["bike_no"]=field(f,"Bike No",1,0,20)
            self.plt["type"]=combo(f,"प्लेट प्रकार",["New Registration","Re-registration","Name Transfer","Duplicate","Other"],1,1)
            self.plt["type"].current(0)
            self.plt["charge"]=field(f,"शुल्क",2,0,20)
            self.plt["paid"]=field(f,"पैसा पाइयो",2,1,20)
            self.plt["payment"]=combo(f,"भुक्तानी",list(PAYMENT_METHODS),3,0)
            self.plt["payment"].current(0); self.plt["payment"].config(state="readonly")
            self.plt["status"]=combo(f,"स्थिति",["Pending","Processing","Done"],3,1)
            self.plt["status"].current(0)
            mk_btn(c.body,"🧾 आवेदन + बिल",self._sell_plate,T.ACCENT).pack(fill="x",padx=8,pady=(2,10))
            rc=GlassCard(rf,pad=12,glow=.10); rc.pack(fill="both",expand=True,padx=6,pady=6)
            card_title(rc.body,"📋 प्लेट रेकर्ड")
            bar=tk.Frame(rc.body,bg=glass_fill()); bar.pack(fill="x",padx=4,pady=4)
            mk_btn(bar,"🔄 रिफ्रेस",self.refresh_plate,T.SIDE).pack(side="left",padx=4)
            self.plate_tree=make_tree(rc.body,[("bill",100),("customer",130),("bike",110),("type",150),
                                               ("charge",100),("paid",100),("status",100)],height=14)
            self.plate_tree.pack(fill="both",expand=True,padx=4,pady=4)

        def refresh_plate(self):
            if not hasattr(self,"plate_tree"): return
            for i in self.plate_tree.get_children(): self.plate_tree.delete(i)
            for r in self.q("SELECT * FROM plates WHERE is_deleted=0 ORDER BY id DESC LIMIT 200"):
                tag=("due",) if (r["due"] or 0)>0 else (("ok",) if r["status"]=="Done" else ())
                self.plate_tree.insert("","end",values=(r["bill_no"],r["customer"],r["bike_no"],
                    r["plate_type"],f"{r['charge']:,.0f}",f"{r['paid']:,.0f}",r["status"]),
                    tags=tag,iid=str(r["id"]))

        def _sell_plate(self):
            try:
                f=self.plt
                customer=f["customer"].get().strip(); phone=f["phone"].get().strip()
                if not customer: raise ValueError("ग्राहक नाम हाल्नुस्")
                if not is_valid_phone(phone): raise ValueError("फोन १० अंकको हुनुपर्छ")
                charge=parse_money(f["charge"],"शुल्क"); paid=parse_money(f["paid"],"पैसा पाइयो")
                validate_payment(charge,paid,"Paid")               # FIX 2
                due=calc_due(charge,paid); payment=f["payment"].get() or "Cash"
                bike=f["bike_no"].get().strip(); ptype=f["type"].get(); status=f["status"].get()
                lines=[f"सेवा: {ptype}",f"Bike No: {bike or '-'}"]
                with DB.transaction() as con:
                    bno=_create_bill(con,"PLATE",customer,phone,f"{ptype} | {bike}",charge,paid,due,payment)
                    con.execute("INSERT INTO plates(customer,phone,bike_no,plate_type,charge,paid,due,status,date,bill_no) "
                                "VALUES(?,?,?,?,?,?,?,?,?,?)",(customer,phone,bike,ptype,charge,paid,due,status,
                                datetime.now().strftime("%Y-%m-%d"),bno))
                    if due>0: _ledger_due(con,customer,phone,"उधारो",f"प्लेट {bno}",due,bno)
                    _cash(con,f"प्लेट शुल्क: {customer} ({bno})",paid,0,"Plate Service")
                    _audit(con,self.username,"PLATE_BILL",f"{bno} {charge:,.0f}")
                show_bill(make_bill_text("नम्बर प्लेट बिल",lines,customer=customer,phone=phone,
                          total=charge,paid=paid,due=due,payment=payment,bill_no=bno),bno)
                for k in ("customer","phone","bike_no","charge","paid"): f[k].delete(0,"end")
                Toast.show(self.root,"✅ प्लेट बिल भयो",T.GREEN)
                self.refresh_plate(); self.refresh_dash(); self.refresh_bills()
            except Exception as exc:
                messagebox.showerror("प्लेट त्रुटि",str(exc),parent=self.root)

        def _build_repair(self):
            b=self.saman_pages["repair"]
            main=tk.Frame(b,bg=b["bg"]); main.pack(fill="both",expand=True,padx=12,pady=6)
            lf=tk.Frame(main,bg=b["bg"]); lf.configure(width=480); lf.pack(side="left",fill="y"); lf.pack_propagate(False)
            rf=tk.Frame(main,bg=b["bg"]); rf.pack(side="left",fill="both",expand=True)
            c=GlassCard(lf,pad=12,glow=.26); c.pack(fill="x",padx=6,pady=6)
            card_title(c.body,"🔧 मर्मत / Repair","पार्ट्स + लेबर = जम्मा")
            f=tk.Frame(c.body,bg=glass_fill()); f.pack(fill="x",padx=4,pady=6)
            for i in range(4): f.columnconfigure(i,weight=1)
            self.rep={}
            self.rep["customer"]=field(f,"ग्राहक नाम",0,0,20)
            self.rep["phone"]=field(f,"फोन",0,1,20)
            self.rep["bike_no"]=field(f,"Bike No",1,0,20)
            self.rep["model"]=field(f,"Bike Model",1,1,20)
            self.rep["problem"]=field(f,"समस्या",2,0,20); f.columnconfigure(4,weight=1)
            self.rep["problem"].grid(columnspan=3,sticky="ew",padx=8,pady=6)
            self.rep["parts"]=field(f,"पार्ट्स खर्च",3,0,20)
            self.rep["labour"]=field(f,"लेबर खर्च",3,1,20)
            self.rep["paid"]=field(f,"पैसा पाइयो",4,0,20)
            self.rep["payment"]=combo(f,"भुक्तानी",list(PAYMENT_METHODS),4,1)
            self.rep["payment"].current(0); self.rep["payment"].config(state="readonly")
            self.rep["status"]=combo(f,"स्थिति",["Pending","In Progress","Done"],5,0)
            self.rep["status"].current(0)
            self.rep_total=tk.Label(c.body,text="जम्मा: Rs. 0",bg=glass_fill(),fg=T.GOLD,font=fnt(10,True))
            self.rep_total.pack(anchor="w",padx=8)
            def prev(e=None):
                try:
                    t=calc_repair_total(parse_money(self.rep["parts"],"पार्ट्स"),parse_money(self.rep["labour"],"लेबर"))
                    self.rep_total.config(text=f"जम्मा: {CURRENCY} {t:,.0f}")
                except Exception: self.rep_total.config(text="जम्मा: Rs. 0")
            for w in (self.rep["parts"],self.rep["labour"]): w.bind("<KeyRelease>",prev)
            prev()
            mk_btn(c.body,"🧾 मर्मत बिल",self._do_repair,T.ACCENT).pack(fill="x",padx=8,pady=(2,10))
            rc=GlassCard(rf,pad=12,glow=.10); rc.pack(fill="both",expand=True,padx=6,pady=6)
            card_title(rc.body,"📋 मर्मत रेकर्ड")
            bar=tk.Frame(rc.body,bg=glass_fill()); bar.pack(fill="x",padx=4,pady=4)
            mk_btn(bar,"🔄 रिफ्रेस",self.refresh_repair,T.SIDE).pack(side="left",padx=4)
            self.repair_tree=make_tree(rc.body,[("bill",100),("customer",130),("bike",110),("problem",170),
                                                ("total",100),("paid",100),("status",100)],height=14)
            self.repair_tree.pack(fill="both",expand=True,padx=4,pady=4)

        def refresh_repair(self):
            if not hasattr(self,"repair_tree"): return
            for i in self.repair_tree.get_children(): self.repair_tree.delete(i)
            for r in self.q("SELECT * FROM repairs WHERE is_deleted=0 ORDER BY id DESC LIMIT 200"):
                tag=("due",) if (r["due"] or 0)>0 else (("ok",) if r["status"]=="Done" else ())
                self.repair_tree.insert("","end",values=(r["bill_no"],r["customer"],r["bike_no"],r["problem"],
                    f"{r['total']:,.0f}",f"{r['paid']:,.0f}",r["status"]),tags=tag,iid=str(r["id"]))

        def _do_repair(self):
            try:
                f=self.rep
                customer=f["customer"].get().strip(); phone=f["phone"].get().strip()
                if not customer: raise ValueError("ग्राहक नाम हाल्नुस्")
                if not is_valid_phone(phone): raise ValueError("फोन १० अंकको हुनुपर्छ")
                parts=parse_money(f["parts"],"पार्ट्स खर्च"); labour=parse_money(f["labour"],"लेबर खर्च")
                total=calc_repair_total(parts,labour)
                paid=parse_money(f["paid"],"पैसा पाइयो")
                validate_payment(total,paid,"Paid")                 # FIX 2
                due=calc_due(total,paid); payment=f["payment"].get() or "Cash"
                bike=f["bike_no"].get().strip(); model=f["model"].get().strip()
                problem=f["problem"].get().strip(); status=f["status"].get()
                lines=[f"समस्या: {problem or '-'}",f"Bike: {model}  |  {bike}",
                       f"Parts: {CURRENCY}{parts:,.0f}   Labour: {CURRENCY}{labour:,.0f}"]
                with DB.transaction() as con:
                    bno=_create_bill(con,"REPAIR",customer,phone,f"Repair | {bike} | {model}",total,paid,due,payment)
                    con.execute("INSERT INTO repairs(customer,phone,bike_no,bike_model,problem,parts_cost,labour,"
                                "total,paid,due,status,date,bill_no) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                (customer,phone,bike,model,problem,parts,labour,total,paid,due,status,
                                 datetime.now().strftime("%Y-%m-%d"),bno))
                    if due>0: _ledger_due(con,customer,phone,"उधारो",f"मर्मत {bno}",due,bno)
                    _cash(con,f"मर्मत: {customer} ({bno})",paid,0,"Repair Service")
                    _audit(con,self.username,"REPAIR_BILL",f"{bno} {total:,.0f}")
                show_bill(make_bill_text("मर्मत बिल",lines,customer=customer,phone=phone,total=total,
                          paid=paid,due=due,payment=payment,bill_no=bno),bno)
                for k in ("customer","phone","bike_no","model","problem","parts","labour","paid"):
                    f[k].delete(0,"end")
                Toast.show(self.root,"✅ मर्मत बिल भयो",T.GREEN)
                self.refresh_repair(); self.refresh_dash(); self.refresh_bills()
            except Exception as exc:
                messagebox.showerror("मर्मत त्रुटि",str(exc),parent=self.root)

        # ---------------- HISAB ----------------
        def build_hisab(self):
            pg=tk.Frame(self.content,bg=blend(T.BG0,T.BG1,0.65)); self.pages["hisab"]=pg
            sf=ScrollFrame(pg); sf.pack(fill="both",expand=True); pg.wheel=sf.wheel
            b=sf.body
            head=tk.Frame(b,bg=b["bg"]); head.pack(fill="x",padx=12,pady=(14,6))
            self.hisab_seg=Seg(head,[("उधारो लेजर","ledger"),("क्यासबुक","cash"),("आय / खर्च","entry")],
                               self._hisab_tab)
            self.hisab_seg.pack(side="left")
            self.hisab_pages={}
            for k in ("ledger","cash","entry"):
                f=tk.Frame(b,bg=b["bg"]); self.hisab_pages[k]=f
            self._build_ledger(); self._build_cash(); self._build_entry()
            for f in self.hisab_pages.values(): f.pack_forget()
            self.hisab_pages["ledger"].pack(fill="both",expand=True)

        def _hisab_tab(self,key):
            self.hisab_key=key
            for k,f in self.hisab_pages.items():
                if k==key: f.pack(fill="both",expand=True)
                else: f.pack_forget()
            getattr(self,"refresh_"+key,lambda:None)()

        def _build_ledger(self):
            b=self.hisab_pages["ledger"]
            main=tk.Frame(b,bg=b["bg"]); main.pack(fill="both",expand=True,padx=12,pady=6)
            lf=tk.Frame(main,bg=b["bg"]); lf.configure(width=440); lf.pack(side="left",fill="y"); lf.pack_propagate(False)
            rf=tk.Frame(main,bg=b["bg"]); rf.pack(side="left",fill="both",expand=True)
            c=GlassCard(lf,pad=12,glow=.30); c.pack(fill="x",padx=6,pady=6)
            card_title(c.body,"💰 उधारो असुल","बिलको बाँकी रकम घट्छ — bell सही हुन्छ")
            f=tk.Frame(c.body,bg=glass_fill()); f.pack(fill="x",padx=4,pady=6)
            for i in range(4): f.columnconfigure(i,weight=1)
            self.rcv={}
            self.rcv["bill"]=combo(f,"बाँकी बिल",[],0,0)
            self.rcv["amount"]=field(f,"असुल रकम",1,0,20)
            self.rcv["payment"]=combo(f,"भुक्तानी विधि",list(PAYMENT_METHODS),2,0)
            self.rcv["payment"].current(0); self.rcv["payment"].config(state="readonly")
            self.rcv["note"]=field(f,"नोट (वैकल्पिक)",1,1,20)
            self.rcv_info=tk.Label(c.body,text="बिल छान्नुस्",bg=glass_fill(),fg=T.MUTED,font=fnt(9))
            self.rcv_info.pack(anchor="w",padx=8)
            self.rcv["bill"].bind("<<ComboboxSelected>>",lambda e:self._rcv_info())
            mk_btn(c.body,"✓ असुल गर",self._receive,T.GREEN).pack(fill="x",padx=8,pady=(2,10))
            s=GlassCard(lf,pad=12); s.pack(fill="x",padx=6,pady=6)
            card_title(s.body,"सारांश")
            self.led_summary=tk.Label(s.body,text="",bg=glass_fill(),fg=T.TEXT,font=fnt(10,True),
                                      justify="left")
            self.led_summary.pack(anchor="w",padx=8,pady=6)
            rc=GlassCard(rf,pad=12,glow=.10); rc.pack(fill="both",expand=True,padx=6,pady=6)
            card_title(rc.body,"📒 लेजर"," running balance सही रूपमा देखाइन्छ")
            bar=tk.Frame(rc.body,bg=glass_fill()); bar.pack(fill="x",padx=4,pady=4)
            mk_btn(bar,"🔄 रिफ्रेस",self.refresh_ledger,T.SIDE).pack(side="left",padx=4)
            self.ledger_tree=make_tree(rc.body,[("date",95),("name",140),("type",120),
                 ("desc",210),("udharo",100),("tiryo",100),("balance",110)],height=15)
            self.ledger_tree.pack(fill="both",expand=True,padx=4,pady=4)

        def _rcv_info(self):
            raw=self.rcv["bill"].get().strip()
            if not raw: return
            r=self.q1("SELECT customer,due FROM bills WHERE bill_no=?",(raw,))
            if r:
                self.rcv_info.config(text=f"{r['customer']} — बाँकी {CURRENCY}{r['due']:,.0f}",fg=T.GOLD)
                self.rcv["amount"].delete(0,"end"); self.rcv["amount"].insert(0,str(r["due"]))

        def refresh_ledger(self):
            if not hasattr(self,"ledger_tree"): return
            for i in self.ledger_tree.get_children(): self.ledger_tree.delete(i)
            for r in self.q("SELECT * FROM ledger ORDER BY id DESC LIMIT 200"):
                tag=("due",) if (r["balance"] or 0)>0 else ("ok",)
                self.ledger_tree.insert("","end",values=(r["date"],r["name"],r["type"],r["description"],
                    f"{r['udharo']:,.0f}",f"{r['tiryo']:,.0f}",f"{r['balance']:,.0f}"),tags=tag)
            opts=[r["bill_no"] for r in self.q("SELECT bill_no FROM bills WHERE due>0 AND is_deleted=0 ORDER BY id DESC")]
            self.rcv["bill"]["values"]=opts
            if opts: self.rcv["bill"].current(0); self._rcv_info()
            udh=self.val("SELECT COALESCE(SUM(udharo),0) FROM ledger")
            tir=self.val("SELECT COALESCE(SUM(tiryo),0) FROM ledger")
            self.led_summary.config(text=f"कुल उधारो: {CURRENCY}{udh:,.0f}\nकुल असुल: {CURRENCY}{tir:,.0f}\n"
                                         f"बाँकी: {CURRENCY}{udh-tir:,.0f}")

        def _receive(self):
            try:
                bno=self.rcv["bill"].get().strip()
                if not bno: raise ValueError("बिल छान्नुस्")
                amt=parse_money(self.rcv["amount"],"असुल रकम")
                note=self.rcv["note"].get().strip()
                payment=self.rcv["payment"].get() or "Cash"
                new_due=receive_payment(bno,amt,self.username,note,payment=payment)   # FIX 5
                Toast.show(self.root,f"✅ {CURRENCY}{amt:,.0f} असुल भयो — बाँकी {CURRENCY}{new_due:,.0f}",T.GREEN)
                self.rcv["note"].delete(0,"end")
                self.refresh_ledger(); self.refresh_cash(); self.refresh_bills()
                self.refresh_dash(); self.refresh_hisab()
            except Exception as exc:
                messagebox.showerror("असुल त्रुटि",str(exc),parent=self.root)

        def _build_cash(self):
            b=self.hisab_pages["cash"]
            main=tk.Frame(b,bg=b["bg"]); main.pack(fill="both",expand=True,padx=12,pady=6)
            c=GlassCard(main,pad=14,glow=.16); c.pack(fill="both",expand=True,padx=6,pady=6)
            card_title(c.body,"💵 क्यासबुक","सबै आय / व्यय एकै ठाउँ")
            bar=tk.Frame(c.body,bg=glass_fill()); bar.pack(fill="x",padx=4,pady=4)
            mk_btn(bar,"🔄 रिफ्रेस",self.refresh_cash,T.SIDE).pack(side="left",padx=4)
            self.cash_sum=tk.Label(bar,text="",bg=glass_fill(),fg=T.TEXT,font=fnt(9,True))
            self.cash_sum.pack(side="right",padx=8)
            self.cash_tree=make_tree(c.body,[("date",150),("desc",280),("category",150),
                 ("income",120),("expense",120)],height=16)
            self.cash_tree.pack(fill="both",expand=True,padx=4,pady=4)

        def refresh_cash(self):
            if not hasattr(self,"cash_tree"): return
            for i in self.cash_tree.get_children(): self.cash_tree.delete(i)
            for r in self.q("SELECT * FROM cashbook ORDER BY id DESC LIMIT 250"):
                self.cash_tree.insert("","end",values=(r["date"],r["description"],r["category"],
                    f"{r['income']:,.0f}",f"{r['expense']:,.0f}"),
                    tags=("ok",) if r["income"]>0 else ())
            inc=self.val("SELECT COALESCE(SUM(income),0) FROM cashbook")
            exp=self.val("SELECT COALESCE(SUM(expense),0) FROM cashbook")
            self.cash_sum.config(text=f"आय {CURRENCY}{inc:,.0f}   |   व्यय {CURRENCY}{exp:,.0f}   |   बाँकी {CURRENCY}{inc-exp:,.0f}")

        def _build_entry(self):
            b=self.hisab_pages["entry"]
            main=tk.Frame(b,bg=b["bg"]); main.pack(fill="both",expand=True,padx=12,pady=6)
            c=GlassCard(main,pad=14,glow=.20); c.pack(fill="x",padx=6,pady=6)
            card_title(c.body,"➕ नयाँ आय / खर्च","क्यासबुकमा तुरुन्त देखिन्छ")
            f=tk.Frame(c.body,bg=glass_fill()); f.pack(fill="x",padx=4,pady=8)
            for i in range(4): f.columnconfigure(i,weight=1)
            self.cen={}
            self.cen["desc"]=field(f,"विवरण",0,0,24)
            self.cen["amount"]=field(f,"रकम",0,1,24)
            self.cen["category"]=combo(f,"श्रेणी",["General","Bike Purchase","Repair","Name Transfer",
                 "Tax","Accessories Purchase","Office","Other"],1,0)
            self.cen["kind"]=combo(f,"प्रकार",["खर्च (Expense)","आय (Income)"],1,1)
            self.cen["kind"].current(0); self.cen["category"].current(0)
            mk_btn(c.body,"💾 सेभ गर्नुहोस्",self._add_cash_entry,T.GREEN).pack(fill="x",padx=8,pady=(2,10))

        def _add_cash_entry(self):
            try:
                desc=self.cen["desc"].get().strip()
                amt=parse_money(self.cen["amount"],"रकम")
                if not desc: raise ValueError("विवरण हाल्नुस्")
                if amt<=0: raise ValueError("रकम 0 भन्दा माथि हाल्नुस्")
                income=amt if self.cen["kind"].get().startswith("आय") else 0
                expense=0 if income else amt
                add_cash(desc,income,expense,self.cen["category"].get(),DB)
                Toast.show(self.root,"✅ क्यासबुक अपडेट भयो",T.GREEN)
                self.cen["desc"].delete(0,"end"); self.cen["amount"].delete(0,"end")
                self.refresh_cash(); self.refresh_dash()
            except Exception as exc:
                messagebox.showerror("त्रुटि",str(exc),parent=self.root)

        def refresh_hisab(self):
            key=getattr(self,"hisab_key","ledger")
            getattr(self,"refresh_"+key,lambda:None)()

        # ---------------- BILL CENTER ----------------
        def build_bills(self):
            pg=tk.Frame(self.content,bg=blend(T.BG0,T.BG1,0.65)); self.pages["bills"]=pg
            b=pg
            head=tk.Frame(b,bg=b["bg"]); head.pack(fill="x",padx=12,pady=(14,6))
            self.bill_seg=Seg(head,[("सबै","all"),("बाँकी छ","due"),("आज","today")],self._bill_filter)
            self.bill_seg.pack(side="left")
            self.bill_filter_key="all"
            self.bill_search=tk.Entry(head,width=26,font=fnt(10),bg=T.INPUT,fg=T.TEXT,
                                      relief="flat",insertbackground=T.TEXT)
            self.bill_search.pack(side="right",padx=6,ipady=6)
            self.bill_search.bind("<KeyRelease>",lambda e:self.refresh_bills())
            mk_btn(head,"🔍",self.refresh_bills,T.PURPLE).pack(side="right",padx=4)
            c=GlassCard(b,pad=14,glow=.18); c.pack(fill="both",expand=True,padx=12,pady=6)
            card_title(c.body,"🧾 बिल केन्द्र","Reprint • सम्पादन • सुरक्षित डिलिट • उधारो असुल")
            bar=tk.Frame(c.body,bg=glass_fill()); bar.pack(fill="x",padx=4,pady=4)
            mk_btn(bar,"🖨 Reprint",self._reprint_bill,T.ACCENT).pack(side="left",padx=4)
            mk_btn(bar,"✏ सम्पादन",self._edit_bill_dlg,T.BLUE).pack(side="left",padx=4)
            mk_btn(bar,"💰 उधारो असुल",self._bill_receive,T.GREEN).pack(side="left",padx=4)
            mk_btn(bar,"🗑 डिलिट",self._del_bill,T.RED).pack(side="left",padx=4)
            mk_btn(bar,"🔄 रिफ्रेस",self.refresh_bills,T.SIDE).pack(side="left",padx=4)
            self.bill_tree=make_tree(c.body,[("bill",105),("type",85),("customer",140),("phone",120),
                 ("total",105),("paid",105),("due",105),("payment",90),("date",150)],height=17)
            self.bill_tree.pack(fill="both",expand=True,padx=4,pady=4)
            self.bill_tree.bind("<Double-1>",lambda e:self._reprint_bill())

        def _bill_filter(self,key):
            self.bill_filter_key=key; self.refresh_bills()

        def refresh_bills(self):
            if not hasattr(self,"bill_tree"): return
            sql="SELECT * FROM bills WHERE is_deleted=0"; params=[]
            f=getattr(self,"bill_filter_key","all")
            if f=="due": sql+=" AND due>0"
            elif f=="today": sql+=" AND date(created_at)=date('now')"
            s=self.bill_search.get().strip() if hasattr(self,"bill_search") else ""
            if s:
                sql+=" AND (bill_no LIKE ? OR customer LIKE ? OR phone LIKE ?)"
                params += [f"%{s}%"]*3
            sql+=" ORDER BY id DESC LIMIT 200"
            for i in self.bill_tree.get_children(): self.bill_tree.delete(i)
            for r in self.q(sql,tuple(params)):
                self.bill_tree.insert("","end",values=(r["bill_no"],r["bill_type"],r["customer"],r["phone"],
                    f"{r['total']:,.0f}",f"{r['paid']:,.0f}",f"{r['due']:,.0f}",r["payment"],
                    r["created_at"]),tags=("due",) if (r["due"] or 0)>0 else ("ok",),iid=str(r["id"]))

        def _bill_row(self):
            sel=self.bill_tree.selection()
            if not sel:
                messagebox.showwarning("बिल","पहिले बिल छान्नुस्",parent=self.root); return None
            r=self.q1("SELECT * FROM bills WHERE id=?",(int(sel[0]),))
            if not r:
                messagebox.showwarning("बिल","बिल भेटिएन",parent=self.root)
            return r

        def _reprint_bill(self):
            r=self._bill_row()
            if not r: return
            lines=[f"विवरण: {r['detail'] or '-'}"]
            try:
                txt=make_bill_text(f"{r['bill_type']} बिल",lines,customer=r["customer"],phone=r["phone"],
                    total=r["total"],paid=r["paid"],due=r["due"],payment=r["payment"] or "Cash",
                    bill_no=r["bill_no"],bill_date=r["created_at"])
                show_bill(txt,r["bill_no"])
            except Exception as exc:
                messagebox.showerror("Reprint त्रुटि",str(exc),parent=self.root)

        def _edit_bill_dlg(self):
            r=self._bill_row()
            if not r: return
            win=tk.Toplevel(self.root); win.title(f"बिल सम्पादन — {r['bill_no']}")
            win.geometry("520x400"); win.configure(bg=T.BG0)
            c=GlassCard(win,pad=14,glow=.22); c.pack(fill="both",expand=True,padx=14,pady=14)
            card_title(c.body,f"✏ {r['bill_no']}","चुक्ता रकम total भन्दा बढी हुन सक्दैन")
            f=tk.Frame(c.body,bg=glass_fill()); f.pack(fill="x",padx=4,pady=10)
            for i in range(4): f.columnconfigure(i,weight=1)
            ef={}
            ef["customer"]=field(f,"ग्राहक",0,0,22); ef["customer"].insert(0,r["customer"] or "")
            ef["phone"]=field(f,"फोन",0,1,22); ef["phone"].insert(0,r["phone"] or "")
            ef["total"]=field(f,"जम्मा",1,0,22); ef["total"].insert(0,str(r["total"]))
            ef["paid"]=field(f,"चुक्ता",1,1,22); ef["paid"].insert(0,str(r["paid"]))
            lab=tk.Label(c.body,text="",bg=glass_fill(),fg=T.GOLD,font=fnt(10,True)); lab.pack(anchor="w",padx=8)
            def prev(e=None):
                try: lab.config(text=f"बाँकी: {CURRENCY}{calc_due(parse_money(ef['total'],'Total'),parse_money(ef['paid'],'Paid')):,.0f}")
                except Exception: lab.config(text="")
            for w in (ef["total"],ef["paid"]): w.bind("<KeyRelease>",prev)
            prev()
            def save():
                try:
                    edit_bill(r["bill_no"],ef["customer"].get().strip(),ef["phone"].get().strip(),
                              parse_money(ef["total"],"जम्मा"),parse_money(ef["paid"],"चुक्ता"),self.username)
                    Toast.show(self.root,"✅ बिल अपडेट भयो",T.GREEN)
                    win.destroy(); self.refresh_bills(); self.refresh_dash(); self.refresh_bike()
                    self.refresh_hisab()
                except Exception as exc:
                    messagebox.showerror("सम्पादन त्रुटि",str(exc),parent=win)
            bfr=tk.Frame(c.body,bg=glass_fill()); bfr.pack(fill="x",pady=8)
            mk_btn(bfr,"💾 सेभ",save,T.GREEN).pack(side="left",padx=6)
            mk_btn(bfr,"रद्द",win.destroy,T.SIDE).pack(side="left",padx=6)
            c.sweep()

        def _bill_receive(self):
            r=self._bill_row()
            if not r: return
            if (r["due"] or 0)<=0:
                messagebox.showinfo("बिल","यो बिल चुक्ता भइसकेको छ",parent=self.root); return
            win=tk.Toplevel(self.root); win.title(f"उधारो असुल — {r['bill_no']}")
            win.geometry("480x340"); win.configure(bg=T.BG0)
            c=GlassCard(win,pad=14,glow=.28); c.pack(fill="both",expand=True,padx=14,pady=14)
            card_title(c.body,f"💰 {r['customer']}",f"बाँकी {CURRENCY}{r['due']:,.0f}")
            f=tk.Frame(c.body,bg=glass_fill()); f.pack(fill="x",padx=4,pady=8)
            amt=field(f,"रकम",0,0,20); amt.insert(0,str(r["due"]))
            pay=combo(f,"भुक्तानी विधि",list(PAYMENT_METHODS),1,0); pay.current(0); pay.config(state="readonly")
            note=field(f,"नोट",2,0,20)
            def go():
                try:
                    nd=receive_payment(r["bill_no"],parse_money(amt,"रकम"),self.username,
                                       note.get().strip(),payment=pay.get() or "Cash")
                    Toast.show(self.root,f"✅ असुल भयो — नयाँ बाँकी {CURRENCY}{nd:,.0f}",T.GREEN)
                    win.destroy(); self.refresh_bills(); self.refresh_hisab(); self.refresh_dash()
                except Exception as exc:
                    messagebox.showerror("त्रुटि",str(exc),parent=win)
            bfr=tk.Frame(c.body,bg=glass_fill()); bfr.pack(fill="x",pady=8)
            mk_btn(bfr,"✓ असुल गर",go,T.GREEN).pack(side="left",padx=6)
            mk_btn(bfr,"रद्द",win.destroy,T.SIDE).pack(side="left",padx=6)

        def _del_bill(self):
            r=self._bill_row()
            if not r: return
            if messagebox.askyesno("सुरक्षित डिलिट",
                    f"बिल '{r['bill_no']}' लाई सूचीबाट हटाउने हो?\nडाटा audit मा सुरक्षित रहन्छ।",
                    parent=self.root):
                try:
                    soft_delete("bills",int(r["id"]),self.username)
                    Toast.show(self.root,"🗑 बिल हटाइयो (audit सहित)",T.RED)
                    self.refresh_bills(); self.refresh_dash()
                except Exception as exc:
                    messagebox.showerror("डिलिट त्रुटि",str(exc),parent=self.root)

        # ---------------- SETTINGS ----------------
        def build_settings(self):
            pg=tk.Frame(self.content,bg=blend(T.BG0,T.BG1,0.65)); self.pages["settings"]=pg
            sf=ScrollFrame(pg); sf.pack(fill="both",expand=True); pg.wheel=sf.wheel
            b=sf.body
            tk.Label(b,text="⚙ सेटिङ्स",bg=b["bg"],fg=T.TEXT,font=fnt(17,True)).pack(anchor="w",padx=18,pady=(16,6))
            c1=GlassCard(b,pad=14,glow=.16); c1.pack(fill="x",padx=12,pady=6)
            card_title(c1.body,"🏪 दुकान विवरण","बिलमा यही विवरण देखिन्छ")
            f=tk.Frame(c1.body,bg=glass_fill()); f.pack(fill="x",padx=4,pady=6)
            for i in range(4): f.columnconfigure(i,weight=1)
            s=get_settings()
            self.setf={}
            self.setf["shop"]=field(f,"दुकान नाम",0,0,24); self.setf["shop"].insert(0,s[0])
            self.setf["addr"]=field(f,"ठेगाना",0,1,24); self.setf["addr"].insert(0,s[1])
            self.setf["mob"]=field(f,"मोबाइल",1,0,24); self.setf["mob"].insert(0,s[2])
            self.setf["pan"]=field(f,"PAN",1,1,24); self.setf["pan"].insert(0,s[3])
            self.setf["owner"]=field(f,"मालिक",2,0,24); self.setf["owner"].insert(0,s[4])
            self.setf["note"]=field(f,"बिल नोट",2,1,24); self.setf["note"].insert(0,s[5])
            self.setf["theme"]=combo(f,"Theme",[THEME_LABELS[k] for k in THEME_ORDER],3,0)
            self.setf["theme"].set(THEME_LABELS.get(s[6], THEME_LABELS[DEFAULT_THEME]))
            self.setf["lang"]=combo(f,"Language",["Nepali","English"],4,0)
            self.setf["lang"].set("Nepali" if CURRENT_LANG=="ne" else "English")
            self.setf["lang"].config(state="readonly")
            mk_btn(c1.body,"💾 विवरण सेभ",self._save_settings,T.GREEN).pack(fill="x",padx=8,pady=(2,10))

            c2=GlassCard(b,pad=14,glow=.24); c2.pack(fill="x",padx=12,pady=6)
            card_title(c2.body,"🔐 पासवर्ड परिवर्तन","कम्तीमा ८ अक्षर")
            f2=tk.Frame(c2.body,bg=glass_fill()); f2.pack(fill="x",padx=4,pady=6)
            self.pwf={}
            self.pwf["old"]=field(f2,"पुरानो पासवर्ड",0,0,24); self.pwf["old"].config(show="*")
            self.pwf["new"]=field(f2,"नयाँ पासवर्ड",1,0,24); self.pwf["new"].config(show="*")
            self.pwf["conf"]=field(f2,"पुष्टि गर्नुहोस्",2,0,24); self.pwf["conf"].config(show="*")
            mk_btn(c2.body,"🔑 पासवर्ड बदल्नुहोस्",self._change_password,T.ACCENT).pack(fill="x",padx=8,pady=(2,10))

            row2=tk.Frame(b,bg=b["bg"]); row2.pack(fill="x",padx=12,pady=6)
            c3=GlassCard(row2,pad=14); c3.pack(side="left",fill="both",expand=True,padx=6,pady=6)
            card_title(c3.body,"👥 प्रयोगकर्ता (Role Enforcement)","Owner ले मात्र Hisab / Settings हेर्न सक्छ")
            uf=tk.Frame(c3.body,bg=glass_fill()); uf.pack(fill="x",padx=4,pady=6)
            self.acc_user=field(uf,"नयाँ Username",0,0,20)
            self.acc_pass=field(uf,"पासवर्ड",1,0,20); self.acc_pass.config(show="*")
            self.acc_role=combo(uf,"Role",["owner","staff"],2,0); self.acc_role.current(1)
            mk_btn(c3.body,"➕ User थप्नुहोस्",self._add_user,T.BLUE).pack(fill="x",padx=8,pady=4)
            self.user_tree=make_tree(c3.body,[("username",150),("role",100),("created",180)],height=5)
            self.user_tree.pack(fill="x",padx=8,pady=6)
            c4=GlassCard(row2,pad=14,glow=.30); c4.pack(side="left",fill="both",expand=True,padx=6,pady=6)
            card_title(c4.body,"🛡 डाटा सुरक्षा","SQLite backup API + Audit hash-chain")
            mk_btn(c4.body,"💾 Backup Download",self._backup,T.GREEN).pack(fill="x",padx=8,pady=4)
            mk_btn(c4.body,"🔍 Audit Chain जाँच",self._check_audit,T.PURPLE).pack(fill="x",padx=8,pady=4)
            self.audit_lab=tk.Label(c4.body,text="",bg=glass_fill(),fg=T.MUTED,font=fnt(9),wraplength=340,justify="left")
            self.audit_lab.pack(anchor="w",padx=8,pady=6)
            tk.Label(c4.body,text=f"DB: {DB_FILE}\nConfig: {CONFIG_FILE}\n{APP_VERSION}",
                     bg=glass_fill(),fg=T.MUTED,font=fnt(8),justify="left").pack(anchor="sw",padx=8,pady=8)

            # ---- Windows Hello / Cloud / Updates ----
            row3=tk.Frame(b,bg=b["bg"]); row3.pack(fill="x",padx=12,pady=(6,24))
            hello=GlassCard(row3,pad=14,glow=.30); hello.pack(side="left",fill="both",expand=True,padx=6,pady=6)
            card_title(hello.body,"😊 Windows Hello / Biometric","Fingerprint • Face • PIN — password सधैं fallback")
            self.hello_var=tk.IntVar(value=1 if s[7] else 0)
            tk.Checkbutton(hello.body,text="Windows Hello लगइन सक्षम गर्नुस्",variable=self.hello_var,
                           command=self._toggle_hello,bg=glass_fill(),fg=T.TEXT,selectcolor=T.INPUT,
                           activebackground=glass_fill(),font=fnt(9,True)).pack(anchor="w",padx=8,pady=(4,2))
            mk_btn(hello.body,"🔎 Windows Hello जाँच",self._test_hello,T.PURPLE).pack(fill="x",padx=8,pady=4)
            self.hello_lab=tk.Label(hello.body,text=("सक्षम छ — login पर्दामा Hello button देखिन्छ" if s[7]
                                    else "अहिले बन्द छ — password ले लगइन हुन्छ"),
                                    bg=glass_fill(),fg=T.GREEN if s[7] else T.MUTED,font=fnt(8),
                                    wraplength=320,justify="left")
            self.hello_lab.pack(anchor="w",padx=8,pady=6)
            tk.Label(hello.body,text="Windows Hello verification Windows को आफ्नै secure prompt बाट हुन्छ।",
                     bg=glass_fill(),fg=T.MUTED,font=fnt(8),wraplength=320,justify="left").pack(anchor="w",padx=8,pady=(0,8))

            cloud=GlassCard(row3,pad=14,glow=.22); cloud.pack(side="left",fill="both",expand=True,padx=6,pady=6)
            card_title(cloud.body,"☁ Cloud Sync","Data securely synced to cloud")
            cfg=load_cloud_config()
            self.cloud={}
            self.cloud_auto=tk.IntVar(value=1 if (get_settings()[10] or cfg.get("enabled")) else 0)
            tk.Checkbutton(cloud.body,text="Auto-sync (recommended)",variable=self.cloud_auto,
                           bg=glass_fill(),fg=T.TEXT,selectcolor=T.INPUT,activebackground=glass_fill(),
                           font=fnt(9,True)).pack(anchor="w",padx=8,pady=(4,2))
            cb=tk.Frame(cloud.body,bg=glass_fill()); cb.pack(fill="x",padx=4,pady=4)
            mk_btn(cb,"⬆ Sync now",self._sync_cloud,T.GREEN).pack(side="left",padx=3)
            mk_btn(cb,"⬇ Restore",self._restore_cloud,T.GOLD).pack(side="left",padx=3)
            self.cloud_lab=tk.Label(cloud.body,text=(f"Last sync: {cfg.get('last_sync') or 'never'}"),
                                    bg=glass_fill(),fg=T.MUTED,font=fnt(8),wraplength=330,justify="left")
            self.cloud_lab.pack(anchor="w",padx=8,pady=6)
            tk.Label(cloud.body,text="Your data is encrypted and stored securely. Only you can access it through this app.",
                     bg=glass_fill(),fg=T.MUTED,font=fnt(8),wraplength=330,justify="left").pack(anchor="w",padx=8,pady=(0,8))

            upd=GlassCard(row3,pad=14,glow=.18); upd.pack(side="left",fill="both",expand=True,padx=6,pady=6)
            card_title(upd.body,"🚀 Auto Update","GitHub Releases बाट नयाँ version")
            tk.Label(upd.body,text=f"हालको version:  v{APP_VERSION}  •  Build {APP_BUILD}",
                     bg=glass_fill(),fg=T.TEXT,font=fnt(9,True)).pack(anchor="w",padx=8,pady=(4,2))
            self.auto_update_var=tk.IntVar(value=1 if s[9] else 0)
            tk.Checkbutton(upd.body,text="App खुल्दा update जाँच",variable=self.auto_update_var,
                           bg=glass_fill(),fg=T.TEXT,selectcolor=T.INPUT,activebackground=glass_fill(),
                           font=fnt(9,True)).pack(anchor="w",padx=8)
            mk_btn(upd.body,"🔄 Update जाँच",self._check_update,T.ACCENT).pack(fill="x",padx=8,pady=6)
            mk_btn(upd.body,"🌐 GitHub खोल्नुस्",lambda: self._open_url(GITHUB_REPO),T.SIDE).pack(fill="x",padx=8,pady=2)
            self.upd_lab=tk.Label(upd.body,text=f"Latest जाँच: {GITHUB_RAW}/version.json",
                                  bg=glass_fill(),fg=T.MUTED,font=fnt(8),wraplength=330,justify="left")
            self.upd_lab.pack(anchor="w",padx=8,pady=6)
            tk.Label(upd.body,text="Update install अघि पुरानो file को .bak backup स्वतः बन्छ।",
                     bg=glass_fill(),fg=T.MUTED,font=fnt(8),wraplength=330,justify="left").pack(anchor="w",padx=8,pady=(0,8))

            self.refresh_settings()
            self.root.after(1800,self._auto_boot_services)

        def _auto_boot_services(self):
            try:
                if not self.root.winfo_exists(): return
                if int(get_settings()[9] or 0):
                    def upd_ok(info):
                        if info:
                            Toast.show(self.root,f"🚀 नयाँ v{info['version']} उपलब्ध — Settings बाट update गर्नुस्",T.ACCENT,4200)
                    self._bg(check_for_update,upd_ok,lambda e:log.info("auto update check: %s",e))
                cfg=load_cloud_config()
                if int(get_settings()[10] or 0) and cfg.get("enabled") and cfg.get("token"):
                    self._bg(lambda:cloud_push(cfg),lambda ts:log.info("auto cloud sync: %s",ts),
                             lambda e:log.warning("auto cloud sync: %s",e))
            except Exception as exc:
                log.info("boot services: %s",exc)

        def _open_url(self,url):
            try: os.startfile(url)
            except Exception as exc: messagebox.showerror("Browser",str(exc),parent=self.root)

        def _bg(self,work,ok,err):
            def run():
                try:
                    if not self.root.winfo_exists(): return
                    result=work()
                except Exception as exc:
                    try:
                        if self.root.winfo_exists(): self.root.after(0,lambda e=exc:err(e))
                    except Exception: pass
                    return
                try:
                    if self.root.winfo_exists(): self.root.after(0,lambda r=result:ok(r))
                except Exception: pass
            threading.Thread(target=run,daemon=True).start()

        def _toggle_hello(self):
            if not self.hello_var.get():
                with DB.transaction() as con:
                    con.execute("UPDATE settings SET hello_login=0,hello_user='' WHERE id=1")
                    _audit(con,self.username,"HELLO_DISABLE","")
                self.hello_lab.config(text="बन्द छ — password ले लगइन हुन्छ",fg=T.MUTED)
                Toast.show(self.root,"Windows Hello लगइन बन्द भयो",T.SIDE)
                return
            ok,detail=windows_hello_verify("Enable Windows Hello for SHUVAM login")
            if not ok:
                self.hello_var.set(0)
                messagebox.showwarning("Windows Hello",f"सक्षम गर्न सकिएन:\n{detail}",parent=self.root)
                return
            with DB.transaction() as con:
                con.execute("UPDATE settings SET hello_login=1,hello_user=? WHERE id=1",(self.username,))
                _audit(con,self.username,"HELLO_ENABLE",self.username)
            self.hello_lab.config(text=f"सक्षम छ — {self.username} का लागि Hello login",fg=T.GREEN)
            Toast.show(self.root,"✅ Windows Hello सक्षम भयो",T.GREEN)

        def _test_hello(self):
            self.hello_lab.config(text="जाँच हुँदैछ — Windows Hello prompt हेर्नुस्…",fg=T.GOLD)
            self.root.update_idletasks()
            ok,detail=windows_hello_verify("SHUVAM Windows Hello test")
            if ok:
                self.hello_lab.config(text="✅ Windows Hello सफल — device काम गर्छ",fg=T.GREEN)
                Toast.show(self.root,"✅ Windows Hello सफल",T.GREEN)
            else:
                self.hello_lab.config(text=f"⚠ {detail}",fg=T.RED)

        def _cloud_cfg_from_form(self):
            cfg=load_cloud_config()
            return {"url":cfg.get("url") or TURSO_URL_BUILTIN,
                    "token":cfg.get("token") or TURSO_TOKEN_BUILTIN,
                    "enabled":bool(self.cloud_auto.get()),
                    "last_sync":cfg.get("last_sync","")}

        def _save_cloud(self):
            try:
                cfg=self._cloud_cfg_from_form()
                save_cloud_config(cfg)
                with DB.transaction() as con:
                    con.execute("UPDATE settings SET auto_cloud=? WHERE id=1",(int(cfg["enabled"]),))
                    _audit(con,self.username,"CLOUD_CONFIG","enabled="+str(cfg["enabled"]))
                self.cloud_lab.config(text=f"✅ सेभ भयो • अन्तिम sync: {cfg.get('last_sync') or 'कहिल्यै छैन'}",fg=T.GREEN)
                Toast.show(self.root,"✅ Cloud settings सेभ भयो",T.GREEN)
            except Exception as exc:
                messagebox.showerror("Cloud",str(exc),parent=self.root)

        def _test_cloud(self):
            try: cfg=self._cloud_cfg_from_form()
            except Exception as exc: messagebox.showerror("Cloud",str(exc),parent=self.root); return
            self.cloud_lab.config(text="Turso जाँच हुँदैछ…",fg=T.GOLD)
            def work():
                TursoClient(cfg["url"],cfg["token"]).ping(); return True
            def ok(_):
                self.cloud_lab.config(text="✅ Turso connection सफल",fg=T.GREEN)
                Toast.show(self.root,"✅ Turso जडान सफल",T.GREEN)
            def err(e):
                self.cloud_lab.config(text=f"⚠ {e}",fg=T.RED)
                messagebox.showerror("Turso",str(e),parent=self.root)
            self._bg(work,ok,err)

        def _sync_cloud(self):
            try: cfg=self._cloud_cfg_from_form()
            except Exception as exc: messagebox.showerror("Cloud",str(exc),parent=self.root); return
            save_cloud_config(cfg)
            self.cloud_lab.config(text="Encrypted snapshot upload हुँदैछ…",fg=T.GOLD)
            def work(): return cloud_push(cfg)
            def ok(ts):
                self.cloud_lab.config(text=f"✅ Sync सम्पन्न — {ts}",fg=T.GREEN)
                Toast.show(self.root,"☁ Encrypted sync सम्पन्न",T.GREEN)
                with DB.transaction() as con:
                    _audit(con,self.username,"CLOUD_PUSH",ts)
            def err(e):
                self.cloud_lab.config(text=f"⚠ Sync असफल: {e}",fg=T.RED)
                messagebox.showerror("Cloud Sync",str(e),parent=self.root)
            self._bg(work,ok,err)

        def _restore_cloud(self):
            if not messagebox.askyesno("Cloud Restore",
                    "Turso को encrypted snapshot ले local data बदल्ने हो?\nपहिले local backup स्वतः बन्छ।",
                    parent=self.root): return
            try: cfg=self._cloud_cfg_from_form()
            except Exception as exc: messagebox.showerror("Cloud",str(exc),parent=self.root); return
            self.cloud_lab.config(text="Snapshot download र restore हुँदैछ…",fg=T.GOLD)
            def work(): return cloud_pull(cfg)
            def ok(res):
                count,ts=res
                Toast.show(self.root,f"✅ {count} rows restore भयो — UI refresh हुँदैछ",T.GREEN)
                self.hello_var.set(1 if get_settings()[7] else 0)
                self.set_theme(get_settings()[6] or DEFAULT_THEME)
            def err(e):
                self.cloud_lab.config(text=f"⚠ Restore असफल: {e}",fg=T.RED)
                messagebox.showerror("Cloud Restore",str(e),parent=self.root)
            self._bg(work,ok,err)

        def _check_update(self):
            self.upd_lab.config(text="GitHub बाट नयाँ version जाँच हुँदैछ…",fg=T.GOLD)
            def work(): return check_for_update()
            def ok(info):
                if not info:
                    self.upd_lab.config(text=f"✅ तपाईंको v{APP_VERSION} नै latest छ",fg=T.GREEN)
                    Toast.show(self.root,"✅ App latest version मा छ",T.GREEN); return
                notes=(info.get("notes") or "").strip()
                if messagebox.askyesno("नयाँ Update",
                        f"v{info['version']} उपलब्ध छ (हाल v{APP_VERSION})\n\n{notes}\n\nअहिले install गर्ने?",
                        parent=self.root):
                    self._install_update(info)
            def err(e):
                self.upd_lab.config(text=f"⚠ Update जाँच असफल: {e}",fg=T.RED)
                Toast.show(self.root,f"Update जाँच असफल: {e}",T.RED)
            self._bg(work,ok,err)

        def _install_update(self,info):
            self.upd_lab.config(text="Update download हुँदैछ…",fg=T.GOLD)
            def work(): return install_update(info)
            def ok(res):
                good,msg=res
                self.upd_lab.config(text=("✅ "+msg) if good else ("⚠ "+msg),fg=T.GREEN if good else T.RED)
                messagebox.showinfo("Auto Update",msg,parent=self.root)
                if good and messagebox.askyesno("Restart","अहिले app बन्द गरेर नयाँ version खोल्ने?",
                                                parent=self.root):
                    self.root.destroy()
                    if not getattr(sys,"frozen",False):
                        try: subprocess.Popen([sys.executable,str(Path(__file__).resolve())])
                        except Exception: pass
            def err(e): self.upd_lab.config(text=f"⚠ {e}",fg=T.RED)
            self._bg(work,ok,err)

        def refresh_settings(self):
            if not hasattr(self,"user_tree"): return
            for i in self.user_tree.get_children(): self.user_tree.delete(i)
            for r in self.q("SELECT username,role,created_at FROM users ORDER BY username"):
                self.user_tree.insert("","end",values=(r["username"],r["role"],r["created_at"] or "-"))

        def _save_settings(self):
            try:
                label=self.setf["theme"].get()
                key=next((k for k,v in THEME_LABELS.items() if v==label),DEFAULT_THEME)
                old=(get_settings()[6] or DEFAULT_THEME)
                auto=int(self.auto_update_var.get()) if hasattr(self,"auto_update_var") else 1
                with DB.transaction() as con:
                    con.execute("UPDATE settings SET shop_name=?,address=?,mobile=?,pan=?,owner=?,bill_note=?,theme=?,auto_update=? WHERE id=1",
                        (self.setf["shop"].get().strip(),self.setf["addr"].get().strip(),self.setf["mob"].get().strip(),
                         self.setf["pan"].get().strip(),self.setf["owner"].get().strip(),self.setf["note"].get().strip(),
                         key,auto))
                    _audit(con,self.username,"SAVE_SETTINGS","theme="+key)
                lang="ne" if self.setf["lang"].get()=="Nepali" else "en"
                save_lang(lang)
                if key!=old:
                    self.set_theme(key); return
                Toast.show(self.root,"✅ सेटिङ्स सेभ भयो",T.GREEN)
            except Exception as exc:
                messagebox.showerror("त्रुटि",str(exc),parent=self.root)

        def _change_password(self):
            try:
                old=self.pwf["old"].get(); new=self.pwf["new"].get(); conf=self.pwf["conf"].get()
                if new!=conf: raise ValueError("नयाँ पासवर्ड र पुष्टि मिलेन")
                if len(new)<PASSWORD_MIN_LEN: raise ValueError(f"कम्तीमा {PASSWORD_MIN_LEN} अक्षर चाहिन्छ")
                with DB.transaction() as con:
                    r=con.execute("SELECT password_hash,salt FROM users WHERE username=?",(self.username,)).fetchone()
                    if not r or not verify_password(old,r["password_hash"],r["salt"]):
                        raise ValueError("पुरानो पासवर्ड गलत छ")
                    h,s=hash_password(new)
                    con.execute("UPDATE users SET password_hash=?,salt=? WHERE username=?",(h,s,self.username))
                    _audit(con,self.username,"CHANGE_PASSWORD",self.username)
                for e in self.pwf.values(): e.delete(0,"end")
                Toast.show(self.root,"✅ पासवर्ड परिवर्तन भयो",T.GREEN)
            except Exception as exc:
                messagebox.showerror("त्रुटि",str(exc),parent=self.root)

        def _add_user(self):
            try:
                u=self.acc_user.get().strip(); p=self.acc_pass.get(); role=self.acc_role.get()
                if not create_user(u,p,role,DB): raise ValueError("Username पहिले नै छ")
                Toast.show(self.root,f"✅ User '{u}' ({role}) थपियो",T.GREEN)
                self.acc_user.delete(0,"end"); self.acc_pass.delete(0,"end")
                self.refresh_settings()
            except Exception as exc:
                messagebox.showerror("त्रुटि",str(exc),parent=self.root)

        def _backup(self):
            try:
                dest=filedialog.asksaveasfilename(defaultextension=".db",initialfile="shuvam_backup.db",
                      filetypes=[("SQLite Database","*.db")],title="Backup कहाँ राख्ने?",parent=self.root)
                if not dest: return
                DB.backup(Path(dest))
                Toast.show(self.root,"✅ Backup सम्पन्न भयो",T.GREEN)
            except Exception as exc:
                messagebox.showerror("Backup त्रुटि",str(exc),parent=self.root)

        def _check_audit(self):
            ok,n=verify_audit_chain()
            self.audit_lab.config(text=(f"✅ {n} वटा रेकर्ड चेन सही छ" if ok else f"⚠ चेन #{n} मा समस्या"),
                                  fg=T.GREEN if ok else T.RED)

# ================= LOGIN / SETUP =================
if HAS_TK:
    def _glass_bg(root):
        cv=GradientCanvas(root); cv.place(relwidth=1,relheight=1)
        cv.blobs=[(0.18,0.16,230,T.PURPLE),(0.86,0.24,210,T.BLUE),
                  (0.62,0.92,250,T.GREEN),(0.22,0.82,190,T.GOLD)]
        cv.redraw()
        return cv

    def login_screen(root):
        s=get_settings()
        apply_theme(s[6] or DEFAULT_THEME)
        for w in root.winfo_children(): w.destroy()
        root.title(f"{APP_VERSION_LABEL} — Login"); root.geometry("900x620"); root.resizable(False,False)
        root.configure(bg=T.BG0)
        try:
            ensure_icon_assets()
            root.iconbitmap(default=str(ICON_ICO))
            root._login_icon=tk.PhotoImage(file=str(ICON_PNG)).subsample(2)
        except Exception:
            root._login_icon=None
        # animated 3D-ish background canvas
        bgc=tk.Canvas(root,bg=T.BG0,highlightthickness=0); bgc.place(relwidth=1,relheight=1)
        blobs=[(0.15,0.2,260,T.PURPLE),(0.85,0.25,230,T.BLUE),(0.7,0.85,280,T.ACCENT3),(0.2,0.8,200,T.GOLD)]
        def draw_bg(t=0):
            bgc.delete("all")
            w,h=bgc.winfo_width() or 900, bgc.winfo_height() or 620
            for i in range(28):
                yy=i/27
                bgc.create_rectangle(0,h*yy,w,h*(yy+1)+1,fill=blend(T.BG0,T.BG1,yy),outline="")
            for x,y,r,col in blobs:
                cx,cy=x*w+math.sin(t+x)*18, y*h+math.cos(t+y)*18
                for rr in range(r,0,-18):
                    bgc.create_oval(cx-rr,cy-rr,cx+rr,cy+rr,fill=blend(T.BG0,col,0.06+0.002*(r-rr)),outline="")
            bgc.create_text(w/2,48,text="SHUVAM",fill=T.TEXT,font=("Segoe UI",40,"bold"))
            bgc.create_text(w/2,82,text="RECONDITION HOUSE  •  PRO",fill=T.ACCENT2,font=("Segoe UI",11,"bold"))
            bgc.create_text(w/2,h-24,text="Secure login • Windows Hello • Cloud sync",fill=T.MUTED,font=("Segoe UI",9))
        def tick(t=0):
            if not bgc.winfo_exists(): return
            draw_bg(t); bgc.after(40,lambda:tick(t+0.05))
        root.after(50,tick)
        # language toggle
        def _set_lang_toggle(btn):
            global CURRENT_LANG
            CURRENT_LANG = "en" if CURRENT_LANG=="ne" else "ne"
            btn.config(text=("EN" if CURRENT_LANG=="ne" else "NE"))
            login_screen(root)
        lb=tk.Button(root,text=("EN" if CURRENT_LANG=="ne" else "NE"),bg=T.SIDE,fg=T.TEXT,font=fnt(9,True),bd=0,cursor="hand2",
                     command=lambda:_set_lang_toggle(lb))
        lb.place(relx=.97,rely=.03,anchor="ne")
        # 3D card container
        c=GlassCard(root,pad=24,glow=.45,stretch=False); c.place(relx=.5,rely=.55,anchor="center",width=400)
        # parallax tilt
        def _parallax(e):
            try:
                rx=(e.x_root/root.winfo_screenwidth()-0.5)
                ry=(e.y_root/root.winfo_screenheight()-0.5)
                c.place(relx=.5,rely=.55,anchor="center",x=int(rx*16),y=int(ry*16))
                c._draw()
            except Exception: pass
        root.bind("<Motion>",_parallax)
        if getattr(root,"_login_icon",None):
            tk.Label(c.body,image=root._login_icon,bg=glass_fill()).pack(pady=(2,2))
        tk.Label(c.body,text="🔐 "+t("login"),bg=glass_fill(),fg=T.TEXT,font=fnt(20,True)).pack(pady=(4,2))
        tk.Label(c.body,text=APP_TITLE,bg=glass_fill(),fg=T.MUTED,font=fnt(9,True)).pack()
        tk.Frame(c.body,bg=T.EDGE,height=1).pack(fill="x",pady=12)
        f=tk.Frame(c.body,bg=glass_fill()); f.pack(fill="x",padx=8)
        u=field(f,t("username"),0,0,24); p=field(f,t("password"),1,0,24); p.config(show="*")
        u.focus_set()
        msg=tk.Label(c.body,text="",bg=glass_fill(),fg=T.RED,font=fnt(9),wraplength=340,justify="center")
        msg.pack(pady=6)
        attempts={"n":0,"lock":False}
        def enter_app(username,role):
            for w in root.winfo_children(): w.destroy()
            root.resizable(True,True); root.geometry("1360x860")
            App(root,role,username)
        def submit(e=None):
            if attempts["lock"]: return
            username=u.get().strip()
            role=check_login(username,p.get())
            if role:
                enter_app(username,role); return
            attempts["n"]+=1
            msg.config(text=f"⚠ गलत {t('username')}/{t('password')} ({attempts['n']}/{MAX_LOGIN_ATTEMPTS})")
            if attempts["n"]>=MAX_LOGIN_ATTEMPTS:
                attempts["lock"]=True; left={"n":LOCKOUT_SECONDS}
                def tick():
                    if not root.winfo_exists(): return
                    if left["n"]<=0:
                        attempts["lock"]=False; attempts["n"]=0; msg.config(text=""); return
                    msg.config(text=f"⛔ धेरै पटक गलत — {left['n']} सेकेन्ड पर्खनुस्")
                    left["n"]-=1; root.after(1000,tick)
                tick()
        p.bind("<Return>",submit); u.bind("<Return>",lambda e:p.focus_set())
        mk_btn(c.body,"🚪 "+t("login"),submit,T.ACCENT).pack(fill="x",padx=8,pady=(4,6))
        hello_on=bool(s[7])
        if hello_on:
            def hello_login():
                msg.config(text="Windows Hello prompt हेर्नुस्…",fg=T.GOLD)
                hb.config(state="disabled")
                def work(): return windows_hello_verify("Login to SHUVAM Recondition House")
                def done(res):
                    if not root.winfo_exists(): return
                    ok,detail=res
                    if not ok:
                        hb.config(state="normal")
                        msg.config(text=f"⚠ {detail}",fg=T.RED); return
                    uname=(s[8] or s[4] or "").strip()
                    role=None
                    if uname:
                        with DB.read() as con:
                            r=con.execute("SELECT role FROM users WHERE username=?",(uname,)).fetchone()
                            role=r["role"] if r else None
                    if not role:
                        with DB.read() as con:
                            r=con.execute("SELECT username,role FROM users WHERE role='owner' ORDER BY created_at LIMIT 1").fetchone()
                            if r: uname,role=r["username"],r["role"]
                    if role: enter_app(uname,role)
                    else:
                        hb.config(state="normal")
                        msg.config(text="⚠ Hello user भेटिएन",fg=T.RED)
                def bg():
                    res=work()
                    try: root.after(0,lambda:done(res))
                    except Exception: pass
                threading.Thread(target=bg,daemon=True).start()
            hb=mk_btn(c.body,"😊 Windows Hello",hello_login,T.PURPLE)
            hb.pack(fill="x",padx=8,pady=(0,6))
        tk.Label(c.body,text=BRAND_LINE,bg=glass_fill(),fg=T.MUTED,font=fnt(7),wraplength=360,justify="center").pack(pady=(4,8))

    def setup_screen(root):
        apply_theme(get_settings()[6] or DEFAULT_THEME)
        for w in root.winfo_children(): w.destroy()
        root.title(f"{APP_VERSION_LABEL} — पहिलो सेटअप"); root.geometry("800x720"); root.resizable(False,False)
        root.configure(bg=T.BG0); _glass_bg(root)
        try:
            ensure_icon_assets()
            root.iconbitmap(default=str(ICON_ICO))
            root._setup_icon=tk.PhotoImage(file=str(ICON_PNG)).subsample(3)
        except Exception:
            root._setup_icon=None
        c=GlassCard(root,pad=22,glow=.34,stretch=False); c.place(relx=.5,rely=.5,anchor="center")
        if getattr(root,"_setup_icon",None):
            tk.Label(c.body,image=root._setup_icon,bg=glass_fill()).pack(pady=(2,2))
        tk.Label(c.body,text="👋 स्वागत छ!",bg=glass_fill(),fg=T.TEXT,font=fnt(22,True)).pack(pady=(2,0))
        tk.Label(c.body,text="पहिलो Owner खाता बनाउनुहोस्",bg=glass_fill(),fg=T.MUTED,font=fnt(10)).pack()
        tk.Label(c.body,text=f"SHUVAM PRO v{APP_VERSION} • {len(THEMES)} themes • Windows Hello ready",
                 bg=glass_fill(),fg=T.ACCENT2,font=fnt(8,True)).pack(pady=(3,0))
        tk.Frame(c.body,bg=T.EDGE,height=1).pack(fill="x",pady=12)
        f=tk.Frame(c.body,bg=glass_fill()); f.pack(fill="x",padx=8)
        ef={}
        ef["shop"]=field(f,"दुकान नाम",0,0,24); ef["shop"].insert(0,DEFAULT_SHOP_NAME)
        ef["addr"]=field(f,"ठेगाना",1,0,24); ef["addr"].insert(0,DEFAULT_ADDRESS)
        ef["user"]=field(f,"Owner Username",2,0,24); ef["user"].insert(0,"owner")
        ef["pass"]=field(f,"पासवर्ड (८+ अक्षर)",3,0,24); ef["pass"].config(show="*")
        ef["conf"]=field(f,"पासवर्ड पुष्टि",4,0,24); ef["conf"].config(show="*")
        msg=tk.Label(c.body,text="",bg=glass_fill(),fg=T.RED,font=fnt(9)); msg.pack(pady=6)
        def submit():
            try:
                if ef["pass"].get()!=ef["conf"].get(): raise ValueError("पासवर्ड मिलेन")
                if not create_user(ef["user"].get().strip(),ef["pass"].get(),"owner",DB):
                    raise ValueError("User पहिले नै छ")
                with DB.transaction() as con:
                    con.execute("UPDATE settings SET shop_name=?,address=?,owner=? WHERE id=1",
                        (ef["shop"].get().strip(),ef["addr"].get().strip(),ef["user"].get().strip()))
                    _audit(con,"system","SETUP","owner account created")
                login_screen(root)
            except Exception as exc:
                msg.config(text=str(exc))
        mk_btn(c.body,"✅ सेटअप पूरा गर",submit,T.GREEN).pack(fill="x",padx=8,pady=(2,8))
        tk.Label(c.body,text="पछि Settings बाट Windows Hello, theme र Turso cloud sync सक्षम गर्न सकिन्छ।",
                 bg=glass_fill(),fg=T.MUTED,font=fnt(8),wraplength=340,justify="center").pack(pady=(0,4))
        tk.Label(c.body,text=BRAND_LINE,bg=glass_fill(),fg=T.MUTED,font=fnt(7),
                 wraplength=320,justify="center").pack(pady=(2,8))

    def launch():
        root=tk.Tk()
        try: ensure_icon_assets()
        except Exception as exc: log.info("icon: %s", exc)
        try:
            root.iconbitmap(default=str(ICON_ICO))
            root._launch_icon=tk.PhotoImage(file=str(ICON_PNG))
            root.iconphoto(True,root._launch_icon)
        except Exception as exc:
            log.info("window icon: %s", exc)
        root.withdraw()
        splash=tk.Toplevel(root)
        splash.overrideredirect(True)
        sw,sh=root.winfo_screenwidth(),root.winfo_screenheight()
        w,h=420,260
        splash.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        splash.configure(bg="#0F0D1A")
        cv=tk.Canvas(splash,bg="#0F0D1A",highlightthickness=0,width=w,height=h)
        cv.pack(fill="both",expand=True)
        cv.create_text(w/2,h/2-20,text="SHUVAM",fill="#FFFFFF",font=("Segoe UI",34,"bold"))
        cv.create_text(w/2,h/2+22,text="RECONDITION HOUSE  •  PRO",fill="#7C5CFF",font=("Segoe UI",11,"bold"))
        cv.create_text(w/2,h-28,text="Loading…",fill="#A89FC5",font=("Segoe UI",9))
        bar=cv.create_rectangle(w/2-120,h-46,w/2+120,h-42,fill="#1E1B3A",outline="")
        def anim(i=0):
            if not splash.winfo_exists(): return
            cv.coords(bar,w/2-120,h-46,w/2-120+240*(i/40),h-42)
            if i<40: splash.after(25,lambda:anim(i+1))
        anim()
        splash.update()
        def done():
            splash.destroy()
            root.deiconify()
            root.geometry("1360x860"); root.minsize(1120,730)
            try: root.attributes("-alpha",0.0)
            except Exception: pass
            if has_any_user(): login_screen(root)
            else: setup_screen(root)
            try: Anim.run(root,"launch",420,14,lambda p:root.attributes("-alpha",0.94+0.06*p))
            except Exception: pass
        root.after(1100,done)
        root.mainloop()

def main():
    if "--test" in sys.argv:
        ok=run_tests()
        sys.exit(0 if ok else 1)
    if "--version" in sys.argv:
        print(APP_VERSION_LABEL); return
    if "--generate-icon" in sys.argv:
        print("OK", *ensure_icon_assets(True)); return
    if "--sync" in sys.argv:
        try:
            print("OK synced at", cloud_push()); return
        except Exception as exc:
            print("SYNC FAILED:", exc); sys.exit(1)
    if not HAS_TK:
        print("Tkinter उपलब्ध छैन। Headless परीक्षणका लागि: python shuvam_glass_pro.py --test")
        sys.exit(1)
    launch()

# ================= TEST SUITE (8 सुधार कभर) =================
def run_tests() -> bool:
    import traceback
    try:
        sys.stdout.reconfigure(encoding="utf-8",errors="replace")
    except Exception:
        pass
    passed=[]; failed=[]
    def check(name,fn):
        try:
            fn(); passed.append(name); print(f"  [PASS] {name}")
        except Exception as exc:
            failed.append((name,exc)); print(f"  [FAIL] {name} -> {exc}")
            if os.environ.get("SHUVAM_TEST_VERBOSE"): traceback.print_exc()

    print("="*70)
    print("SHUVAM Liquid Glass Pro — TEST SUITE")
    print("="*70)

    # ---------- 1. बिलबाट Profit + banned-word guard ----------
    def t_banned():
        try:
            assert_customer_safe("Profit", "कुनै रेखा", "नोट")
            raise AssertionError("Banned word पास भयो")
        except ValueError: pass
        for w in ("faida","lagat","नाफा","फाइदा","लागत","भित्री","internal","cost"):
            try:
                assert_customer_safe(f"यसमा {w} शब्द छ")
                raise AssertionError(f"{w} पास भयो")
            except ValueError: pass
        try:
            make_bill_text("बाइक बिल",["Profit Rs. 5000"],customer="Ram",phone="9800000000")
            raise AssertionError("Profit सहित बिल बनेको छ")
        except ValueError: pass
        txt=make_bill_text("बाइक बिल",["Brand/Model: Honda Shine"],customer="Ram",
                           phone="9800000000",total=100000,paid=100000,bill_no="SVM00001")
        low=txt.lower()
        for w in ("profit","faida","lagat","cost","internal","नाफा","फाइदा","लागत"):
            assert w not in low, f"बिलमा '{w}' देखियो"
        assert "7654321" not in txt
    check("1. बिलबाट Profit हटाउने + banned-word guard",t_banned)

    # ---------- 2. Overpayment validation ----------
    def t_overpay():
        for label in ("Paid","Plate Paid","Repair Paid"):
            try:
                validate_payment(1000,1500,label)
                raise AssertionError(f"{label} मा overpayment पास भयो")
            except ValueError: pass
        validate_payment(1000,1000,"Paid")
        validate_payment(1000,0,"Paid")
        assert calc_due(100000,150000)==0.0
        assert calc_due(100000,60000)==40000.0
    check("2. Overpayment validation (sell/plate/repair)",t_overpay)

    # ---------- 3. कर अलर्ट overdue ----------
    def t_kar():
        past=date.today()-timedelta(days=KAR_VALID_DAYS+12)
        st=kar_status(past.isoformat())
        assert st is not None, "Overdue करमा अलर्ट आएन"
        assert st[1]<0 and "नाघिसकेको" in st[0], str(st)
        soon=date.today()-timedelta(days=KAR_VALID_DAYS-10)   # १० दिन बाँकी
        st2=kar_status(soon.isoformat())
        assert st2 is not None and 0<=st2[1]<=KAR_ALERT_DAYS, str(st2)
        far=date.today()-timedelta(days=KAR_VALID_DAYS-100)   # १०० दिन बाँकी
        assert kar_status(far.isoformat()) is None
        assert kar_status("") is None
    check("3. कर अलर्ट overdue समेट्ने",t_kar)

    # ---------- temp DB ----------
    tmp=Path(tempfile.mkdtemp(prefix="shuvam_test_"))
    tdb=Database(tmp/"test.db")

    # ---------- 7. config path + role ----------
    def t_config_role():
        assert CONFIG_FILE.name=="shuvam_config.json"
        assert CONFIG_FILE.parent==BASE
        assert create_user("owner","password123","owner",tdb) is True
        assert create_user("staff","password123","staff",tdb) is True
        assert check_login("owner","password123",tdb)=="owner"
        assert check_login("staff","password123",tdb)=="staff"
        assert check_login("owner","galat",tdb) is None
        assert has_any_user(tdb) is True
        try:
            create_user("x","short","staff",tdb); raise AssertionError("छोटो password पास भयो")
        except ValueError: pass
    check("7. Config path + role enforcement",t_config_role)

    # ---------- 4. Restock ----------
    def t_restock():
        restock_accessory("TEST Helmet",10,100,200,"tester",tdb)
        restock_accessory("TEST Helmet",5,120,250,"tester",tdb)
        with tdb.read() as con:
            rows=con.execute("SELECT * FROM accessories WHERE name='TEST Helmet'").fetchall()
            assert len(rows)==1, "डुप्लिकेट सामान बनेको छ"
            r=rows[0]
            assert r["stock"]==15, f"स्टक {r['stock']} छ, 15 चाहिए"
            assert r["buy_price"]==120 and r["sell_price"]==250, "मूल्य update भएन"
        try:
            restock_accessory("X",0,1,2,"tester",tdb); raise AssertionError("qty 0 पास भयो")
        except ValueError: pass
    check("4. Restock (ON CONFLICT DO UPDATE)",t_restock)

    # ---------- 5. Ledger + bills.due ----------
    state={}
    def t_ledger_due():
        with tdb.transaction() as con:
            cur=con.execute("INSERT INTO bikes(brand,model,bike_no,buy_price,total_cost,buy_date,status) "
                            "VALUES(?,?,?,?,?,?,?)",("Honda","Shine","TEST-001",50000,60000,
                            date.today().isoformat(),"Stock Ma"))
            bid=cur.lastrowid
            bno=_create_bill(con,"BIKE","Ram","9800000000","Shine | TEST-001",100000,60000,40000,
                             "Cash",ref_id=bid)
            _ledger_due(con,"Ram","9800000000","उधारो",f"Bike {bno}",40000,bno)
        state["bid"]=bid; state["bno"]=bno
        with tdb.read() as con:
            b=con.execute("SELECT * FROM bills WHERE bill_no=?",(bno,)).fetchone()
            l=con.execute("SELECT * FROM ledger WHERE bill_no=?",(bno,)).fetchone()
            assert b["due"]==40000 and b["paid"]==60000
            assert l["balance"]==40000 and l["udharo"]==40000
        nd=receive_payment(bno,15000,"tester","पहिलो किस्ता",tdb)
        assert nd==25000, f"बाँकी {nd} छ"
        with tdb.read() as con:
            b=con.execute("SELECT * FROM bills WHERE bill_no=?",(bno,)).fetchone()
            assert b["paid"]==75000 and b["due"]==25000
            rec=con.execute("SELECT * FROM ledger WHERE type='उधारो असुल' AND bill_no=?",(bno,)).fetchone()
            assert rec is not None and rec["tiryo"]==15000 and rec["balance"]==25000
            cash=con.execute("SELECT * FROM cashbook WHERE description LIKE ?",(f"%{bno}%",)).fetchone()
            assert cash is not None and cash["income"]==15000
        nd2=receive_payment(bno,25000,"tester",db=tdb)
        assert nd2==0, "बेल बज्न बाँकी 0 हुनुपर्छ"
        with tdb.read() as con:
            b=con.execute("SELECT paid,due FROM bills WHERE bill_no=?",(bno,)).fetchone()
            assert b["paid"]==100000 and b["due"]==0
        try:
            receive_payment(bno,100,"tester",db=tdb); raise AssertionError("चुक्ता बिलमा फेरि असुल भयो")
        except ValueError: pass
    check("5. Ledger semantics + bills.due घट्ने flow",t_ledger_due)

    # ---------- 6. Bill/Bike edit + safe delete ----------
    def t_edit_delete():
        bno=state["bno"]; bid=state["bid"]
        old=edit_bill(bno,"Ram","9800000001",110000,110000,"tester",tdb)
        with tdb.read() as con:
            b=con.execute("SELECT * FROM bills WHERE bill_no=?",(bno,)).fetchone()
            bike=con.execute("SELECT * FROM bikes WHERE id=?",(bid,)).fetchone()
            assert b["total"]==110000 and b["paid"]==110000 and b["due"]==0
            assert bike["sell_price"]==110000 and bike["profit"]==50000
            assert b["created_at"]==old, "बिलको मिति परिवर्तन भयो"
        with tdb.transaction() as con:
            con.execute("UPDATE bikes SET status='Bechiyo' WHERE id=?",(bid,))
        edit_bike(bid,{"brand":"Honda","model":"Shine","color":"Black","year":"2024",
                       "bike_no":"TEST-001","buy_price":50000,"repair_cost":2000,
                       "naam_sari":1000,"kar_cost":3000,"kar_paid":1},"tester",tdb)
        with tdb.read() as con:
            bike=con.execute("SELECT * FROM bikes WHERE id=?",(bid,)).fetchone()
            assert bike["total_cost"]==56000, f"Total {bike['total_cost']}"
            assert bike["profit"]==54000, f"Profit {bike['profit']}"
        soft_delete("bills",_bill_id(tdb,bno),"tester",tdb)
        soft_delete("bikes",bid,"tester",tdb)
        with tdb.read() as con:
            assert con.execute("SELECT is_deleted FROM bills WHERE bill_no=?",(bno,)).fetchone()[0]==1
            assert con.execute("SELECT is_deleted FROM bikes WHERE id=?",(bid,)).fetchone()[0]==1
            assert con.execute("SELECT COUNT(*) c FROM audit_log WHERE action IN "
                               "('EDIT_BILL','EDIT_BIKE','SOFT_DELETE')").fetchone()["c"]>=3
        try:
            soft_delete("users",1,"tester",tdb); raise AssertionError("अनुमति नभएको table डिलिट भयो")
        except ValueError: pass
        ok,n=verify_audit_chain(tdb)
        assert ok and n>0, f"Audit chain समस्या: {ok},{n}"
    check("6. Bill/Bike edit + सुरक्षित soft-delete",t_edit_delete)

    print("-"*70)
    print(f"RESULT: {len(passed)} passed, {len(failed)} failed")
    print("="*70)
    for name,exc in failed: print(f"  FAILED -> {name}: {exc}")
    return not failed

def _bill_id(db,bill_no):
    with db.read() as con:
        return int(con.execute("SELECT id FROM bills WHERE bill_no=?",(bill_no,)).fetchone()[0])

if __name__=="__main__":
    main()
