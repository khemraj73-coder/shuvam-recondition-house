#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SHUVAM RECONDITION HOUSE — ULTIMATE v10.1.2 (single-file, stdlib-only)
Design & Developed by Khemraj Bhattarai | KRB STUDIO
चलाउने:  python shuvam_ultimate.py
परीक्षण: python shuvam_ultimate.py --test          (offline)
        python shuvam_ultimate.py --test-cloud    (network सहित)
अन्य:   --version | --icon | --backup | --sync
"""
from __future__ import annotations
import base64, ctypes, hashlib, hmac, json, logging, math, os, re, secrets
import shutil, sqlite3, struct, subprocess, sys, tempfile, threading, time
import urllib.error, urllib.request, webbrowser, zlib
from contextlib import contextmanager
from datetime import datetime, timedelta, date
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog, simpledialog, font as tkfont
    HAS_TK = True
except ImportError:
    tk = ttk = messagebox = filedialog = simpledialog = tkfont = None
    HAS_TK = False
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ══════════════ १. CONSTANTS ══════════════
APP_NAME = "SHUVAM RECONDITION HOUSE"
APP_CODE = "ULTIMATE"
APP_VER = "10.1.2"
BRAND = "Design & Developed by Khemraj Bhattarai · KRB STUDIO · khemraj73@gmail.com"
CUR = "Rs. "
PAGE_LIMIT = 300
LOCK_TRIES, LOCK_SECONDS, PW_MIN = 5, 30, 8
KAR_DAYS, KAR_WARN = 365, 30
PBKDF2 = 600_000
GENESIS = "GENESIS"
METHODS = ("Cash", "eSewa", "Khalti", "ConnectIPS", "Bank Transfer", "Fonepay", "IME Pay", "Cheque", "Other")
EXP_CATS = ("Rent", "Fuel", "Electricity", "Marketing", "Transport", "Office", "Misc", "Other")
PART_CATS = ("General", "Engine", "Brake", "Electrical", "Body", "Tyre/Tube", "Other")
ACC_CATS = ("Helmet", "Gloves", "Jacket", "Mirror", "Oil", "Cover", "Other")
PLATE_KINDS = ("New Registration", "Re-registration", "Name Transfer", "Duplicate", "Other")
JOB_STATUS = ("Pending", "Processing", "Done")
PHOTO_EXTS = (".jpg", ".jpeg", ".png", ".webp")
MAX_PHOTO_MB = 8
BANNED = ("profit", "faida", "lagat", "cost", "internal", "नाफा", "फाइदा", "लागत", "भित्री")
ACTIVE = "voided=0 AND is_deleted=0"
BRANDS = {"Honda": ["Shine 125", "Unicorn 160", "SP 125", "Dio 110", "CB200X"],
          "Yamaha": ["FZ-S V3", "MT-15 V2", "R15 V4", "Ray ZR 125"],
          "Bajaj": ["Pulsar 150", "Pulsar NS 200", "Pulsar 220F", "Dominar 400", "Platina 110"],
          "TVS": ["Apache RTR 160 4V", "Apache RTR 200 4V", "Raider 125", "NTorq 125"],
          "Hero": ["Splendor Plus", "Xtreme 160R", "XPulse 200 4V", "Passion Pro"],
          "Suzuki": ["Gixxer 150", "Gixxer SF 150", "Access 125"],
          "KTM": ["Duke 200", "Duke 250", "Duke 390", "RC 200"],
          "Royal Enfield": ["Classic 350", "Hunter 350", "Meteor 350", "Himalayan 450"],
          "Other": ["Other — manual"]}
COLORS = ("Black", "White", "Red", "Blue", "Grey", "Silver", "Green", "Yellow", "Orange", "Matt Black")
YEARS = tuple(str(y) for y in range(date.today().year + 1, 2009, -1))
SNAP_TABLES = ("settings", "users", "bikes", "customers", "bills", "payments", "ledger",
               "cashbook", "cash_closures", "accessories", "acc_sales", "plates", "repairs",
               "parts", "part_usage", "labour", "expenses", "staff", "salaries", "audit", "bill_counter")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("shuvam")

# ══════════════ २. PATHS ══════════════
BASE = Path(__file__).resolve().parent
def _data_dir() -> Path:
    env = os.environ.get("SHUVAM_HOME")
    if env:
        p = Path(env); p.mkdir(parents=True, exist_ok=True); return p
    p = Path(r"C:\ShuvamReconditionHouse\Data")
    try:
        p.mkdir(parents=True, exist_ok=True)
        probe = p / ".probe"; probe.write_text("ok"); probe.unlink(); return p
    except Exception:
        p = BASE / "Data"; p.mkdir(parents=True, exist_ok=True); return p
DATA = _data_dir()
DB_FILE = DATA / "shuvam_ultimate.db"
BACKUP_DIR = DATA / "Backups"; BACKUP_DIR.mkdir(exist_ok=True)
BILL_DIR = DATA / "Bills"; BILL_DIR.mkdir(exist_ok=True)
PHOTO_DIR = DATA / "BikePhotos"; PHOTO_DIR.mkdir(exist_ok=True)
CLOUD_FILE = DATA / "cloud_v10.json"
TURSO_URL_ULTIMATE = "libsql://shuvam-recondition-house-khemraj73-coder.aws-ap-south-1.turso.io"
TURSO_TOKEN_ULTIMATE = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3OTUyMTM3NzgsImlkIjoiMDFhMWZhYTItYzUwMS03ZjNlLWEwMjctZmY0YWQ4YTBlOWVmIiwia2lkIjoiTUFONElfcXVPMVBzLXZMNm9SY3BnVjRIMlV4cG4tWm9mNHJ4NnNvN2lpYyIsInJpZCI6ImE3Mjc1MWUyLTQ3NTEtNGZmNC1iMTFiLTI4Zjg4MGUwMzhmMSJ9.OuI33n3uQL_1XrydzTK-yqpYcR3TJpbG81t0jyGhClQfh5RpfNZP_5ThxY8_e4-j3mOjjBvV2U9hZUEUJgNWAA"
UPDATE_URL_DEFAULT = "https://raw.githubusercontent.com/khemraj73-coder/shuvam-recondition-house/main/version_ultimate.json"
ICON_PNG = DATA / "shuvam_icon.png"
LOG_FILE = DATA / "error.log"
_fh = logging.FileHandler(LOG_FILE, encoding="utf-8"); _fh.setLevel(logging.ERROR)
log.addHandler(_fh)

# ══════════════ ३. UTILS ══════════════
def today(): return date.today().isoformat()
def now(): return datetime.now().isoformat(timespec="seconds")
def num(v, label="रकम", zero_ok=True) -> float:
    s = str(v if v is not None else "").replace(",", "").strip()
    if not s: raise ValueError(f"{label} खाली छ")
    if not re.fullmatch(r"\d+(\.\d+)?|\.\d+", s): raise ValueError(f"{label} मा मान्य number हाल्नुहोस्")
    x = float(s)
    if not math.isfinite(x) or x > 1e12: raise ValueError(f"{label} धेरै ठूलो छ")
    if x == 0 and not zero_ok: raise ValueError(f"{label} 0 भन्दा माथि हुनुपर्छ")
    return round(x, 2)
def qint(v, label="संख्या") -> int:
    s = str(v).strip()
    if not re.fullmatch(r"\d{1,9}", s): raise ValueError(f"{label} पूर्ण संख्या हुनुपर्छ")
    return int(s)
def money(v, dec=0):
    v = float(v or 0)
    return f"{CUR}{v:,.{dec}f}"
def compact(v):
    v = float(v or 0)
    if abs(v) >= 1e7: return f"{v/1e7:.2f}Cr"
    if abs(v) >= 1e5: return f"{v/1e5:.2f}L"
    if abs(v) >= 1e3: return f"{v/1e3:.1f}K"
    return f"{v:.0f}"
def vdate(s):
    s = str(s or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s): raise ValueError("मिति YYYY-MM-DD मा लेख्नुहोस्")
    datetime.strptime(s, "%Y-%m-%d")
    if s > today(): raise ValueError("भविष्यको मिति मिल्दैन")
    return s
def vmonth(s):
    s = str(s or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}", s): raise ValueError("महिना YYYY-MM मा लेख्नुहोस्")
    datetime.strptime(s, "%Y-%m")
    return s
def phone_ok(p):
    p = re.sub(r"[\s\-+]", "", str(p or ""))
    return len(p) >= 10 and p.isdigit()
def phone_norm(p): return re.sub(r"[\s\-+]", "", str(p or "")) or None
def due_of(total, paid): return max(0.0, round(float(total or 0) - float(paid or 0), 2))
def pay_check(total, paid):
    if float(paid) > float(total): raise ValueError("भुक्तानी जम्मा भन्दा बढी हुन सक्दैन")
def total_cost(buy, repair, naam, kar, kar_paid):
    return round(float(buy or 0) + float(repair or 0) + float(naam or 0) + (float(kar or 0) if kar_paid else 0), 2)
def kar_alert(buy_date):
    try: due = datetime.strptime(buy_date, "%Y-%m-%d").date() + timedelta(days=KAR_DAYS)
    except Exception: return None
    days = (due - date.today()).days
    if days > KAR_WARN: return None
    lab = "म्याद नाघ्यो ⚠" if days < 0 else ("आज नै ⚠" if days == 0 else f"{days} दिन बाँकी")
    return lab, days
def esc(v):
    import html
    return html.escape("" if v is None else str(v))
def fname(s): return re.sub(r"[^A-Za-z0-9_-]", "_", str(s))[:60]
def csv_safe(v):
    s = "" if v is None else str(v)
    return "'" + s if s[:1] in ("=", "+", "-", "@", "\t") else s
def ver_tuple(v):
    out = []
    for p in str(v or "0").split("."):
        out.append(int("".join(c for c in p if c.isdigit()) or 0))
    return tuple((out + [0, 0, 0])[:4])
def bill_safe(text):
    low = str(text or "").lower()
    for w in BANNED:
        if w in low: raise ValueError(f"बिलमा भित्री शब्द '{w}' राख्न मिल्दैन")
def export_csv(rows, path):
    import csv
    if not rows: raise ValueError("निर्यात गर्न डाटा छैन")
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows: w.writerow({k: csv_safe(v) for k, v in r.items()})
def save_photo(src, bike_no):
    src = str(src or "")
    if not os.path.isfile(src): raise ValueError("फोटो फाइल भेटिएन")
    ext = os.path.splitext(src)[1].lower()
    if ext not in PHOTO_EXTS: raise ValueError("JPG/PNG/WEBP मात्र समर्थित")
    if os.path.getsize(src) > MAX_PHOTO_MB * 1024 * 1024: raise ValueError(f"फोटो अधिकतम {MAX_PHOTO_MB} MB")
    name = f"{fname(bike_no)}_{int(time.time()*1000)}{ext}"
    shutil.copy2(src, PHOTO_DIR / name)
    return name
def photo_uri(name):
    if not name: return None
    p = PHOTO_DIR / os.path.basename(str(name))
    if not p.is_file(): return None
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(p.suffix.lower().lstrip("."), "jpeg")
    return f"data:image/{mime};base64,{base64.b64encode(p.read_bytes()).decode('ascii')}"

# ══════════════ ४. THEMES (६) ══════════════
class Theme:
    def __init__(self, key, label, **kw):
        self.key, self.label = key, label
        for k, v in kw.items(): setattr(self, k, v)
def _mk(key, label, bg, panel, ink, muted, faint, line, field, acc, accink, ok, bad, warn, info, rail, railink, railmuted, railact, chart):
    return Theme(key, label, BG=bg, PANEL=panel, INK=ink, MUTED=muted, FAINT=faint, LINE=line,
                 FIELD=field, ACCENT=acc, ACCENT_INK=accink, OK=ok, BAD=bad, WARN=warn, INFO=info,
                 RAIL=rail, RAIL_INK=railink, RAIL_MUTED=railmuted, RAIL_ACT=railact, CHART=chart)
THEMES = {
 "porcelain": _mk("porcelain", "Porcelain", "#EEF2F8", "#FFFFFF", "#1A2340", "#6B7690", "#9AA4BC", "#DCE3F0", "#F4F7FC", "#5A5FE0", "#FFFFFF", "#16A34A", "#DC2626", "#D97706", "#0284C7", "#17203A", "#E7ECF7", "#93A0C0", "#5A5FE0", ("#5A5FE0", "#0EA5E9", "#16A34A", "#D97706", "#EC4899")),
 "midnight": _mk("midnight", "Midnight", "#0B1120", "#141B2D", "#F8FAFC", "#94A3B8", "#64748B", "#26324A", "#0F1629", "#3B82F6", "#FFFFFF", "#34D399", "#F87171", "#FBBF24", "#38BDF8", "#070B14", "#CBD5E1", "#64748B", "#3B82F6", ("#3B82F6", "#06B6D4", "#34D399", "#FBBF24", "#EC4899")),
 "ocean": _mk("ocean", "Ocean", "#061826", "#0C2B3E", "#EFFBFF", "#8FB6C9", "#5E8296", "#1B4A63", "#0A2537", "#0EA5E9", "#FFFFFF", "#6EE7B7", "#FDA4AF", "#FBBF24", "#7DD3FC", "#04121C", "#B9D6E4", "#5E8296", "#0EA5E9", ("#0EA5E9", "#22D3EE", "#2DD4BF", "#FBBF24", "#F472B6")),
 "emerald": _mk("emerald", "Emerald", "#071B15", "#0E2A21", "#EFFFF8", "#8FBFAE", "#5F8F7E", "#1E5340", "#0B241C", "#10B981", "#FFFFFF", "#6EE7B7", "#FDA4AF", "#FBBF24", "#7DD3FC", "#04120D", "#BFE3D6", "#5F8F7E", "#10B981", ("#10B981", "#2DD4BF", "#A3E635", "#FBBF24", "#F472B6")),
 "sunset": _mk("sunset", "Sunset", "#1B0813", "#2A1220", "#FFF1F6", "#C79AAE", "#96687C", "#59243A", "#2A1020", "#F43F5E", "#FFFFFF", "#6EE7B7", "#FDA4AF", "#FDBA74", "#C4B5FD", "#140711", "#E4BCCB", "#96687C", "#F43F5E", ("#F43F5E", "#FB923C", "#FBBF24", "#A855F7", "#2DD4BF")),
 "slate": _mk("slate", "Slate", "#101418", "#1A2027", "#E8EDF2", "#9AA7B4", "#6B7885", "#2C3641", "#161C23", "#8B5CF6", "#FFFFFF", "#4ADE80", "#F87171", "#FACC15", "#60A5FA", "#0B0E12", "#C6D0DA", "#6B7885", "#8B5CF6", ("#8B5CF6", "#60A5FA", "#4ADE80", "#FACC15", "#F472B6")),
}
THEME_ORDER = ("porcelain", "midnight", "ocean", "emerald", "sunset", "slate")
T = THEMES["porcelain"]
def apply_theme(key):
    global T
    T = THEMES.get(str(key or "").strip(), THEMES["porcelain"])
def mix(a, b, t):
    a, b = a.lstrip("#"), b.lstrip("#")
    ar, ag, ab = (int(a[i:i+2], 16) for i in (0, 2, 4))
    br, bg, bb = (int(b[i:i+2], 16) for i in (0, 2, 4))
    return "#%02X%02X%02X" % (int(ar+(br-ar)*t), int(ag+(bg-ag)*t), int(ab+(bb-ab)*t))

# ══════════════ ५. भाषा ══════════════
_lang = "ne"
LANGS = {
 "ne": {"dash": "ड्यासबोर्ड", "bikes": "बाइक", "cost": "लागत पाना", "acc": "सामान", "svc": "सेवा",
        "parts": "पार्ट्स", "cust": "ग्राहक", "bills": "बिल", "cash": "नगद", "exp": "खर्च",
        "staff": "कर्मचारी", "rep": "रिपोर्ट", "audit": "लग", "set": "सेटिङ", "pw": "पासवर्ड",
        "login": "लगइन", "user": "प्रयोगकर्ता", "pass": "पासवर्ड", "logout": "लगआउट",
        "buy": "खरिद", "sell": "बिक्री", "edit": "सम्पादन", "delete": "हटाउनु", "add": "थप्नु",
        "print": "छाप्नु", "collect": "असुल", "void": "रद्द", "stock": "स्टक", "sold": "बिकिभयो",
        "today": "आज", "month": "यो महिना", "pending": "बाँकी", "in_stock": "स्टक बाइक",
        "opening": "खुल्दा", "cash_in": "नगद आयो", "cash_out": "नगद गयो", "closing": "बन्द मौज्दात",
        "close_day": "दिन बन्द", "reopen": "पुनः खोल्नु", "theme": "थिम", "lang": "भाषा",
        "welcome": "स्वागत छ", "select_row": "पहिले पङ्क्ति छान्नुहोस्", "confirm": "पुष्टि"},
 "en": {"dash": "Dashboard", "bikes": "Bikes", "cost": "Cost Sheet", "acc": "Accessories", "svc": "Services",
        "parts": "Parts", "cust": "Customers", "bills": "Bills", "cash": "Cash Book", "exp": "Expenses",
        "staff": "Staff", "rep": "Reports", "audit": "Audit", "set": "Settings", "pw": "Password",
        "login": "Login", "user": "Username", "pass": "Password", "logout": "Logout",
        "buy": "Buy", "sell": "Sell", "edit": "Edit", "delete": "Delete", "add": "Add",
        "print": "Print", "collect": "Collect", "void": "Void", "stock": "Stock", "sold": "Sold",
        "today": "Today", "month": "This Month", "pending": "Pending", "in_stock": "In Stock",
        "opening": "Opening", "cash_in": "Cash In", "cash_out": "Cash Out", "closing": "Closing",
        "close_day": "Close Day", "reopen": "Re-open", "theme": "Theme", "lang": "Language",
        "welcome": "Welcome", "select_row": "Select a row first", "confirm": "Confirm"},
}
def t(k): return LANGS.get(_lang, LANGS["ne"]).get(k, k)
def set_lang(l):
    global _lang
    if l in LANGS: _lang = l

# ══════════════ ६. DPAPI (Windows मात्र) ══════════════
DPAPI_ENTROPY = b"SHUVAM.RH.v10"
def dpapi_ok(): return os.name == "nt"
if os.name == "nt":
    from ctypes import wintypes
    class _BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]
    _c32, _k32 = ctypes.windll.crypt32, ctypes.windll.kernel32
    _c32.CryptProtectData.argtypes = [ctypes.POINTER(_BLOB), wintypes.LPCWSTR, ctypes.POINTER(_BLOB),
                                      ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_BLOB)]
    _c32.CryptProtectData.restype = wintypes.BOOL
    _c32.CryptUnprotectData.argtypes = [ctypes.POINTER(_BLOB), ctypes.POINTER(wintypes.LPWSTR),
                                        ctypes.POINTER(_BLOB), ctypes.c_void_p, ctypes.c_void_p,
                                        wintypes.DWORD, ctypes.POINTER(_BLOB)]
    _c32.CryptUnprotectData.restype = wintypes.BOOL
    _k32.LocalFree.argtypes = [ctypes.c_void_p]
    def _dpapi(data, protect):
        buf = ctypes.create_string_buffer(data, len(data))
        inb = _BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
        eb = ctypes.create_string_buffer(DPAPI_ENTROPY, len(DPAPI_ENTROPY))
        ent = _BLOB(len(DPAPI_ENTROPY), ctypes.cast(eb, ctypes.POINTER(ctypes.c_char)))
        out = _BLOB()
        if protect:
            ok = _c32.CryptProtectData(ctypes.byref(inb), "SHUVAM Vault", ctypes.byref(ent), None, None, 0x1, ctypes.byref(out))
        else:
            ok = _c32.CryptUnprotectData(ctypes.byref(inb), None, ctypes.byref(ent), None, None, 0x1, ctypes.byref(out))
        if not ok: raise OSError("DPAPI असफल")
        try: return ctypes.string_at(out.pbData, out.cbData)
        finally: _k32.LocalFree(ctypes.cast(out.pbData, ctypes.c_void_p))
else:
    def _dpapi(data, protect):
        raise RuntimeError("DPAPI केवल Windows मा — cloud sync Windows मा मात्र चल्छ")
def dp_encrypt(b): return base64.b64encode(_dpapi(b, True)).decode("ascii")
def dp_decrypt(tok): return _dpapi(base64.b64decode(tok), False)

# ══════════════ ७. Windows Hello ══════════════
HELLO_PS = r'''
$ErrorActionPreference = 'Stop'
try {
  Add-Type -AssemblyName System.Runtime.WindowsRuntime | Out-Null
  [Windows.Security.Credentials.UI.UserConsentVerifier,Windows.Security.Credentials.UI,ContentType=WindowsRuntime] | Out-Null
  $asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
  $op = [Windows.Security.Credentials.UI.UserConsentVerifier]::RequestVerificationAsync($env:SHUVAM_HELLO_MSG)
  $task = $asTask.MakeGenericMethod([Windows.Security.Credentials.UI.UserConsentVerificationResult]).Invoke($null, @($op))
  if (-not $task.Wait(65000)) { Write-Output 'RESULT:Timeout'; exit 2 }
  Write-Output ('RESULT:' + $task.Result)
} catch { Write-Output ('ERROR:' + $_.Exception.Message); exit 1 }
'''
def hello_verify(message="Login to SHUVAM"):
    if os.name != "nt": return False, "Windows Hello केवल Windows मा"
    path = None
    try:
        fd, path = tempfile.mkstemp(prefix="shuvam_hello_", suffix=".ps1")
        with os.fdopen(fd, "w", encoding="utf-8") as fh: fh.write(HELLO_PS)
        env = dict(os.environ, SHUVAM_HELLO_MSG=message[:120])
        p = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-STA",
                            "-ExecutionPolicy", "Bypass", "-File", path],
                           capture_output=True, text=True, timeout=75,
                           creationflags=0x08000000, env=env)
        out = (p.stdout or "").strip()
        if "RESULT:Verified" in out: return True, "Verified"
        if "RESULT:Canceled" in out: return False, "रद्द गरियो"
        if "RESULT:Timeout" in out: return False, "समय सकियो"
        if "ERROR:" in out: return False, out.split("ERROR:", 1)[1].strip()[:160]
        return False, (out.splitlines()[-1] if out else (p.stderr or "उपलब्ध छैन")[:160])
    except Exception as e:
        return False, str(e)[:160]
    finally:
        try:
            if path: os.unlink(path)
        except OSError: pass

# ══════════════ ८. ICON (stdlib PNG) ══════════════
def _png_chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
def make_icon(size=256):
    try:
        w = h = size; buf = bytearray(w * h * 4)
        c1, c2 = (23, 32, 58), (90, 95, 224)
        rad = size * 0.22; m = size * 0.06
        cx, cy = w / 2, h / 2
        for y in range(h):
            for x in range(w):
                qx = abs(x + .5 - cx) - (w / 2 - m - rad); qy = abs(y + .5 - cy) - (h / 2 - m - rad)
                d = math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - rad
                if d > 0.5: continue
                tt = (x / w + y / h) / 2
                r = int(c1[0] + (c2[0] - c1[0]) * tt); g = int(c1[1] + (c2[1] - c1[1]) * tt); b = int(c1[2] + (c2[2] - c1[2]) * tt)
                ring = abs(math.hypot(x - cx, y - cy) - size * 0.30)
                if ring < size * 0.045: r, g, b = 255, 255, 255
                i = (y * w + x) * 4
                buf[i:i+4] = bytes((r, g, b, 255 if d < -0.5 else int(255 * (0.5 - d))))
        raw = bytearray()
        for y in range(h):
            raw.append(0); raw.extend(buf[y * w * 4:(y + 1) * w * 4])
        png = (b"\x89PNG\r\n\x1a\n" + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
               + _png_chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + _png_chunk(b"IEND", b""))
        ICON_PNG.write_bytes(png)
        return ICON_PNG
    except Exception:
        log.exception("icon"); return None

# ══════════════ ९. STORE (SQLite + hash-chain audit) ══════════════
SCHEMA = """
CREATE TABLE IF NOT EXISTS settings(id INTEGER PRIMARY KEY CHECK(id=1), shop_name TEXT, address TEXT,
  mobile TEXT, pan TEXT, owner TEXT, bill_note TEXT, theme TEXT DEFAULT 'porcelain', lang TEXT DEFAULT 'ne',
  hello_login INTEGER DEFAULT 0, hello_user TEXT DEFAULT '', update_url TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, hash TEXT, salt TEXT, role TEXT DEFAULT 'staff',
  must_change INTEGER DEFAULT 0, created_at TEXT);
CREATE TABLE IF NOT EXISTS guard(k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE IF NOT EXISTS bikes(id INTEGER PRIMARY KEY AUTOINCREMENT, brand TEXT, model TEXT, color TEXT,
  year TEXT, engine_no TEXT DEFAULT '', chassis_no TEXT DEFAULT '', bb_expiry TEXT DEFAULT '',
  photo_path TEXT DEFAULT '', bike_no TEXT UNIQUE, seller_name TEXT DEFAULT '', seller_phone TEXT DEFAULT '',
  buy_price REAL DEFAULT 0, repair_cost REAL DEFAULT 0, naam_sari REAL DEFAULT 0, kar_cost REAL DEFAULT 0,
  kar_paid INTEGER DEFAULT 0, total_cost REAL DEFAULT 0, sell_price REAL DEFAULT 0, profit REAL DEFAULT 0,
  status TEXT DEFAULT 'Stock', buy_date TEXT, sell_date TEXT DEFAULT '', method TEXT DEFAULT 'Cash',
  is_deleted INTEGER DEFAULT 0, created_at TEXT);
CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT,
  address TEXT DEFAULT '', citizenship TEXT DEFAULT '', created_at TEXT);
CREATE TABLE IF NOT EXISTS bills(id INTEGER PRIMARY KEY AUTOINCREMENT, bill_no TEXT UNIQUE, bill_type TEXT,
  ref_id INTEGER, customer_id INTEGER, customer TEXT, phone TEXT, detail TEXT, total REAL DEFAULT 0,
  paid REAL DEFAULT 0, due REAL DEFAULT 0, payment TEXT, voided INTEGER DEFAULT 0, void_reason TEXT DEFAULT '',
  is_deleted INTEGER DEFAULT 0, created_at TEXT);
CREATE TABLE IF NOT EXISTS bill_counter(id INTEGER PRIMARY KEY CHECK(id=1), next_no INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS payments(id INTEGER PRIMARY KEY AUTOINCREMENT, bill_id INTEGER, bill_no TEXT,
  amount REAL, method TEXT, note TEXT DEFAULT '', created_at TEXT);
CREATE TABLE IF NOT EXISTS ledger(id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER, name TEXT,
  phone TEXT, type TEXT, description TEXT, udharo REAL DEFAULT 0, tiryo REAL DEFAULT 0, balance REAL DEFAULT 0,
  date TEXT, bill_no TEXT);
CREATE TABLE IF NOT EXISTS cashbook(id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, type TEXT, category TEXT,
  amount REAL, method TEXT, note TEXT DEFAULT '', created_at TEXT);
CREATE TABLE IF NOT EXISTS cash_closures(date TEXT PRIMARY KEY, opening REAL, cash_in REAL, cash_out REAL,
  closing REAL, note TEXT, closed_by TEXT, closed_at TEXT);
CREATE TABLE IF NOT EXISTS accessories(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, category TEXT,
  stock INTEGER DEFAULT 0, buy_price REAL DEFAULT 0, sell_price REAL DEFAULT 0);
CREATE TABLE IF NOT EXISTS acc_sales(id INTEGER PRIMARY KEY AUTOINCREMENT, accessory_id INTEGER, item TEXT,
  qty INTEGER, price REAL, unit_cost REAL DEFAULT 0, total REAL, customer_id INTEGER, customer TEXT,
  phone TEXT, payment TEXT, date TEXT, bill_no TEXT, is_deleted INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS plates(id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER, customer TEXT,
  phone TEXT, bike_no TEXT, plate_no TEXT DEFAULT '', plate_type TEXT, cost REAL DEFAULT 0, charge REAL DEFAULT 0,
  paid REAL DEFAULT 0, due REAL DEFAULT 0, status TEXT, date TEXT, bill_no TEXT, is_deleted INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS repairs(id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER, customer TEXT,
  phone TEXT, bike_no TEXT, bike_model TEXT, problem TEXT, parts_cost REAL DEFAULT 0, labour REAL DEFAULT 0,
  total REAL DEFAULT 0, paid REAL DEFAULT 0, due REAL DEFAULT 0, status TEXT, date TEXT, bill_no TEXT,
  is_deleted INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS parts(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, category TEXT,
  stock INTEGER DEFAULT 0, unit_cost REAL DEFAULT 0, threshold INTEGER DEFAULT 3);
CREATE TABLE IF NOT EXISTS part_usage(id INTEGER PRIMARY KEY AUTOINCREMENT, part_id INTEGER, bike_no TEXT,
  qty INTEGER, unit_cost REAL, date TEXT);
CREATE TABLE IF NOT EXISTS labour(id INTEGER PRIMARY KEY AUTOINCREMENT, bike_no TEXT, description TEXT,
  mechanic TEXT, amount REAL, paid_cash INTEGER DEFAULT 1, date TEXT);
CREATE TABLE IF NOT EXISTS expenses(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, category TEXT,
  amount REAL, date TEXT, method TEXT, note TEXT DEFAULT '', is_deleted INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS staff(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT, role TEXT,
  salary REAL DEFAULT 0, active INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS salaries(id INTEGER PRIMARY KEY AUTOINCREMENT, staff_id INTEGER, month TEXT,
  amount REAL, date TEXT, method TEXT, note TEXT DEFAULT '', UNIQUE(staff_id, month));
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, actor TEXT, action TEXT,
  detail TEXT, prev_hash TEXT, hash TEXT);
CREATE INDEX IF NOT EXISTS idx_bills_no ON bills(bill_no);
CREATE INDEX IF NOT EXISTS idx_bills_cust ON bills(customer_id);
CREATE INDEX IF NOT EXISTS idx_cash_date ON cashbook(date);
CREATE INDEX IF NOT EXISTS idx_ledger_cust ON ledger(customer_id);
CREATE INDEX IF NOT EXISTS idx_usage_bike ON part_usage(bike_no);
CREATE INDEX IF NOT EXISTS idx_labour_bike ON labour(bike_no);
"""
class Store:
    def __init__(self, path):
        self.path = Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
        self.actor = "system"
        boot = sqlite3.connect(str(self.path), timeout=30)
        try: boot.execute("PRAGMA journal_mode=WAL")
        finally: boot.close()
        with self.tx() as c:
            c.executescript(SCHEMA)
            c.execute("INSERT OR IGNORE INTO settings(id,shop_name,address,mobile,pan,owner,bill_note,update_url) "
                      "VALUES(1,?,?,?,?,?,?,?)", (APP_NAME, "Hatti Chowk, Tulsipur, Dang", "", "", "Shuvam",
                      "७ दिनभित्र समस्या भए सम्पर्क गर्नुहोला। धन्यवाद!", UPDATE_URL_DEFAULT))
            c.execute("INSERT OR IGNORE INTO bill_counter(id,next_no) VALUES(1,1)")
            have = {r[1] for r in c.execute("PRAGMA table_info(bikes)")}
            for col, typ in (("photo_path", "TEXT DEFAULT ''"), ("engine_no", "TEXT DEFAULT ''"),
                             ("chassis_no", "TEXT DEFAULT ''"), ("bb_expiry", "TEXT DEFAULT ''")):
                if col not in have: c.execute(f"ALTER TABLE bikes ADD COLUMN {col} {typ}")
            have_s = {r[1] for r in c.execute("PRAGMA table_info(settings)")}
            for col, typ in (("email", "TEXT DEFAULT ''"), ("website", "TEXT DEFAULT ''")):
                if col not in have_s: c.execute(f"ALTER TABLE settings ADD COLUMN {col} {typ}")
    def _conn(self):
        c = sqlite3.connect(str(self.path), timeout=30)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA busy_timeout=30000"); c.execute("PRAGMA foreign_keys=ON")
        return c
    @contextmanager
    def rd(self):
        c = self._conn()
        try: yield c
        finally: c.close()
    @contextmanager
    def tx(self):
        c = self._conn()
        try:
            c.execute("BEGIN IMMEDIATE"); yield c; c.commit()
        except BaseException:
            c.rollback(); raise
        finally: c.close()
    def q(self, sql, args=()):
        with self.rd() as c: return c.execute(sql, args).fetchall()
    def one(self, sql, args=()):
        with self.rd() as c: return c.execute(sql, args).fetchone()
    def val(self, sql, args=(), default=0):
        r = self.one(sql, args)
        return r[0] if r and r[0] is not None else default
    def audit(self, c, action, detail=""):
        prev = c.execute("SELECT hash FROM audit ORDER BY id DESC LIMIT 1").fetchone()
        ph = prev["hash"] if prev else GENESIS
        ts = now()
        h = hashlib.sha256(f"{ph}|{self.actor}|{action}|{detail}|{ts}".encode()).hexdigest()
        c.execute("INSERT INTO audit(ts,actor,action,detail,prev_hash,hash) VALUES(?,?,?,?,?,?)",
                  (ts, self.actor, action, str(detail)[:500], ph, h))
    def verify_chain(self):
        prev = GENESIS
        with self.rd() as c:
            rows = c.execute("SELECT * FROM audit ORDER BY id").fetchall()
        for r in rows:
            if r["prev_hash"] != prev: return False, r["id"]
            if hashlib.sha256(f"{r['prev_hash']}|{r['actor']}|{r['action']}|{r['detail']}|{r['ts']}".encode()).hexdigest() != r["hash"]:
                return False, r["id"]
            prev = r["hash"]
        return True, len(rows)
    def backup(self, dest):
        dest = Path(dest); dest.parent.mkdir(parents=True, exist_ok=True)
        src = self._conn(); dst = sqlite3.connect(str(dest))
        try: src.backup(dst)
        finally: dst.close(); src.close()
        return dest
    def auto_backup(self, keep=14):
        p = BACKUP_DIR / f"auto_{date.today():%Y%m%d}.db"
        if p.exists(): return
        self.backup(p)
        files = sorted(BACKUP_DIR.glob("auto_*.db"))
        for f in files[:-keep]:
            try: f.unlink()
            except OSError: pass
DB = None
def db():
    global DB
    if DB is None: DB = Store(DB_FILE)
    return DB

# ══════════════ १०. AUTH ══════════════
def _hash(pw, salt=None):
    salt = salt or secrets.token_bytes(16)
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, PBKDF2).hex(), salt.hex()
def user_count(): return db().val("SELECT COUNT(*) FROM users")
def user_add(u, p, role="staff"):
    u = (u or "").strip()
    if not u: raise ValueError("Username खाली हुन सक्दैन")
    if role not in ("owner", "staff"): raise ValueError("Role owner/staff मात्र")
    if len(p or "") < PW_MIN: raise ValueError(f"पासवर्ड कम्तीमा {PW_MIN} अक्षर")
    h, s = _hash(p)
    try:
        with db().tx() as c:
            c.execute("INSERT INTO users(username,hash,salt,role,must_change,created_at) VALUES(?,?,?,?,0,?)",
                      (u, h, s, role, now()))
            db().audit(c, "USER_ADD", f"{u} ({role})")
    except sqlite3.IntegrityError:
        raise ValueError("Username पहिले नै छ") from None
def user_delete(u, actor="system"):
    u = (u or "").strip()
    if not u: raise ValueError("Username खाली हुन सक्दैन")
    r = db().one("SELECT role FROM users WHERE username=?", (u,))
    if not r: raise ValueError("प्रयोगकर्ता भेटिएन")
    if r["role"] == "owner":
        owners = db().val("SELECT COUNT(*) FROM users WHERE role='owner'")
        if owners <= 1: raise ValueError("कम्तीमा एक Owner राख्नुपर्छ")
    if u == actor: raise ValueError("आफैलाई हटाउन मिल्दैन")
    with db().tx() as c:
        c.execute("DELETE FROM users WHERE username=?", (u,))
        db().audit(c, "USER_DELETE", u)
def authenticate(u, p):
    r = db().one("SELECT * FROM users WHERE username=?", ((u or "").strip(),))
    if not r: return None
    h, _ = _hash(p or "", bytes.fromhex(r["salt"]))
    if hmac.compare_digest(h, r["hash"]):
        return {"user": r["username"], "role": r["role"], "must": int(r["must_change"] or 0)}
    return None
def change_pw(u, old, new, conf):
    if new != conf: raise ValueError("नयाँ पासवर्ड र पुष्टि मिलेन")
    if len(new or "") < PW_MIN: raise ValueError(f"पासवर्ड कम्तीमा {PW_MIN} अक्षर")
    if old == new: raise ValueError("नयाँ पासवर्ड पुरानो जस्तै हुन सक्दैन")
    r = db().one("SELECT * FROM users WHERE username=?", (u,))
    if not r: raise ValueError("प्रयोगकर्ता भेटिएन")
    h, _ = _hash(old or "", bytes.fromhex(r["salt"]))
    if not hmac.compare_digest(h, r["hash"]): raise ValueError("पुरानो पासवर्ड गलत")
    nh, ns = _hash(new)
    with db().tx() as c:
        c.execute("UPDATE users SET hash=?,salt=?,must_change=0 WHERE username=?", (nh, ns, u))
        db().audit(c, "PW_CHANGE", u)
def login_state(u):
    f = db().val("SELECT v FROM guard WHERE k=?", (f"f:{u}",), "0")
    l = db().val("SELECT v FROM guard WHERE k=?", (f"l:{u}",), "0")
    try: return int(f), float(l)
    except (ValueError, TypeError): return 0, 0.0
def login_fail(u):
    f, _ = login_state(u); f += 1; lock = 0.0
    if f >= LOCK_TRIES: f, lock = 0, time.time() + LOCK_SECONDS
    with db().tx() as c:
        c.execute("INSERT OR REPLACE INTO guard(k,v) VALUES(?,?)", (f"f:{u}", str(f)))
        c.execute("INSERT OR REPLACE INTO guard(k,v) VALUES(?,?)", (f"l:{u}", str(lock)))
        if lock: db().audit(c, "LOGIN_LOCK", u)
    return f, lock
def login_ok(u):
    with db().tx() as c:
        c.execute("DELETE FROM guard WHERE k IN (?,?)", (f"f:{u}", f"l:{u}"))

# ══════════════ ११. BUSINESS LOGIC ══════════════
def _customer_resolve(c, name, phone, address="", citizenship=""):
    name = re.sub(r"\s+", " ", (name or "").strip())
    if not name: raise ValueError("ग्राहक नाम चाहिन्छ")
    ph = phone_norm(phone)
    if ph:
        r = c.execute("SELECT id FROM customers WHERE name=? COLLATE NOCASE AND "
                      "REPLACE(REPLACE(REPLACE(COALESCE(phone,''),' ',''),'-',''),'+','')=? ORDER BY id LIMIT 1",
                      (name, ph)).fetchone()
    else:
        r = c.execute("SELECT id FROM customers WHERE name=? COLLATE NOCASE AND "
                      "(phone IS NULL OR phone='') ORDER BY id LIMIT 1", (name,)).fetchone()
    if r:
        c.execute("UPDATE customers SET address=CASE WHEN COALESCE(address,'')='' THEN ? ELSE address END, "
                  "citizenship=CASE WHEN COALESCE(citizenship,'')='' THEN ? ELSE citizenship END WHERE id=?",
                  ((address or "").strip(), (citizenship or "").strip(), r["id"]))
        return r["id"]
    return c.execute("INSERT INTO customers(name,phone,address,citizenship,created_at) VALUES(?,?,?,?,?)",
                     (name, ph, (address or "").strip(), (citizenship or "").strip(), now())).lastrowid
def _bill_no(c):
    n = c.execute("SELECT next_no FROM bill_counter WHERE id=1").fetchone()["next_no"]
    c.execute("UPDATE bill_counter SET next_no=? WHERE id=1", (n + 1,))
    return f"SVM{n:05d}"
def _ledger(c, cid, name, phone, typ, desc, udharo, tiryo, bill_no=""):
    prev = c.execute("SELECT COALESCE(SUM(udharo-tiryo),0) FROM ledger WHERE customer_id=?", (cid,)).fetchone()[0]
    bal = round(prev + udharo - tiryo, 2)
    c.execute("INSERT INTO ledger(customer_id,name,phone,type,description,udharo,tiryo,balance,date,bill_no) "
              "VALUES(?,?,?,?,?,?,?,?,?,?)", (cid, name, phone, typ, desc, udharo, tiryo, bal, today(), bill_no))
    return bal
def _cash(c, d, typ, cat, amount, method, note=""):
    if method != "Cash" or round(float(amount or 0), 2) <= 0: return
    vdate(d)
    mx = c.execute("SELECT MAX(date) FROM cash_closures").fetchone()[0]
    if mx and d <= mx:
        raise ValueError(f"नगद {mx} सम्म बन्द छ — {d} मा entry मिल्दैन। पहिले दिन पुनः खोल्नुहोस्।")
    c.execute("INSERT INTO cashbook(date,type,category,amount,method,note,created_at) VALUES(?,?,?,?,?,?,?)",
              (d, typ, cat, round(float(amount), 2), method, note, now()))
def _create_bill(c, btype, ref_id, cid, name, phone, detail, total, paid, method):
    bill_safe(detail)
    pay_check(total, paid)
    no = _bill_no(c)
    due = due_of(total, paid)
    bid = c.execute("INSERT INTO bills(bill_no,bill_type,ref_id,customer_id,customer,phone,detail,total,paid,due,"
                    "payment,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (no, btype, ref_id, cid, name, phone, detail, total, paid, due, method, now())).lastrowid
    if paid > 0:
        c.execute("INSERT INTO payments(bill_id,bill_no,amount,method,note,created_at) VALUES(?,?,?,?,?,?)",
                  (bid, no, paid, method, "बिक्री", now()))
        _cash(c, today(), "In", f"{btype} Sale", paid, method, f"{no} {name}")
    if due > 0:
        _ledger(c, cid, name, phone, "उधारो", f"{btype} {no}", due, 0, no)
    return no
def bike_extra_cost(c, bike_no):
    p = c.execute("SELECT COALESCE(SUM(qty*unit_cost),0) FROM part_usage WHERE bike_no=?", (bike_no,)).fetchone()[0]
    l = c.execute("SELECT COALESCE(SUM(amount),0) FROM labour WHERE bike_no=?", (bike_no,)).fetchone()[0]
    return round(p + l, 2)
def bike_buy(d):
    bno = re.sub(r"\s+", " ", str(d.get("bike_no") or "").strip().upper())
    if not bno: raise ValueError("Bike No चाहिन्छ")
    buy = num(d.get("buy_price"), "खरिद मूल्य", zero_ok=False)
    rep = num(d.get("repair_cost") or 0, "मर्मत"); ns = num(d.get("naam_sari") or 0, "नामसारी")
    kc = num(d.get("kar_cost") or 0, "कर"); kp = bool(d.get("kar_paid"))
    method = d.get("method") or "Cash"
    if method not in METHODS: raise ValueError("भुक्तानी माध्यम मान्य छैन")
    bd = vdate(d.get("buy_date") or today())
    bb = str(d.get("bb_expiry") or "").strip()
    if bb: vdate(bb) if bb <= today() else datetime.strptime(bb, "%Y-%m-%d")
    tc = total_cost(buy, rep, ns, kc, kp)
    with db().tx() as c:
        if c.execute("SELECT 1 FROM bikes WHERE bike_no=? AND is_deleted=0", (bno,)).fetchone():
            raise ValueError(f"Bike {bno} पहिले नै छ")
        bid = c.execute("INSERT INTO bikes(brand,model,color,year,engine_no,chassis_no,bb_expiry,photo_path,"
                        "bike_no,seller_name,seller_phone,buy_price,repair_cost,naam_sari,kar_cost,kar_paid,"
                        "total_cost,status,buy_date,method,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'Stock',?,?,?)",
                        (d.get("brand", "Honda"), d.get("model", ""), d.get("color", COLORS[0]), d.get("year", YEARS[0]),
                         str(d.get("engine_no") or "").upper(), str(d.get("chassis_no") or "").upper(), bb,
                         d.get("photo_path") or "", bno, d.get("seller_name", ""), d.get("seller_phone", ""),
                         buy, rep, ns, kc, int(kp), tc, bd, method, now())).lastrowid
        _cash(c, bd, "Out", "Bike Purchase", buy, method, bno)
        if rep: _cash(c, bd, "Out", "Repair", rep, method, bno)
        if ns: _cash(c, bd, "Out", "Name Transfer", ns, method, bno)
        if kp and kc: _cash(c, bd, "Out", "Tax", kc, method, bno)
        db().audit(c, "BIKE_BUY", f"{bno} cost {tc}")
    return bid
def bike_edit(bid, d):
    with db().tx() as c:
        r = c.execute("SELECT * FROM bikes WHERE id=? AND is_deleted=0", (bid,)).fetchone()
        if not r: raise ValueError("Bike भेटिएन")
        buy = num(d.get("buy_price", r["buy_price"]), "खरिद")
        rep = num(d.get("repair_cost", r["repair_cost"]), "मर्मत")
        ns = num(d.get("naam_sari", r["naam_sari"]), "नामसारी")
        kc = num(d.get("kar_cost", r["kar_cost"]), "कर"); kp = bool(d.get("kar_paid", r["kar_paid"]))
        tc = total_cost(buy, rep, ns, kc, kp)
        extra = bike_extra_cost(c, r["bike_no"])
        profit = round((r["sell_price"] or 0) - tc - extra, 2) if r["status"] == "Sold" else 0
        bno = re.sub(r"\s+", " ", str(d.get("bike_no", r["bike_no"])).strip().upper())
        dup = c.execute("SELECT 1 FROM bikes WHERE bike_no=? AND id<>? AND is_deleted=0", (bno, bid)).fetchone()
        if dup: raise ValueError("उक्त Bike No अर्कोमा छ")
        c.execute("UPDATE bikes SET brand=?,model=?,color=?,year=?,engine_no=?,chassis_no=?,bb_expiry=?, "
                  "bike_no=?,seller_name=?,seller_phone=?,buy_price=?,repair_cost=?,naam_sari=?,kar_cost=?, "
                  "kar_paid=?,total_cost=?,profit=? WHERE id=?",
                  (d.get("brand", r["brand"]), d.get("model", r["model"]), d.get("color", r["color"]),
                   d.get("year", r["year"]), str(d.get("engine_no", r["engine_no"])).upper(),
                   str(d.get("chassis_no", r["chassis_no"])).upper(), d.get("bb_expiry", r["bb_expiry"]),
                   bno, d.get("seller_name", r["seller_name"]), d.get("seller_phone", r["seller_phone"]),
                   buy, rep, ns, kc, int(kp), tc, profit, bid))
        db().audit(c, "BIKE_EDIT", f"{bno} cost {tc}")
def bike_docs(bid, engine, chassis, bb, photo):
    bb = str(bb or "").strip()
    if bb: datetime.strptime(bb, "%Y-%m-%d")
    with db().tx() as c:
        r = c.execute("SELECT bike_no, photo_path FROM bikes WHERE id=?", (bid,)).fetchone()
        if not r: raise ValueError("Bike भेटिएन")
        c.execute("UPDATE bikes SET engine_no=?,chassis_no=?,bb_expiry=?,photo_path=? WHERE id=?",
                  (str(engine or "").upper(), str(chassis or "").upper(), bb, photo or r["photo_path"], bid))
        db().audit(c, "BIKE_DOCS", r["bike_no"])
        return r["photo_path"]
def bike_sell(bid, d, price, paid, method):
    price = num(price, "बिक्री मूल्य", zero_ok=False); paid = num(paid or 0, "भुक्तानी")
    pay_check(price, paid)
    if method not in METHODS: raise ValueError("माध्यम मान्य छैन")
    with db().tx() as c:
        r = c.execute("SELECT * FROM bikes WHERE id=? AND is_deleted=0", (bid,)).fetchone()
        if not r or r["status"] != "Stock": raise ValueError("यो बाइक स्टकमा छैन")
        cid = _customer_resolve(c, d.get("name"), d.get("phone"), d.get("address", ""), d.get("citizenship", ""))
        extra = bike_extra_cost(c, r["bike_no"])
        profit = round(price - (r["total_cost"] or 0) - extra, 2)
        detail = f"{r['brand']} {r['model']} · {r['bike_no']}"
        no = _create_bill(c, "BIKE", bid, cid, d["name"].strip(), phone_norm(d.get("phone")) or "",
                          detail, price, paid, method)
        c.execute("UPDATE bikes SET status='Sold',sell_price=?,profit=?,sell_date=? WHERE id=?",
                  (price, profit, today(), bid))
        db().audit(c, "BIKE_SELL", f"{no} {r['bike_no']} {price}")
    return no
def bike_delete(bid):
    with db().tx() as c:
        r = c.execute("SELECT bike_no FROM bikes WHERE id=?", (bid,)).fetchone()
        if not r: raise ValueError("Bike भेटिएन")
        c.execute("UPDATE bikes SET is_deleted=1 WHERE id=?", (bid,))
        db().audit(c, "BIKE_DELETE", r["bike_no"])
def acc_add(name, cat, qty, buy, sell):
    name = (name or "").strip()
    if not name: raise ValueError("नाम चाहिन्छ")
    qty = qint(qty, "मात्रा"); buy = num(buy or 0, "खरिद"); sell = num(sell or 0, "बिक्री")
    with db().tx() as c:
        if c.execute("SELECT 1 FROM accessories WHERE name=? COLLATE NOCASE", (name,)).fetchone():
            raise ValueError("सामान पहिले नै छ — Restock प्रयोग गर्नुहोस्")
        c.execute("INSERT INTO accessories(name,category,stock,buy_price,sell_price) VALUES(?,?,?,?,?)",
                  (name, cat, qty, buy, sell))
        if qty and buy: _cash(c, today(), "Out", "Accessory Purchase", qty * buy, "Cash", name)
        db().audit(c, "ACC_ADD", name)
def acc_restock(aid, qty, buy, sell, method):
    qty = qint(qty, "मात्रा")
    if qty <= 0: raise ValueError("मात्रा 1+ हुनुपर्छ")
    buy = num(buy or 0, "खरिद"); sell = num(sell or 0, "बिक्री")
    if method not in METHODS: raise ValueError("माध्यम मान्य छैन")
    with db().tx() as c:
        r = c.execute("SELECT * FROM accessories WHERE id=?", (aid,)).fetchone()
        if not r: raise ValueError("सामान भेटिएन")
        nq = (r["stock"] or 0) + qty
        avg = round(((r["stock"] or 0) * (r["buy_price"] or 0) + qty * buy) / nq, 2) if buy > 0 else r["buy_price"]
        ns = sell if sell > 0 else r["sell_price"]
        c.execute("UPDATE accessories SET stock=?,buy_price=?,sell_price=? WHERE id=?", (nq, avg, ns, aid))
        _cash(c, today(), "Out", "Accessory Purchase", qty * buy, method, r["name"])
        db().audit(c, "ACC_RESTOCK", f"{r['name']} +{qty}")
def acc_sell(aid, qty, price, d, paid, method):
    qty = qint(qty, "संख्या")
    if qty <= 0: raise ValueError("संख्या 1+ हुनुपर्छ")
    price = num(price, "दर", zero_ok=False); paid = num(paid or 0, "भुक्तानी")
    pay_check(price * qty, paid)
    if method not in METHODS: raise ValueError("माध्यम मान्य छैन")
    with db().tx() as c:
        r = c.execute("SELECT * FROM accessories WHERE id=?", (aid,)).fetchone()
        if not r: raise ValueError("सामान भेटिएन")
        if (r["stock"] or 0) < qty: raise ValueError(f"स्टक अपर्याप्त ({r['stock']})")
        total = round(price * qty, 2)
        cid = _customer_resolve(c, d.get("name"), d.get("phone"))
        no = _create_bill(c, "ACC", aid, cid, d["name"].strip(), phone_norm(d.get("phone")) or "",
                          f"{r['name']} x {qty}", total, paid, method)
        c.execute("UPDATE accessories SET stock=stock-? WHERE id=?", (qty, aid))
        c.execute("INSERT INTO acc_sales(accessory_id,item,qty,price,unit_cost,total,customer_id,customer,phone,"
                  "payment,date,bill_no) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                  (aid, r["name"], qty, price, r["buy_price"] or 0, total, cid, d["name"].strip(),
                   phone_norm(d.get("phone")) or "", method, today(), no))
        db().audit(c, "ACC_SELL", f"{no} {r['name']} x{qty}")
    return no
def plate_add(d, bike_no, plate_no, kind, cost, charge, paid, method, status):
    cost = num(cost or 0, "लागत"); charge = num(charge, "शुल्क", zero_ok=False); paid = num(paid or 0, "भुक्तानी")
    pay_check(charge, paid)
    if method not in METHODS or status not in JOB_STATUS: raise ValueError("माध्यम/स्थिति मान्य छैन")
    with db().tx() as c:
        cid = _customer_resolve(c, d.get("name"), d.get("phone"))
        no = _create_bill(c, "PLATE", None, cid, d["name"].strip(), phone_norm(d.get("phone")) or "",
                          f"{kind} · {bike_no or '-'}", charge, paid, method)
        rid = c.execute("INSERT INTO plates(customer_id,customer,phone,bike_no,plate_no,plate_type,cost,charge,"
                        "paid,due,status,date,bill_no) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (cid, d["name"].strip(), phone_norm(d.get("phone")) or "", (bike_no or "").upper(),
                         (plate_no or "").upper(), kind, cost, charge, paid, due_of(charge, paid),
                         status, today(), no)).lastrowid
        c.execute("UPDATE bills SET ref_id=? WHERE bill_no=?", (rid, no))
        if cost: _cash(c, today(), "Out", "Plate Cost", cost, method, no)
        db().audit(c, "PLATE_ADD", no)
    return no
def repair_add(d, bike_no, model, problem, parts, labour, paid, method, status):
    parts = num(parts or 0, "पार्ट्स"); labour = num(labour or 0, "लेबर")
    total = round(parts + labour, 2)
    if total <= 0: raise ValueError("पार्ट्स/लेबर रकम चाहिन्छ")
    paid = num(paid or 0, "भुक्तानी"); pay_check(total, paid)
    if method not in METHODS or status not in JOB_STATUS: raise ValueError("माध्यम/स्थिति मान्य छैन")
    with db().tx() as c:
        cid = _customer_resolve(c, d.get("name"), d.get("phone"))
        no = _create_bill(c, "REPAIR", None, cid, d["name"].strip(), phone_norm(d.get("phone")) or "",
                          f"मर्मत · {bike_no or '-'} · {problem or '-'}", total, paid, method)
        rid = c.execute("INSERT INTO repairs(customer_id,customer,phone,bike_no,bike_model,problem,parts_cost,"
                        "labour,total,paid,due,status,date,bill_no) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (cid, d["name"].strip(), phone_norm(d.get("phone")) or "", (bike_no or "").upper(),
                         model or "", problem or "", parts, labour, total, paid, due_of(total, paid),
                         status, today(), no)).lastrowid
        c.execute("UPDATE bills SET ref_id=? WHERE bill_no=?", (rid, no))
        db().audit(c, "REPAIR_ADD", no)
    return no
def job_status(kind, rid, status):
    if status not in JOB_STATUS: raise ValueError("स्थिति मान्य छैन")
    tbl = "plates" if kind == "PLATE" else "repairs"
    with db().tx() as c:
        c.execute(f"UPDATE {tbl} SET status=? WHERE id=?", (status, rid))
        db().audit(c, "JOB_STATUS", f"{tbl}#{rid} {status}")
def bill_collect(no, amount, method, note=""):
    amount = num(amount, "रकम", zero_ok=False)
    if method not in METHODS: raise ValueError("माध्यम मान्य छैन")
    with db().tx() as c:
        b = c.execute(f"SELECT * FROM bills WHERE bill_no=? AND {ACTIVE}", (no,)).fetchone()
        if not b: raise ValueError("बिल भेटिएन")
        if amount > b["due"]: raise ValueError("रकम बाँकी भन्दा बढी हुन सक्दैन")
        nd = due_of(b["total"], b["paid"] + amount)
        c.execute("UPDATE bills SET paid=paid+?,due=? WHERE id=?", (amount, nd, b["id"]))
        c.execute("INSERT INTO payments(bill_id,bill_no,amount,method,note,created_at) VALUES(?,?,?,?,?,?)",
                  (b["id"], no, amount, method, note or "असुल", now()))
        _ledger(c, b["customer_id"], b["customer"], b["phone"], "असुल", f"{note or 'असुल'} {no}", 0, amount, no)
        _cash(c, today(), "In", "Due Collection", amount, method, no)
        if b["bill_type"] in ("PLATE", "REPAIR"):
            tbl = "plates" if b["bill_type"] == "PLATE" else "repairs"
            c.execute(f"UPDATE {tbl} SET paid=?,due=? WHERE bill_no=?", (b["paid"] + amount, nd, no))
        db().audit(c, "BILL_COLLECT", f"{no} {amount}")
    return nd
def bill_edit(no, cid, total=None, paid=None, method=None):
    with db().tx() as c:
        b = c.execute(f"SELECT * FROM bills WHERE bill_no=? AND {ACTIVE}", (no,)).fetchone()
        if not b: raise ValueError("बिल भेटिएन")
        cust = c.execute("SELECT * FROM customers WHERE id=?", (cid,)).fetchone()
        if not cust: raise ValueError("ग्राहक भेटिएन")
        pays = c.execute("SELECT * FROM payments WHERE bill_id=?", (b["id"],)).fetchall()
        if total is None:
            c.execute("UPDATE bills SET customer_id=?,customer=?,phone=? WHERE id=?",
                      (cid, cust["name"], cust["phone"] or "", b["id"]))
            db().audit(c, "BILL_EDIT", f"{no} customer")
            return
        if len(pays) > 1: raise ValueError("असुल किस्ता बनिसकेको — रकम बदल्न मिल्दैन (रद्द गरेर नयाँ बनाउनुहोस्)")
        total = num(total, "जम्मा", zero_ok=False); paid = num(paid or 0, "भुक्तानी"); pay_check(total, paid)
        if method not in METHODS: raise ValueError("माध्यम मान्य छैन")
        old_cash = c.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE bill_id=? AND method='Cash'",
                             (b["id"],)).fetchone()[0]
        if old_cash: _cash(c, today(), "Out", "Bill Edit Reversal", old_cash, "Cash", no)
        nd = due_of(total, paid)
        c.execute("UPDATE bills SET customer_id=?,customer=?,phone=?,total=?,paid=?,due=?,payment=? WHERE id=?",
                  (cid, cust["name"], cust["phone"] or "", total, paid, nd, method, b["id"]))
        c.execute("DELETE FROM payments WHERE bill_id=?", (b["id"],))
        if paid > 0:
            c.execute("INSERT INTO payments(bill_id,bill_no,amount,method,note,created_at) VALUES(?,?,?,?,?,?)",
                      (b["id"], no, paid, method, "सम्पादन", now()))
            _cash(c, today(), "In", f"{b['bill_type']} Sale", paid, method, no)
        old_due = b["due"] or 0
        if nd != old_due:
            diff = round(nd - old_due, 2)
            _ledger(c, cid, cust["name"], cust["phone"], "सम्पादन", f"{no} समायोजन",
                    max(diff, 0), max(-diff, 0), no)
        if b["bill_type"] == "BIKE" and b["ref_id"]:
            bk = c.execute("SELECT * FROM bikes WHERE id=?", (b["ref_id"],)).fetchone()
            if bk:
                extra = bike_extra_cost(c, bk["bike_no"])
                c.execute("UPDATE bikes SET sell_price=?,profit=? WHERE id=?",
                          (total, round(total - (bk["total_cost"] or 0) - extra, 2), b["ref_id"]))
        if b["bill_type"] in ("PLATE", "REPAIR"):
            tbl = "plates" if b["bill_type"] == "PLATE" else "repairs"
            col = "charge" if tbl == "plates" else "total"
            c.execute(f"UPDATE {tbl} SET customer=?,phone=?,{col}=?,paid=?,due=? WHERE bill_no=?",
                      (cust["name"], cust["phone"] or "", total, paid, nd, no))
        db().audit(c, "BILL_EDIT", f"{no} {total}")
def bill_void(no, reason):
    reason = (reason or "").strip()
    if not reason: raise ValueError("रद्द गर्ने कारण चाहिन्छ")
    with db().tx() as c:
        b = c.execute(f"SELECT * FROM bills WHERE bill_no=? AND {ACTIVE}", (no,)).fetchone()
        if not b: raise ValueError("बिल भेटिएन")
        cash = c.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE bill_id=? AND method='Cash'",
                         (b["id"],)).fetchone()[0]
        if cash: _cash(c, today(), "Out", "Bill Void Reversal", cash, "Cash", no)
        c.execute("UPDATE bills SET voided=1,void_reason=?,due=0 WHERE id=?", (reason, b["id"]))
        if (b["due"] or 0) > 0:
            _ledger(c, b["customer_id"], b["customer"], b["phone"], "रद्द", f"{no} रद्द", -(b["due"] or 0), 0, no)
        if b["bill_type"] == "BIKE" and b["ref_id"]:
            c.execute("UPDATE bikes SET status='Stock',sell_price=0,profit=0,sell_date='' WHERE id=?", (b["ref_id"],))
        elif b["bill_type"] == "ACC":
            s = c.execute("SELECT * FROM acc_sales WHERE bill_no=?", (no,)).fetchone()
            if s:
                c.execute("UPDATE accessories SET stock=stock+? WHERE id=?", (s["qty"], s["accessory_id"]))
                c.execute("UPDATE acc_sales SET is_deleted=1 WHERE id=?", (s["id"],))
        elif b["bill_type"] in ("PLATE", "REPAIR"):
            tbl = "plates" if b["bill_type"] == "PLATE" else "repairs"
            c.execute(f"UPDATE {tbl} SET is_deleted=1 WHERE bill_no=?", (no,))
        db().audit(c, "BILL_VOID", f"{no} cash {cash}")
def part_add(name, cat, qty, cost, thr):
    name = (name or "").strip()
    if not name: raise ValueError("नाम चाहिन्छ")
    qty = qint(qty, "स्टक"); cost = num(cost or 0, "लागत"); thr = qint(thr, "अलर्ट")
    with db().tx() as c:
        if c.execute("SELECT 1 FROM parts WHERE name=? COLLATE NOCASE", (name,)).fetchone():
            raise ValueError("पार्ट्स पहिले नै छ")
        c.execute("INSERT INTO parts(name,category,stock,unit_cost,threshold) VALUES(?,?,?,?,?)",
                  (name, cat, qty, cost, thr))
        if qty and cost: _cash(c, today(), "Out", "Parts Purchase", qty * cost, "Cash", name)
        db().audit(c, "PART_ADD", name)
def part_buy(pid, qty, cost, method):
    qty = qint(qty, "मात्रा")
    if qty <= 0: raise ValueError("मात्रा 1+")
    cost = num(cost or 0, "लागत")
    if method not in METHODS: raise ValueError("माध्यम मान्य छैन")
    with db().tx() as c:
        r = c.execute("SELECT * FROM parts WHERE id=?", (pid,)).fetchone()
        if not r: raise ValueError("पार्ट्स भेटिएन")
        nq = (r["stock"] or 0) + qty
        avg = round(((r["stock"] or 0) * (r["unit_cost"] or 0) + qty * cost) / nq, 2)
        c.execute("UPDATE parts SET stock=?,unit_cost=? WHERE id=?", (nq, avg, pid))
        _cash(c, today(), "Out", "Parts Purchase", qty * cost, method, r["name"])
        db().audit(c, "PART_BUY", f"{r['name']} +{qty}")
def part_use(pid, bike_no, qty):
    qty = qint(qty, "मात्रा")
    if qty <= 0: raise ValueError("मात्रा 1+")
    with db().tx() as c:
        bk = c.execute("SELECT status FROM bikes WHERE bike_no=? AND is_deleted=0", (bike_no,)).fetchone()
        if not bk or bk["status"] != "Stock": raise ValueError("बाइक स्टकमा हुनुपर्छ")
        p = c.execute("SELECT * FROM parts WHERE id=?", (pid,)).fetchone()
        if not p or (p["stock"] or 0) < qty: raise ValueError("स्टक अपर्याप्त")
        c.execute("UPDATE parts SET stock=stock-? WHERE id=?", (qty, pid))
        c.execute("INSERT INTO part_usage(part_id,bike_no,qty,unit_cost,date) VALUES(?,?,?,?,?)",
                  (pid, bike_no, qty, p["unit_cost"] or 0, today()))
        db().audit(c, "PART_USE", f"{bike_no} {qty}x{p['name']}")
def labour_add(bike_no, desc, mech, amount, cash):
    amount = num(amount, "रकम", zero_ok=False)
    if not (desc or "").strip() or not (mech or "").strip(): raise ValueError("विवरण र मिस्त्री चाहिन्छ")
    with db().tx() as c:
        bk = c.execute("SELECT status FROM bikes WHERE bike_no=? AND is_deleted=0", (bike_no,)).fetchone()
        if not bk or bk["status"] != "Stock": raise ValueError("बाइक स्टकमा हुनुपर्छ")
        c.execute("INSERT INTO labour(bike_no,description,mechanic,amount,paid_cash,date) VALUES(?,?,?,?,?,?)",
                  (bike_no, desc.strip(), mech.strip(), amount, int(bool(cash)), today()))
        if cash: _cash(c, today(), "Out", "Labour", amount, "Cash", bike_no)
        db().audit(c, "LABOUR_ADD", f"{bike_no} {amount}")
def exp_add(title, cat, amount, d, method, note=""):
    title = (title or "").strip()
    if not title: raise ValueError("शीर्षक चाहिन्छ")
    amount = num(amount, "रकम", zero_ok=False); d = vdate(d)
    if method not in METHODS: raise ValueError("माध्यम मान्य छैन")
    with db().tx() as c:
        eid = c.execute("INSERT INTO expenses(title,category,amount,date,method,note) VALUES(?,?,?,?,?,?)",
                        (title, cat, amount, d, method, note)).lastrowid
        _cash(c, d, "Out", cat, amount, method, title)
        db().audit(c, "EXP_ADD", f"{title} {amount}")
    return eid
def exp_edit(eid, title, cat, amount, d, method, note=""):
    title = (title or "").strip()
    if not title: raise ValueError("शीर्षक चाहिन्छ")
    amount = num(amount, "रकम", zero_ok=False); d = vdate(d)
    if method not in METHODS: raise ValueError("माध्यम मान्य छैन")
    with db().tx() as c:
        old = c.execute("SELECT * FROM expenses WHERE id=? AND is_deleted=0", (eid,)).fetchone()
        if not old: raise ValueError("खर्च भेटिएन")
        if old["method"] == "Cash": _cash(c, today(), "In", "Expense Reversal", old["amount"], "Cash", old["title"])
        c.execute("UPDATE expenses SET title=?,category=?,amount=?,date=?,method=?,note=? WHERE id=?",
                  (title, cat, amount, d, method, note, eid))
        _cash(c, d, "Out", cat, amount, method, title)
        db().audit(c, "EXP_EDIT", f"#{eid}")
def exp_delete(eid):
    with db().tx() as c:
        old = c.execute("SELECT * FROM expenses WHERE id=? AND is_deleted=0", (eid,)).fetchone()
        if not old: raise ValueError("खर्च भेटिएन")
        if old["method"] == "Cash": _cash(c, today(), "In", "Expense Reversal", old["amount"], "Cash", old["title"])
        c.execute("UPDATE expenses SET is_deleted=1 WHERE id=?", (eid,))
        db().audit(c, "EXP_DELETE", f"#{eid}")
def staff_add(name, phone, role, salary):
    name = (name or "").strip()
    if not name: raise ValueError("नाम चाहिन्छ")
    salary = num(salary or 0, "तलब")
    with db().tx() as c:
        sid = c.execute("INSERT INTO staff(name,phone,role,salary) VALUES(?,?,?,?)",
                        (name, phone or "", role or "", salary)).lastrowid
        db().audit(c, "STAFF_ADD", name)
    return sid
def staff_off(sid):
    with db().tx() as c:
        c.execute("UPDATE staff SET active=0 WHERE id=?", (sid,))
        db().audit(c, "STAFF_OFF", f"#{sid}")
def salary_pay(sid, month, amount, d, method, note=""):
    month = vmonth(month); d = vdate(d); amount = num(amount, "रकम", zero_ok=False)
    if method not in METHODS: raise ValueError("माध्यम मान्य छैन")
    with db().tx() as c:
        st = c.execute("SELECT * FROM staff WHERE id=? AND active=1", (sid,)).fetchone()
        if not st: raise ValueError("कर्मचारी भेटिएन")
        if c.execute("SELECT 1 FROM salaries WHERE staff_id=? AND month=?", (sid, month)).fetchone():
            raise ValueError(f"{month} को तलब दिइसकियो")
        c.execute("INSERT INTO salaries(staff_id,month,amount,date,method,note) VALUES(?,?,?,?,?,?)",
                  (sid, month, amount, d, method, note))
        _cash(c, d, "Out", "Salary", amount, method, f"{st['name']} {month}")
        db().audit(c, "SALARY_PAY", f"{st['name']} {month}")
def cash_manual(d, typ, amount, note):
    if typ not in ("In", "Out"): raise ValueError("प्रकार मान्य छैन")
    amount = num(amount, "रकम", zero_ok=False)
    if not (note or "").strip(): raise ValueError("कारण/टिप्पणी चाहिन्छ")
    with db().tx() as c:
        _cash(c, vdate(d), typ, "Manual", amount, "Cash", note.strip())
        db().audit(c, "CASH_MANUAL", f"{typ} {amount}")
def cash_summary(d):
    d = vdate(d)
    with db().rd() as c:
        row = c.execute("SELECT * FROM cash_closures WHERE date=?", (d,)).fetchone()
        if row: opening = row["opening"]
        else:
            last = c.execute("SELECT closing,date FROM cash_closures WHERE date<? ORDER BY date DESC LIMIT 1",
                             (d,)).fetchone()
            if last:
                s = c.execute("SELECT COALESCE(SUM(CASE WHEN type='In' THEN amount END),0) i, "
                              "COALESCE(SUM(CASE WHEN type='Out' THEN amount END),0) o "
                              "FROM cashbook WHERE date>? AND date<?", (last["date"], d)).fetchone()
                opening = last["closing"] + s["i"] - s["o"]
            else:
                s = c.execute("SELECT COALESCE(SUM(CASE WHEN type='In' THEN amount END),0) i, "
                              "COALESCE(SUM(CASE WHEN type='Out' THEN amount END),0) o "
                              "FROM cashbook WHERE date<?", (d,)).fetchone()
                opening = s["i"] - s["o"]
        s = c.execute("SELECT COALESCE(SUM(CASE WHEN type='In' THEN amount END),0) i, "
                      "COALESCE(SUM(CASE WHEN type='Out' THEN amount END),0) o FROM cashbook WHERE date=?",
                      (d,)).fetchone()
    return {"opening": round(opening, 2), "in": round(s["i"], 2), "out": round(s["o"], 2),
            "closing": round(opening + s["i"] - s["o"], 2),
            "closed": row is not None, "note": (row["note"] or "") if row else ""}
def cash_close(d, note, user):
    d = vdate(d)
    with db().tx() as c:
        mx = c.execute("SELECT MAX(date) FROM cash_closures").fetchone()[0]
        if mx and d <= mx: raise ValueError(f"{mx} सम्म बन्द छ")
        gap = (c.execute("SELECT MIN(date) FROM cashbook WHERE date>? AND date<?", (mx, d)).fetchone()[0]
               if mx else c.execute("SELECT MIN(date) FROM cashbook WHERE date<?", (d,)).fetchone()[0])
        if gap: raise ValueError(f"{gap} मा नबन्द entry छ — क्रमशः बन्द गर्नुहोस्")
        s = cash_summary(d)
        c.execute("INSERT INTO cash_closures(date,opening,cash_in,cash_out,closing,note,closed_by,closed_at) "
                  "VALUES(?,?,?,?,?,?,?,?)", (d, s["opening"], s["in"], s["out"], s["closing"],
                  (note or "").strip(), user, now()))
        db().audit(c, "CASH_CLOSE", d)
def cash_reopen():
    with db().tx() as c:
        mx = c.execute("SELECT MAX(date) FROM cash_closures").fetchone()[0]
        if not mx: raise ValueError("बन्द दिन छैन")
        c.execute("DELETE FROM cash_closures WHERE date=?", (mx,))
        db().audit(c, "CASH_REOPEN", mx)
    return mx
def stats():
    m = today()[:7]
    pm = (date.today().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    v = db().val
    today_rev = v(f"SELECT COALESCE(SUM(total),0) FROM bills WHERE {ACTIVE} AND date(created_at)=?", (today(),))
    month_rev = v(f"SELECT COALESCE(SUM(total),0) FROM bills WHERE {ACTIVE} AND substr(created_at,1,7)=?", (m,))
    prev = v(f"SELECT COALESCE(SUM(total),0) FROM bills WHERE {ACTIVE} AND substr(created_at,1,7)=?", (pm,))
    rev = v(f"SELECT COALESCE(SUM(total),0) FROM bills WHERE {ACTIVE}")
    bike_c = v(f"SELECT COALESCE(SUM(b.total_cost),0) FROM bikes b JOIN bills x ON x.ref_id=b.id "
               f"WHERE x.bill_type='BIKE' AND x.voided=0 AND x.is_deleted=0")
    sold_nos = "(SELECT detail FROM bills WHERE bill_type='BIKE' AND " + ACTIVE + ")"
    extra = v("SELECT COALESCE(SUM(pu.qty*pu.unit_cost),0) FROM part_usage pu WHERE pu.bike_no IN "
              "(SELECT bike_no FROM bikes WHERE status='Sold' AND is_deleted=0)")
    lab = v("SELECT COALESCE(SUM(amount),0) FROM labour WHERE bike_no IN "
            "(SELECT bike_no FROM bikes WHERE status='Sold' AND is_deleted=0)")
    acc_c = v("SELECT COALESCE(SUM(qty*unit_cost),0) FROM acc_sales WHERE is_deleted=0")
    plate_c = v("SELECT COALESCE(SUM(cost),0) FROM plates WHERE is_deleted=0")
    exp = v("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE is_deleted=0")
    sal = v("SELECT COALESCE(SUM(amount),0) FROM salaries")
    net = round(rev - bike_c - extra - lab - acc_c - plate_c - exp - sal, 2)
    return {"today": today_rev, "today_n": v(f"SELECT COUNT(*) FROM bills WHERE {ACTIVE} AND date(created_at)=?", (today(),)),
            "month": month_rev, "prev_month": prev,
            "due": v(f"SELECT COALESCE(SUM(due),0) FROM bills WHERE {ACTIVE} AND due>0"),
            "due_n": v(f"SELECT COUNT(*) FROM bills WHERE {ACTIVE} AND due>0"),
            "stock": v("SELECT COUNT(*) FROM bikes WHERE status='Stock' AND is_deleted=0"),
            "sold": v("SELECT COUNT(*) FROM bikes WHERE status='Sold' AND is_deleted=0"),
            "revenue": rev, "net": net}
def chart_days(n):
    out = []
    for i in range(n - 1, -1, -1):
        d = (date.today() - timedelta(days=i)).isoformat()
        inc = db().val("SELECT COALESCE(SUM(amount),0) FROM cashbook WHERE date=? AND type='In'", (d,))
        exp = db().val("SELECT COALESCE(SUM(amount),0) FROM cashbook WHERE date=? AND type='Out'", (d,))
        out.append((d[5:], inc, exp))
    return out
def sales_mix():
    out = []
    for bt, lab in (("BIKE", "बाइक"), ("ACC", "सामान"), ("PLATE", "प्लेट"), ("REPAIR", "मर्मत")):
        v = db().val(f"SELECT COALESCE(SUM(total),0) FROM bills WHERE bill_type=? AND {ACTIVE}", (bt,))
        out.append((lab, v))
    return out
def alerts():
    out = []
    for r in db().q("SELECT bike_no,buy_date FROM bikes WHERE kar_paid=0 AND status='Stock' AND is_deleted=0"):
        ka = kar_alert(r["buy_date"])
        if ka: out.append(("warn" if ka[1] >= 0 else "bad", f"कर {ka[0]} · {r['bike_no']}"))
    for r in db().q("SELECT name,stock,threshold FROM parts WHERE stock<=threshold"):
        out.append(("bad", f"पार्ट्स कम: {r['name']} ({r['stock']})"))
    for r in db().q("SELECT name,stock FROM accessories WHERE stock<=2"):
        out.append(("warn", f"सामान कम: {r['name']} ({r['stock']})"))
    for r in db().q(f"SELECT bill_no,customer,due FROM bills WHERE {ACTIVE} AND due>0 ORDER BY due DESC LIMIT 4"):
        out.append(("bad", f"{money(r['due'])} बाँकी · {r['customer']}"))
    return out[:8]
def monthly(month):
    month = vmonth(month); like = month + "%"
    v = lambda sql: db().val(sql, (like,))
    bike_rev = v(f"SELECT COALESCE(SUM(total),0) FROM bills WHERE bill_type='BIKE' AND {ACTIVE} AND created_at LIKE ?")
    acc_rev = v(f"SELECT COALESCE(SUM(total),0) FROM bills WHERE bill_type='ACC' AND {ACTIVE} AND created_at LIKE ?")
    plate_rev = v(f"SELECT COALESCE(SUM(total),0) FROM bills WHERE bill_type='PLATE' AND {ACTIVE} AND created_at LIKE ?")
    rep_rev = v(f"SELECT COALESCE(SUM(total),0) FROM bills WHERE bill_type='REPAIR' AND {ACTIVE} AND created_at LIKE ?")
    rev = round(bike_rev + acc_rev + plate_rev + rep_rev, 2)
    bike_c = v("SELECT COALESCE(SUM(b.total_cost),0) FROM bikes b JOIN bills x ON x.ref_id=b.id "
               f"WHERE x.bill_type='BIKE' AND x.voided=0 AND x.is_deleted=0 AND x.created_at LIKE ?")
    extra = v("SELECT COALESCE(SUM(pu.qty*pu.unit_cost),0) FROM part_usage pu JOIN bikes b ON b.bike_no=pu.bike_no "
              "JOIN bills x ON x.ref_id=b.id WHERE x.bill_type='BIKE' AND x.voided=0 AND x.is_deleted=0 AND x.created_at LIKE ?")
    lab = v("SELECT COALESCE(SUM(l.amount),0) FROM labour l JOIN bikes b ON b.bike_no=l.bike_no "
            "JOIN bills x ON x.ref_id=b.id WHERE x.bill_type='BIKE' AND x.voided=0 AND x.is_deleted=0 AND x.created_at LIKE ?")
    acc_c = v("SELECT COALESCE(SUM(qty*unit_cost),0) FROM acc_sales WHERE is_deleted=0 AND date LIKE ?")
    plate_c = v("SELECT COALESCE(SUM(cost),0) FROM plates WHERE is_deleted=0 AND date LIKE ?")
    exp = v("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE is_deleted=0 AND date LIKE ?")
    sal = v("SELECT COALESCE(SUM(amount),0) FROM salaries WHERE date LIKE ?")
    gross = round(rev - bike_c - extra - lab - acc_c - plate_c, 2)
    return {"Month": month, "Bike Revenue": bike_rev, "Accessory Revenue": acc_rev,
            "Plate Revenue": plate_rev, "Repair Revenue": rep_rev, "Total Revenue": rev,
            "Bike Cost": bike_c, "Parts (COGS)": extra, "Labour (COGS)": lab,
            "Accessory COGS": acc_c, "Plate Cost": plate_c, "Gross Profit": gross,
            "Operating Exp": exp, "Salary Paid": sal, "NET PROFIT": round(gross - exp - sal, 2)}
def snapshot():
    tables = {}
    with db().rd() as c:
        for tb in SNAP_TABLES:
            try: tables[tb] = [dict(r) for r in c.execute(f"SELECT * FROM {tb}").fetchall()]
            except sqlite3.Error: tables[tb] = []
    return {"format": 2, "app": APP_NAME, "version": APP_VER, "created_at": now(), "tables": tables}
def restore(data):
    if not isinstance(data, dict) or data.get("format") != 2 or not isinstance(data.get("tables"), dict):
        raise ValueError("Snapshot format मान्य छैन")
    db().backup(BACKUP_DIR / f"pre_restore_{datetime.now():%Y%m%d_%H%M%S}.db")
    n = 0
    with db().tx() as c:
        for tb in SNAP_TABLES:
            rows = data["tables"].get(tb)
            if not isinstance(rows, list): continue
            c.execute(f"DELETE FROM {tb}")
            for row in rows:
                if not isinstance(row, dict) or not row: continue
                cols = [k for k in row if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", str(k))]
                if not cols: continue
                c.execute(f"INSERT INTO {tb}({','.join(cols)}) VALUES({','.join('?'*len(cols))})",
                          tuple(row[k] for k in cols))
                n += 1
        db().audit(c, "RESTORE", f"{n} rows")
    return n

# ══════════════ १२. CLOUD (DPAPI-only + अनिवार्य checksum) ══════════════
class TursoError(RuntimeError): pass
class TursoClient:
    def __init__(self, url, token, timeout=30):
        u = (url or "").strip().rstrip("/")
        if u.startswith("libsql://"): u = "https://" + u[9:]
        if not u.startswith(("https://", "http://")): raise TursoError("Turso URL गलत")
        self.pipe = u + "/v2/pipeline"; self.token = (token or "").strip(); self.timeout = timeout
        if not self.token: raise TursoError("Token खाली छ")
    @staticmethod
    def _arg(v):
        if v is None: return {"type": "null"}
        if isinstance(v, bool): return {"type": "integer", "value": "1" if v else "0"}
        if isinstance(v, int): return {"type": "integer", "value": str(v)}
        if isinstance(v, float): return {"type": "float", "value": repr(v)}
        return {"type": "text", "value": str(v)}
    def _post(self, payload):
        req = urllib.request.Request(self.pipe, data=json.dumps(payload).encode(), method="POST",
                                     headers={"Authorization": f"Bearer {self.token}",
                                              "Content-Type": "application/json",
                                              "User-Agent": f"SHUVAM/{APP_VER}"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                body = r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            raise TursoError(f"HTTP {e.code}: {e.read().decode('utf-8','replace')[:200]}") from e
        except Exception as e:
            raise TursoError(f"जडान असफल: {e}") from e
        try: return json.loads(body)
        except Exception as e: raise TursoError("अमान्य JSON") from e
    def execute(self, sql, args=()):
        data = self._post({"requests": [{"type": "execute", "stmt": {"sql": sql, "args": [self._arg(a) for a in args]}}]})
        res = data.get("results") or []
        if not res: raise TursoError("परिणाम आएन")
        if res[0].get("type") == "error": raise TursoError(res[0].get("error", {}).get("message", "error"))
        return (res[0].get("response") or {}).get("result") or {}
    def query(self, sql, args=()):
        r = self.execute(sql, args)
        return [[(c or {}).get("value") for c in row] for row in r.get("rows", []) or []]
    def ping(self): self.query("SELECT 1")
def cloud_cfg():
    if os.environ.get("SHUVAM_NO_CLOUD") == "1":
        return {"url": TURSO_URL_ULTIMATE, "token": TURSO_TOKEN_ULTIMATE, "on": False}
    cfg = {"url": TURSO_URL_ULTIMATE, "token": TURSO_TOKEN_ULTIMATE, "on": True}
    try:
        if CLOUD_FILE.exists():
            raw = json.loads(CLOUD_FILE.read_text(encoding="utf-8-sig"))
            cfg["url"] = raw.get("url", cfg["url"]); cfg["on"] = bool(raw.get("on", cfg["on"]))
            if raw.get("token_enc") and dpapi_ok():
                cfg["token"] = dp_decrypt(raw["token_enc"]).decode()
            elif raw.get("token"):
                cfg["token"] = raw["token"]
    except Exception: log.exception("cloud cfg")
    if not cfg.get("url"): cfg["url"] = TURSO_URL_ULTIMATE
    if not cfg.get("token"): cfg["token"] = TURSO_TOKEN_ULTIMATE
    return cfg
def cloud_save(url, token, on):
    url = (url or "").strip() or TURSO_URL_ULTIMATE
    token = (token or "").strip() or TURSO_TOKEN_ULTIMATE
    if on and not dpapi_ok(): raise RuntimeError("DPAPI छैन — cloud sync Windows मा मात्र सक्षम गर्नुहोस्")
    out = {"url": url, "on": bool(on)}
    if dpapi_ok():
        out["token_enc"] = dp_encrypt(token.encode())
    else:
        out["token"] = token
    tmp = CLOUD_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, CLOUD_FILE)
def cloud_push():
    if not dpapi_ok(): raise RuntimeError("Cloud sync Windows मा मात्र (DPAPI अनिवार्य)")
    cfg = cloud_cfg()
    if not cfg["on"]: raise TursoError("Cloud बन्द छ — सेटिङमा सक्षम गर्नुहोस्")
    cl = TursoClient(cfg["url"], cfg["token"]); cl.ping()
    plain = json.dumps(snapshot(), ensure_ascii=False).encode()
    checksum = hashlib.sha256(plain).hexdigest()
    enc = dp_encrypt(plain); ts = now()
    cl.execute("CREATE TABLE IF NOT EXISTS shuvam_vault_v10(id INTEGER PRIMARY KEY, payload TEXT NOT NULL, "
               "updated_at TEXT, app_version TEXT, checksum TEXT)")
    cl.execute("INSERT INTO shuvam_vault_v10(id,payload,updated_at,app_version,checksum) VALUES(1,?,?,?,?) "
               "ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,updated_at=excluded.updated_at,"
               "app_version=excluded.app_version,checksum=excluded.checksum", (enc, ts, APP_VER, checksum))
    with db().tx() as c: db().audit(c, "CLOUD_PUSH", ts)
    return ts
def cloud_pull():
    if not dpapi_ok(): raise RuntimeError("Cloud restore Windows मा मात्र (DPAPI अनिवार्य)")
    cfg = cloud_cfg()
    if not cfg["on"]: raise TursoError("Cloud बन्द छ")
    cl = TursoClient(cfg["url"], cfg["token"])
    rows = cl.query("SELECT payload,checksum FROM shuvam_vault_v10 WHERE id=1")
    if not rows or not rows[0][0]: raise TursoError("Cloud मा snapshot छैन")
    payload, checksum = rows[0][0], rows[0][1]
    if not checksum: raise TursoError("Checksum छैन — पुरानो/असुरक्षित snapshot अस्वीकृत")
    plain = dp_decrypt(payload)
    if hashlib.sha256(plain).hexdigest() != checksum: raise TursoError("Checksum मिलेन — डाटा बिग्रिएको हुनसक्छ")
    return restore(json.loads(plain.decode()))

# ══════════════ १३. UPDATE (sha256 अनिवार्य) ══════════════
def _http_get(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": f"SHUVAM/{APP_VER}", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=timeout) as r: return r.read()
def update_check(url):
    url = (url or "").strip()
    if not url: raise ValueError("version.json URL सेटिङमा हाल्नुहोस्")
    raw = json.loads(_http_get(url).decode())
    remote = str(raw.get("version") or "")
    if remote and ver_tuple(remote) > ver_tuple(APP_VER):
        raw["version"] = remote; return raw
    return None
def update_skipped_ver():
    try: return str(json.loads((DATA / "update_skip.json").read_text(encoding="utf-8-sig")).get("version") or "")
    except Exception: return ""
def set_update_skipped(v):
    try:
        (DATA / "update_skip.json").write_text(json.dumps({"version": str(v or "")}), encoding="utf-8")
    except Exception: log.exception("update skip save")
def update_install(info):
    info = info or {}
    frozen = bool(getattr(sys, "frozen", False))
    if frozen:
        url = (info.get("exe_url") or info.get("url") or "").strip()
        expected = (info.get("exe_sha256") or info.get("sha256") or "").strip().lower()
        if not url.lower().split("?")[0].endswith(".exe"):
            raise ValueError("Packaged app का लागि .exe update URL चाहिन्छ")
    else:
        url = (info.get("py_url") or info.get("url") or "").strip()
        expected = (info.get("py_sha256") or info.get("sha256") or "").strip().lower()
        if not url.lower().split("?")[0].endswith(".py"):
            raise ValueError("Source app का लागि .py update URL चाहिन्छ")
    if not expected:
        raise ValueError("sha256 अनिवार्य — नभए install हुँदैन")
    if not url:
        raise ValueError("update url छैन")
    data = _http_get(url, timeout=120 if frozen else 60)
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("Checksum मिलेन — update रोकियो")
    if frozen:
        if len(data) < 1_000_000 or data[:2] != b"MZ":
            raise ValueError("डाउनलोड EXE फाइल मिलेन — update रोकियो")
        target = Path(sys.executable); new = target.with_suffix(".new.exe"); new.write_bytes(data)
        ps = Path(tempfile.gettempdir()) / f"shuvam_upd_{int(time.time())}.ps1"
        def q(p): return "'" + str(p).replace("'", "''") + "'"
        ps.write_text(
            f"$ErrorActionPreference='SilentlyContinue'\n"
            f"Wait-Process -Id {os.getpid()} -Timeout 60\n"
            f"Start-Sleep -Milliseconds 600\n"
            f"Copy-Item -LiteralPath {q(new)} -Destination {q(target)} -Force\n"
            f"Start-Process -FilePath {q(target)}\n"
            f"Remove-Item -LiteralPath $MyInvocation.MyCommand.Path -Force\n",
            encoding="utf-8-sig")
        subprocess.Popen(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                          "-WindowStyle", "Hidden", "-File", str(ps)],
                         creationflags=0x08000000, close_fds=True)
        return "Update तयार — app आफै बन्द भएर नयाँ version खुल्नेछ"
    target = Path(__file__).resolve()
    if b"APP_VER" not in data:
        raise ValueError("डाउनलोड Python फाइल मिलेन — update रोकियो")
    target.with_suffix(f".bak-{datetime.now():%Y%m%d_%H%M%S}.py").write_bytes(target.read_bytes())
    tmp = target.with_suffix(".upd.tmp"); tmp.write_bytes(data); os.replace(tmp, target)
    return f"v{info.get('version')} install भयो — app पुनः सुरु गर्नुहोस्"

# ══════════════ १४. WIDGETS ══════════════
BILL_CSS = """
body{font-family:Arial,sans-serif;color:#111;margin:0;background:#f1f5f9}
.wrap{max-width:820px;margin:20px auto;background:#fff;padding:28px;border-radius:10px}
.hd{display:flex;justify-content:space-between;border-bottom:3px solid #17203A;padding-bottom:12px}
.hd h1{margin:0;color:#17203A}.tag{font-weight:bold;color:#5A5FE0}
.meta{display:flex;gap:24px;background:#f8fafc;padding:12px;border-radius:8px;margin:14px 0}
.meta b{display:block;font-size:12px;color:#64748b}
table{width:100%;border-collapse:collapse;margin-top:12px}
th,td{border:1px solid #cbd5e1;padding:8px;text-align:left}th{background:#e2e8f0}
.num{text-align:right}.tot{text-align:right;font-size:17px;margin-top:16px}
.due{color:#dc2626;font-weight:bold}.ok{color:#16a34a;font-weight:bold}
.void{background:#fee2e2;border:2px solid #dc2626;color:#991b1b;padding:10px;border-radius:8px;font-weight:bold;margin:12px 0}
.sig{display:flex;justify-content:space-between;margin-top:60px;color:#475569}
.btn{padding:8px 18px;background:#17203A;color:#fff;border:none;border-radius:6px;cursor:pointer}
.photo{max-height:130px;border:1px solid #ddd;border-radius:6px}
@media print{.noprint{display:none}body{background:#fff}.wrap{margin:0}}
"""
def open_bill(bill_no):
    b = db().one("SELECT * FROM bills WHERE bill_no=?", (bill_no,))
    if not b: raise ValueError("बिल भेटिएन")
    s = db().one("SELECT * FROM settings WHERE id=1")
    bill_safe(b["detail"])
    photo = ""
    if b["bill_type"] == "BIKE" and b["ref_id"]:
        bk = db().one("SELECT * FROM bikes WHERE id=?", (b["ref_id"],))
        if bk:
            uri = photo_uri(bk["photo_path"])
            if uri: photo = f"<img class='photo' src='{uri}'>"
    pays = db().q("SELECT * FROM payments WHERE bill_no=? ORDER BY id", (bill_no,))
    prows = "".join(f"<tr><td>{esc(p['created_at'][:10])}</td><td>{esc(p['method'])}</td>"
                    f"<td>{esc(p['note'])}</td><td class='num'>{money(p['amount'],2)}</td></tr>" for p in pays)
    void = (f"<div class='void'>*** रद्द / VOIDED ***<br>कारण: {esc(b['void_reason'])}</div>" if b["voided"] else "")
    due_cls = "due" if (b["due"] or 0) > 0 and not b["voided"] else "ok"
    doc = (f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{esc(bill_no)}</title>"
           f"<style>{BILL_CSS}</style></head><body><div class='wrap'>"
           f"<div class='noprint' style='text-align:right'><button class='btn' onclick='window.print()'>🖨 Print / PDF</button></div>"
           f"<div class='hd'><div><h1>{esc(s['shop_name'])}</h1><p>{esc(s['address'])} · {esc(s['mobile'])}"
           f"{' · PAN: '+esc(s['pan']) if s['pan'] else ''}</p></div>"
           f"<div class='tag'>{esc(bill_no)}<br>{esc(b['created_at'][:10])}</div></div>{void}"
           f"<div class='meta'><div><b>ग्राहक</b>{esc(b['customer'])}</div><div><b>फोन</b>{esc(b['phone'] or '—')}</div>"
           f"<div><b>प्रकार</b>{esc(b['bill_type'])}</div></div>{photo}"
           f"<table><tr><th>विवरण</th><th class='num'>रकम</th></tr>"
           f"<tr><td>{esc(b['detail'])}</td><td class='num'>{money(b['total'],2)}</td></tr></table>"
           + (f"<h3>भुक्तानी इतिहास</h3><table><tr><th>मिति</th><th>माध्यम</th><th>टिप्पणी</th>"
              f"<th class='num'>रकम</th></tr>{prows}</table>" if pays else "")
           + f"<div class='tot'><p>जम्मा: {money(b['total'],2)}</p><p>भुक्तानी: {money(b['paid'],2)}</p>"
           f"<p class='{due_cls}'>बाँकी: {money(0 if b['voided'] else b['due'],2)}</p></div>"
           f"<p style='color:#475569'>{esc(s['bill_note'])}</p>"
           f"<div class='sig'><span>ग्राहक हस्ताक्षर</span><span>अधिकृत हस्ताक्षर</span></div>"
           f"<p style='text-align:center;color:#94a3b8;font-size:11px'>{esc(BRAND)}</p></div></body></html>")
    p = BILL_DIR / f"bill_{fname(bill_no)}_{int(time.time())}.html"
    p.write_text(doc, encoding="utf-8")
    webbrowser.open(p.as_uri())
    return p

if HAS_TK:
    FONT = "Segoe UI"
    def pick_font(root):
        global FONT
        try:
            fams = set(tkfont.families(root))
            for f in ("Segoe UI", "Nirmala UI", "Inter", "DejaVu Sans", "Arial"):
                if f in fams: FONT = f; return
        except Exception: pass
    def F(size, weight="normal"): return (FONT, size, weight)
    def style_ttk():
        st = ttk.Style()
        try: st.theme_use("clam")
        except tk.TclError: pass
        st.configure("Treeview", background=T.PANEL, fieldbackground=T.PANEL, foreground=T.INK,
                     rowheight=28, borderwidth=0, font=F(9))
        st.configure("Treeview.Heading", background=T.FIELD, foreground=T.MUTED, font=F(9, "bold"), relief="flat")
        st.map("Treeview", background=[("selected", T.ACCENT)], foreground=[("selected", T.ACCENT_INK)])
        st.configure("TCombobox", fieldbackground=T.FIELD, background=T.PANEL, foreground=T.INK, arrowcolor=T.INK)
        st.map("TCombobox", fieldbackground=[("readonly", T.FIELD)])
        st.configure("Vertical.TScrollbar", background=T.LINE, troughcolor=T.BG, bordercolor=T.BG, arrowcolor=T.MUTED)
        for o, v in (("*TCombobox*Listbox.background", T.PANEL), ("*TCombobox*Listbox.foreground", T.INK),
                     ("*TCombobox*Listbox.selectBackground", T.ACCENT), ("*TCombobox*Listbox.selectForeground", T.ACCENT_INK)):
            st.master.option_add(o, v)
    class Btn(tk.Button):
        KINDS = {"primary": ("ACCENT", "ACCENT_INK"), "ok": ("OK", "#FFFFFF"), "bad": ("BAD", "#FFFFFF"),
                 "warn": ("WARN", "#FFFFFF"), "ghost": ("FIELD", "INK"), "rail": ("RAIL_ACT", "#FFFFFF")}
        def __init__(self, parent, text, cmd, kind="primary", w=None, small=False):
            bgk, fgk = self.KINDS.get(kind, self.KINDS["primary"])
            bg = getattr(T, bgk)
            fg = fgk if str(fgk).startswith("#") else getattr(T, fgk)
            font = F(9 if small else 10, "bold")
            pad = 12 if small else 18
            # width लाई pixel मा बुझिन्छ (Tk को character-width होइन)
            width = 0
            if w:
                try:
                    cw = max(1, tkfont.Font(font=font).measure("0"))
                    width = max(1, (max(1, int(w) - 2 * pad)) // cw)
                except Exception:
                    width = max(1, int(w) // 9)
            super().__init__(parent, text=text, command=cmd, bg=bg, fg=fg,
                             activebackground=mix(bg, "#FFFFFF", .15), activeforeground=fg,
                             font=font, bd=0, relief="flat", cursor="hand2",
                             padx=pad, pady=6 if small else 9, width=width)
            self._bg = bg
            self.bind("<Enter>", lambda e: self.config(bg=mix(self._bg, "#FFFFFF", .12)))
            self.bind("<Leave>", lambda e: self.config(bg=self._bg))
    class Card(tk.Frame):
        def __init__(self, parent, pad=16, accent=None):
            super().__init__(parent, bg=T.LINE, padx=1, pady=1)
            inner = tk.Frame(self, bg=T.PANEL)
            inner.pack(fill="both", expand=True)
            if accent:
                tk.Frame(inner, bg=accent, height=3).pack(fill="x")
            self.body = tk.Frame(inner, bg=T.PANEL, padx=pad, pady=pad)
            self.body.pack(fill="both", expand=True)
    class Field(tk.Frame):
        def __init__(self, parent, label, width=24, bg=None, default="", show=None):
            bg = bg or T.PANEL
            super().__init__(parent, bg=bg)
            lbl = tk.Label(self, text=label, bg=bg, fg=T.MUTED, font=F(8, "bold"))
            lbl.pack(anchor="w")
            wrap = tk.Frame(self, bg=T.LINE, padx=1, pady=1); wrap.pack(fill="x")
            self.e = tk.Entry(wrap, width=width, font=F(10), bg=T.FIELD, fg=T.INK, relief="flat",
                              insertbackground=T.ACCENT, insertwidth=2, show=show or "")
            self.e.pack(fill="x", ipady=5, padx=4)
            if default != "": self.e.insert(0, str(default))
            # लेबल/बोर्डरमा क्लिक गर्दा पनि सिधै टाइप गर्न सकियोस्
            for _w in (lbl, wrap, self.e):
                _w.bind("<Button-1>", lambda e: self.e.focus_set(), add="+")
        def get(self): return self.e.get()
        def set(self, v): self.e.delete(0, "end"); self.e.insert(0, str(v))
    class Combo(tk.Frame):
        def __init__(self, parent, label, values, default=None, width=20, bg=None):
            bg = bg or T.PANEL
            super().__init__(parent, bg=bg)
            tk.Label(self, text=label, bg=bg, fg=T.MUTED, font=F(8, "bold")).pack(anchor="w")
            self.cb = ttk.Combobox(self, values=list(values), width=width, font=F(10), state="readonly")
            self.cb.pack(fill="x", ipady=3)
            if default is not None and str(default) in [str(v) for v in values]: self.cb.set(default)
            elif values: self.cb.current(0)
        def get(self): return self.cb.get()
        def set(self, v): self.cb.set(v)
        def values(self, vals): self.cb["values"] = list(vals)
    class Check(tk.Frame):
        def __init__(self, parent, label, default=False, bg=None):
            bg = bg or T.PANEL
            super().__init__(parent, bg=bg)
            self.var = tk.BooleanVar(value=bool(default))
            tk.Checkbutton(self, text=label, variable=self.var, bg=bg, fg=T.INK, selectcolor=T.FIELD,
                           activebackground=bg, activeforeground=T.INK, font=F(9, "bold"), bd=0).pack(anchor="w")
        def get(self): return bool(self.var.get())
    class Pill(tk.Canvas):
        COL = {"ok": "OK", "bad": "BAD", "warn": "WARN", "info": "INFO", "mute": "FAINT"}
        def __init__(self, parent, text, kind="info", bg=None):
            bg = bg or T.PANEL
            super().__init__(parent, bg=bg, highlightthickness=0, height=20)
            f = tkfont.Font(font=F(8, "bold")); w = f.measure(text) + 16
            self.configure(width=w)
            col = getattr(T, self.COL.get(kind, "INFO"))
            self.create_rectangle(0, 2, w, 18, fill=mix(bg, col, .18), outline="")
            self.create_text(w / 2, 10, text=text, fill=col, font=F(8, "bold"))
    class Seg(tk.Frame):
        def __init__(self, parent, options, cmd):
            super().__init__(parent, bg=T.LINE, padx=1, pady=1)
            inner = tk.Frame(self, bg=T.FIELD); inner.pack()
            self.btns = {}; self.cmd = cmd; self.cur = options[0][1]
            for lab, key in options:
                b = tk.Button(inner, text=lab, font=F(9, "bold"), bd=0, relief="flat", cursor="hand2",
                              padx=14, pady=6, command=lambda k=key: self.set(k, True))
                b.pack(side="left", padx=1, pady=1)
                self.btns[key] = b
            self._paint()
        def set(self, key, fire=False):
            self.cur = key; self._paint()
            if fire: self.cmd(key)
        def _paint(self):
            for k, b in self.btns.items():
                on = k == self.cur
                b.config(bg=T.ACCENT if on else T.PANEL, fg=T.ACCENT_INK if on else T.MUTED)
    class Table(tk.Frame):
        def __init__(self, parent, cols, height=12, dbl=None):
            super().__init__(parent, bg=T.BG)
            self.cols = cols; self._rows = {}
            keys = [c[0] for c in cols]
            self.tree = ttk.Treeview(self, columns=keys, show="headings", height=height, selectmode="browse")
            ys = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
            xs = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
            self.tree.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
            self.tree.grid(row=0, column=0, sticky="nsew"); ys.grid(row=0, column=1, sticky="ns")
            xs.grid(row=1, column=0, sticky="ew")
            self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)
            for c in cols:
                key, lab, w = c[0], c[1], c[2]
                align = "e" if len(c) > 3 and c[3] == "e" else "w"
                self.tree.heading(key, text=lab)
                self.tree.column(key, width=w, anchor=align, minwidth=50, stretch=True)
            for tag, col in (("ok", T.OK), ("bad", T.BAD), ("warn", T.WARN), ("mute", T.FAINT)):
                self.tree.tag_configure(tag, foreground=col)
            if dbl: self.tree.bind("<Double-1>", lambda e: self.selected() and dbl(self.selected()))
        def fill(self, rows, tagfn=None):
            self.tree.delete(*self.tree.get_children()); self._rows = {}
            for r in rows:
                iid = str(r.get("_id", len(self._rows)))
                self._rows[iid] = r
                tags = (tagfn(r),) if tagfn and tagfn(r) else ()
                self.tree.insert("", "end", iid=iid, tags=tags,
                                 values=[r.get(c[0], "") for c in self.cols])
        def selected(self):
            sel = self.tree.selection()
            return self._rows.get(sel[0]) if sel else None
    class Scroll(tk.Frame):
        def __init__(self, parent, bg=None):
            bg = bg or T.BG
            super().__init__(parent, bg=bg)
            self.cv = tk.Canvas(self, bg=bg, highlightthickness=0)
            sb = ttk.Scrollbar(self, orient="vertical", command=self.cv.yview)
            self.cv.configure(yscrollcommand=sb.set)
            self.cv.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")
            self.body = tk.Frame(self.cv, bg=bg)
            self.win = self.cv.create_window(0, 0, anchor="nw", window=self.body)
            self.body.bind("<Configure>", lambda e: self.cv.configure(scrollregion=self.cv.bbox("all")))
            self.cv.bind("<Configure>", lambda e: self.cv.itemconfigure(self.win, width=e.width))
            self.cv.bind("<Enter>", lambda e: self.cv.bind_all("<MouseWheel>", self._wheel))
            self.cv.bind("<Leave>", lambda e: self.cv.unbind_all("<MouseWheel>"))
        def _wheel(self, e): self.cv.yview_scroll(-1 if e.delta > 0 else 1, "units")
    class Toast:
        @staticmethod
        def show(root, text, kind="ok", dur=2600):
            col = {"ok": T.OK, "bad": T.BAD, "warn": T.WARN, "info": T.INFO}.get(kind, T.INFO)
            win = tk.Toplevel(root); win.overrideredirect(True)
            win.configure(bg=col)
            tk.Label(win, text=text, bg=T.PANEL, fg=T.INK, font=F(10, "bold"), padx=18, pady=10).pack(padx=2, pady=2)
            win.update_idletasks()
            w, h = win.winfo_width(), win.winfo_height()
            x = root.winfo_screenwidth() - w - 24
            win.geometry(f"{w}x{h}+{x}+30")
            try: win.attributes("-alpha", 0.96)
            except Exception: pass
            try: win.after(dur, win.destroy)
            except Exception: pass
    class Bars(tk.Canvas):
        def __init__(self, parent, h=200):
            super().__init__(parent, bg=T.PANEL, highlightthickness=0, height=h)
            self.data = []; self.bind("<Configure>", lambda e: self.draw())
        def fill(self, data): self.data = data; self.draw()
        def draw(self):
            self.delete("all"); w, h = self.winfo_width(), self.winfo_height()
            if w < 60: return
            pl, pt, pb = 46, 14, 24
            pw, ph = w - pl - 10, h - pt - pb
            mx = max([max(i, o) for _, i, o in self.data] + [1])
            for g in range(5):
                y = pt + ph * g / 4
                self.create_line(pl, y, w - 10, y, fill=T.LINE, dash=(2, 4))
                self.create_text(pl - 6, y, text=compact(mx * (1 - g / 4)), anchor="e", fill=T.FAINT, font=F(7))
            n = max(1, len(self.data)); slot = pw / n; bw = max(4, min(14, slot / 3.2))
            for idx, (lab, inc, exp) in enumerate(self.data):
                cx = pl + slot * idx + slot / 2
                for off, val, col in ((-bw * .65, inc, T.CHART[0]), (bw * .65, exp, T.CHART[1])):
                    bh = ph * val / mx
                    if bh >= 1: self.create_rectangle(cx + off - bw / 2, pt + ph - bh, cx + off + bw / 2, pt + ph, fill=col, outline="")
                if idx % max(1, n // 10) == 0:
                    self.create_text(cx, h - 8, text=lab, fill=T.FAINT, font=F(7))
    class Donut(tk.Canvas):
        def __init__(self, parent, size=150):
            super().__init__(parent, bg=T.PANEL, highlightthickness=0, width=size, height=size)
            self.size = size; self.segs = []; self.draw()
        def fill(self, segs): self.segs = [(n, v) for n, v in segs if v > 0]; self.draw()
        def draw(self):
            self.delete("all"); s = self.size; m = 12
            tot = sum(v for _, v in self.segs)
            if tot <= 0:
                self.create_oval(m, m, s - m, s - m, outline=T.LINE, width=18)
                self.create_text(s / 2, s / 2, text="डाटा छैन", fill=T.FAINT, font=F(8)); return
            acc = 0.0
            for i, (n, v) in enumerate(self.segs):
                deg = v / tot * 360
                self.create_arc(m, m, s - m, s - m, start=90 - acc, extent=-min(deg, 359.9),
                                style="arc", outline=T.CHART[i % len(T.CHART)], width=18)
                acc += deg
            self.create_text(s / 2, s / 2 - 6, text=compact(tot), fill=T.INK, font=F(11, "bold"))
            self.create_text(s / 2, s / 2 + 12, text="जम्मा बिक्री", fill=T.FAINT, font=F(7))
    class Spark(tk.Canvas):
        def __init__(self, parent, h=60):
            super().__init__(parent, bg=T.PANEL, highlightthickness=0, height=h)
            self.vals = []; self.bind("<Configure>", lambda e: self.draw())
        def fill(self, vals): self.vals = vals; self.draw()
        def draw(self):
            self.delete("all"); w, h = self.winfo_width(), self.winfo_height()
            if w < 40 or not self.vals: return
            vals = self.vals if len(self.vals) > 1 else self.vals * 2
            mx = max(vals + [1]); pad = 6; pts = []
            for i, v in enumerate(vals):
                pts += [pad + (w - 2 * pad) * i / (len(vals) - 1), h - pad - (h - 2 * pad) * v / mx]
            self.create_line(*pts, fill=T.ACCENT, width=2, smooth=True)
            self.create_oval(pts[-2] - 3, pts[-1] - 3, pts[-2] + 3, pts[-1] + 3, fill=T.ACCENT, outline=T.PANEL)
    class Ring(tk.Canvas):
        def __init__(self, parent, label, color):
            super().__init__(parent, bg=T.PANEL, highlightthickness=0, width=90, height=102)
            self.label, self.color, self.pct = label, color, 0.0
            self.draw()
        def set(self, pct): self.pct = max(0.0, min(100.0, float(pct or 0))); self.draw()
        def draw(self):
            self.delete("all"); m, s = 12, 72
            self.create_oval(m, m, m + s, m + s, outline=T.LINE, width=8)
            if self.pct > 0:
                self.create_arc(m, m, m + s, m + s, start=90, extent=-max(.01, self.pct * 3.6),
                                style="arc", outline=self.color, width=8)
            self.create_text(m + s / 2, m + s / 2, text=f"{self.pct:.0f}%", fill=T.INK, font=F(10, "bold"))
            self.create_text(45, 94, text=self.label, fill=T.FAINT, font=F(8))
    class NavBtn(tk.Canvas):
        def __init__(self, parent, icon, text, cmd):
            super().__init__(parent, bg=T.RAIL, highlightthickness=0, height=38, cursor="hand2")
            self.icon, self.text, self.cmd = icon, text, cmd
            self._act = self._hov = False
            self.bind("<Configure>", lambda e: self.draw())
            self.bind("<Enter>", lambda e: self._h(True)); self.bind("<Leave>", lambda e: self._h(False))
            self.bind("<Button-1>", lambda e: self.cmd())
            self.draw()
        def _h(self, v): self._hov = v; self.draw()
        def active(self, v): self._act = v; self.draw()
        def draw(self):
            self.delete("all"); w = self.winfo_width()
            if w < 10: return
            if self._act:
                self.create_rectangle(0, 2, w, 36, fill=mix(T.RAIL, T.RAIL_ACT, .30), outline="")
                self.create_rectangle(0, 8, 3, 30, fill=T.ACCENT, outline="")
            elif self._hov:
                self.create_rectangle(0, 2, w, 36, fill=mix(T.RAIL, "#FFFFFF", .06), outline="")
            fg = "#FFFFFF" if (self._act or self._hov) else T.RAIL_INK
            self.create_text(16, 19, text=self.icon, fill=fg, font=F(11), anchor="w")
            self.create_text(42, 19, text=self.text, fill=fg, font=F(9, "bold" if self._act else "normal"), anchor="w")
    def modal(root, title, w, h):
        d = tk.Toplevel(root); d.title(title); d.configure(bg=T.BG)
        w = min(w, root.winfo_screenwidth() - 40); h = min(h, root.winfo_screenheight() - 80)
        x = root.winfo_rootx() + max((root.winfo_width() - w) // 2, 0)
        y = root.winfo_rooty() + max((root.winfo_height() - h) // 3, 0)
        d.geometry(f"{w}x{h}+{x}+{y}"); d.transient(root)
        d.after(150, lambda: (d.grab_set(), d.focus_force()) if d.winfo_exists() else None)
        d.bind("<Escape>", lambda e: d.destroy())
        return d
    def confirm(root, title, msg): return messagebox.askyesno(title, msg, parent=root)
    def ask_text(root, title, prompt, default=""):
        return simpledialog.askstring(title, prompt, initialvalue=default, parent=root)
    def form(root, title, fields, on_save, values=None, width=460, note=None):
        """Declarative form — link hook ले due-preview जोड्न सक्छ।"""
        values = values or {}
        h = 120 + len(fields) * 52 + (40 if note else 0)
        d = modal(root, title, width, min(h, root.winfo_screenheight() - 100))
        sc = Scroll(d, T.BG); sc.pack(fill="both", expand=True)
        b = sc.body
        tk.Label(b, text=title, bg=T.BG, fg=T.INK, font=F(14, "bold")).pack(anchor="w", padx=20, pady=(16, 4))
        if note:
            tk.Label(b, text=note, bg=T.BG, fg=T.WARN, font=F(8), wraplength=width - 50,
                     justify="left").pack(anchor="w", padx=20, pady=(0, 6))
        grid = tk.Frame(b, bg=T.BG); grid.pack(fill="x", padx=20)
        grid.columnconfigure(0, weight=1); grid.columnconfigure(1, weight=1)
        ws = {}; r = 0; col = 0
        for f in fields:
            k = f["k"]; dv = values.get(k, f.get("default", ""))
            typ = f.get("type", "text")
            if typ == "select": w = Combo(grid, f["label"], f.get("values", []), dv, 22, T.BG)
            elif typ == "check": w = Check(grid, f["label"], bool(dv), T.BG)
            else: w = Field(grid, f["label"], 24, T.BG, dv)
            span = f.get("span", 1)
            w.grid(row=r, column=col, columnspan=span, sticky="ew", padx=4, pady=4)
            ws[k] = w
            col += span
            if col >= 2: col = 0; r += 1
        for f in fields:
            if f.get("link"):
                try: f["link"](ws, ws[f["k"]])
                except Exception: log.exception("form link")
        def save():
            data = {}
            for f in fields:
                w = ws[f["k"]]
                data[f["k"]] = w.get() if f.get("type") == "check" else w.get()
            try: on_save(data)
            except Exception as e:
                messagebox.showerror("त्रुटि", str(e), parent=d); return
            d.destroy()
        bf = tk.Frame(b, bg=T.BG); bf.pack(fill="x", padx=20, pady=14)
        Btn(bf, "💾  सेभ", save, "ok").pack(side="left", padx=4)
        Btn(bf, "रद्द", d.destroy, "ghost").pack(side="left", padx=4)
        d.bind("<Return>", lambda e: save())
        return d
    def make_due_link(total_keys, paid_key, qty_key=None):
        """form को link hook — जम्मा/बाँकी live देखाउँछ।"""
        def link(ws, wdg):
            top = wdg.winfo_toplevel()
            lbl = tk.Label(top, text="", bg=T.BG, fg=T.MUTED, font=F(10, "bold"))
            lbl.pack(side="bottom", fill="x", pady=(0, 8))
            def upd(_=None):
                try:
                    tot = sum(num(ws[k].get() or 0, "रकम") for k in total_keys)
                    if qty_key: tot *= qint(ws[qty_key].get() or 1, "संख्या")
                    paid = num(ws[paid_key].get() or 0, "भुक्तानी")
                except Exception:
                    lbl.config(text="बाँकी: —", fg=T.FAINT); return
                if paid > tot:
                    lbl.config(text="⚠ भुक्तानी जम्मा भन्दा बढी — रोकिन्छ", fg=T.BAD); return
                d = due_of(tot, paid)
                lbl.config(text=f"जम्मा {money(tot)}  ·  बाँकी {money(d)}", fg=T.BAD if d > 0 else T.OK)
            for k in list(total_keys) + [paid_key] + ([qty_key] if qty_key else []):
                w = ws.get(k)
                if w is None: continue
                e = getattr(w, "e", None) or getattr(w, "cb", None)
                if e is not None: e.bind("<KeyRelease>", upd, add="+")
            upd()
        return link

# ══════════════ १५. APP SHELL ══════════════
if HAS_TK:
    NAV = [("dash", "◈", "dash"), ("bikes", "🏍", "bikes"), ("cost", "📋", "cost"),
           ("acc", "🛡", "acc"), ("svc", "🔧", "svc"), ("parts", "⚙", "parts"),
           ("cust", "👥", "cust"), ("bills", "🧾", "bills"), ("cash", "💵", "cash"),
           ("exp", "📉", "exp"), ("staff", "👷", "staff"), ("rep", "📊", "rep"),
           ("audit", "🛡", "audit"), ("set", "⚙", "set"), ("pw", "🔑", "pw")]
    # FIX: "set" owner-only रहन्छ; staff को लागि "pw" page छ → must-change deadlock हट्यो
    OWNER_ONLY = {"cash", "exp", "staff", "rep", "audit", "set", "cost"}

    class App:
        def __init__(self, root, user, role, must=0):
            self.root, self.user, self.role = root, user, role
            self.owner = role == "owner"
            self.must = bool(must)
            self.page_key = ""
            self.pages = {}; self.navw = {}; self._timers = []
            db().actor = user
            self._shell()
            for k, _, _ in NAV:
                if k in OWNER_ONLY and not self.owner: continue
                getattr(self, "pg_" + k)()
            self.go("pw" if (self.must and not self.owner) else ("set" if self.must else "dash"))
            self.after(2000, self._auto_update_check)
            if self.must:
                self.after(400, lambda: messagebox.showwarning(
                    "सुरक्षा", "पूर्वनिर्धारित पासवर्ड प्रयोगमा छ।\nपासवर्ड बदल्नुहोस्।"))
        def after(self, ms, fn):
            tid = self.root.after(ms, fn); self._timers.append(tid); return tid
        def destroy(self):
            for tid in self._timers:
                try: self.root.after_cancel(tid)
                except Exception: pass
            self._timers.clear()
            for w in self.root.winfo_children(): w.destroy()
        def _shell(self):
            r = self.root
            r.title(f"{APP_NAME} · {APP_CODE} v{APP_VER}")
            r.configure(bg=T.BG)
            sw, sh = r.winfo_screenwidth(), r.winfo_screenheight()
            w = min(1420, max(1080, sw - 60)); h = min(900, max(640, sh - 100))
            r.geometry(f"{w}x{h}+{max((sw - w) // 2, 0)}+{max((sh - h - 80) // 2, 0)}")
            r.minsize(min(1140, w), min(700, h))
            style_ttk()
            try:
                p = make_icon()
                if p: r._icon = tk.PhotoImage(file=str(p)); r.iconphoto(True, r._icon)
            except Exception: pass
            self.rail = tk.Frame(r, bg=T.RAIL, width=232); self.rail.pack(side="left", fill="y")
            self.rail.pack_propagate(False)
            right = tk.Frame(r, bg=T.BG); right.pack(side="left", fill="both", expand=True)
            self.bar = tk.Frame(right, bg=T.BG, height=70); self.bar.pack(fill="x"); self.bar.pack_propagate(False)
            tk.Frame(right, bg=T.LINE, height=1).pack(fill="x")
            self.content = tk.Frame(right, bg=T.BG); self.content.pack(fill="both", expand=True)
            self._rail(); self._bar()
        def _rail(self):
            s = self.rail
            top = tk.Frame(s, bg=T.RAIL); top.pack(fill="x", padx=20, pady=(22, 14))
            tk.Label(top, text="SHUVAM", bg=T.RAIL, fg="#FFFFFF", font=F(18, "bold")).pack(anchor="w")
            tk.Label(top, text="RECONDITION HOUSE", bg=T.RAIL, fg=T.RAIL_MUTED, font=F(7, "bold")).pack(anchor="w")
            tk.Label(top, text=f"{APP_CODE} · v{APP_VER}", bg=T.RAIL, fg=T.ACCENT, font=F(8, "bold")).pack(anchor="w", pady=(4, 0))
            tk.Frame(s, bg=mix(T.RAIL, "#FFFFFF", .10), height=1).pack(fill="x", padx=16)
            navscroll = Scroll(s, T.RAIL); navscroll.pack(fill="both", expand=True, pady=8)
            for key, icon, lbl in NAV:
                if key in OWNER_ONLY and not self.owner: continue
                b = NavBtn(navscroll.body, icon, t(lbl), lambda k=key: self.go(k))
                b.pack(fill="x", padx=8, pady=1)
                self.navw[key] = b
            foot = tk.Frame(s, bg=T.RAIL); foot.pack(fill="x", side="bottom", pady=14)
            tk.Label(foot, text=f"● {self.user} · {self.role.upper()}", bg=T.RAIL, fg=T.RAIL_MUTED,
                     font=F(8, "bold")).pack(anchor="w", padx=20)
            Btn(foot, "🚪 " + t("logout"), self.logout, "rail", w=190, small=True).pack(padx=20, pady=(8, 0))
            tk.Label(foot, text=BRAND, bg=T.RAIL, fg=mix(T.RAIL_MUTED, T.RAIL, .45), font=F(6),
                     wraplength=192, justify="left").pack(anchor="w", padx=20, pady=(10, 0))
        def _bar(self):
            b = self.bar
            left = tk.Frame(b, bg=T.BG); left.pack(side="left", padx=24, pady=14)
            self.title_l = tk.Label(left, text="", bg=T.BG, fg=T.INK, font=F(18, "bold")); self.title_l.pack(anchor="w")
            self.sub_l = tk.Label(left, text="", bg=T.BG, fg=T.MUTED, font=F(9)); self.sub_l.pack(anchor="w")
            right = tk.Frame(b, bg=T.BG); right.pack(side="right", padx=20)
            self.clock = tk.Label(right, text="", bg=T.BG, fg=T.MUTED, font=F(9)); self.clock.pack(side="right", padx=(12, 0))
            Btn(right, "◐", self.theme_menu, "ghost", w=36, small=True).pack(side="right", padx=3)
            Btn(right, "ने" if _lang == "en" else "EN", self.toggle_lang, "ghost", w=48, small=True).pack(side="right", padx=3)
            Btn(right, "⟳", lambda: self.go(self.page_key, force=True), "ghost", w=36, small=True).pack(side="right", padx=3)
            self._tick()
        def _tick(self):
            if not self.root.winfo_exists(): return
            try: self.clock.config(text=datetime.now().strftime("%a %d %b · %I:%M %p"))
            except tk.TclError: return
            self.after(1000, self._tick)
        def logout(self):
            self.destroy(); login_screen(self.root)
        def _rebuild(self, page):
            self.destroy()
            app = App(self.root, self.user, self.role, self.must)
            app.go(page)
        def toggle_lang(self):
            set_lang("en" if _lang == "ne" else "ne")
            with db().tx() as c: c.execute("UPDATE settings SET lang=? WHERE id=1", (_lang,))
            self._rebuild(self.page_key or "dash")
        def theme_menu(self):
            m = tk.Menu(self.root, tearoff=0, bg=T.PANEL, fg=T.INK, activebackground=T.ACCENT,
                        activeforeground=T.ACCENT_INK, bd=0, font=F(10))
            cur = db().val("SELECT theme FROM settings WHERE id=1", (), "porcelain")
            for k in THEME_ORDER:
                m.add_command(label=("● " if k == cur else "○ ") + THEMES[k].label,
                              command=lambda kk=k: self.set_theme(kk))
            m.tk_popup(self.root.winfo_pointerx(), self.root.winfo_pointery())
        def set_theme(self, k):
            apply_theme(k)
            with db().tx() as c: c.execute("UPDATE settings SET theme=? WHERE id=1", (k,))
            self._rebuild(self.page_key or "dash")
        def go(self, key, force=False):
            if key not in self.pages: return
            if key in OWNER_ONLY and not self.owner:
                Toast.show(self.root, "यो पेज Owner का लागि मात्र हो", "bad"); return
            if self.must and key not in ("set", "pw"):
                Toast.show(self.root, "पहिले पासवर्ड बदल्नुहोस्", "warn")
                key = "set" if self.owner else "pw"
            for w in self.content.winfo_children(): w.pack_forget()
            self.page_key = key
            self.pages[key].pack(fill="both", expand=True)
            for k, nb in self.navw.items(): nb.active(k == key)
            self.title_l.config(text=t(dict((k, l) for k, _, l in NAV).get(key, key)))
            subs = {"dash": "व्यवसायको प्रत्यक्ष झलक", "bikes": "खरिद · मर्मत · बिक्री",
                    "cost": "प्रति-बाइक वास्तविक लागत र नाफा", "acc": "हेल्मेट र सामान",
                    "svc": "नम्बर प्लेट र मर्मत सेवा", "parts": "स्पेयर पार्ट्स (ग्यारेज प्रयोग)",
                    "cust": "ग्राहक र उधारो खाता", "bills": "बिल · असुल · रद्द",
                    "cash": "दैनिक नगद र दिनबन्द", "exp": "सञ्चालन खर्च", "staff": "कर्मचारी र तलब",
                    "rep": "नाफा-नोक्सान", "audit": "hash-chain लग", "set": "दुकान · प्रयोगकर्ता · ब्याकअप",
                    "pw": "पासवर्ड परिवर्तन"}
            self.sub_l.config(text=subs.get(key, ""))
            getattr(self, "rf_" + key, lambda: None)()
        def page(self, key, scroll=True):
            f = tk.Frame(self.content, bg=T.BG); self.pages[key] = f
            if scroll:
                sc = Scroll(f, T.BG); sc.pack(fill="both", expand=True); return f, sc.body
            return f, f
        def toolbar(self, parent, buttons, search_cb=None, seg=None):
            bar = tk.Frame(parent, bg=T.BG); bar.pack(fill="x", padx=22, pady=(16, 8))
            if seg: seg.pack(side="left", padx=(0, 8))
            for text, cmd, kind in buttons:
                Btn(bar, text, cmd, kind, small=True).pack(side="left", padx=3)
            if search_cb:
                wrap = tk.Frame(bar, bg=T.LINE, padx=1, pady=1); wrap.pack(side="right")
                e = tk.Entry(wrap, width=24, font=F(10), bg=T.FIELD, fg=T.INK, relief="flat", insertbackground=T.ACCENT)
                e.pack(ipady=5, padx=6)
                e.bind("<KeyRelease>", lambda ev: search_cb(e.get()))
                tk.Label(bar, text="🔍", bg=T.BG, fg=T.MUTED, font=F(10)).pack(side="right", padx=(0, 4))
            return bar
        def card(self, parent, title=None, sub=None, accent=None, pad=16):
            c = Card(parent, pad=pad, accent=accent); c.pack(fill="x", padx=22, pady=8)
            if title: tk.Label(c.body, text=title, bg=T.PANEL, fg=T.INK, font=F(12, "bold")).pack(anchor="w")
            if sub: tk.Label(c.body, text=sub, bg=T.PANEL, fg=T.MUTED, font=F(8)).pack(anchor="w", pady=(0, 8))
            return c
        def need(self, tbl, msg=None):
            r = tbl.selected()
            if not r: Toast.show(self.root, msg or t("select_row"), "warn")
            return r
        def _bg(self, work, ok, err):
            def run():
                try: r = work()
                except Exception as e:
                    self.root.after(0, lambda: err(e)); return
                self.root.after(0, lambda: ok(r))
            threading.Thread(target=run, daemon=True).start()
        def _auto_update_check(self):
            def work():
                try:
                    url = db().val("SELECT update_url FROM settings WHERE id=1", (), UPDATE_URL_DEFAULT) or UPDATE_URL_DEFAULT
                    info = update_check(url)
                    if info and str(info.get("version")) != update_skipped_ver():
                        self.root.after(0, lambda: self._prompt_update(info))
                except Exception:
                    log.exception("auto update check")
            threading.Thread(target=work, daemon=True).start()
        def _prompt_update(self, info):
            if not messagebox.askyesno("Update", f"नयाँ version {info.get('version')} उपलब्ध छ।\nInstall गर्ने?"):
                set_update_skipped(info.get("version")); return
            try:
                msg = update_install(info)
                messagebox.showinfo("Update", msg)
                if getattr(sys, "frozen", False):
                    self.root.after(800, self.root.destroy)
            except Exception as e:
                messagebox.showerror("Update", str(e))

        # ---------- DASHBOARD ----------
        def pg_dash(self):
            f, b = self.page("dash")
            hero = self.card(b, accent=T.ACCENT, pad=20)
            tk.Label(hero.body, text=f"{t('welcome')}, {self.user} 👋", bg=T.PANEL, fg=T.INK,
                     font=F(21, "bold")).pack(anchor="w")
            s = db().one("SELECT shop_name,address FROM settings WHERE id=1")
            tk.Label(hero.body, text=f"{s['shop_name']} · {s['address']} · {datetime.now():%A, %d %B %Y}",
                     bg=T.PANEL, fg=T.MUTED, font=F(10)).pack(anchor="w", pady=(2, 0))
            self.kpi = {}
            row = tk.Frame(b, bg=T.BG); row.pack(fill="x", padx=16, pady=6)
            for k, lbl, icon, col in (("today", t("today"), "💰", T.OK), ("month", t("month"), "📈", T.ACCENT),
                                      ("due", t("pending"), "⏳", T.BAD), ("stock", t("in_stock"), "🏍", T.INFO)):
                c = Card(row, pad=14, accent=col); c.pack(side="left", fill="both", expand=True, padx=6, pady=6)
                hd = tk.Frame(c.body, bg=T.PANEL); hd.pack(fill="x")
                tk.Label(hd, text=icon, bg=col, fg="#FFFFFF", font=F(12), width=2).pack(side="left")
                tk.Label(hd, text=lbl, bg=T.PANEL, fg=T.MUTED, font=F(9, "bold")).pack(side="left", padx=8)
                v = tk.Label(c.body, text="—", bg=T.PANEL, fg=T.INK, font=F(21, "bold")); v.pack(anchor="w", pady=(8, 0))
                sub = tk.Label(c.body, text="", bg=T.PANEL, fg=T.FAINT, font=F(8)); sub.pack(anchor="w")
                self.kpi[k] = (v, sub)
            row2 = tk.Frame(b, bg=T.BG); row2.pack(fill="x", padx=16, pady=6)
            c1 = Card(row2, pad=14); c1.pack(side="left", fill="both", expand=True, padx=6)
            tk.Label(c1.body, text="नगद प्रवाह — १४ दिन", bg=T.PANEL, fg=T.INK, font=F(11, "bold")).pack(anchor="w")
            self.bars = Bars(c1.body, 200); self.bars.pack(fill="both", expand=True, pady=(8, 0))
            c2 = Card(row2, pad=14); c2.pack(side="left", fill="y", padx=6)
            tk.Label(c2.body, text="बिक्री विभाजन", bg=T.PANEL, fg=T.INK, font=F(11, "bold")).pack(anchor="w")
            self.donut = Donut(c2.body, 150); self.donut.pack(pady=8)
            self.mixl = tk.Frame(c2.body, bg=T.PANEL); self.mixl.pack(fill="x")
            row3 = tk.Frame(b, bg=T.BG); row3.pack(fill="x", padx=16, pady=(6, 20))
            c3 = Card(row3, pad=14); c3.pack(side="left", fill="y", padx=6)
            tk.Label(c3.body, text="व्यवसाय स्वास्थ्य", bg=T.PANEL, fg=T.INK, font=F(11, "bold")).pack(anchor="w")
            rr = tk.Frame(c3.body, bg=T.PANEL); rr.pack(pady=6)
            self.ring1 = Ring(rr, "असुल दर", T.OK); self.ring1.pack(side="left", padx=4)
            self.ring2 = Ring(rr, "स्टक", T.INFO); self.ring2.pack(side="left", padx=4)
            c4 = Card(row3, pad=14); c4.pack(side="left", fill="both", expand=True, padx=6)
            tk.Label(c4.body, text="बिक्री प्रवृत्ति", bg=T.PANEL, fg=T.INK, font=F(11, "bold")).pack(anchor="w")
            self.spark = Spark(c4.body, 56); self.spark.pack(fill="x", pady=8)
            self.netl = tk.Label(c4.body, text="", bg=T.PANEL, fg=T.OK, font=F(14, "bold")); self.netl.pack(anchor="w")
            c5 = Card(row3, pad=14, accent=T.WARN); c5.pack(side="left", fill="both", expand=True, padx=6)
            tk.Label(c5.body, text="⚠ अलर्ट", bg=T.PANEL, fg=T.INK, font=F(11, "bold")).pack(anchor="w")
            self.alertbox = tk.Frame(c5.body, bg=T.PANEL); self.alertbox.pack(fill="both", expand=True, pady=(6, 0))
        def rf_dash(self):
            s = stats()
            self.kpi["today"][0].config(text=money(s["today"])); self.kpi["today"][1].config(text=f"{s['today_n']} बिल आज")
            g = (s["month"] - s["prev_month"]) / s["prev_month"] * 100 if s["prev_month"] > 0 else None
            self.kpi["month"][0].config(text=money(s["month"]))
            self.kpi["month"][1].config(text=f"{g:+.1f}% गत महिनाभन्दा" if g is not None else "गत महिनाको डाटा छैन")
            self.kpi["due"][0].config(text=money(s["due"])); self.kpi["due"][1].config(text=f"{s['due_n']} बिल बाँकी")
            self.kpi["stock"][0].config(text=str(s["stock"])); self.kpi["stock"][1].config(text=f"{s['sold']} बिकिभयो")
            d = chart_days(14); self.bars.fill(d); self.spark.fill([i + o for _, i, o in d])
            mix_ = sales_mix(); self.donut.fill(mix_)
            for w in self.mixl.winfo_children(): w.destroy()
            for i, (n, v) in enumerate(mix_):
                r = tk.Frame(self.mixl, bg=T.PANEL); r.pack(fill="x", pady=1)
                tk.Label(r, text="●", bg=T.PANEL, fg=T.CHART[i % len(T.CHART)], font=F(9)).pack(side="left")
                tk.Label(r, text=n, bg=T.PANEL, fg=T.MUTED, font=F(8)).pack(side="left", padx=3)
                tk.Label(r, text=compact(v), bg=T.PANEL, fg=T.INK, font=F(8, "bold")).pack(side="right")
            recv = db().val("SELECT COALESCE(SUM(tiryo),0) FROM ledger")
            udh = db().val("SELECT COALESCE(SUM(udharo),0) FROM ledger")
            self.ring1.set(100 * recv / (recv + udh) if (recv + udh) else 0)
            low = db().val("SELECT COUNT(*) FROM parts WHERE stock<=threshold") + db().val("SELECT COUNT(*) FROM accessories WHERE stock<=2")
            self.ring2.set(max(0, 100 - low * 12))
            self.netl.config(text=f"खुद नाफा  {money(s['net'])}", fg=T.OK if s["net"] >= 0 else T.BAD)
            for w in self.alertbox.winfo_children(): w.destroy()
            al = alerts()
            if not al:
                tk.Label(self.alertbox, text="✅ सबै ठीक छ", bg=T.PANEL, fg=T.OK, font=F(10, "bold")).pack(pady=12)
            for kind, txt_ in al:
                r = tk.Frame(self.alertbox, bg=T.PANEL); r.pack(fill="x", pady=2)
                Pill(r, "●", kind, bg=T.PANEL).pack(side="left")
                tk.Label(r, text=txt_, bg=T.PANEL, fg=T.MUTED, font=F(8), wraplength=230, justify="left").pack(side="left", padx=6)

        # ---------- BIKES ----------
        def pg_bikes(self):
            f, b = self.page("bikes", scroll=False)
            self.bike_tab = "Stock"; self._bike_q = ""
            seg = Seg(f, [(t("stock"), "Stock"), (t("sold"), "Sold"), ("सबै", "all")], self._bike_tab)
            self.toolbar(f, [("＋ " + t("buy"), self.bike_new, "ok"),
                             ("💰 " + t("sell"), self.bike_sell_ui, "primary"),
                             ("📷 Docs/Photo", self.bike_docs_ui, "ghost"),
                             ("✎ " + t("edit"), self.bike_edit_ui, "ghost"),
                             ("🗑 " + t("delete"), self.bike_del, "bad")], self._bike_search, seg)
            wrap = tk.Frame(f, bg=T.BG); wrap.pack(fill="both", expand=True, padx=22, pady=(0, 16))
            self.bike_tbl = Table(wrap, [("bike_no", "Bike No", 130), ("brand", "Brand", 100), ("model", "Model", 150),
                                         ("cost", "लागत", 110, "e"), ("sell", "बिक्री", 110, "e"),
                                         ("profit", "नाफा", 100, "e"), ("status", "स्थिति", 90),
                                         ("kar", "कर", 120), ("bb", "Bluebook", 100), ("ph", "📷", 40)],
                                  18, lambda r: self.bike_docs_ui())
            self.bike_tbl.pack(fill="both", expand=True)
        def _bike_tab(self, k): self.bike_tab = k; self.rf_bikes()
        def _bike_search(self, q): self._bike_q = q.lower(); self.rf_bikes()
        def rf_bikes(self):
            sql = "SELECT * FROM bikes WHERE is_deleted=0"; a = []
            if self.bike_tab != "all": sql += " AND status=?"; a.append(self.bike_tab)
            sql += f" ORDER BY id DESC LIMIT {PAGE_LIMIT}"
            rows = []
            with db().rd() as c:
                for r in c.execute(sql, tuple(a)):
                    blob = f"{r['bike_no']} {r['brand']} {r['model']} {r['color']}".lower()
                    if self._bike_q and self._bike_q not in blob: continue
                    extra = bike_extra_cost(c, r["bike_no"])
                    cost = (r["total_cost"] or 0) + extra
                    ka = kar_alert(r["buy_date"]) if (not r["kar_paid"] and r["status"] == "Stock") else None
                    rows.append({"_id": r["id"], "bike_no": r["bike_no"], "brand": r["brand"], "model": r["model"],
                                 "cost": money(cost), "sell": money(r["sell_price"]),
                                 "profit": money(r["profit"]) if r["status"] == "Sold" else "—",
                                 "status": "स्टक" if r["status"] == "Stock" else "बिकिभयो",
                                 "kar": ka[0] if ka else ("तिर्यो ✓" if r["kar_paid"] else "—"),
                                 "bb": r["bb_expiry"] or "—", "ph": "📷" if r["photo_path"] else "",
                                 "_kar": ka[1] if ka else 99, "_p": r["profit"] or 0})
            self.bike_tbl.fill(rows, lambda r: "bad" if r["_kar"] < 0 else "warn" if r["_kar"] <= KAR_WARN
                               else "mute" if r["status"] == "बिकिभयो" else ("ok" if r["_p"] > 0 else None))
        def _bike_fields(self, v=None):
            v = v or {}
            return [{"k": "brand", "label": "Brand", "type": "select", "values": list(BRANDS), "default": v.get("brand", "Honda")},
                    {"k": "model", "label": "Model", "type": "select", "values": BRANDS.get(v.get("brand", "Honda"), BRANDS["Honda"]), "default": v.get("model", "")},
                    {"k": "color", "label": "Color", "type": "select", "values": COLORS, "default": v.get("color", COLORS[0])},
                    {"k": "year", "label": "Year", "type": "select", "values": YEARS, "default": v.get("year", YEARS[0])},
                    {"k": "bike_no", "label": "Bike No *", "default": v.get("bike_no", "")},
                    {"k": "buy_date", "label": "खरिद मिति", "default": v.get("buy_date", today())},
                    {"k": "engine_no", "label": "Engine No", "default": v.get("engine_no", "")},
                    {"k": "chassis_no", "label": "Chassis No", "default": v.get("chassis_no", "")},
                    {"k": "bb_expiry", "label": "Bluebook Expiry", "default": v.get("bb_expiry", "")},
                    {"k": "method", "label": "भुक्तानी माध्यम", "type": "select", "values": METHODS, "default": "Cash"},
                    {"k": "seller_name", "label": "बिक्रेता", "default": v.get("seller_name", "")},
                    {"k": "seller_phone", "label": "बिक्रेता फोन", "default": v.get("seller_phone", "")},
                    {"k": "buy_price", "label": "खरिद मूल्य *", "default": v.get("buy_price", "")},
                    {"k": "repair_cost", "label": "मर्मत खर्च", "default": v.get("repair_cost", 0)},
                    {"k": "naam_sari", "label": "नामसारी", "default": v.get("naam_sari", 0)},
                    {"k": "kar_cost", "label": "कर रकम", "default": v.get("kar_cost", 0)},
                    {"k": "kar_paid", "label": "कर तिरिसकेको", "type": "check", "default": v.get("kar_paid", False)}]
        def bike_new(self):
            def link(ws, w):
                def upd(val):
                    ws["model"].values(BRANDS.get(val, ["Other — manual"]))
                    ws["model"].set(BRANDS.get(val, [""])[0])
                w.cb.bind("<<ComboboxSelected>>", lambda e: upd(w.get()))
            flds = self._bike_fields(); flds[0]["link"] = link
            def save(d):
                bike_buy(d)
                Toast.show(self.root, "✅ बाइक खरिद दर्ता", "ok")
                self.rf_bikes(); self.rf_dash()
            form(self.root, "नयाँ बाइक खरिद", flds, save, width=540,
                 note="लागत = खरिद + मर्मत + नामसारी + (कर तिरिएमा कर)। फोटो 📷 Docs बाट थप्नुहोस्।")
        def bike_edit_ui(self):
            r = self.need(self.bike_tbl)
            if not r: return
            b = db().one("SELECT * FROM bikes WHERE id=?", (r["_id"],))
            if not b: return
            v = dict(b); v["kar_paid"] = bool(b["kar_paid"])
            flds = [f for f in self._bike_fields(v) if f["k"] not in ("method", "buy_date")]
            flds[0]["link"] = lambda ws, w: w.cb.bind("<<ComboboxSelected>>", lambda e: (
                ws["model"].values(BRANDS.get(w.get(), [])), ws["model"].set(BRANDS.get(w.get(), [""])[0])))
            def save(d):
                bike_edit(r["_id"], d)
                Toast.show(self.root, "✅ अपडेट भयो", "ok"); self.rf_bikes(); self.rf_dash()
            form(self.root, f"सम्पादन — {b['bike_no']}", flds, save, v, width=540)
        def bike_docs_ui(self):
            r = self.need(self.bike_tbl, "बाइक छान्नुहोस्")
            if not r: return
            b = db().one("SELECT * FROM bikes WHERE id=?", (r["_id"],))
            d = modal(self.root, f"Docs/Photo — {b['bike_no']}", 420, 560)
            body = tk.Frame(d, bg=T.BG); body.pack(fill="both", expand=True, padx=20, pady=14)
            tk.Label(body, text=f"{b['bike_no']} · {b['model']}", bg=T.BG, fg=T.INK, font=F(13, "bold")).pack(anchor="w")
            pbox = tk.Frame(body, bg=T.PANEL, width=300, height=170); pbox.pack(pady=8); pbox.pack_propagate(False)
            def show_photo(name):
                for w in pbox.winfo_children(): w.destroy()
                p = PHOTO_DIR / os.path.basename(name or "")
                if name and HAS_PIL and p.is_file():
                    try:
                        img = Image.open(p); img.load()
                        ratio = min(288 / img.width, 158 / img.height)
                        img = img.resize((max(1, int(img.width * ratio)), max(1, int(img.height * ratio))))
                        ph = ImageTk.PhotoImage(img); pbox._ph = ph
                        tk.Label(pbox, image=ph, bg=T.PANEL).place(relx=.5, rely=.5, anchor="center"); return
                    except Exception: pass
                tk.Label(pbox, text=("फोटो छ (preview का लागि PIL चाहिन्छ)" if name else "फोटो छैन"),
                         bg=T.PANEL, fg=T.FAINT, font=F(9)).place(relx=.5, rely=.5, anchor="center")
            show_photo(b["photo_path"])
            picked = {"path": b["photo_path"] or ""}
            def pick():
                p = filedialog.askopenfilename(title="बाइक फोटो", filetypes=[("Images", "*.jpg *.jpeg *.png *.webp")], parent=d)
                if p:
                    try:
                        picked["path"] = save_photo(p, b["bike_no"]); show_photo(picked["path"])
                        Toast.show(d, "फोटो सेभ भयो (Save थिच्नुहोस्)", "info")
                    except Exception as e: messagebox.showerror("त्रुटि", str(e), parent=d)
            Btn(body, "📷 फोटो छान्नुहोस्", pick, "ghost", small=True).pack(pady=4)
            fe = Field(body, "Engine No", 30, T.BG, b["engine_no"] or ""); fe.pack(fill="x", pady=4)
            fc = Field(body, "Chassis No", 30, T.BG, b["chassis_no"] or ""); fc.pack(fill="x", pady=4)
            fb = Field(body, "Bluebook Expiry (YYYY-MM-DD)", 30, T.BG, b["bb_expiry"] or ""); fb.pack(fill="x", pady=4)
            def save():
                try: bike_docs(b["id"], fe.get(), fc.get(), fb.get(), picked["path"])
                except Exception as e: messagebox.showerror("त्रुटि", str(e), parent=d); return
                d.destroy(); Toast.show(self.root, "✅ Docs सेभ", "ok"); self.rf_bikes()
            Btn(body, "💾 सेभ", save, "ok").pack(pady=10)
        def bike_sell_ui(self):
            r = self.need(self.bike_tbl)
            if not r: return
            b = db().one("SELECT * FROM bikes WHERE id=? AND is_deleted=0", (r["_id"],))
            if not b or b["status"] != "Stock":
                Toast.show(self.root, "यो बाइक स्टकमा छैन", "warn"); return
            flds = [{"k": "name", "label": "ग्राहक नाम *", "span": 2},
                    {"k": "phone", "label": "फोन"}, {"k": "address", "label": "ठेगाना"},
                    {"k": "citizenship", "label": "नागरिकता / ID"},
                    {"k": "price", "label": "बिक्री मूल्य *", "default": b["sell_price"] or ""},
                    {"k": "paid", "label": "भुक्तानी *", "default": 0, "link": make_due_link(["price"], "paid")},
                    {"k": "method", "label": "माध्यम", "type": "select", "values": METHODS}]
            def save(d):
                no = bike_sell(r["_id"], d, d["price"], d["paid"], d["method"])
                Toast.show(self.root, f"✅ बिक्री · {no}", "ok")
                self.rf_bikes(); self.rf_dash(); self.rf_bills()
                if confirm(self.root, "बिल", f"{no} बन्यो। अहिले छाप्ने?"): open_bill(no)
            form(self.root, f"बिक्री — {b['bike_no']} {b['model']}", flds, save, width=520,
                 note="नाफा ग्राहकको बिलमा कहिल्यै देखिँदैन।")
        def bike_del(self):
            r = self.need(self.bike_tbl)
            if r and confirm(self.root, t("confirm"), f"{r['bike_no']} हटाउने? (soft-delete, लगमा रहन्छ)"):
                try:
                    bike_delete(r["_id"]); Toast.show(self.root, "🗑 हटाइयो", "bad"); self.rf_bikes(); self.rf_dash()
                except Exception as e: messagebox.showerror("त्रुटि", str(e), parent=self.root)

        # ---------- COST SHEET (owner-only) ----------
        def pg_cost(self):
            f, b = self.page("cost", scroll=False)
            self._cost_q = ""
            self.toolbar(f, [("🖨 Print", self.cost_print, "primary"), ("📥 CSV", self.cost_csv, "ghost")],
                         lambda q: (setattr(self, "_cost_q", q.lower()), self.rf_cost()))
            tk.Label(f, text="डबल-क्लिक → पार्ट्स/लेबर breakdown + फोटो", bg=T.BG, fg=T.MUTED,
                     font=F(8)).pack(anchor="w", padx=24)
            wrap = tk.Frame(f, bg=T.BG); wrap.pack(fill="both", expand=True, padx=22, pady=(4, 16))
            self.cost_tbl = Table(wrap, [("bike_no", "Bike No", 120), ("model", "Model", 140),
                                         ("buy", "खरिद", 100, "e"), ("rep", "मर्मत", 90, "e"),
                                         ("naam", "नामसारी", 90, "e"), ("kar", "कर", 80, "e"),
                                         ("parts", "पार्ट्स", 90, "e"), ("lab", "लेबर", 90, "e"),
                                         ("total", "वास्तविक लागत", 120, "e"), ("sell", "बिक्री", 100, "e"),
                                         ("profit", "नाफा", 100, "e"), ("margin", "%", 70, "e"),
                                         ("status", "स्थिति", 80)], 18, lambda r: self.cost_detail(r))
            self.cost_tbl.pack(fill="both", expand=True)
        def _cost_rows(self):
            rows = []
            with db().rd() as c:
                for r in c.execute("SELECT * FROM bikes WHERE is_deleted=0 ORDER BY id DESC"):
                    blob = f"{r['bike_no']} {r['model']}".lower()
                    if self._cost_q and self._cost_q not in blob: continue
                    p = c.execute("SELECT COALESCE(SUM(qty*unit_cost),0) FROM part_usage WHERE bike_no=?", (r["bike_no"],)).fetchone()[0]
                    l = c.execute("SELECT COALESCE(SUM(amount),0) FROM labour WHERE bike_no=?", (r["bike_no"],)).fetchone()[0]
                    tc = round((r["total_cost"] or 0) + p + l, 2)
                    sell = r["sell_price"] or 0
                    profit = round(sell - tc, 2) if r["status"] == "Sold" else 0
                    rows.append({"_id": r["id"], "bike_no": r["bike_no"], "model": r["model"],
                                 "buy": money(r["buy_price"]), "rep": money(r["repair_cost"]),
                                 "naam": money(r["naam_sari"]), "kar": money(r["kar_cost"] if r["kar_paid"] else 0),
                                 "parts": money(p), "lab": money(l), "total": money(tc), "sell": money(sell),
                                 "profit": money(profit) if r["status"] == "Sold" else "—",
                                 "margin": f"{profit/sell*100:.1f}%" if sell > 0 and r["status"] == "Sold" else "—",
                                 "status": "स्टक" if r["status"] == "Stock" else "बिकिभयो",
                                 "_p": profit, "_tc": tc, "_sold": r["status"] == "Sold"})
            return rows
        def rf_cost(self):
            self.cost_tbl.fill(self._cost_rows(), lambda r: ("ok" if r["_p"] > 0 else "bad") if r["_sold"] else None)
        def cost_detail(self, r=None):
            r = r or self.need(self.cost_tbl)
            if not r: return
            b = db().one("SELECT * FROM bikes WHERE id=?", (r["_id"],))
            d = modal(self.root, f"लागत — {b['bike_no']}", 680, 640)
            body = tk.Frame(d, bg=T.BG); body.pack(fill="both", expand=True, padx=18, pady=12)
            tk.Label(body, text=f"{b['bike_no']} · {b['brand']} {b['model']}", bg=T.BG, fg=T.INK, font=F(14, "bold")).pack(anchor="w")
            tk.Label(body, text=f"Engine: {b['engine_no'] or '—'} · Chassis: {b['chassis_no'] or '—'} · BB: {b['bb_expiry'] or '—'}",
                     bg=T.BG, fg=T.MUTED, font=F(9)).pack(anchor="w", pady=(2, 6))
            tk.Label(body, text="पार्ट्स प्रयोग", bg=T.BG, fg=T.INK, font=F(10, "bold")).pack(anchor="w")
            pt = Table(body, [("name", "पार्ट्स", 220), ("qty", "संख्या", 70, "e"), ("rate", "दर", 100, "e"),
                              ("total", "जम्मा", 110, "e"), ("date", "मिति", 100)], 5)
            pt.pack(fill="x", pady=(2, 8))
            prows = []
            for i, x in enumerate(db().q("SELECT pu.*, p.name FROM part_usage pu LEFT JOIN parts p ON p.id=pu.part_id "
                                         "WHERE pu.bike_no=? ORDER BY pu.id", (b["bike_no"],))):
                prows.append({"_id": i, "name": x["name"] or "(मेटिएको)", "qty": x["qty"], "rate": money(x["unit_cost"], 2),
                              "total": money(x["qty"] * x["unit_cost"], 2), "date": x["date"]})
            pt.fill(prows)
            tk.Label(body, text="लेबर", bg=T.BG, fg=T.INK, font=F(10, "bold")).pack(anchor="w")
            lt = Table(body, [("date", "मिति", 100), ("desc", "काम", 240), ("mech", "मिस्त्री", 140),
                              ("amt", "रकम", 110, "e")], 5)
            lt.pack(fill="x", pady=(2, 8))
            lt.fill([{"_id": x["id"], "date": x["date"], "desc": x["description"], "mech": x["mechanic"],
                      "amt": money(x["amount"], 2)} for x in db().q("SELECT * FROM labour WHERE bike_no=? ORDER BY id", (b["bike_no"],))])
            tk.Label(body, text=f"वास्तविक लागत {money(r['_tc'])} · बिक्री {money(b['sell_price'])} · "
                     f"नाफा {money(r['_p']) if r['_sold'] else '—'}", bg=T.BG,
                     fg=T.OK if r["_p"] >= 0 else T.BAD, font=F(11, "bold")).pack(anchor="w", pady=6)
            Btn(body, "🖨 Print", lambda: self._cost_html(b["id"]), "primary", small=True).pack(anchor="w")
        def _cost_html(self, bid):
            b = db().one("SELECT * FROM bikes WHERE id=?", (bid,))
            with db().rd() as c:
                p = c.execute("SELECT COALESCE(SUM(qty*unit_cost),0) FROM part_usage WHERE bike_no=?", (b["bike_no"],)).fetchone()[0]
                l = c.execute("SELECT COALESCE(SUM(amount),0) FROM labour WHERE bike_no=?", (b["bike_no"],)).fetchone()[0]
            tc = (b["total_cost"] or 0) + p + l
            uri = photo_uri(b["photo_path"])
            ph = f"<div style='text-align:center'><img class='photo' src='{uri}'></div>" if uri else ""
            prows = "".join(f"<tr><td>{esc(x['name'] or '(मेटिएको)')}</td><td>{x['qty']}</td>"
                            f"<td class='num'>{money(x['unit_cost'],2)}</td><td class='num'>{money(x['qty']*x['unit_cost'],2)}</td></tr>"
                            for x in db().q("SELECT pu.*, p.name FROM part_usage pu LEFT JOIN parts p ON p.id=pu.part_id WHERE pu.bike_no=?", (b["bike_no"],)))
            lrows = "".join(f"<tr><td>{esc(x['date'])}</td><td>{esc(x['description'])}</td><td>{esc(x['mechanic'])}</td>"
                            f"<td class='num'>{money(x['amount'],2)}</td></tr>"
                            for x in db().q("SELECT * FROM labour WHERE bike_no=?", (b["bike_no"],)))
            s = db().one("SELECT shop_name FROM settings WHERE id=1")
            doc = (f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Cost {esc(b['bike_no'])}</title>"
                   f"<style>{BILL_CSS}</style></head><body><div class='wrap'>"
                   f"<div class='noprint' style='text-align:right'><button class='btn' onclick='window.print()'>🖨 Print</button></div>"
                   f"<h1>लागत पाना — {esc(s['shop_name'])}</h1>"
                   f"<p><b>{esc(b['bike_no'])}</b> · {esc(b['brand'])} {esc(b['model'])} · {esc(b['status'])}</p>{ph}"
                   f"<table><tr><th>खरिद</th><th>मर्मत</th><th>नामसारी</th><th>कर</th><th>पार्ट्स</th><th>लेबर</th><th>जम्मा लागत</th></tr>"
                   f"<tr><td class='num'>{money(b['buy_price'])}</td><td class='num'>{money(b['repair_cost'])}</td>"
                   f"<td class='num'>{money(b['naam_sari'])}</td><td class='num'>{money(b['kar_cost'] if b['kar_paid'] else 0)}</td>"
                   f"<td class='num'>{money(p)}</td><td class='num'>{money(l)}</td><td class='num'><b>{money(tc)}</b></td></tr></table>"
                   f"<h3>पार्ट्स</h3><table><tr><th>नाम</th><th>संख्या</th><th>दर</th><th>जम्मा</th></tr>{prows or '<tr><td colspan=4>छैन</td></tr>'}</table>"
                   f"<h3>लेबर</h3><table><tr><th>मिति</th><th>काम</th><th>मिस्त्री</th><th>रकम</th></tr>{lrows or '<tr><td colspan=4>छैन</td></tr>'}</table>"
                   f"<div class='tot'><p>बिक्री: {money(b['sell_price'])}</p><p class='{'ok' if (b['profit'] or 0)>=0 else 'due'}'>नाफा: {money(b['profit'])}</p></div>"
                   f"</div></body></html>")
            pth = BILL_DIR / f"cost_{fname(b['bike_no'])}_{int(time.time())}.html"
            pth.write_text(doc, encoding="utf-8"); webbrowser.open(pth.as_uri())
        def cost_print(self):
            r = self.need(self.cost_tbl)
            if r: self._cost_html(r["_id"])
        def cost_csv(self):
            rows = self._cost_rows()
            if not rows: Toast.show(self.root, "डाटा छैन", "warn"); return
            p = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="cost_sheet.csv", parent=self.root)
            if p:
                export_csv([{k: v for k, v in r.items() if not k.startswith("_")} for r in rows], Path(p))
                Toast.show(self.root, "📥 निर्यात", "ok")

        # ---------- ACCESSORIES ----------
        def pg_acc(self):
            f, b = self.page("acc", scroll=False)
            self._acc_q = ""
            self.toolbar(f, [("＋ सामान", self.acc_new, "ok"), ("📦 Restock", self.acc_restock_ui, "primary"),
                             ("💰 " + t("sell"), self.acc_sell_ui, "primary")],
                         lambda q: (setattr(self, "_acc_q", q.lower()), self.rf_acc()))
            wrap = tk.Frame(f, bg=T.BG); wrap.pack(fill="both", expand=True, padx=22, pady=(0, 8))
            self.acc_tbl = Table(wrap, [("name", "सामान", 220), ("category", "श्रेणी", 120), ("stock", "स्टक", 80, "e"),
                                        ("buy", "खरिद", 110, "e"), ("sell", "बिक्री", 110, "e")], 9)
            self.acc_tbl.pack(fill="both", expand=True)
            tk.Label(f, text="— हालैको बिक्री —", bg=T.BG, fg=T.MUTED, font=F(9, "bold")).pack(anchor="w", padx=24)
            w2 = tk.Frame(f, bg=T.BG); w2.pack(fill="both", expand=True, padx=22, pady=(4, 16))
            self.accs_tbl = Table(w2, [("bill_no", "बिल", 100), ("item", "सामान", 190), ("qty", "संख्या", 70, "e"),
                                       ("price", "दर", 100, "e"), ("total", "जम्मा", 110, "e"),
                                       ("customer", "ग्राहक", 150), ("payment", "माध्यम", 100), ("date", "मिति", 100)], 7)
            self.accs_tbl.pack(fill="both", expand=True)
        def rf_acc(self):
            rows = []
            for r in db().q("SELECT * FROM accessories ORDER BY stock ASC, name"):
                if self._acc_q and self._acc_q not in r["name"].lower(): continue
                rows.append({"_id": r["id"], "name": r["name"], "category": r["category"], "stock": r["stock"],
                             "buy": money(r["buy_price"]), "sell": money(r["sell_price"])})
            self.acc_tbl.fill(rows, lambda r: "bad" if r["stock"] <= 2 else ("warn" if r["stock"] <= 5 else None))
            self.accs_tbl.fill([{"_id": r["id"], "bill_no": r["bill_no"] or "—", "item": r["item"], "qty": r["qty"],
                                 "price": money(r["price"]), "total": money(r["total"]), "customer": r["customer"],
                                 "payment": r["payment"], "date": r["date"]}
                                for r in db().q(f"SELECT * FROM acc_sales WHERE is_deleted=0 ORDER BY id DESC LIMIT {PAGE_LIMIT}")])
        def acc_new(self):
            flds = [{"k": "name", "label": "सामान नाम *", "span": 2},
                    {"k": "category", "label": "श्रेणी", "type": "select", "values": ACC_CATS},
                    {"k": "qty", "label": "मात्रा", "default": 10},
                    {"k": "buy", "label": "खरिद मूल्य", "default": 0},
                    {"k": "sell", "label": "बिक्री मूल्य", "default": 0}]
            def save(d):
                acc_add(d["name"], d["category"], d["qty"], d["buy"], d["sell"])
                Toast.show(self.root, "✅ सामान थपियो", "ok"); self.rf_acc()
            form(self.root, "नयाँ सामान", flds, save)
        def acc_restock_ui(self):
            r = self.need(self.acc_tbl)
            if not r: return
            a = db().one("SELECT * FROM accessories WHERE id=?", (r["_id"],))
            flds = [{"k": "qty", "label": "थप मात्रा *", "default": 10},
                    {"k": "buy", "label": "खरिद मूल्य", "default": a["buy_price"]},
                    {"k": "sell", "label": "बिक्री मूल्य (0=यथावत)", "default": a["sell_price"]},
                    {"k": "method", "label": "माध्यम", "type": "select", "values": METHODS}]
            def save(d):
                acc_restock(r["_id"], d["qty"], d["buy"], d["sell"], d["method"])
                Toast.show(self.root, "✅ स्टक बढ्यो", "ok"); self.rf_acc()
            form(self.root, f"Restock — {a['name']}", flds, save)
        def acc_sell_ui(self):
            r = self.need(self.acc_tbl)
            if not r: return
            a = db().one("SELECT * FROM accessories WHERE id=?", (r["_id"],))
            if (a["stock"] or 0) <= 0: Toast.show(self.root, "स्टक सकियो", "bad"); return
            flds = [{"k": "qty", "label": "संख्या *", "default": 1},
                    {"k": "price", "label": "दर (बदल्न मिल्छ) *", "default": a["sell_price"]},
                    {"k": "name", "label": "ग्राहक नाम *", "span": 2},
                    {"k": "phone", "label": "फोन"},
                    {"k": "paid", "label": "भुक्तानी *", "default": a["sell_price"],
                     "link": make_due_link(["price"], "paid", "qty")},
                    {"k": "method", "label": "माध्यम", "type": "select", "values": METHODS}]
            def save(d):
                no = acc_sell(r["_id"], d["qty"], d["price"], d, d["paid"], d["method"])
                Toast.show(self.root, f"✅ बिक्री · {no}", "ok")
                self.rf_acc(); self.rf_bills(); self.rf_dash()
                if confirm(self.root, "बिल", f"{no} छाप्ने?"): open_bill(no)
            form(self.root, f"बिक्री — {a['name']} (स्टक {a['stock']})", flds, save, width=520)

        # ---------- SERVICES ----------
        def pg_svc(self):
            f, b = self.page("svc", scroll=False)
            self.svc_tab = "PLATE"; self._svc_q = ""
            seg = Seg(f, [("🚗 नम्बर प्लेट", "PLATE"), ("🔧 मर्मत", "REPAIR")], self._svc_tab)
            self.toolbar(f, [("＋ नयाँ", self.svc_new, "ok"), ("✓ स्थिति", self.svc_status, "ghost")],
                         lambda q: (setattr(self, "_svc_q", q.lower()), self.rf_svc()), seg)
            wrap = tk.Frame(f, bg=T.BG); wrap.pack(fill="both", expand=True, padx=22, pady=(0, 16))
            self.svc_tbl = Table(wrap, [("bill_no", "बिल", 100), ("customer", "ग्राहक", 150), ("phone", "फोन", 110),
                                        ("bike_no", "Bike", 120), ("info", "विवरण", 220), ("total", "जम्मा", 110, "e"),
                                        ("paid", "भुक्तानी", 110, "e"), ("due", "बाँकी", 100, "e"),
                                        ("status", "स्थिति", 100), ("date", "मिति", 100)], 18)
            self.svc_tbl.pack(fill="both", expand=True)
        def _svc_tab(self, k): self.svc_tab = k; self.rf_svc()
        def rf_svc(self):
            rows = []
            if self.svc_tab == "PLATE":
                for r in db().q(f"SELECT * FROM plates WHERE is_deleted=0 ORDER BY id DESC LIMIT {PAGE_LIMIT}"):
                    blob = f"{r['customer']} {r['bike_no']} {r['bill_no']}".lower()
                    if self._svc_q and self._svc_q not in blob: continue
                    rows.append({"_id": r["id"], "bill_no": r["bill_no"] or "—", "customer": r["customer"],
                                 "phone": r["phone"], "bike_no": r["bike_no"],
                                 "info": f"{r['plate_type']} · {r['plate_no']}", "total": money(r["charge"]),
                                 "paid": money(r["paid"]), "due": money(r["due"]), "status": r["status"],
                                 "date": r["date"], "_due": r["due"] or 0})
            else:
                for r in db().q(f"SELECT * FROM repairs WHERE is_deleted=0 ORDER BY id DESC LIMIT {PAGE_LIMIT}"):
                    blob = f"{r['customer']} {r['bike_no']} {r['problem']}".lower()
                    if self._svc_q and self._svc_q not in blob: continue
                    rows.append({"_id": r["id"], "bill_no": r["bill_no"] or "—", "customer": r["customer"],
                                 "phone": r["phone"], "bike_no": r["bike_no"],
                                 "info": f"{r['problem']} · {r['bike_model']}", "total": money(r["total"]),
                                 "paid": money(r["paid"]), "due": money(r["due"]), "status": r["status"],
                                 "date": r["date"], "_due": r["due"] or 0})
            self.svc_tbl.fill(rows, lambda r: "bad" if r["_due"] > 0 else "ok")
        def svc_new(self):
            if self.svc_tab == "PLATE":
                flds = [{"k": "name", "label": "ग्राहक नाम *", "span": 2},
                        {"k": "phone", "label": "फोन"}, {"k": "bike_no", "label": "Bike No"},
                        {"k": "plate_no", "label": "Plate No"},
                        {"k": "kind", "label": "प्रकार", "type": "select", "values": PLATE_KINDS},
                        {"k": "cost", "label": "लागत (आन्तरिक)", "default": 0},
                        {"k": "charge", "label": "शुल्क *", "default": 0},
                        {"k": "paid", "label": "भुक्तानी *", "default": 0, "link": make_due_link(["charge"], "paid")},
                        {"k": "method", "label": "माध्यम", "type": "select", "values": METHODS},
                        {"k": "status", "label": "स्थिति", "type": "select", "values": JOB_STATUS}]
                def save(d):
                    no = plate_add(d, d["bike_no"], d["plate_no"], d["kind"], d["cost"], d["charge"],
                                   d["paid"], d["method"], d["status"])
                    Toast.show(self.root, f"✅ प्लेट बिल · {no}", "ok")
                    self.rf_svc(); self.rf_bills(); self.rf_dash()
                form(self.root, "नम्बर प्लेट सेवा", flds, save, width=540)
            else:
                flds = [{"k": "name", "label": "ग्राहक नाम *", "span": 2},
                        {"k": "phone", "label": "फोन"}, {"k": "bike_no", "label": "Bike No"},
                        {"k": "model", "label": "Bike Model"}, {"k": "problem", "label": "समस्या"},
                        {"k": "parts", "label": "पार्ट्स खर्च", "default": 0},
                        {"k": "labour", "label": "लेबर खर्च", "default": 0},
                        {"k": "paid", "label": "भुक्तानी *", "default": 0,
                         "link": make_due_link(["parts", "labour"], "paid")},
                        {"k": "method", "label": "माध्यम", "type": "select", "values": METHODS},
                        {"k": "status", "label": "स्थिति", "type": "select", "values": JOB_STATUS}]
                def save(d):
                    no = repair_add(d, d["bike_no"], d["model"], d["problem"], d["parts"], d["labour"],
                                    d["paid"], d["method"], d["status"])
                    Toast.show(self.root, f"✅ मर्मत बिल · {no}", "ok")
                    self.rf_svc(); self.rf_bills(); self.rf_dash()
                form(self.root, "मर्मत सेवा", flds, save, width=540)
        def svc_status(self):
            r = self.need(self.svc_tbl)
            if not r: return
            d = modal(self.root, "स्थिति बदल्नुहोस्", 320, 180)
            body = tk.Frame(d, bg=T.BG); body.pack(fill="both", expand=True, padx=20, pady=16)
            cb = Combo(body, "नयाँ स्थिति", JOB_STATUS, r["status"], 20, T.BG); cb.pack(fill="x")
            def save():
                job_status(self.svc_tab, r["_id"], cb.get())
                d.destroy(); Toast.show(self.root, "✅ स्थिति अपडेट", "ok"); self.rf_svc()
            Btn(body, "सेभ", save, "ok").pack(pady=12)

        # ---------- PARTS ----------
        def pg_parts(self):
            f, b = self.page("parts", scroll=False)
            self._part_q = ""
            tk.Label(f, text="पार्ट्स छुट्टै बेचिँदैन — बाइक मर्मतमा मात्र प्रयोग हुन्छ।", bg=T.BG,
                     fg=T.MUTED, font=F(9)).pack(anchor="w", padx=24, pady=(12, 0))
            self.toolbar(f, [("＋ पार्ट्स", self.part_new, "ok"), ("📦 खरिद", self.part_buy_ui, "primary"),
                             ("🔧 बाइकमा लगाउनु", self.part_use_ui, "warn"), ("＋ लेबर", self.labour_ui, "ghost")],
                         lambda q: (setattr(self, "_part_q", q.lower()), self.rf_parts()))
            wrap = tk.Frame(f, bg=T.BG); wrap.pack(fill="both", expand=True, padx=22, pady=(0, 16))
            self.part_tbl = Table(wrap, [("name", "पार्ट्स", 220), ("category", "श्रेणी", 130), ("stock", "स्टक", 80, "e"),
                                         ("cost", "लागत/पिस", 120, "e"), ("thr", "अलर्ट", 80, "e")], 18)
            self.part_tbl.pack(fill="both", expand=True)
        def rf_parts(self):
            rows = []
            for r in db().q("SELECT * FROM parts ORDER BY name"):
                if self._part_q and self._part_q not in r["name"].lower(): continue
                rows.append({"_id": r["id"], "name": r["name"], "category": r["category"], "stock": r["stock"],
                             "cost": money(r["unit_cost"], 2), "thr": r["threshold"]})
            self.part_tbl.fill(rows, lambda r: "bad" if r["stock"] <= r["thr"] else None)
        def part_new(self):
            flds = [{"k": "name", "label": "पार्ट्स नाम *", "span": 2},
                    {"k": "cat", "label": "श्रेणी", "type": "select", "values": PART_CATS},
                    {"k": "qty", "label": "स्टक", "default": 0},
                    {"k": "cost", "label": "लागत/पिस", "default": 0},
                    {"k": "thr", "label": "अलर्ट सीमा", "default": 3}]
            def save(d):
                part_add(d["name"], d["cat"], d["qty"], d["cost"], d["thr"])
                Toast.show(self.root, "✅ पार्ट्स थपियो", "ok"); self.rf_parts()
            form(self.root, "नयाँ पार्ट्स", flds, save)
        def part_buy_ui(self):
            r = self.need(self.part_tbl)
            if not r: return
            p = db().one("SELECT * FROM parts WHERE id=?", (r["_id"],))
            flds = [{"k": "qty", "label": "मात्रा *", "default": 1},
                    {"k": "cost", "label": "लागत/पिस", "default": p["unit_cost"]},
                    {"k": "method", "label": "माध्यम", "type": "select", "values": METHODS}]
            def save(d):
                part_buy(r["_id"], d["qty"], d["cost"], d["method"])
                Toast.show(self.root, "✅ स्टक बढ्यो (औसत लागत)", "ok"); self.rf_parts()
            form(self.root, f"खरिद — {p['name']}", flds, save)
        def _stock_bikes(self):
            return [r["bike_no"] for r in db().q("SELECT bike_no FROM bikes WHERE status='Stock' AND is_deleted=0 ORDER BY bike_no")]
        def part_use_ui(self):
            r = self.need(self.part_tbl)
            if not r: return
            bikes = self._stock_bikes()
            if not bikes: Toast.show(self.root, "स्टकमा बाइक छैन", "warn"); return
            flds = [{"k": "bike", "label": "बाइक", "type": "select", "values": bikes},
                    {"k": "qty", "label": "मात्रा *", "default": 1}]
            def save(d):
                part_use(r["_id"], d["bike"], d["qty"])
                Toast.show(self.root, "✅ पार्ट्स लागतमा जोडियो", "ok")
                self.rf_parts(); self.rf_bikes()
                if hasattr(self, "cost_tbl"): self.rf_cost()
            form(self.root, f"{r['name']} → बाइक", flds, save)
        def labour_ui(self):
            bikes = self._stock_bikes()
            if not bikes: Toast.show(self.root, "स्टकमा बाइक छैन", "warn"); return
            flds = [{"k": "bike", "label": "बाइक", "type": "select", "values": bikes},
                    {"k": "mech", "label": "मिस्त्री *"},
                    {"k": "desc", "label": "कामको विवरण *", "span": 2},
                    {"k": "amount", "label": "रकम *"},
                    {"k": "cash", "label": "नगद तिरेको", "type": "check", "default": True}]
            def save(d):
                labour_add(d["bike"], d["desc"], d["mech"], d["amount"], d["cash"])
                Toast.show(self.root, "✅ लेबर थपियो", "ok"); self.rf_bikes()
                if hasattr(self, "cost_tbl"): self.rf_cost()
            form(self.root, "लेबर / मर्मत खर्च", flds, save)

        # ---------- CUSTOMERS ----------
        def pg_cust(self):
            f, b = self.page("cust", scroll=False)
            self._cust_q = ""
            self.toolbar(f, [("＋ " + t("add"), self.cust_new, "ok"), ("📜 खाता", self.cust_ledger, "primary"),
                             ("📩 Reminder", self.cust_remind, "warn")],
                         lambda q: (setattr(self, "_cust_q", q.lower()), self.rf_cust()))
            wrap = tk.Frame(f, bg=T.BG); wrap.pack(fill="both", expand=True, padx=22, pady=(0, 16))
            self.cust_tbl = Table(wrap, [("name", "नाम", 190), ("phone", "फोन", 120), ("citizenship", "ID", 130),
                                         ("address", "ठेगाना", 180), ("n", "बिल", 60, "e"), ("bought", "किनेको", 120, "e"),
                                         ("paid", "तिरेको", 120, "e"), ("due", "बाँकी", 120, "e")], 18,
                                  lambda r: self.cust_ledger())
            self.cust_tbl.pack(fill="both", expand=True)
        def rf_cust(self):
            rows = []
            for r in db().q(f"""SELECT c.*,
                (SELECT COUNT(*) FROM bills WHERE customer_id=c.id AND {ACTIVE}) n,
                COALESCE((SELECT SUM(total) FROM bills WHERE customer_id=c.id AND {ACTIVE}),0) bought,
                COALESCE((SELECT SUM(paid) FROM bills WHERE customer_id=c.id AND {ACTIVE}),0) paid,
                COALESCE((SELECT SUM(due) FROM bills WHERE customer_id=c.id AND {ACTIVE}),0) due
                FROM customers c ORDER BY c.name COLLATE NOCASE LIMIT {PAGE_LIMIT}"""):
                blob = f"{r['name']} {r['phone']} {r['citizenship']}".lower()
                if self._cust_q and self._cust_q not in blob: continue
                rows.append({"_id": r["id"], "name": r["name"], "phone": r["phone"] or "—",
                             "citizenship": r["citizenship"] or "—", "address": r["address"] or "—",
                             "n": r["n"], "bought": money(r["bought"]), "paid": money(r["paid"]),
                             "due": money(r["due"]), "_due": r["due"]})
            self.cust_tbl.fill(rows, lambda r: "bad" if r["_due"] > 0 else None)
        def cust_new(self):
            flds = [{"k": "name", "label": "पूरा नाम *", "span": 2},
                    {"k": "phone", "label": "फोन (परिवारले साझा गर्न मिल्छ)"},
                    {"k": "citizenship", "label": "नागरिकता / लाइसेन्स"},
                    {"k": "address", "label": "ठेगाना", "span": 2}]
            def save(d):
                with db().tx() as c:
                    _customer_resolve(c, d["name"], d["phone"], d["address"], d["citizenship"])
                    db().audit(c, "CUST_ADD", d["name"])
                Toast.show(self.root, "✅ ग्राहक सुरक्षित", "ok"); self.rf_cust()
            form(self.root, "नयाँ ग्राहक", flds, save)
        def cust_ledger(self):
            r = self.need(self.cust_tbl)
            if not r: return
            d = modal(self.root, f"खाता — {r['name']}", 780, 640)
            body = tk.Frame(d, bg=T.BG); body.pack(fill="both", expand=True, padx=18, pady=12)
            tk.Label(body, text="बिल (डबल-क्लिक → छाप्नुहोस्)", bg=T.BG, fg=T.INK, font=F(11, "bold")).pack(anchor="w")
            bt = Table(body, [("bill_no", "बिल", 100), ("type", "प्रकार", 80), ("detail", "विवरण", 230),
                              ("total", "जम्मा", 110, "e"), ("due", "बाँकी", 100, "e"), ("date", "मिति", 100)], 7,
                       lambda x: open_bill(x["bill_no"]))
            bt.pack(fill="x", pady=(4, 12))
            bt.fill([{"_id": x["id"], "bill_no": x["bill_no"], "type": x["bill_type"], "detail": x["detail"],
                      "total": money(x["total"]), "due": money(x["due"]), "date": x["created_at"][:10],
                      "_v": x["voided"], "_d": x["due"]}
                     for x in db().q("SELECT * FROM bills WHERE customer_id=? AND is_deleted=0 ORDER BY id DESC", (r["_id"],))],
                    lambda x: "mute" if x["_v"] else ("bad" if x["_d"] > 0 else "ok"))
            tk.Label(body, text="उधारो खाता (running balance)", bg=T.BG, fg=T.INK, font=F(11, "bold")).pack(anchor="w")
            lt = Table(body, [("date", "मिति", 100), ("type", "प्रकार", 100), ("description", "विवरण", 260),
                              ("udharo", "उधारो", 100, "e"), ("tiryo", "असुल", 100, "e"), ("balance", "मौज्दात", 110, "e")], 7)
            lt.pack(fill="both", expand=True, pady=4)
            lt.fill([{"_id": x["id"], "date": x["date"], "type": x["type"], "description": x["description"],
                      "udharo": money(x["udharo"]), "tiryo": money(x["tiryo"]), "balance": money(x["balance"])}
                     for x in db().q("SELECT * FROM ledger WHERE customer_id=? ORDER BY id DESC", (r["_id"],))])
        def cust_remind(self):
            r = self.need(self.cust_tbl)
            if not r: return
            if r["_due"] <= 0: Toast.show(self.root, "बाँकी रकम छैन", "info"); return
            s = db().one("SELECT shop_name,mobile FROM settings WHERE id=1")
            bills = db().q(f"SELECT bill_no,due FROM bills WHERE customer_id=? AND {ACTIVE} AND due>0", (r["_id"],))
            lines = "\n".join(f"• {b['bill_no']}: {money(b['due'])}" for b in bills)
            msg = (f"नमस्ते {r['name']} जी,\n{s['shop_name']} मा तपाईंको कुल बाँकी {money(r['_due'])} छ।\n"
                   f"कृपया छिट्टै भुक्तानी गरिदिनुहोला।\n\n{lines}\n\nसम्पर्क: {s['mobile'] or '—'}\nधन्यवाद!")
            self.root.clipboard_clear(); self.root.clipboard_append(msg)
            Toast.show(self.root, "📩 Reminder कपी भयो", "ok")

        # ---------- BILLS ----------
        def pg_bills(self):
            f, b = self.page("bills", scroll=False)
            self.bill_tab = "active"; self._bill_q = ""
            seg = Seg(f, [("सक्रिय", "active"), ("बाँकी", "due"), ("रद्द", "void"), ("सबै", "all")], self._bill_tab)
            self.toolbar(f, [("🖨 " + t("print"), self.bill_print, "primary"),
                             ("💰 " + t("collect"), self.bill_collect_ui, "ok"),
                             ("✎ " + t("edit"), self.bill_edit_ui, "ghost"),
                             ("🚫 " + t("void"), self.bill_void_ui, "bad")],
                         lambda q: (setattr(self, "_bill_q", q.lower()), self.rf_bills()), seg)
            wrap = tk.Frame(f, bg=T.BG); wrap.pack(fill="both", expand=True, padx=22, pady=(0, 16))
            self.bill_tbl = Table(wrap, [("bill_no", "बिल", 100), ("type", "प्रकार", 80), ("customer", "ग्राहक", 160),
                                         ("phone", "फोन", 110), ("detail", "विवरण", 240), ("total", "जम्मा", 110, "e"),
                                         ("paid", "भुक्तानी", 110, "e"), ("due", "बाँकी", 100, "e"),
                                         ("payment", "माध्यम", 100), ("state", "स्थिति", 90), ("date", "मिति", 100)],
                                  18, lambda r: self.bill_print())
            self.bill_tbl.pack(fill="both", expand=True)
        def _bill_tab(self, k): self.bill_tab = k; self.rf_bills()
        def rf_bills(self):
            sql = "SELECT * FROM bills WHERE is_deleted=0"
            if self.bill_tab == "active": sql += " AND voided=0"
            elif self.bill_tab == "due": sql += " AND voided=0 AND due>0"
            elif self.bill_tab == "void": sql += " AND voided=1"
            sql += f" ORDER BY id DESC LIMIT {PAGE_LIMIT}"
            rows = []
            for r in db().q(sql):
                blob = f"{r['bill_no']} {r['customer']} {r['phone']} {r['detail']}".lower()
                if self._bill_q and self._bill_q not in blob: continue
                rows.append({"_id": r["id"], "bill_no": r["bill_no"], "type": r["bill_type"], "customer": r["customer"],
                             "phone": r["phone"] or "—", "detail": r["detail"], "total": money(r["total"]),
                             "paid": money(r["paid"]), "due": money(r["due"]), "payment": r["payment"],
                             "state": "रद्द" if r["voided"] else ("चुक्ता" if r["due"] <= 0 else "बाँकी"),
                             "date": r["created_at"][:10], "_v": r["voided"], "_d": r["due"]})
            self.bill_tbl.fill(rows, lambda r: "mute" if r["_v"] else ("bad" if r["_d"] > 0 else "ok"))
        def bill_print(self):
            r = self.need(self.bill_tbl)
            if r:
                try: open_bill(r["bill_no"])
                except Exception as e: messagebox.showerror("त्रुटि", str(e), parent=self.root)
        def bill_collect_ui(self):
            r = self.need(self.bill_tbl)
            if not r: return
            b = db().one("SELECT * FROM bills WHERE id=?", (r["_id"],))
            if b["voided"]: Toast.show(self.root, "रद्द बिलमा असुल मिल्दैन", "bad"); return
            if b["due"] <= 0: Toast.show(self.root, "पूरा चुक्ता भइसक्यो", "info"); return
            flds = [{"k": "amount", "label": f"रकम (बाँकी {money(b['due'])}) *", "default": b["due"]},
                    {"k": "method", "label": "माध्यम", "type": "select", "values": METHODS},
                    {"k": "note", "label": "टिप्पणी", "span": 2}]
            def save(d):
                nd = bill_collect(b["bill_no"], d["amount"], d["method"], d["note"])
                Toast.show(self.root, f"✅ असुल — बाँकी {money(nd)}", "ok")
                self.rf_bills(); self.rf_cust(); self.rf_dash()
            form(self.root, f"असुल — {b['bill_no']}", flds, save)
        def bill_edit_ui(self):
            r = self.need(self.bill_tbl)
            if not r: return
            b = db().one("SELECT * FROM bills WHERE id=?", (r["_id"],))
            if b["voided"]: Toast.show(self.root, "रद्द बिल सम्पादन मिल्दैन", "bad"); return
            pays = db().q("SELECT * FROM payments WHERE bill_id=?", (b["id"],))
            can = len(pays) <= 1
            custs = db().q("SELECT id,name,phone FROM customers ORDER BY name")
            if not custs: Toast.show(self.root, "ग्राहक छैन", "warn"); return
            keys = [f"{c['name']} ({c['phone'] or '—'}) #{c['id']}" for c in custs]
            cmap = dict(zip(keys, [c["id"] for c in custs]))
            cur = next((k for k, v in cmap.items() if v == b["customer_id"]), keys[0])
            flds = [{"k": "cust", "label": "ग्राहक", "type": "select", "values": keys, "default": cur, "span": 2},
                    {"k": "total", "label": "जम्मा *", "default": b["total"]},
                    {"k": "paid", "label": "भुक्तानी *", "default": b["paid"],
                     "link": make_due_link(["total"], "paid")},
                    {"k": "method", "label": "माध्यम", "type": "select", "values": METHODS, "default": b["payment"]}]
            def save(d):
                cid = cmap[d["cust"]]
                if can: bill_edit(b["bill_no"], cid, d["total"], d["paid"], d["method"])
                else: bill_edit(b["bill_no"], cid)
                Toast.show(self.root, "✅ बिल अपडेट", "ok")
                self.rf_bills(); self.rf_cust(); self.rf_dash()
            form(self.root, f"सम्पादन — {b['bill_no']}", flds, save, width=520,
                 note="" if can else "असुल किस्ता बनिसकेको — रकम बदल्न मिल्दैन; ग्राहक मात्र।")
        def bill_void_ui(self):
            r = self.need(self.bill_tbl)
            if not r: return
            b = db().one("SELECT * FROM bills WHERE id=?", (r["_id"],))
            if b["voided"]: Toast.show(self.root, "पहिले नै रद्द छ", "warn"); return
            cash = db().val("SELECT COALESCE(SUM(amount),0) FROM payments WHERE bill_id=? AND method='Cash'", (b["id"],))
            flds = [{"k": "reason", "label": "रद्द गर्ने कारण *", "span": 2}]
            def save(d):
                if not confirm(self.root, t("confirm"), f"{b['bill_no']} रद्द गर्ने?\nनगद {money(cash)} फिर्ता हुन्छ।\nयो कार्य फिर्ता हुँदैन।"):
                    return
                bill_void(b["bill_no"], d["reason"])
                Toast.show(self.root, "🚫 बिल रद्द", "bad")
                self.rf_bills(); self.rf_bikes(); self.rf_acc(); self.rf_cust(); self.rf_dash()
            form(self.root, f"रद्द — {b['bill_no']}", flds, save,
                 note=f"नगद फिर्ता: {money(cash)} · स्टक स्वतः फिर्ता हुन्छ")

        # ---------- CASH ----------
        def pg_cash(self):
            f, b = self.page("cash", scroll=False)
            bar = tk.Frame(f, bg=T.BG); bar.pack(fill="x", padx=22, pady=(16, 6))
            tk.Label(bar, text="मिति", bg=T.BG, fg=T.MUTED, font=F(9, "bold")).pack(side="left")
            wrap = tk.Frame(bar, bg=T.LINE, padx=1, pady=1); wrap.pack(side="left", padx=8)
            self.cb_date = tk.Entry(wrap, width=12, font=F(10), bg=T.FIELD, fg=T.INK, relief="flat", insertbackground=T.ACCENT)
            self.cb_date.pack(ipady=5, padx=6); self.cb_date.insert(0, today())
            self.cb_date.bind("<Return>", lambda e: self.rf_cash())
            Btn(bar, "◀", lambda: self._shift(-1), "ghost", w=32, small=True).pack(side="left", padx=2)
            Btn(bar, "▶", lambda: self._shift(1), "ghost", w=32, small=True).pack(side="left", padx=2)
            Btn(bar, "देखाउनु", self.rf_cash, "ghost", small=True).pack(side="left", padx=6)
            Btn(bar, "＋ आयो", lambda: self.cash_manual_ui("In"), "ok", small=True).pack(side="left", padx=3)
            Btn(bar, "－ गयो", lambda: self.cash_manual_ui("Out"), "bad", small=True).pack(side="left", padx=3)
            Btn(bar, "🖨", self.cash_print, "ghost", small=True).pack(side="right", padx=3)
            Btn(bar, "🔓 " + t("reopen"), self.cash_reopen_ui, "warn", small=True).pack(side="right", padx=3)
            Btn(bar, "🔒 " + t("close_day"), self.cash_close_ui, "primary", small=True).pack(side="right", padx=3)
            cards = tk.Frame(f, bg=T.BG); cards.pack(fill="x", padx=16, pady=6)
            self.cbk = {}
            for k, lbl, col in (("opening", t("opening"), T.MUTED), ("in", t("cash_in"), T.OK),
                                ("out", t("cash_out"), T.BAD), ("closing", t("closing"), T.ACCENT)):
                c = Card(cards, pad=12, accent=col); c.pack(side="left", fill="both", expand=True, padx=6)
                tk.Label(c.body, text=lbl, bg=T.PANEL, fg=T.MUTED, font=F(9, "bold")).pack(anchor="w")
                v = tk.Label(c.body, text="—", bg=T.PANEL, fg=T.INK, font=F(17, "bold")); v.pack(anchor="w", pady=(4, 0))
                self.cbk[k] = v
            self.cb_state = tk.Label(f, text="", bg=T.BG, fg=T.OK, font=F(10, "bold")); self.cb_state.pack(anchor="w", padx=24)
            wrap2 = tk.Frame(f, bg=T.BG); wrap2.pack(fill="both", expand=True, padx=22, pady=(4, 16))
            self.cb_tbl = Table(wrap2, [("type", "प्रकार", 80), ("category", "श्रेणी", 170), ("amount", "रकम", 130, "e"),
                                        ("method", "माध्यम", 110), ("note", "टिप्पणी", 380)], 16)
            self.cb_tbl.pack(fill="both", expand=True)
        def _shift(self, n):
            try: d = datetime.strptime(vdate(self.cb_date.get()), "%Y-%m-%d").date() + timedelta(days=n)
            except Exception as e: messagebox.showerror("त्रुटि", str(e), parent=self.root); return
            self.cb_date.delete(0, "end"); self.cb_date.insert(0, d.isoformat()); self.rf_cash()
        def rf_cash(self):
            try: s = cash_summary(self.cb_date.get())
            except Exception as e: messagebox.showerror("त्रुटि", str(e), parent=self.root); return
            for k in ("opening", "in", "out", "closing"): self.cbk[k].config(text=money(s[k], 2))
            self.cb_state.config(text=f"🔒 बन्द · {s['note'] or '—'}" if s["closed"] else "🔓 खुला — entry मिल्छ",
                                 fg=T.WARN if s["closed"] else T.OK)
            d = vdate(self.cb_date.get())
            self.cb_tbl.fill([{"_id": r["id"], "type": "आयो" if r["type"] == "In" else "गयो", "category": r["category"],
                               "amount": money(r["amount"], 2), "method": r["method"], "note": r["note"], "_t": r["type"]}
                              for r in db().q("SELECT * FROM cashbook WHERE date=? ORDER BY id", (d,))],
                             lambda r: "ok" if r["_t"] == "In" else "bad")
        def cash_manual_ui(self, typ):
            flds = [{"k": "amount", "label": "रकम *"}, {"k": "note", "label": "कारण / टिप्पणी *"}]
            def save(d):
                cash_manual(self.cb_date.get(), typ, d["amount"], d["note"])
                Toast.show(self.root, "✅ नगद entry", "ok"); self.rf_cash(); self.rf_dash()
            form(self.root, f"नगद {'आयो' if typ == 'In' else 'गयो'} — {self.cb_date.get()}", flds, save)
        def cash_close_ui(self):
            d = self.cb_date.get()
            flds = [{"k": "note", "label": "टिप्पणी (मौज्दात फरक भए लेख्नुहोस्)", "span": 2}]
            def save(dd):
                if not confirm(self.root, t("confirm"), f"{d} बन्द गर्ने?\nत्यसपछि उक्त मितिमा नगद entry मिल्दैन।"): return
                cash_close(d, dd["note"], self.user)
                Toast.show(self.root, f"🔒 {d} बन्द", "ok"); self.rf_cash()
            form(self.root, f"दिन बन्द — {d}", flds, save)
        def cash_reopen_ui(self):
            if not confirm(self.root, t("confirm"), "सबैभन्दा पछिल्लो बन्द दिन पुनः खोल्ने?"): return
            try:
                d = cash_reopen(); Toast.show(self.root, f"🔓 {d} खुल्यो", "warn"); self.rf_cash()
            except Exception as e: messagebox.showerror("त्रुटि", str(e), parent=self.root)
        def cash_print(self):
            d = vdate(self.cb_date.get()); s = cash_summary(d)
            rows = db().q("SELECT * FROM cashbook WHERE date=? ORDER BY id", (d,))
            tr = "".join(f"<tr><td>{esc(r['type'])}</td><td>{esc(r['category'])}</td><td>{esc(r['note'])}</td>"
                         f"<td class='num'>{money(r['amount'],2)}</td></tr>" for r in rows)
            sh = db().one("SELECT shop_name,address FROM settings WHERE id=1")
            doc = (f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Cash {d}</title><style>{BILL_CSS}</style></head>"
                   f"<body><div class='wrap'><div class='noprint' style='text-align:right'>"
                   f"<button class='btn' onclick='window.print()'>🖨 Print</button></div>"
                   f"<div class='hd'><div><h1>{esc(sh['shop_name'])}</h1><p>{esc(sh['address'])}</p></div>"
                   f"<div class='tag'>{d}</div></div>"
                   f"<div class='meta'><div><b>{t('opening')}</b>{money(s['opening'],2)}</div>"
                   f"<div><b>{t('cash_in')}</b>{money(s['in'],2)}</div><div><b>{t('cash_out')}</b>{money(s['out'],2)}</div>"
                   f"<div><b>{t('closing')}</b>{money(s['closing'],2)}</div></div>"
                   f"<table><tr><th>प्रकार</th><th>श्रेणी</th><th>टिप्पणी</th><th class='num'>रकम</th></tr>"
                   f"{tr or '<tr><td colspan=4>entry छैन</td></tr>'}</table>"
                   f"<div class='sig'><span>तयार पार्ने</span><span>प्रमाणित गर्ने</span></div></div></body></html>")
            p = BILL_DIR / f"cash_{fname(d)}_{int(time.time())}.html"
            p.write_text(doc, encoding="utf-8"); webbrowser.open(p.as_uri())

        # ---------- EXPENSES ----------
        def pg_exp(self):
            f, b = self.page("exp", scroll=False)
            self._exp_q = ""
            self.toolbar(f, [("＋ " + t("add"), self.exp_new, "ok"), ("✎ " + t("edit"), self.exp_edit_ui, "ghost"),
                             ("🗑 " + t("delete"), self.exp_del_ui, "bad"), ("📥 CSV", self.exp_csv, "ghost")],
                         lambda q: (setattr(self, "_exp_q", q.lower()), self.rf_exp()))
            self.exp_total = tk.Label(f, text="", bg=T.BG, fg=T.MUTED, font=F(10, "bold")); self.exp_total.pack(anchor="e", padx=26)
            wrap = tk.Frame(f, bg=T.BG); wrap.pack(fill="both", expand=True, padx=22, pady=(4, 16))
            self.exp_tbl = Table(wrap, [("date", "मिति", 110), ("title", "शीर्षक", 260), ("category", "श्रेणी", 140),
                                        ("method", "माध्यम", 120), ("amount", "रकम", 130, "e"), ("note", "टिप्पणी", 220)], 18)
            self.exp_tbl.pack(fill="both", expand=True)
        def rf_exp(self):
            rows, tot = [], 0
            for r in db().q(f"SELECT * FROM expenses WHERE is_deleted=0 ORDER BY date DESC, id DESC LIMIT {PAGE_LIMIT}"):
                blob = f"{r['title']} {r['category']}".lower()
                if self._exp_q and self._exp_q not in blob: continue
                tot += r["amount"] or 0
                rows.append({"_id": r["id"], "date": r["date"], "title": r["title"], "category": r["category"],
                             "method": r["method"], "amount": money(r["amount"], 2), "note": r["note"] or ""})
            self.exp_tbl.fill(rows); self.exp_total.config(text=f"जम्मा: {money(tot,2)}")
        def _exp_fields(self, v=None):
            v = v or {}
            return [{"k": "title", "label": "शीर्षक *", "span": 2, "default": v.get("title", "")},
                    {"k": "cat", "label": "श्रेणी", "type": "select", "values": EXP_CATS, "default": v.get("category", EXP_CATS[0])},
                    {"k": "amount", "label": "रकम *", "default": v.get("amount", "")},
                    {"k": "date", "label": "मिति *", "default": v.get("date", today())},
                    {"k": "method", "label": "माध्यम", "type": "select", "values": METHODS, "default": v.get("method", "Cash")},
                    {"k": "note", "label": "टिप्पणी", "span": 2, "default": v.get("note", "")}]
        def exp_new(self):
            def save(d):
                exp_add(d["title"], d["cat"], d["amount"], d["date"], d["method"], d["note"])
                Toast.show(self.root, "✅ खर्च दर्ता", "ok"); self.rf_exp(); self.rf_dash()
            form(self.root, "नयाँ खर्च", self._exp_fields(), save, width=520)
        def exp_edit_ui(self):
            r = self.need(self.exp_tbl)
            if not r: return
            e = db().one("SELECT * FROM expenses WHERE id=?", (r["_id"],))
            def save(d):
                exp_edit(r["_id"], d["title"], d["cat"], d["amount"], d["date"], d["method"], d["note"])
                Toast.show(self.root, "✅ अपडेट — नगद समायोजन", "ok"); self.rf_exp(); self.rf_dash()
            form(self.root, "खर्च सम्पादन", self._exp_fields(dict(e)), save, dict(e), width=520,
                 note="पुरानो नगद प्रभाव उल्टिएर नयाँ लागू हुन्छ।")
        def exp_del_ui(self):
            r = self.need(self.exp_tbl)
            if r and confirm(self.root, t("confirm"), f"{r['title']} ({r['amount']}) हटाउने?\nनगद फिर्ता हुन्छ।"):
                try:
                    exp_delete(r["_id"]); Toast.show(self.root, "🗑 हटाइयो", "bad"); self.rf_exp(); self.rf_dash()
                except Exception as e: messagebox.showerror("त्रुटि", str(e), parent=self.root)
        def exp_csv(self):
            p = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="expenses.csv", parent=self.root)
            if not p: return
            rows = [dict(r) for r in db().q("SELECT date,title,category,amount,method,note FROM expenses "
                                            "WHERE is_deleted=0 ORDER BY date DESC")]
            try:
                export_csv(rows, Path(p)); Toast.show(self.root, "📥 निर्यात", "ok")
            except Exception as e: messagebox.showerror("त्रुटि", str(e), parent=self.root)

        # ---------- STAFF ----------
        def pg_staff(self):
            f, b = self.page("staff", scroll=False)
            self._staff_q = ""
            self.toolbar(f, [("＋ कर्मचारी", self.staff_new, "ok"), ("💰 तलब", self.salary_ui, "primary"),
                             ("📜 इतिहास", self.salary_hist, "ghost"), ("🚫 निष्क्रिय", self.staff_off_ui, "bad")],
                         lambda q: (setattr(self, "_staff_q", q.lower()), self.rf_staff()))
            wrap = tk.Frame(f, bg=T.BG); wrap.pack(fill="both", expand=True, padx=22, pady=(0, 16))
            self.staff_tbl = Table(wrap, [("name", "नाम", 200), ("phone", "फोन", 130), ("role", "भूमिका", 160),
                                          ("salary", "मासिक तलब", 140, "e")], 18)
            self.staff_tbl.pack(fill="both", expand=True)
        def rf_staff(self):
            rows = []
            for r in db().q("SELECT * FROM staff WHERE active=1 ORDER BY name"):
                if self._staff_q and self._staff_q not in r["name"].lower(): continue
                rows.append({"_id": r["id"], "name": r["name"], "phone": r["phone"] or "—",
                             "role": r["role"] or "—", "salary": money(r["salary"])})
            self.staff_tbl.fill(rows)
        def staff_new(self):
            flds = [{"k": "name", "label": "नाम *", "span": 2}, {"k": "phone", "label": "फोन"},
                    {"k": "role", "label": "भूमिका"}, {"k": "salary", "label": "मासिक तलब", "default": 0}]
            def save(d):
                staff_add(d["name"], d["phone"], d["role"], d["salary"])
                Toast.show(self.root, "✅ कर्मचारी थपियो", "ok"); self.rf_staff()
            form(self.root, "नयाँ कर्मचारी", flds, save)
        def salary_ui(self):
            r = self.need(self.staff_tbl)
            if not r: return
            s = db().one("SELECT * FROM staff WHERE id=?", (r["_id"],))
            flds = [{"k": "month", "label": "महिना (YYYY-MM) *", "default": date.today().strftime("%Y-%m")},
                    {"k": "amount", "label": "रकम *", "default": s["salary"]},
                    {"k": "date", "label": "मिति *", "default": today()},
                    {"k": "method", "label": "माध्यम", "type": "select", "values": METHODS}]
            def save(d):
                salary_pay(r["_id"], d["month"], d["amount"], d["date"], d["method"], "Monthly")
                Toast.show(self.root, "✅ तलब दिइयो", "ok"); self.rf_dash()
            form(self.root, f"तलब — {s['name']}", flds, save)
        def salary_hist(self):
            r = self.need(self.staff_tbl)
            if not r: return
            d = modal(self.root, f"तलब इतिहास — {r['name']}", 600, 420)
            body = tk.Frame(d, bg=T.BG); body.pack(fill="both", expand=True, padx=18, pady=12)
            tt = Table(body, [("month", "महिना", 110), ("amount", "रकम", 130, "e"), ("date", "मिति", 120),
                              ("method", "माध्यम", 130)], 10)
            tt.pack(fill="both", expand=True)
            tt.fill([{"_id": x["id"], "month": x["month"], "amount": money(x["amount"]), "date": x["date"],
                      "method": x["method"]} for x in db().q("SELECT * FROM salaries WHERE staff_id=? ORDER BY month DESC", (r["_id"],))])
        def staff_off_ui(self):
            r = self.need(self.staff_tbl)
            if r and confirm(self.root, t("confirm"), f"{r['name']} निष्क्रिय गर्ने?"):
                staff_off(r["_id"]); Toast.show(self.root, "निष्क्रिय", "warn"); self.rf_staff()

        # ---------- REPORTS ----------
        def pg_rep(self):
            f, b = self.page("rep", scroll=False)
            bar = tk.Frame(f, bg=T.BG); bar.pack(fill="x", padx=22, pady=(16, 8))
            tk.Label(bar, text="महिना (YYYY-MM)", bg=T.BG, fg=T.MUTED, font=F(9, "bold")).pack(side="left")
            wrap = tk.Frame(bar, bg=T.LINE, padx=1, pady=1); wrap.pack(side="left", padx=8)
            self.rep_m = tk.Entry(wrap, width=10, font=F(10), bg=T.FIELD, fg=T.INK, relief="flat", insertbackground=T.ACCENT)
            self.rep_m.pack(ipady=5, padx=6); self.rep_m.insert(0, date.today().strftime("%Y-%m"))
            self.rep_m.bind("<Return>", lambda e: self.rf_rep())
            Btn(bar, "निकाल्नु", self.rf_rep, "primary", small=True).pack(side="left", padx=6)
            Btn(bar, "📥 CSV", self.rep_csv, "ghost", small=True).pack(side="right")
            body = tk.Frame(f, bg=T.BG); body.pack(fill="both", expand=True, padx=22, pady=(0, 16))
            self.rep_txt = tk.Text(body, font=("Consolas", 12), bg=T.PANEL, fg=T.INK, relief="flat", bd=0,
                                   padx=22, pady=18, wrap="none")
            self.rep_txt.pack(fill="both", expand=True)
            self._rep = {}
        def rf_rep(self):
            try: r = monthly(self.rep_m.get())
            except Exception as e: messagebox.showerror("त्रुटि", str(e), parent=self.root); return
            self._rep = r
            s = db().one("SELECT shop_name FROM settings WHERE id=1")
            lines = ["═" * 58, f"  नाफा–नोक्सान · {r['Month']}", f"  {s['shop_name']}", "═" * 58, ""]
            for k, v in r.items():
                if k == "Month": continue
                if k in ("Gross Profit", "NET PROFIT"): lines.append("─" * 58)
                lines.append(f"  {k:<26}{money(v,2):>28}")
            lines += ["═" * 58, "", "  * रद्द बिल समावेश छैनन्", f"  * {now()} मा तयार"]
            self.rep_txt.configure(state="normal"); self.rep_txt.delete("1.0", "end")
            self.rep_txt.insert("1.0", "\n".join(lines)); self.rep_txt.configure(state="disabled")
        def rep_csv(self):
            if not self._rep: Toast.show(self.root, "पहिले रिपोर्ट निकाल्नुहोस्", "warn"); return
            p = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=f"pnl_{self._rep['Month']}.csv", parent=self.root)
            if p:
                export_csv([{"Metric": k, "Value": v} for k, v in self._rep.items()], Path(p))
                Toast.show(self.root, "📥 निर्यात", "ok")

        # ---------- AUDIT ----------
        def pg_audit(self):
            f, b = self.page("audit", scroll=False)
            self._audit_q = ""
            self.toolbar(f, [("🔍 चेन जाँच", self.audit_verify, "primary"), ("📥 CSV", self.audit_csv, "ghost")],
                         lambda q: (setattr(self, "_audit_q", q.lower()), self.rf_audit()))
            self.audit_lab = tk.Label(f, text="", bg=T.BG, fg=T.MUTED, font=F(9, "bold")); self.audit_lab.pack(anchor="w", padx=26)
            wrap = tk.Frame(f, bg=T.BG); wrap.pack(fill="both", expand=True, padx=22, pady=(4, 16))
            self.audit_tbl = Table(wrap, [("ts", "समय", 160), ("actor", "प्रयोगकर्ता", 120), ("action", "कार्य", 170),
                                          ("detail", "विवरण", 520)], 20)
            self.audit_tbl.pack(fill="both", expand=True)
        def rf_audit(self):
            rows = []
            for r in db().q(f"SELECT * FROM audit ORDER BY id DESC LIMIT {PAGE_LIMIT}"):
                blob = f"{r['actor']} {r['action']} {r['detail']}".lower()
                if self._audit_q and self._audit_q not in blob: continue
                rows.append({"_id": r["id"], "ts": r["ts"].replace("T", " "), "actor": r["actor"],
                             "action": r["action"], "detail": r["detail"]})
            self.audit_tbl.fill(rows)
            self.audit_lab.config(text=f"{len(rows)} रेकर्ड · hash-chain सुरक्षित")
        def audit_verify(self):
            ok, n = db().verify_chain()
            self.audit_lab.config(text=f"✅ {n} रेकर्ड — चेन सही" if ok else f"⚠ चेन #{n} मा समस्या",
                                  fg=T.OK if ok else T.BAD)
            Toast.show(self.root, "चेन सही छ" if ok else "चेनमा समस्या!", "ok" if ok else "bad")
        def audit_csv(self):
            p = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="audit.csv", parent=self.root)
            if p:
                export_csv([dict(r) for r in db().q("SELECT ts,actor,action,detail,hash FROM audit ORDER BY id DESC")], Path(p))
                Toast.show(self.root, "📥 निर्यात", "ok")

        # ---------- SETTINGS (owner) ----------
        def pg_set(self):
            f, b = self.page("set")
            s = db().one("SELECT * FROM settings WHERE id=1")
            c = self.card(b, "🏪 दुकान विवरण", "बिलमा यही देखिन्छ")
            g = tk.Frame(c.body, bg=T.PANEL); g.pack(fill="x"); g.columnconfigure((0, 1), weight=1)
            self.sf = {}
            for i, (k, lbl, dv) in enumerate((("shop_name", "दुकान नाम", s["shop_name"]), ("address", "ठेगाना", s["address"]),
                                              ("mobile", "मोबाइल", s["mobile"]), ("pan", "PAN / VAT", s["pan"]),
                                              ("owner", "सञ्चालक", s["owner"]), ("email", "इमेल", s["email"]),
                                              ("website", "वेबसाइट", s["website"]), ("bill_note", "बिल टिप्पणी", s["bill_note"]))):
                r, cc = divmod(i, 2)
                cell = tk.Frame(g, bg=T.PANEL); cell.grid(row=r, column=cc, sticky="ew", padx=6, pady=5)
                self.sf[k] = Field(cell, lbl, 28, T.PANEL, dv or "")
            br = tk.Frame(c.body, bg=T.PANEL); br.pack(anchor="w", pady=(10, 0))
            Btn(br, "💾 सेभ", self.save_shop, "ok").pack(side="left", padx=(0, 6))
            Btn(br, "🗑 खाली गर्नु", self.clear_shop, "bad", small=True).pack(side="left", padx=3)
            Btn(br, "↺ डिफल्ट", self.reset_shop, "ghost", small=True).pack(side="left", padx=3)
            # clickable links
            lr = tk.Frame(c.body, bg=T.PANEL); lr.pack(anchor="w", pady=(8, 0))
            for txt, url in (("🔗 Turso Dashboard", "https://turso.tech/"), ("🔗 GitHub Repo", "https://github.com/khemraj73-coder/shuvam-recondition-house")):
                lb = tk.Label(lr, text=txt, bg=T.PANEL, fg=T.ACCENT, font=F(8, "bold"), cursor="hand2")
                lb.pack(side="left", padx=(0, 14))
                lb.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
            c2 = self.card(b, "🎨 रूप र भाषा")
            row = tk.Frame(c2.body, bg=T.PANEL); row.pack(fill="x")
            th = Combo(row, t("theme"), [THEMES[k].label for k in THEME_ORDER], THEMES[T.key].label, 22, T.PANEL)
            th.pack(side="left", padx=(0, 14))
            def thchange(v):
                k = next((kk for kk in THEME_ORDER if THEMES[kk].label == v), None)
                if k: self.set_theme(k)
            th.cb.bind("<<ComboboxSelected>>", lambda e: thchange(th.get()))
            lg = Combo(row, t("lang"), ["नेपाली", "English"], "नेपाली" if _lang == "ne" else "English", 16, T.PANEL)
            lg.pack(side="left")
            def lgchange(v):
                set_lang("ne" if v == "नेपाली" else "en")
                with db().tx() as cc2: cc2.execute("UPDATE settings SET lang=? WHERE id=1", (_lang,))
                self._rebuild("set")
            lg.cb.bind("<<ComboboxSelected>>", lambda e: lgchange(lg.get()))
            c4 = self.card(b, "👥 प्रयोगकर्ता", "Owner ले सबै हेर्छ; Staff को पहुँच सीमित")
            gg = tk.Frame(c4.body, bg=T.PANEL); gg.pack(fill="x")
            self.nu = {}
            for i, (k, lbl) in enumerate((("u", "Username"), ("p", "Password"))):
                cell = tk.Frame(gg, bg=T.PANEL); cell.grid(row=0, column=i, padx=6, sticky="ew")
                self.nu[k] = Field(cell, lbl, 20, T.PANEL, show="●" if k == "p" else None)
            cell = tk.Frame(gg, bg=T.PANEL); cell.grid(row=0, column=2, padx=6, sticky="ew")
            self.nu["r"] = Combo(cell, "Role", ["staff", "owner"], "staff", 12, T.PANEL)
            Btn(c4.body, "＋ थप्नुहोस्", self.add_user, "primary").pack(anchor="w", pady=(10, 0))
            Btn(c4.body, "🗑 चयन गरिएको हटाउनु", self.del_user, "bad", small=True).pack(anchor="w", pady=(6, 0))
            self.utbl = Table(c4.body, [("username", "प्रयोगकर्ता", 180), ("role", "भूमिका", 120),
                                        ("created_at", "सिर्जना", 200)], 5)
            self.utbl.pack(fill="x", pady=(10, 0))
            c5 = self.card(b, "🛡 डाटा सुरक्षा", "SQLite backup API · hash-chain audit")
            rr = tk.Frame(c5.body, bg=T.PANEL); rr.pack(fill="x")
            Btn(rr, "💾 Backup", self.do_backup, "ok").pack(side="left", padx=4)
            Btn(rr, "📥 Restore", self.do_restore, "warn").pack(side="left", padx=4)
            Btn(rr, "🔍 Audit जाँच", self.do_chain, "ghost").pack(side="left", padx=4)
            tk.Label(c5.body, text=f"DB: {DB_FILE}\nडाटा फोल्डर: {DATA}", bg=T.PANEL, fg=T.FAINT,
                     font=F(8), justify="left").pack(anchor="w", pady=(10, 0))
            c6 = self.card(b, "☁ Cloud Sync", "DPAPI-encrypted + अनिवार्य checksum · code मा कुनै token छैन")
            cfg = cloud_cfg()
            g6 = tk.Frame(c6.body, bg=T.PANEL); g6.pack(fill="x")
            self.cl_url = Field(g6, "Turso URL", 40, T.PANEL, cfg["url"]); self.cl_url.pack(side="left", padx=(0, 10))
            self.cl_tok = Field(g6, "Auth Token", 32, T.PANEL, cfg["token"], show="●"); self.cl_tok.pack(side="left")
            self.cl_on = Check(c6.body, "Cloud सक्षम", cfg["on"], T.PANEL); self.cl_on.pack(anchor="w", pady=6)
            r6 = tk.Frame(c6.body, bg=T.PANEL); r6.pack(fill="x")
            Btn(r6, "💾 सेभ", self.cloud_save_ui, "ghost", small=True).pack(side="left", padx=3)
            Btn(r6, "⬆ Sync", self.cloud_push_ui, "ok", small=True).pack(side="left", padx=3)
            Btn(r6, "⬇ Restore", self.cloud_pull_ui, "warn", small=True).pack(side="left", padx=3)
            Btn(r6, "🔄 जाँच", self.test_cloud, "ghost", small=True).pack(side="left", padx=3)
            r6b = tk.Frame(c6.body, bg=T.PANEL); r6b.pack(fill="x", pady=(6, 0))
            Btn(r6b, "↺ डिफल्ट Turso", lambda: (self.cl_url.set(TURSO_URL_ULTIMATE), self.cl_tok.set(TURSO_TOKEN_ULTIMATE)), "ghost", small=True).pack(side="left", padx=3)
            Btn(r6b, "🔗 Turso खोल्नु", lambda: webbrowser.open("https://turso.tech/"), "ghost", small=True).pack(side="left", padx=3)
            if not dpapi_ok():
                tk.Label(c6.body, text="⚠ यो OS मा DPAPI छैन — cloud sync Windows मा मात्र चल्छ।",
                         bg=T.PANEL, fg=T.WARN, font=F(8)).pack(anchor="w", pady=(6, 0))
            c7 = self.card(b, "🚀 Update", "sha256 अनिवार्य — नभए install हुँदैन")
            self.up_url = Field(c7.body, "version.json URL", 48, T.PANEL, s["update_url"] or "")
            self.up_url.pack(anchor="w")
            r7 = tk.Frame(c7.body, bg=T.PANEL); r7.pack(fill="x", pady=(8, 0))
            Btn(r7, "💾 URL सेभ", self.save_upurl, "ghost", small=True).pack(side="left", padx=3)
            Btn(r7, "🔄 जाँच", self.check_update, "primary", small=True).pack(side="left", padx=3)
            Btn(r7, "↺ डिफल्ट GitHub", lambda: self.up_url.set(UPDATE_URL_DEFAULT), "ghost", small=True).pack(side="left", padx=3)
            Btn(r7, "🔗 Release खोल्नु", lambda: webbrowser.open("https://github.com/khemraj73-coder/shuvam-recondition-house/releases"), "ghost", small=True).pack(side="left", padx=3)
            tk.Label(c7.body, text=f"हालको: v{APP_VER} · {APP_CODE}", bg=T.PANEL, fg=T.FAINT, font=F(8)).pack(anchor="w", pady=(8, 0))
            if os.name == "nt":
                c8 = self.card(b, "😊 Windows Hello", "Fingerprint / Face / PIN")
                self.hello = Check(c8.body, "Hello लगइन सक्षम", bool(s["hello_login"]), T.PANEL); self.hello.pack(anchor="w")
                Btn(c8.body, "जाँच गर्नुहोस्", self.test_hello, "ghost", small=True).pack(anchor="w", pady=8)
            tk.Label(b, text=BRAND, bg=T.BG, fg=T.FAINT, font=F(8)).pack(pady=(4, 24))
        def rf_set(self):
            self.utbl.fill([dict(r, _id=r["username"]) for r in db().q("SELECT username,role,created_at FROM users ORDER BY username")])
        def save_shop(self):
            v = {k: w.get().strip() for k, w in self.sf.items()}
            if not v["shop_name"]: Toast.show(self.root, "दुकान नाम खाली हुन सक्दैन", "bad"); return
            with db().tx() as c:
                c.execute("UPDATE settings SET shop_name=?,address=?,mobile=?,pan=?,owner=?,email=?,website=?,bill_note=? WHERE id=1",
                          (v["shop_name"], v["address"], v["mobile"], v["pan"], v["owner"], v["email"], v["website"], v["bill_note"]))
                db().audit(c, "SHOP_SAVE", v["shop_name"])
            self.root.title(f"{v['shop_name']} · {APP_CODE} v{APP_VER}")
            Toast.show(self.root, "✅ सेभ", "ok")
        def clear_shop(self):
            if not confirm(self.root, t("confirm"), "मोबाइल, PAN, इमेल, वेबसाइट, टिप्पणी खाली गर्ने?"): return
            for k in ("mobile", "pan", "owner", "email", "website", "bill_note"):
                self.sf[k].set("")
            Toast.show(self.root, "खाली गरियो", "ok")
        def reset_shop(self):
            if not confirm(self.root, t("confirm"), "दुकान नाम र ठेगाना डिफल्टमा फर्काउने?"): return
            self.sf["shop_name"].set(APP_NAME)
            self.sf["address"].set("Hatti Chowk, Tulsipur, Dang")
            Toast.show(self.root, "डिफल्ट भयो", "ok")
        def add_user(self):
            try:
                user_add(self.nu["u"].get(), self.nu["p"].get(), self.nu["r"].get())
                self.nu["u"].set(""); self.nu["p"].set("")
                Toast.show(self.root, "✅ प्रयोगकर्ता थपियो", "ok"); self.rf_set()
            except Exception as e: messagebox.showerror("त्रुटि", str(e), parent=self.root)
        def del_user(self):
            sel = self.utbl.selected()
            if not sel: Toast.show(self.root, "पहिले प्रयोगकर्ता छान्नुहोस्", "warn"); return
            u = sel["username"]
            if u == db().actor: Toast.show(self.root, "आफैलाई हटाउन मिल्दैन", "bad"); return
            if not confirm(self.root, t("confirm"), f"{u} हटाउने?"): return
            try:
                user_delete(u, db().actor); Toast.show(self.root, "🗑 हटाइयो", "bad"); self.rf_set()
            except Exception as e: messagebox.showerror("त्रुटि", str(e), parent=self.root)
        def do_backup(self):
            p = filedialog.asksaveasfilename(defaultextension=".db", initialfile=f"shuvam_{datetime.now():%Y%m%d_%H%M}.db", parent=self.root)
            if not p: return
            if Path(p).resolve() == DB_FILE.resolve(): Toast.show(self.root, "सक्रिय DB माथि लेख्न मिल्दैन", "bad"); return
            try:
                db().backup(Path(p)); Toast.show(self.root, "✅ Backup", "ok")
            except Exception as e: messagebox.showerror("त्रुटि", str(e), parent=self.root)
        def do_restore(self):
            p = filedialog.askopenfilename(filetypes=[("SQLite", "*.db"), ("JSON", "*.json")], parent=self.root)
            if not p: return
            if not confirm(self.root, t("confirm"), "हालको डाटा प्रतिस्थापन हुन्छ।\nपहिले स्वतः backup बन्छ। अघि बढ्ने?"): return
            try:
                if p.lower().endswith(".json"):
                    n = restore(json.loads(Path(p).read_text(encoding="utf-8-sig")))
                else:
                    tmp = Store(Path(p))
                    with tmp.rd() as c:
                        data = {"format": 2, "tables": {tb: [dict(r) for r in c.execute(f"SELECT * FROM {tb}")] for tb in SNAP_TABLES}}
                    n = restore(data)
                Toast.show(self.root, f"✅ {n} rows restore", "ok"); self._rebuild("dash")
            except Exception as e: messagebox.showerror("त्रुटि", str(e), parent=self.root)
        def do_chain(self):
            ok, n = db().verify_chain()
            Toast.show(self.root, f"चेन सही · {n}" if ok else f"चेन #{n} मा समस्या", "ok" if ok else "bad")
        def cloud_save_ui(self):
            try:
                cloud_save(self.cl_url.get().strip(), self.cl_tok.get().strip(), self.cl_on.get())
                Toast.show(self.root, "✅ Cloud सेभ", "ok")
            except Exception as e: messagebox.showerror("त्रुटि", str(e), parent=self.root)
        def cloud_push_ui(self):
            Toast.show(self.root, "⬆ Sync हुँदैछ…", "info")
            self._bg(cloud_push, lambda ts: Toast.show(self.root, f"✅ Sync {ts}", "ok"),
                     lambda e: messagebox.showerror("Cloud", str(e), parent=self.root))
        def cloud_pull_ui(self):
            if not confirm(self.root, t("confirm"), "Cloud बाट डाटा ल्याएर बदल्ने?"): return
            self._bg(cloud_pull, lambda n: (Toast.show(self.root, f"✅ {n} rows", "ok"), self._rebuild("dash")),
                     lambda e: messagebox.showerror("Cloud", str(e), parent=self.root))
        def save_upurl(self):
            with db().tx() as c: c.execute("UPDATE settings SET update_url=? WHERE id=1", (self.up_url.get().strip(),))
            Toast.show(self.root, "✅ सेभ", "ok")
        def check_update(self):
            url = self.up_url.get().strip()
            if not url: Toast.show(self.root, "URL हाल्नुहोस्", "warn"); return
            Toast.show(self.root, "🔄 जाँच हुँदैछ…", "info")
            def ok(info):
                if not info: Toast.show(self.root, "✅ तपाईं latest मा", "ok"); return
                if confirm(self.root, "Update", f"v{info.get('version')} उपलब्ध। Install गर्ने?"):
                    try:
                        messagebox.showinfo("Update", update_install(info), parent=self.root)
                        if getattr(sys, "frozen", False):
                            self.root.after(800, self.root.destroy)
                    except Exception as e: messagebox.showerror("Update", str(e), parent=self.root)
        def test_cloud(self):
            try:
                TursoClient(self.cl_url.get().strip(), self.cl_tok.get().strip()).ping()
                Toast.show(self.root, "✅ Turso जडान सफल", "ok")
            except Exception as e:
                messagebox.showerror("Cloud", str(e), parent=self.root)
        def _silent_cloud_sync(self):
            def work():
                try:
                    if cloud_cfg().get("on"): cloud_push()
                except Exception: log.exception("silent cloud sync")
            threading.Thread(target=work, daemon=True).start()
            self._bg(lambda: update_check(url), ok, lambda e: messagebox.showerror("Update", str(e), parent=self.root))
        def test_hello(self):
            def ok(res):
                good, msg = res
                if good and self.hello.get():
                    with db().tx() as c:
                        c.execute("UPDATE settings SET hello_login=1,hello_user=? WHERE id=1", (self.user,))
                Toast.show(self.root, "✅ Hello सफल" if good else f"⚠ {msg}", "ok" if good else "bad")
            self._bg(lambda: hello_verify("SHUVAM test"), ok, lambda e: Toast.show(self.root, str(e), "bad"))

        # ---------- PASSWORD (सबैका लागि — deadlock fix) ----------
        def pg_pw(self):
            f, b = self.page("pw")
            c = self.card(b, "🔐 पासवर्ड परिवर्तन", f"कम्तीमा {PW_MIN} अक्षर · सबै प्रयोगकर्ताका लागि")
            self.pw = {}
            for k, lbl in (("old", "पुरानो पासवर्ड"), ("new", "नयाँ पासवर्ड"), ("conf", "पुष्टि")):
                self.pw[k] = Field(c.body, lbl, 28, T.PANEL, show="●")
                self.pw[k].pack(fill="x", pady=5)
            Btn(c.body, "🔑 बदल्नुहोस्", self.do_pw, "warn").pack(anchor="w", pady=(10, 0))
        def do_pw(self):
            try:
                change_pw(self.user, self.pw["old"].get(), self.pw["new"].get(), self.pw["conf"].get())
                for w in self.pw.values(): w.set("")
                self.must = False
                Toast.show(self.root, "✅ पासवर्ड बदलियो", "ok")
                self.go("dash")
            except Exception as e: messagebox.showerror("त्रुटि", str(e), parent=self.root)

    # ══════════════ १६. LOGIN / SETUP ══════════════
    def clear_root(root):
        for w in root.winfo_children(): w.destroy()
        root.unbind("<Motion>")
        try: root.unbind_all("<MouseWheel>")
        except Exception: pass
    def login_screen(root):
        clear_root(root)
        s = db().one("SELECT * FROM settings WHERE id=1")
        apply_theme(s["theme"] or "porcelain"); style_ttk()
        root.title(f"{APP_NAME} — {t('login')}"); root.resizable(False, False)
        root.configure(bg=T.BG)
        root.update_idletasks()
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"980x620+{max((sw - 980) // 2, 0)}+{max((sh - 620) // 3, 0)}")
        left = tk.Frame(root, bg=T.RAIL, width=420); left.pack(side="left", fill="y"); left.pack_propagate(False)
        inner = tk.Frame(left, bg=T.RAIL); inner.place(relx=.5, rely=.5, anchor="center")
        tk.Label(inner, text="SHUVAM", bg=T.RAIL, fg="#FFFFFF", font=F(38, "bold")).pack()
        tk.Label(inner, text="RECONDITION HOUSE", bg=T.RAIL, fg=T.RAIL_MUTED, font=F(10, "bold")).pack()
        tk.Frame(inner, bg=T.ACCENT, height=3, width=64).pack(pady=18)
        tk.Label(inner, text=f"{APP_CODE} · v{APP_VER}", bg=T.RAIL, fg=T.ACCENT, font=F(11, "bold")).pack()
        tk.Label(inner, text="बिक्री · स्टक · उधारो · नगद\nएकै ठाउँमा, भरपर्दो हिसाब", bg=T.RAIL,
                 fg=T.RAIL_MUTED, font=F(9), justify="center").pack(pady=18)
        tk.Label(left, text=BRAND, bg=T.RAIL, fg=mix(T.RAIL_MUTED, T.RAIL, .4), font=F(7),
                 wraplength=380, justify="center").pack(side="bottom", pady=18)
        right = tk.Frame(root, bg=T.BG); right.pack(side="left", fill="both", expand=True)
        box = tk.Frame(right, bg=T.BG); box.place(relx=.5, rely=.5, anchor="center")
        tk.Label(box, text="🔐 " + t("login"), bg=T.BG, fg=T.INK, font=F(24, "bold")).pack(anchor="w")
        tk.Label(box, text="आफ्नो खातामा प्रवेश गर्नुहोस्", bg=T.BG, fg=T.MUTED, font=F(10)).pack(anchor="w", pady=(2, 20))
        fu = Field(box, t("user"), 32, T.BG); fu.pack(fill="x", pady=6)
        fp = Field(box, t("pass"), 32, T.BG, show="●"); fp.pack(fill="x", pady=6)
        msg = tk.Label(box, text="", bg=T.BG, fg=T.BAD, font=F(9), wraplength=320, justify="left")
        msg.pack(anchor="w", pady=8)
        def enter(u, role, must):
            clear_root(root); root.resizable(True, True)
            App(root, u, role, must)
            def _silent():
                try:
                    if cloud_cfg().get("on"): cloud_push()
                except Exception: log.exception("silent cloud sync")
            threading.Thread(target=_silent, daemon=True).start()
        def submit(e=None):
            u, p = fu.get().strip(), fp.get()
            if not u or not p: msg.config(text="प्रयोगकर्ता नाम र पासवर्ड दुवै हाल्नुहोस्"); return
            fails, lock = login_state(u)
            if time.time() < lock:
                msg.config(text=f"⛔ धेरै गलत प्रयास — {int(lock - time.time()) + 1} सेकेन्ड पर्खनुहोस्"); return
            info = authenticate(u, p)
            if info:
                login_ok(u); db().actor = u
                with db().tx() as c: db().audit(c, "LOGIN", u)
                enter(info["user"], info["role"], info["must"]); return
            f2, l2 = login_fail(u)
            msg.config(text=f"⛔ {LOCK_SECONDS} सेकेन्ड lock" if l2 > time.time()
                       else f"⚠ गलत विवरण ({LOCK_TRIES - f2} प्रयास बाँकी)")
            fp.set("")
        Btn(box, "→ " + t("login"), submit, "primary", w=320).pack(pady=(6, 8))
        fp.e.bind("<Return>", submit)
        fu.e.bind("<Return>", lambda e: fp.e.focus_set())
        if s["hello_login"] and os.name == "nt":
            def hello():
                msg.config(text="Windows Hello जाँच हुँदैछ…", fg=T.INFO)
                def done(res):
                    good, detail = res
                    if not good: msg.config(text=f"⚠ {detail}", fg=T.BAD); return
                    uname = s["hello_user"] or s["owner"]
                    # FIX: db().one ले row फर्काउँछ — .fetchone() हटाइयो
                    r = db().one("SELECT username,role,must_change FROM users WHERE username=?", (uname,))
                    if not r:
                        r = db().one("SELECT username,role,must_change FROM users WHERE role='owner' ORDER BY created_at LIMIT 1")
                    if r: enter(r["username"], r["role"], int(r["must_change"] or 0))
                    else: msg.config(text="Hello प्रयोगकर्ता भेटिएन", fg=T.BAD)
                def work():
                    try: res = hello_verify("Login to SHUVAM")
                    except Exception as e: res = (False, str(e))
                    root.after(0, lambda: done(res))
                threading.Thread(target=work, daemon=True).start()
            Btn(box, "😊 Windows Hello", hello, "ghost", w=320).pack()
        lb = tk.Label(box, text="EN" if _lang == "ne" else "नेपाली", bg=T.BG, fg=T.ACCENT, font=F(9, "bold"), cursor="hand2")
        lb.pack(anchor="e", pady=(14, 0))
        lb.bind("<Button-1>", lambda e: (set_lang("en" if _lang == "ne" else "ne"), login_screen(root)))
        def _focus():
            try:
                root.deiconify(); root.lift(); root.focus_force(); fu.e.focus_set()
            except Exception: pass
        root.after(120, _focus)
        root.after(450, _focus)
    def setup_screen(root):
        clear_root(root); apply_theme("porcelain"); style_ttk()
        root.title(f"{APP_NAME} — पहिलो सेटअप"); root.resizable(False, False); root.configure(bg=T.BG)
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"720x640+{max((sw - 720) // 2, 0)}+{max((sh - 640) // 2 - 20, 0)}")
        c = Card(root, pad=28, accent=T.ACCENT); c.place(relx=.5, rely=.5, anchor="center", width=520)
        tk.Label(c.body, text="👋 स्वागत छ!", bg=T.PANEL, fg=T.INK, font=F(24, "bold")).pack(anchor="w")
        tk.Label(c.body, text=f"{APP_CODE} v{APP_VER} — पहिलो Owner खाता बनाउनुहोस्", bg=T.PANEL,
                 fg=T.MUTED, font=F(10)).pack(anchor="w", pady=(2, 18))
        f = {}
        for k, lbl, dv, sh in (("shop", "दुकान नाम", APP_NAME, None), ("addr", "ठेगाना", "Hatti Chowk, Tulsipur, Dang", None),
                               ("user", "Owner Username", "owner", None), ("p1", f"पासवर्ड ({PW_MIN}+ अक्षर)", "", "●"),
                               ("p2", "पासवर्ड पुष्टि", "", "●")):
            f[k] = Field(c.body, lbl, 42, T.PANEL, dv, show=sh); f[k].pack(fill="x", pady=5)
        msg = tk.Label(c.body, text="", bg=T.PANEL, fg=T.BAD, font=F(9)); msg.pack(anchor="w", pady=6)
        def go():
            try:
                if f["p1"].get() != f["p2"].get(): raise ValueError("पासवर्ड मिलेन")
                user_add(f["user"].get(), f["p1"].get(), "owner")
                with db().tx() as cc:
                    cc.execute("UPDATE settings SET shop_name=?,address=?,owner=? WHERE id=1",
                               (f["shop"].get().strip(), f["addr"].get().strip(), f["user"].get().strip()))
                    db().audit(cc, "SETUP", "owner created")
                login_screen(root)
            except Exception as e: msg.config(text=str(e))
        Btn(c.body, "✅ सेटअप पूरा", go, "ok", w=440).pack(pady=(12, 0))
        tk.Label(c.body, text=BRAND, bg=T.PANEL, fg=T.FAINT, font=F(7)).pack(pady=(14, 0))
        def _focus_setup():
            try:
                root.lift(); root.focus_force(); f["user"].e.focus_force()
            except Exception: pass
        root.after(150, _focus_setup)
    def launch():
        root = tk.Tk(); pick_font(root)
        s = db().one("SELECT theme,lang FROM settings WHERE id=1")
        apply_theme(s["theme"] or "porcelain"); set_lang(s["lang"] or "ne")
        try: db().auto_backup()
        except Exception: log.exception("auto backup")
        try:
            p = make_icon()
            if p: root._ic = tk.PhotoImage(file=str(p)); root.iconphoto(True, root._ic)
        except Exception: pass
        if user_count(): login_screen(root)
        else: setup_screen(root)
        def on_err(exc, val, tb):
            log.error("UI error", exc_info=(exc, val, tb))
            try: messagebox.showerror("अप्रत्याशित त्रुटि", f"{val}\n\nविवरण error.log मा सुरक्षित छ।")
            except Exception: pass
        root.report_callback_exception = on_err
        root.mainloop()

# ══════════════ १७. SELF-TEST ══════════════
def run_tests():
    import traceback
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    global DB
    ok, bad = [], []
    def check(name, fn):
        try:
            fn(); ok.append(name); print(f"  [PASS] {name}")
        except Exception as e:
            bad.append((name, e)); print(f"  [FAIL] {name} → {e}")
            if os.environ.get("SHUVAM_VERBOSE"): traceback.print_exc()
    print("=" * 68); print(f"SHUVAM {APP_CODE} v{APP_VER} — SELF TEST"); print("=" * 68)
    tmp = Path(tempfile.mkdtemp(prefix="shuvam_test_"))
    DB = Store(tmp / "t.db")
    def t_utils():
        assert num("1,25,000") == 125000
        for x in ("-5", "1e5", "abc", "NaN"):
            try: num(x); raise AssertionError(f"{x} पास")
            except ValueError: pass
        assert phone_ok("98-1234-5678") and phone_ok("+977 9812345678") and not phone_ok("123")
        assert due_of(1000, 1200) == 0
        try: pay_check(1000, 1500); raise AssertionError("overpay पास")
        except ValueError: pass
        assert total_cost(100, 10, 5, 20, True) == 135 and total_cost(100, 10, 5, 20, False) == 115
    check("१. validation / phone / overpay / cost", t_utils)
    def t_billwords():
        for w in ("profit", "नाफा", "लागत", "cost"):
            try: bill_safe(f"यो {w} हो"); raise AssertionError(f"{w} पास")
            except ValueError: pass
        bill_safe("Honda Shine · BA 1 PA 1234")
    check("२. बिलमा भित्री शब्द रोक", t_billwords)
    def t_auth():
        user_add("owner", "password123", "owner")
        assert authenticate("owner", "password123")["role"] == "owner"
        assert authenticate("owner", "wrong") is None
        for _ in range(LOCK_TRIES): login_fail("owner")
        assert login_state("owner")[1] > time.time()
        login_ok("owner"); assert login_state("owner")[1] == 0
        user_add("staff1", "password123", "staff")
        change_pw("staff1", "password123", "newpass123", "newpass123")
        assert authenticate("staff1", "newpass123")["must"] == 0
    check("३. auth + lockout + password", t_auth)
    state = {}
    def t_bike():
        bid = bike_buy({"brand": "Honda", "model": "Shine 125", "color": "Black", "year": "2023",
                        "bike_no": "TEST-001", "buy_price": 100000, "repair_cost": 5000, "naam_sari": 2000,
                        "kar_cost": 3000, "kar_paid": True, "buy_date": today(), "method": "Cash"})
        b = db().one("SELECT * FROM bikes WHERE id=?", (bid,))
        assert b["total_cost"] == 110000
        no = bike_sell(bid, {"name": "Ram KC", "phone": "9812345678"}, 150000, 100000, "Cash")
        b = db().one("SELECT * FROM bikes WHERE id=?", (bid,))
        assert b["status"] == "Sold" and b["profit"] == 40000
        assert db().one("SELECT * FROM bills WHERE bill_no=?", (no,))["due"] == 50000
        assert bill_collect(no, 20000, "Cash") == 30000
        try: bill_collect(no, 99999, "Cash"); raise AssertionError("over-collect पास")
        except ValueError: pass
        state.update(bid=bid, no=no)
    check("४. बाइक खरिद→बिक्री→असुल", t_bike)
    def t_cash():
        s = cash_summary(today())
        assert s["closing"] == s["opening"] + s["in"] - s["out"]
        cash_close(today(), "test", "owner")
        try: cash_manual(today(), "In", 100, "blocked"); raise AssertionError("बन्द दिनमा entry पास")
        except ValueError: pass
        assert cash_reopen() == today()
        cash_manual(today(), "In", 500, "manual test")
    check("५. दिनबन्द / reopen", t_cash)
    def t_void():
        # edit test on a fresh bill (pays count = 1)
        bid2 = bike_buy({"brand": "Honda", "model": "Shine 125", "color": "Black", "year": "2023",
                         "bike_no": "TEST-VOID", "buy_price": 100000, "buy_date": today(), "method": "Cash"})
        no2 = bike_sell(bid2, {"name": "Ram KC", "phone": "9812345678"}, 150000, 100000, "Cash")
        cid2 = db().val("SELECT customer_id FROM bills WHERE bill_no=?", (no2,))
        bill_edit(no2, cid2, 160000, 160000, "Cash")
        assert db().one("SELECT * FROM bills WHERE bill_no=?", (no2,))["due"] == 0
        assert db().one("SELECT * FROM bikes WHERE id=?", (bid2,))["sell_price"] == 160000
        bill_void(no2, "cleanup")
        # void test on the collected bill
        bid, no = state["bid"], state["no"]
        before = cash_summary(today())["closing"]
        bill_void(no, "test void")
        assert db().one("SELECT * FROM bills WHERE bill_no=?", (no,))["voided"] == 1
        assert db().one("SELECT * FROM bikes WHERE id=?", (bid,))["status"] == "Stock"
        assert cash_summary(today())["closing"] < before
    check("६. बिल edit + void (cash/stock reversal)", t_void)
    def t_acc():
        acc_add("Test Helmet", "Helmet", 10, 800, 1200)
        aid = db().val("SELECT id FROM accessories WHERE name='Test Helmet'")
        no = acc_sell(aid, 2, 1500, {"name": "Sita", "phone": "9800000000"}, 3000, "Cash")
        assert db().val("SELECT stock FROM accessories WHERE id=?", (aid,)) == 8
        bl = db().one("SELECT * FROM bills WHERE bill_no=?", (no,))
        assert bl["total"] == 3000 and bl["bill_type"] == "ACC"
        acc_restock(aid, 5, 900, 0, "eSewa")
        a = db().one("SELECT * FROM accessories WHERE id=?", (aid,))
        assert a["stock"] == 13 and a["sell_price"] == 1200
        assert a["buy_price"] == round((8 * 800 + 5 * 900) / 13, 2)
        bill_void(no, "acc void")
        assert db().val("SELECT stock FROM accessories WHERE id=?", (aid,)) == 15
    check("७. सामान override + restock avg + void restock", t_acc)
    def t_svc():
        n1 = plate_add({"name": "Hari", "phone": "9811111111"}, "TEST-002", "BA 1 PA 1",
                       "New Registration", 1500, 3000, 2000, "Cash", "Pending")
        n2 = repair_add({"name": "Gita", "phone": "9822222222"}, "TEST-003", "Pulsar",
                        "Brake change", 1200, 800, 2000, "Cash", "Done")
        assert db().val("SELECT COUNT(*) FROM bills WHERE bill_no IN (?,?)", (n1, n2)) == 2
        assert db().one("SELECT * FROM plates WHERE bill_no=?", (n1,))["due"] == 1000
        bill_collect(n1, 1000, "Cash")
        assert db().one("SELECT * FROM plates WHERE bill_no=?", (n1,))["due"] == 0
        job_status("PLATE", db().val("SELECT id FROM plates WHERE bill_no=?", (n1,)), "Done")
    check("८. प्लेट/मर्मत → बिल + due + स्थिति", t_svc)
    def t_exp():
        eid = exp_add("Shop Rent", "Rent", 15000, today(), "Cash")
        before = cash_summary(today())["closing"]
        exp_edit(eid, "Shop Rent", "Rent", 18000, today(), "Cash")
        assert cash_summary(today())["closing"] == before - 3000
        before_del = cash_summary(today())["closing"]
        exp_delete(eid)
        assert cash_summary(today())["closing"] == before_del + 18000
        assert db().val("SELECT is_deleted FROM expenses WHERE id=?", (eid,)) == 1
        sid = staff_add("Mechanic Ram", "9812345670", "Mechanic", 25000)
        salary_pay(sid, date.today().strftime("%Y-%m"), 25000, today(), "Cash")
        try: salary_pay(sid, date.today().strftime("%Y-%m"), 25000, today(), "Cash"); raise AssertionError("दोहोरो तलब पास")
        except ValueError: pass
    check("९. खर्च edit/delete + तलब दोहोरो रोक", t_exp)
    def t_parts():
        part_add("Brake Shoe", "Brake", 10, 300, 3)
        pid = db().val("SELECT id FROM parts WHERE name='Brake Shoe'")
        part_buy(pid, 10, 400, "Cash")
        p = db().one("SELECT * FROM parts WHERE id=?", (pid,))
        assert p["stock"] == 20 and p["unit_cost"] == 350
        bid = bike_buy({"brand": "TVS", "model": "Apache RTR 160 4V", "color": "Red", "year": "2023",
                        "bike_no": "TEST-004", "buy_price": 120000, "buy_date": today(), "method": "Cash"})
        part_use(pid, "TEST-004", 2)
        labour_add("TEST-004", "Engine tune", "Ram", 1500, True)
        with db().rd() as c: assert bike_extra_cost(c, "TEST-004") == 2200
    check("१०. पार्ट्स COGS + लेबर", t_parts)
    def t_family():
        with db().tx() as c:
            a = _customer_resolve(c, "Ram KC", "9812345678")
            b = _customer_resolve(c, "Ram KC", "98-1234-5678")
            d = _customer_resolve(c, "Shyam KC", "9812345678")
        assert a == b and a != d
    check("११. family phone sharing", t_family)
    def t_report():
        r = monthly(date.today().strftime("%Y-%m"))
        assert "NET PROFIT" in r
        assert r["Total Revenue"] == r["Bike Revenue"] + r["Accessory Revenue"] + r["Plate Revenue"] + r["Repair Revenue"]
        assert len(chart_days(7)) == 7
        assert stats()["revenue"] >= 0
    check("१२. रिपोर्ट / stats", t_report)
    def t_snap():
        global DB
        good, n = db().verify_chain()
        assert good and n > 0
        snap = snapshot()
        assert snap["format"] == 2 and snap["tables"]["bills"]
        d2 = Store(tmp / "t2.db"); old = DB
        try:
            DB = d2; cnt = restore(snap); assert cnt > 0
        finally: DB = old
    check("१३. audit chain + snapshot restore", t_snap)
    def t_themes():
        assert len(THEMES) == 6
        for k in THEME_ORDER: apply_theme(k); assert T.key == k
        assert ver_tuple("10.1.0") > ver_tuple("10.0.9") > ver_tuple("9.9.9")
        assert len(METHODS) == 9
    check("१४. ६ थिम / version / ९ माध्यम", t_themes)
    def t_dpapi():
        if not dpapi_ok(): print("      (non-Windows — DPAPI skip)"); return
        tok = dp_encrypt(b"shuvam-secret")
        assert dp_decrypt(tok) == b"shuvam-secret"
    check("१५. DPAPI roundtrip", t_dpapi)
    def t_photo():
        p = tmp / "x.png"; p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)
        name = save_photo(str(p), "TEST-001")
        assert (PHOTO_DIR / name).is_file()
        assert photo_uri(name).startswith("data:image/png;base64,")
    check("१६. photo save + data URI", t_photo)
    def t_update_guard():
        try:
            update_install({})
        except ValueError as e:
            assert "sha256" in str(e) or "URL" in str(e)
        else:
            raise AssertionError("खाली update info स्वीकृत भयो")
    check("१७. update checksum guard", t_update_guard)
    print("-" * 68); print(f"नतिजा: {len(ok)} सफल · {len(bad)} असफल"); print("=" * 68)
    for n, e in bad: print(f"  ✗ {n}: {e}")
    return not bad
def run_cloud_test():
    print("=" * 68); print("CLOUD TEST (network)"); print("=" * 68)
    try:
        cfg = cloud_cfg()
        if not cfg["url"] or not cfg["token"]:
            print("  [SKIP] cloud URL/token सेट गरिएको छैन"); return True
        TursoClient(cfg["url"], cfg["token"]).ping()
        print("  [PASS] Turso ping")
        if dpapi_ok():
            plain = json.dumps({"t": 1}).encode()
            enc = dp_encrypt(plain)
            assert dp_decrypt(enc) == plain
            assert hashlib.sha256(plain).hexdigest() == hashlib.sha256(dp_decrypt(enc)).hexdigest()
            print("  [PASS] encrypt + checksum roundtrip")
        else:
            print("  [SKIP] DPAPI (non-Windows)")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}"); return False

# ══════════════ १८. ENTRY POINT ══════════════
def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if "--version" in sys.argv:
        print(f"{APP_NAME} · {APP_CODE} v{APP_VER}"); return
    if "--test" in sys.argv:
        sys.exit(0 if run_tests() else 1)
    if "--test-cloud" in sys.argv:
        ok = run_tests(); ok = run_cloud_test() and ok
        sys.exit(0 if ok else 1)
    if "--icon" in sys.argv:
        print("ICON:", make_icon()); return
    if "--backup" in sys.argv:
        print("BACKUP:", db().backup(BACKUP_DIR / f"cli_{datetime.now():%Y%m%d_%H%M%S}.db")); return
    if "--sync" in sys.argv:
        try: print("SYNC:", cloud_push())
        except Exception as e: print("SYNC FAILED:", e); sys.exit(1)
        return
    if not HAS_TK:
        print("Tkinter उपलब्ध छैन। headless परीक्षण: python shuvam_ultimate.py --test"); sys.exit(1)
    try:
        launch()
    except Exception as e:
        log.exception("startup")
        try:
            r = tk.Tk(); r.withdraw()
            messagebox.showerror("Startup त्रुटि", f"{e}\n\nerror.log हेर्नुहोस्।")
        except Exception:
            print("STARTUP FAILED:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
