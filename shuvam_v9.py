#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shuvam Recondition House - Management System
Version 9.0.0  (Cloud base: Turso sync + auto-update + branding + 9 Nepal payment methods)
"""
import os
import sys
import re
import csv
import json
import time
import html
import math
import hmac
import base64
import shutil
import hashlib
import sqlite3
import logging
import pathlib
import tempfile
import webbrowser
import tkinter as tk
from contextlib import contextmanager
from datetime import datetime, timedelta
from tkinter import messagebox, ttk, filedialog

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ======================= PATHS & CONFIG =======================
APP_VERSION = "9.0.1"
APP_NAME = "SHUVAM RECONDITION HOUSE"
FONT = "Segoe UI"

BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) \
    else os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("SHUVAM_HOME", BASE_DIR)
DB_FILE = os.path.join(DATA_DIR, "shuvam_glass_v6.db")
DB = None  # global DBManager instance, set in ShuvamApp.__init__
CONFIG_FILE = os.path.join(DATA_DIR, "shuvam_config.json")
RECEIPTS_DIR = os.path.join(DATA_DIR, "receipts")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
PHOTOS_DIR = os.path.join(DATA_DIR, "bike_photos")
LOG_FILE = os.path.join(DATA_DIR, "error.log")
for _d in (DATA_DIR, RECEIPTS_DIR, BACKUP_DIR, PHOTOS_DIR):
    os.makedirs(_d, exist_ok=True)

logging.basicConfig(filename=LOG_FILE, level=logging.ERROR,
                    format="%(asctime)s %(levelname)s %(message)s", encoding="utf-8")

PAYMENT_METHODS = ["Cash", "eSewa", "Khalti", "ConnectIPS", "Bank Transfer",
                   "Fonepay", "IME Pay", "Cheque", "Other"]
EXPENSE_CATEGORIES = ["Rent", "Mechanic", "Fuel", "Electricity", "Marketing", "Transport", "Misc", "Other"]
RESERVED_EXPENSE_CATS = ("Salary", "Parts", "Labour")
PART_CATEGORIES = ["General", "Engine", "Brake", "Electrical", "Body", "Tyre/Tube", "Other"]
PHOTO_EXTS = (".jpg", ".jpeg", ".png", ".webp")
MAX_PHOTO_MB = 8
AUDIT_LIMIT = 500
DEFAULT_CONFIG = {"shop_name": APP_NAME, "shop_address": "Kathmandu, Nepal", "shop_phone": "+977-9800000000", "shop_pan": ""}


def save_config(cfg):
    tmp = CONFIG_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)
    os.replace(tmp, CONFIG_FILE)


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                cfg.update({k: str(v) for k, v in data.items() if k in DEFAULT_CONFIG})
        else:
            save_config(cfg)
    except Exception:
        logging.exception("Config load failed")
    return cfg


CONFIG = load_config()
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
COLORS = {"bg_main": "#1e1e24", "sidebar": "#15151a", "card": "#2b2b36", "card_hover": "#353542",
          "text": "#ffffff", "text_muted": "#a0a0b0", "accent_blue": "#2196f3", "accent_green": "#4caf50",
          "accent_pink": "#e91e63", "accent_orange": "#ff9800", "login_bg": "#0f2b46"}


# ============================== HELPERS ==============================

def parse_amount(val, allow_zero=False, label="Amount"):
    if val is None:
        raise ValueError(f"{label} is empty")
    s = str(val).replace(",", "").strip()
    if not s:
        raise ValueError(f"{label} is empty")
    if not re.fullmatch(r"\d+(\.\d+)?|\.\d+", s):
        raise ValueError(f"Invalid {label.lower()}: '{val}'")
    v = float(s)
    if not math.isfinite(v) or v > 1e12:
        raise ValueError(f"{label} is too large")
    if v == 0 and not allow_zero:
        raise ValueError(f"{label} must be greater than 0")
    return round(v, 2)

def parse_int(val, label="Value"):
    s = str(val).strip()
    if not re.fullmatch(r"\d{1,9}", s):
        raise ValueError(f"{label} must be a whole number (0 or more)")
    return int(s)

def validate_date(date_str):
    s = str(date_str).strip()
    try:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
            raise ValueError
        datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD.") from None
    return s

def validate_date_nf(date_str):
    s = validate_date(date_str)
    if s > today_str():
        raise ValueError(f"Date {s} cannot be in the future.")
    return s

def validate_month(month_str):
    s = str(month_str).strip()
    try:
        if not re.fullmatch(r"\d{4}-\d{2}", s):
            raise ValueError
        datetime.strptime(s, "%Y-%m")
    except ValueError:
        raise ValueError(f"Invalid month format: {month_str}. Use YYYY-MM.") from None
    return s

def validate_month_nf(month_str):
    s = validate_month(month_str)
    if s > datetime.now().strftime("%Y-%m"):
        raise ValueError(f"Month {s} cannot be in the future.")
    return s

def today_str():
    return datetime.now().strftime("%Y-%m-%d")

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def escape_html(val):
    return "" if val is None else html.escape(str(val))

def sanitize_csv(val):
    s = "" if val is None else str(val)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        s = "'" + s
    return s

def sanitize_filename(s):
    return re.sub(r"[^a-zA-Z0-9_-]", "_", str(s))[:60]

def txt(v):
    return "" if v is None else str(v)

def money(v):
    v = float(v or 0)
    s = f"{v:,.2f}"
    return f"Rs. {s[:-3] if s.endswith('.00') else s}"

def validate_method(m):
    if m not in PAYMENT_METHODS:
        raise ValueError(f"Invalid payment method: {m}")

def save_bike_photo(src_path, bike_no):
    if not src_path or not os.path.isfile(src_path):
        raise ValueError("Selected photo file does not exist.")
    ext = os.path.splitext(src_path)[1].lower()
    if ext not in PHOTO_EXTS:
        raise ValueError("Unsupported image format. Use JPG, JPEG, PNG or WEBP.")
    if os.path.getsize(src_path) > MAX_PHOTO_MB * 1024 * 1024:
        raise ValueError(f"Photo is too large (max {MAX_PHOTO_MB} MB).")
    name = f"{sanitize_filename(bike_no)}_{int(time.time() * 1000)}{ext}"
    shutil.copy2(src_path, os.path.join(PHOTOS_DIR, name))
    return name

def remove_photo(filename):
    if not filename:
        return
    try:
        p = os.path.join(PHOTOS_DIR, os.path.basename(filename))
        if os.path.isfile(p):
            os.remove(p)
    except OSError:
        logging.exception("Photo cleanup failed")

def photo_data_uri(filename):
    if not filename:
        return None
    p = os.path.join(PHOTOS_DIR, os.path.basename(filename))
    if not os.path.isfile(p):
        return None
    try:
        if os.path.getsize(p) > MAX_PHOTO_MB * 1024 * 1024:
            return None
        ext = os.path.splitext(p)[1].lower().lstrip(".")
        mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(ext, "jpeg")
        with open(p, "rb") as f:
            return f"data:image/{mime};base64,{base64.b64encode(f.read()).decode('ascii')}"
    except OSError:
        return None

def cleanup_old_receipts(days=7):
    cutoff = time.time() - days * 86400
    try:
        for f in os.listdir(RECEIPTS_DIR):
            p = os.path.join(RECEIPTS_DIR, f)
            if f.endswith(".html") and os.path.isfile(p) and os.path.getmtime(p) < cutoff:
                try:
                    os.remove(p)
                except OSError:
                    pass
    except OSError:
        pass

HTML_CSS = """
body{font-family:Arial,Helvetica,sans-serif;padding:24px;color:#111;max-width:860px;margin:auto}
.header{display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid #0f2b46;padding-bottom:12px}
.header h1{margin:0;color:#0f2b46}
.details{display:flex;justify-content:space-between;margin-top:18px;background:#f8fafc;padding:12px;border-radius:6px;gap:20px}
table{width:100%;border-collapse:collapse;margin-top:16px}
th,td{border:1px solid #cbd5e1;padding:8px;text-align:left}
th{background:#e2e8f0}
.total-box{margin-top:20px;text-align:right;font-size:17px}
.footer{text-align:center;margin-top:45px;font-size:12px;color:#475569}
.specs{font-size:13px;color:#444;margin-top:6px}
.photo{max-height:200px;border:1px solid #ccc;border-radius:6px}
.voidbanner{background:#fee2e2;color:#991b1b;border:2px solid #dc2626;padding:10px;border-radius:6px;margin-top:14px;font-weight:bold}
.printbtn{padding:8px 16px;font-size:14px;cursor:pointer;background:#0f2b46;color:#fff;border:none;border-radius:4px}
@media print{.no-print{display:none}body{padding:0}}
"""


def open_html(prefix, ident, body_html, title):
    cleanup_old_receipts()
    btn = ("<div class='no-print' style='text-align:right;margin-bottom:10px'>"
           "<button class='printbtn' onclick='window.print()'>Print / Save as PDF</button></div>")
    doc = ("<!DOCTYPE html><html><head><meta charset='utf-8'><title>%s</title><style>%s</style></head>"
           "<body>%s%s</body></html>") % (escape_html(title), HTML_CSS, btn, body_html)
    path = os.path.join(RECEIPTS_DIR, f"{prefix}_{sanitize_filename(ident)}_{int(time.time() * 1000)}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)
    webbrowser.open(pathlib.Path(path).as_uri())
    return path


# =========================== DATABASE ===========================
SCHEMA = [
    "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, must_change_password INTEGER DEFAULT 0)",
    "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)",
    """CREATE TABLE IF NOT EXISTS bikes (
        id INTEGER PRIMARY KEY, bike_no TEXT UNIQUE, model TEXT,
        engine_no TEXT DEFAULT '', chassis_no TEXT DEFAULT '',
        bluebook_expiry TEXT DEFAULT '', photo_path TEXT DEFAULT '',
        buy_price REAL, sell_price REAL, status TEXT,
        method TEXT DEFAULT 'Unknown', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
    "CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY, name TEXT, phone TEXT, address TEXT, citizenship_no TEXT DEFAULT '', notes TEXT)",
    """CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY, bill_no TEXT UNIQUE, customer_id INTEGER, buyer_name TEXT,
        bike_no TEXT, total REAL, advance REAL, due REAL, status TEXT, payment_method TEXT,
        voided INTEGER DEFAULT 0, void_reason TEXT DEFAULT '', voided_at TEXT DEFAULT '', voided_by TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
    "CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, bill_id INTEGER, bill_no TEXT, amount REAL, method TEXT, note TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
    "CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY, title TEXT, category TEXT, amount REAL, expense_date TEXT, note TEXT, method TEXT DEFAULT 'Unknown')",
    "CREATE TABLE IF NOT EXISTS staff (id INTEGER PRIMARY KEY, name TEXT, phone TEXT, role TEXT, monthly_salary REAL, active INTEGER DEFAULT 1)",
    "CREATE TABLE IF NOT EXISTS salary_payments (id INTEGER PRIMARY KEY, staff_id INTEGER, month TEXT, amount REAL, payment_date TEXT, note TEXT, method TEXT DEFAULT 'Unknown')",
    "CREATE TABLE IF NOT EXISTS parts (id INTEGER PRIMARY KEY, name TEXT, category TEXT, stock_qty INTEGER, unit_cost REAL, low_stock_threshold INTEGER)",
    "CREATE TABLE IF NOT EXISTS parts_usage (id INTEGER PRIMARY KEY, part_id INTEGER, bike_no TEXT, qty INTEGER, unit_cost_at_time REAL, usage_date TEXT)",
    "CREATE TABLE IF NOT EXISTS bike_labour (id INTEGER PRIMARY KEY, bike_no TEXT, labour_date TEXT, description TEXT, mechanic TEXT, amount REAL, paid_in_cash INTEGER)",
    "CREATE TABLE IF NOT EXISTS cash_book (id INTEGER PRIMARY KEY, date TEXT, type TEXT, category TEXT, amount REAL, method TEXT, note TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
    "CREATE TABLE IF NOT EXISTS cash_closures (date TEXT PRIMARY KEY, opening REAL, cash_in REAL, cash_out REAL, closing REAL, note TEXT, closed_by TEXT, closed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
    "CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY, ts TEXT, username TEXT, action TEXT, entity TEXT, entity_id TEXT, details TEXT)",
]
INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_bills_bike_no ON bills(bike_no)",
    "CREATE INDEX IF NOT EXISTS idx_bills_customer_id ON bills(customer_id)",
    "CREATE INDEX IF NOT EXISTS idx_bills_created_at ON bills(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_parts_usage_bike_no ON parts_usage(bike_no)",
    "CREATE INDEX IF NOT EXISTS idx_bike_labour_bike_no ON bike_labour(bike_no)",
    "CREATE INDEX IF NOT EXISTS idx_cash_book_date ON cash_book(date)",
    "CREATE INDEX IF NOT EXISTS idx_payments_bill_id ON payments(bill_id)",
    "CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)",
    "CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name)",
    "CREATE INDEX IF NOT EXISTS idx_salary_staff_month ON salary_payments(staff_id, month)",
    "CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(ts)",
]


class DBManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.current_user = "system"
        self.init_db()
        self.migrate_db()

    def set_user(self, username):
        self.current_user = username or "system"

    @contextmanager
    def get_conn(self, write=False):
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA busy_timeout=30000;")
            conn.execute("PRAGMA foreign_keys=ON;")
            if write:
                conn.execute("BEGIN IMMEDIATE")
            yield conn
            if conn.in_transaction:
                conn.commit()
        except BaseException:
            if conn.in_transaction:
                conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self):
        boot = sqlite3.connect(self.db_path, timeout=30.0)
        try:
            boot.execute("PRAGMA journal_mode=WAL;")
        finally:
            boot.close()
        with self.get_conn(write=True) as conn:
            for ddl in SCHEMA:
                conn.execute(ddl)
            if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
                conn.execute("INSERT INTO users (username, password_hash, must_change_password) VALUES (?,?,1)",
                             ("admin", self.hash_password("admin123")))

    def migrate_db(self):
        with self.get_conn(write=True) as conn:
            def cols(t):
                return [r[1] for r in conn.execute(f"PRAGMA table_info({t})").fetchall()]
            if "must_change_password" not in cols("users"):
                conn.execute("ALTER TABLE users ADD COLUMN must_change_password INTEGER DEFAULT 0")
            if "customer_id" not in cols("bills"):
                conn.execute("ALTER TABLE bills ADD COLUMN customer_id INTEGER")
            for t in ("salary_payments", "bikes", "expenses"):
                if "method" not in cols(t):
                    conn.execute(f"ALTER TABLE {t} ADD COLUMN method TEXT DEFAULT 'Unknown'")
            for c in ("engine_no", "chassis_no", "bluebook_expiry", "photo_path"):
                if c not in cols("bikes"):
                    conn.execute(f"ALTER TABLE bikes ADD COLUMN {c} TEXT DEFAULT ''")
            if "citizenship_no" not in cols("customers"):
                conn.execute("ALTER TABLE customers ADD COLUMN citizenship_no TEXT DEFAULT ''")
            bc = cols("bills")
            if "voided" not in bc:
                conn.execute("ALTER TABLE bills ADD COLUMN voided INTEGER DEFAULT 0")
            for c in ("void_reason", "voided_at", "voided_by"):
                if c not in bc:
                    conn.execute(f"ALTER TABLE bills ADD COLUMN {c} TEXT DEFAULT ''")
        self._rebuild_customers_if_unique()
        with self.get_conn(write=True) as conn:
            for ddl in INDEXES:
                conn.execute(ddl)
            conn.execute("UPDATE bills SET voided=0 WHERE voided IS NULL")
            for row in conn.execute("SELECT id, buyer_name FROM bills WHERE customer_id IS NULL "
                                    "AND buyer_name IS NOT NULL AND TRIM(buyer_name) != ''").fetchall():
                name = row["buyer_name"].strip()
                cust = conn.execute("SELECT id FROM customers WHERE name=? COLLATE NOCASE ORDER BY id LIMIT 1",
                                    (name,)).fetchone()
                cid = cust["id"] if cust else conn.execute(
                    "INSERT INTO customers (name, phone) VALUES (?, NULL)", (name,)).lastrowid
                conn.execute("UPDATE bills SET customer_id=? WHERE id=?", (cid, row["id"]))
            conn.execute("UPDATE customers SET phone=NULL WHERE phone LIKE 'OLD-%'")
            if not conn.execute("SELECT 1 FROM settings WHERE key='cash_migrated'").fetchone():
                if conn.execute("SELECT COUNT(*) FROM cash_book").fetchone()[0] == 0:
                    def put(date, typ, cat, amt):
                        date = (date or "")[:10]
                        if amt and amt > 0 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
                            conn.execute("INSERT INTO cash_book (date,type,category,amount,method,note) "
                                         "VALUES (?,?,?,?, 'Cash','Migration')", (date, typ, cat, amt))
                    for p in conn.execute("SELECT amount, created_at FROM payments WHERE method='Cash'").fetchall():
                        put(p["created_at"], "In", "Bill Payment", p["amount"])
                    for e in conn.execute("SELECT amount, expense_date FROM expenses WHERE method IN ('Cash','Unknown')").fetchall():
                        put(e["expense_date"], "Out", "Expense", e["amount"])
                    for s in conn.execute("SELECT amount, payment_date FROM salary_payments WHERE method IN ('Cash','Unknown')").fetchall():
                        put(s["payment_date"], "Out", "Salary", s["amount"])
                    for b in conn.execute("SELECT buy_price, created_at FROM bikes WHERE method IN ('Cash','Unknown')").fetchall():
                        put(b["created_at"], "Out", "Bike Purchase", b["buy_price"])
                conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('cash_migrated','1')")
            if not conn.execute("SELECT 1 FROM settings WHERE key='default_pw_checked'").fetchone():
                for u in conn.execute("SELECT id, password_hash FROM users").fetchall():
                    if self.verify_password(u["password_hash"], "admin123"):
                        conn.execute("UPDATE users SET must_change_password=1 WHERE id=?", (u["id"],))
                conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('default_pw_checked','1')")

    def _rebuild_customers_if_unique(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        try:
            row = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='customers'").fetchone()
            if not row or not row[0] or "UNIQUE" not in row[0].upper():
                return
            conn.execute("PRAGMA foreign_keys=OFF")
            conn.execute("PRAGMA legacy_alter_table=ON")
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("ALTER TABLE customers RENAME TO _customers_old")
            conn.execute("CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, phone TEXT, "
                         "address TEXT, citizenship_no TEXT DEFAULT '', notes TEXT)")
            conn.execute("INSERT INTO customers (id, name, phone, address, citizenship_no, notes) "
                         "SELECT id, name, phone, address, COALESCE(citizenship_no,''), notes FROM _customers_old")
            conn.execute("DROP TABLE _customers_old")
            conn.execute("COMMIT")
            conn.execute("PRAGMA legacy_alter_table=OFF")
            bad = conn.execute("PRAGMA foreign_key_check").fetchall()
            if bad:
                raise sqlite3.DatabaseError(f"Foreign key check failed: {bad[:3]}")
            conn.execute("PRAGMA foreign_keys=ON")
        except BaseException:
            if conn.in_transaction:
                conn.rollback()
            raise
        finally:
            conn.close()

    def _audit(self, conn, action, entity, entity_id="", details=""):
        conn.execute("INSERT INTO audit_log (ts, username, action, entity, entity_id, details) VALUES (?,?,?,?,?,?)",
                     (now_str(), self.current_user, action, entity, str(entity_id)[:80], str(details)[:500]))

    def get_audit(self, q="", action="All", limit=AUDIT_LIMIT):
        sql = "SELECT * FROM audit_log"
        cond, args = [], []
        if action and action != "All":
            cond.append("action=?")
            args.append(action)
        if q:
            cond.append("(username LIKE ? OR action LIKE ? OR entity LIKE ? OR entity_id LIKE ? OR details LIKE ?)")
            args += [f"%{q}%"] * 5
        if cond:
            sql += " WHERE " + " AND ".join(cond)
        sql += " ORDER BY id DESC LIMIT ?"
        args.append(int(limit))
        with self.get_conn() as conn:
            return conn.execute(sql, args).fetchall()

    def get_audit_actions(self):
        with self.get_conn() as conn:
            return [r[0] for r in conn.execute("SELECT DISTINCT action FROM audit_log ORDER BY action").fetchall()]

    def log_login(self, username):
        with self.get_conn(write=True) as conn:
            self._audit(conn, "LOGIN", "user", username, "Login successful")

    def login_state(self, username):
        with self.get_conn() as conn:
            f = conn.execute("SELECT value FROM settings WHERE key=?", (f"fails:{username}",)).fetchone()
            l = conn.execute("SELECT value FROM settings WHERE key=?", (f"lock:{username}",)).fetchone()
        try:
            fails = int(f["value"]) if f else 0
        except (ValueError, TypeError):
            fails = 0
        try:
            lock = float(l["value"]) if l else 0.0
        except (ValueError, TypeError):
            lock = 0.0
        return fails, lock

    def login_failed(self, username, max_tries, lock_seconds):
        fails, _ = self.login_state(username)
        fails += 1
        lock = 0.0
        if fails >= max_tries:
            fails, lock = 0, time.time() + lock_seconds
        with self.get_conn(write=True) as conn:
            conn.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (f"fails:{username}", str(fails)))
            conn.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (f"lock:{username}", str(lock)))
            if lock:
                self._audit(conn, "LOGIN_LOCKED", "user", username, f"Locked for {lock_seconds}s")
        return fails, lock

    def login_ok(self, username):
        with self.get_conn(write=True) as conn:
            conn.execute("DELETE FROM settings WHERE key IN (?,?)", (f"fails:{username}", f"lock:{username}"))

    def _add_cash_entry_with_conn(self, conn, date_str, c_type, category, amount, method, note="", manual=False):
        if method != "Cash":
            return
        amount = round(float(amount or 0), 2)
        if amount <= 0:
            if manual:
                raise ValueError("Cash amount must be greater than 0")
            return
        if c_type not in ("In", "Out"):
            raise ValueError("Invalid cash entry type")
        validate_date_nf(date_str)
        last_closed = conn.execute("SELECT MAX(date) FROM cash_closures").fetchone()[0]
        if last_closed and date_str <= last_closed:
            raise ValueError(f"The cash book is closed up to {last_closed}, so a cash entry dated {date_str} "
                             "is not allowed. Use a non-cash method, or re-open the last closed day in Cash Book.")
        conn.execute("INSERT INTO cash_book (date, type, category, amount, method, note, created_at) VALUES (?,?,?,?,?,?,?)",
                     (date_str, c_type, category, amount, method, note, now_str()))

    def add_cash_entry(self, date_str, c_type, category, amount, method, note=""):
        with self.get_conn(write=True) as conn:
            self._add_cash_entry_with_conn(conn, validate_date(date_str), c_type, category, amount, method, note, manual=True)
            self._audit(conn, "CASH_MANUAL", "cash", date_str, f"{c_type} {amount} ({category}) {note}")

    def _cash_opening(self, conn, date_str):
        row = conn.execute("SELECT opening FROM cash_closures WHERE date=?", (date_str,)).fetchone()
        if row:
            return row["opening"]
        agg = ("SELECT COALESCE(SUM(CASE WHEN type='In' THEN amount END),0) AS i, "
               "COALESCE(SUM(CASE WHEN type='Out' THEN amount END),0) AS o FROM cash_book WHERE ")
        last = conn.execute("SELECT closing, date FROM cash_closures WHERE date < ? ORDER BY date DESC LIMIT 1",
                            (date_str,)).fetchone()
        if last:
            s = conn.execute(agg + "date > ? AND date < ?", (last["date"], date_str)).fetchone()
            base = last["closing"]
        else:
            s = conn.execute(agg + "date < ?", (date_str,)).fetchone()
            base = 0
        return round(base + s["i"] - s["o"], 2)

    def _cash_summary(self, conn, date_str):
        opening = self._cash_opening(conn, date_str)
        s = conn.execute("SELECT COALESCE(SUM(CASE WHEN type='In' THEN amount END),0) AS i, "
                         "COALESCE(SUM(CASE WHEN type='Out' THEN amount END),0) AS o FROM cash_book WHERE date=?",
                         (date_str,)).fetchone()
        closure = conn.execute("SELECT note FROM cash_closures WHERE date=?", (date_str,)).fetchone()
        cin, cout = round(s["i"], 2), round(s["o"], 2)
        return {"opening": opening, "in": cin, "out": cout, "closing": round(opening + cin - cout, 2),
                "is_closed": closure is not None, "closure_note": (closure["note"] or "") if closure else ""}

    def get_cash_summary(self, date_str):
        validate_date(date_str)
        with self.get_conn() as conn:
            return self._cash_summary(conn, date_str)

    def get_cash_movements(self, date_str):
        with self.get_conn() as conn:
            return conn.execute("SELECT * FROM cash_book WHERE date=? ORDER BY id ASC", (date_str,)).fetchall()

    def close_day(self, date_str, note, user):
        validate_date_nf(date_str)
        with self.get_conn(write=True) as conn:
            mx = conn.execute("SELECT MAX(date) FROM cash_closures").fetchone()[0]
            if mx and date_str <= mx:
                raise ValueError(f"Cannot close this day. The cash book is already closed up to {mx}.")
            gap = (conn.execute("SELECT MIN(date) FROM cash_book WHERE date>? AND date<?", (mx, date_str)).fetchone()[0]
                   if mx else conn.execute("SELECT MIN(date) FROM cash_book WHERE date<?", (date_str,)).fetchone()[0])
            if gap:
                raise ValueError(f"There are unclosed cash entries on {gap}. Please close days in order (next: {gap}).")
            s = self._cash_summary(conn, date_str)
            conn.execute("INSERT INTO cash_closures (date, opening, cash_in, cash_out, closing, note, closed_by) "
                         "VALUES (?,?,?,?,?,?,?)",
                         (date_str, s["opening"], s["in"], s["out"], s["closing"], (note or "").strip(), user))
            self._audit(conn, "CASH_CLOSE", "cash", date_str, f"Closing {s['closing']}; note: {(note or '').strip()}")

    def reopen_last_closure(self):
        with self.get_conn(write=True) as conn:
            mx = conn.execute("SELECT MAX(date) FROM cash_closures").fetchone()[0]
            if not mx:
                raise ValueError("There is no closed day to re-open.")
            conn.execute("DELETE FROM cash_closures WHERE date=?", (mx,))
            self._audit(conn, "CASH_REOPEN", "cash", mx, "Last closure re-opened")
            return mx

    def get_previous_closures(self):
        with self.get_conn() as conn:
            return conn.execute("SELECT * FROM cash_closures ORDER BY date DESC LIMIT 60").fetchall()

    def get_stats(self):
        with self.get_conn() as conn:
            def one(sql, args=()):
                return conn.execute(sql, args).fetchone()[0] or 0
            sold = "(SELECT bike_no FROM bills WHERE voided=0)"
            revenue = one("SELECT SUM(total) FROM bills WHERE voided=0")
            bike_cost = one(f"SELECT SUM(buy_price) FROM bikes WHERE bike_no IN {sold}")
            parts_cost = one(f"SELECT SUM(qty * unit_cost_at_time) FROM parts_usage WHERE bike_no IN {sold}")
            labour_cost = one(f"SELECT SUM(amount) FROM bike_labour WHERE bike_no IN {sold}")
            op_exp = one("SELECT SUM(amount) FROM expenses WHERE category NOT IN ('Salary','Parts','Labour')")
            salary = one("SELECT SUM(amount) FROM salary_payments")
            gross = round(revenue - bike_cost - parts_cost - labour_cost, 2)
            cash = self._cash_summary(conn, today_str())
            return {"revenue": revenue, "total_due": one("SELECT SUM(due) FROM bills WHERE voided=0 AND due > 0"),
                    "gross": gross, "net": round(gross - op_exp - salary, 2), "op_exp": op_exp, "salary": salary,
                    "cash_in": cash["in"], "cash_out": cash["out"], "cash_closing": cash["closing"]}

    def get_last_7_days_data(self):
        sales, costs, dates = [], [], []
        with self.get_conn() as conn:
            def one(sql, args):
                return conn.execute(sql, args).fetchone()[0] or 0
            for i in range(6, -1, -1):
                day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                dates.append(day[5:])
                sold = "(SELECT bike_no FROM bills WHERE voided=0 AND DATE(created_at)=?)"
                sales.append(one("SELECT SUM(total) FROM bills WHERE voided=0 AND DATE(created_at)=?", (day,)))
                exp = one("SELECT SUM(amount) FROM expenses WHERE expense_date=? AND category NOT IN ('Salary','Parts','Labour')", (day,))
                sal = one("SELECT SUM(amount) FROM salary_payments WHERE payment_date=?", (day,))
                bike = one(f"SELECT SUM(buy_price) FROM bikes WHERE bike_no IN {sold}", (day,))
                parts = one(f"SELECT SUM(qty * unit_cost_at_time) FROM parts_usage WHERE bike_no IN {sold}", (day,))
                lab = one(f"SELECT SUM(amount) FROM bike_labour WHERE bike_no IN {sold}", (day,))
                costs.append(exp + sal + bike + parts + lab)
        return dates, sales, costs

    def get_top_debtors(self):
        with self.get_conn() as conn:
            return conn.execute("SELECT c.name, c.phone, SUM(b.due) AS total_due FROM bills b "
                                "JOIN customers c ON b.customer_id = c.id WHERE b.due > 0 AND b.voided=0 "
                                "GROUP BY c.id ORDER BY total_due DESC LIMIT 3").fetchall()

    def add_labour(self, bike_no, date, desc, mechanic, amount, paid_in_cash):
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")
        desc, mechanic = (desc or "").strip(), (mechanic or "").strip()
        if not desc or not mechanic:
            raise ValueError("Description and Mechanic are required")
        validate_date_nf(date)
        with self.get_conn(write=True) as conn:
            row = conn.execute("SELECT status FROM bikes WHERE bike_no=?", (bike_no,)).fetchone()
            if not row or row["status"] != "In Stock":
                raise ValueError("Labour can only be added to a bike that is in stock.")
            conn.execute("INSERT INTO bike_labour (bike_no, labour_date, description, mechanic, amount, paid_in_cash) "
                         "VALUES (?,?,?,?,?,?)", (bike_no, date, desc, mechanic, round(amount, 2), 1 if paid_in_cash else 0))
            if paid_in_cash:
                self._add_cash_entry_with_conn(conn, date, "Out", "Labour", amount, "Cash", f"Labour for {bike_no}")
            self._audit(conn, "LABOUR_ADD", "bike", bike_no, f"{desc} / {mechanic} / {amount}")

    def get_bike_cost_sheet(self):
        with self.get_conn() as conn:
            rows = conn.execute("""
                SELECT b.bike_no, b.model, b.engine_no, b.chassis_no, b.bluebook_expiry, b.photo_path,
                b.buy_price, b.sell_price, b.status,
                (SELECT SUM(qty * unit_cost_at_time) FROM parts_usage WHERE bike_no = b.bike_no) AS parts_cost,
                (SELECT SUM(amount) FROM bike_labour WHERE bike_no = b.bike_no) AS labour_cost,
                (SELECT total FROM bills WHERE bike_no = b.bike_no AND voided=0
                 ORDER BY created_at DESC, id DESC LIMIT 1) AS actual_sale
                FROM bikes b ORDER BY b.id DESC""").fetchall()
            out = []
            for r in rows:
                buy, parts, labour = r["buy_price"] or 0, r["parts_cost"] or 0, r["labour_cost"] or 0
                true_cost = round(buy + parts + labour, 2)
                sale = r["actual_sale"] if (r["status"] == "Sold" and r["actual_sale"] is not None) else (r["sell_price"] or 0)
                profit = round(sale - true_cost, 2)
                out.append({"bike_no": r["bike_no"], "model": r["model"] or "", "engine_no": r["engine_no"] or "",
                            "chassis_no": r["chassis_no"] or "", "bluebook_expiry": r["bluebook_expiry"] or "",
                            "photo_path": r["photo_path"] or "", "status": r["status"], "buy": buy, "parts": parts,
                            "labour": labour, "true_cost": true_cost, "sell": sale, "profit": profit,
                            "margin": round(profit / sale * 100, 2) if sale > 0 else 0.0})
            return out

    def get_bike_details(self, bike_no):
        with self.get_conn() as conn:
            bike = conn.execute("SELECT * FROM bikes WHERE bike_no=?", (bike_no,)).fetchone()
            parts = conn.execute("SELECT pu.qty, pu.unit_cost_at_time, COALESCE(p.name, '(Deleted Part)') AS name "
                                 "FROM parts_usage pu LEFT JOIN parts p ON pu.part_id = p.id "
                                 "WHERE pu.bike_no=? ORDER BY pu.id", (bike_no,)).fetchall()
            labour = conn.execute("SELECT * FROM bike_labour WHERE bike_no=? ORDER BY labour_date, id",
                                  (bike_no,)).fetchall()
            bill = conn.execute("SELECT b.*, c.name AS cust_name, c.phone AS cust_phone, c.citizenship_no AS cust_id_no "
                                "FROM bills b LEFT JOIN customers c ON b.customer_id = c.id "
                                "WHERE b.bike_no=? AND b.voided=0 ORDER BY b.created_at DESC, b.id DESC LIMIT 1",
                                (bike_no,)).fetchone()
            return bike, parts, labour, bill

    def get_customers(self):
        with self.get_conn() as conn:
            return conn.execute("""
                SELECT c.*,
                (SELECT COUNT(*) FROM bills WHERE customer_id=c.id AND voided=0) AS bill_count,
                COALESCE((SELECT SUM(total) FROM bills WHERE customer_id=c.id AND voided=0),0) AS total_bought,
                COALESCE((SELECT SUM(advance) FROM bills WHERE customer_id=c.id AND voided=0),0) AS total_paid,
                COALESCE((SELECT SUM(due) FROM bills WHERE customer_id=c.id AND voided=0),0) AS total_due
                FROM customers c ORDER BY c.name COLLATE NOCASE ASC""").fetchall()

    def get_customer(self, cid):
        with self.get_conn() as conn:
            return conn.execute("SELECT * FROM customers WHERE id=?", (cid,)).fetchone()

    def get_or_create_customer(self, name, phone, address="", citizenship="", notes=""):
        name = re.sub(r"\s+", " ", (name or "").strip())
        if not name:
            raise ValueError("Customer name is required")
        phone = re.sub(r"[\s\-]", "", phone or "") or None
        address, citizenship, notes = (address or "").strip(), (citizenship or "").strip(), (notes or "").strip()
        with self.get_conn(write=True) as conn:
            if phone:
                row = conn.execute("SELECT id, name FROM customers "
                                   "WHERE REPLACE(REPLACE(COALESCE(phone,''),' ',''),'-','')=? "
                                   "AND name=? COLLATE NOCASE ORDER BY id LIMIT 1", (phone, name)).fetchone()
            else:
                row = conn.execute("SELECT id, name FROM customers WHERE phone IS NULL AND name=? COLLATE NOCASE "
                                   "ORDER BY id LIMIT 1", (name,)).fetchone()
            if row:
                conn.execute("UPDATE customers SET "
                             "address = CASE WHEN TRIM(COALESCE(address,''))='' THEN ? ELSE address END, "
                             "citizenship_no = CASE WHEN TRIM(COALESCE(citizenship_no,''))='' THEN ? ELSE citizenship_no END "
                             "WHERE id=?", (address, citizenship, row["id"]))
                return row["id"], row["name"], False
            cid = conn.execute("INSERT INTO customers (name, phone, address, citizenship_no, notes) VALUES (?,?,?,?,?)",
                               (name, phone, address, citizenship, notes)).lastrowid
            self._audit(conn, "CUSTOMER_ADD", "customer", cid, f"{name} / {phone or 'no phone'}")
            return cid, name, True

    def delete_customer(self, cid):
        with self.get_conn(write=True) as conn:
            row = conn.execute("SELECT name FROM customers WHERE id=?", (cid,)).fetchone()
            if conn.execute("SELECT COUNT(*) FROM bills WHERE customer_id=?", (cid,)).fetchone()[0] > 0:
                raise ValueError("Cannot delete a customer who has bills (including voided ones).")
            conn.execute("DELETE FROM customers WHERE id=?", (cid,))
            self._audit(conn, "CUSTOMER_DELETE", "customer", cid, txt(row["name"]) if row else "")

    def get_customer_ledger(self, cid):
        with self.get_conn() as conn:
            bills = conn.execute("SELECT * FROM bills WHERE customer_id=? ORDER BY created_at DESC, id DESC",
                                 (cid,)).fetchall()
            payments = conn.execute("SELECT p.*, b.bill_no AS b_no FROM payments p JOIN bills b ON p.bill_id = b.id "
                                    "WHERE b.customer_id=? ORDER BY p.created_at DESC, p.id DESC", (cid,)).fetchall()
            return bills, payments

    def get_bikes(self):
        with self.get_conn() as conn:
            return conn.execute("SELECT * FROM bikes ORDER BY id DESC").fetchall()

    def get_stock_bikes(self):
        with self.get_conn() as conn:
            return conn.execute("SELECT * FROM bikes WHERE status='In Stock' ORDER BY bike_no COLLATE NOCASE").fetchall()

    def add_bike(self, bike_no, model, buy_price, sell_price, method,
                 engine_no="", chassis_no="", bluebook_expiry="", photo_path=""):
        bike_no = re.sub(r"\s+", " ", (bike_no or "").strip().upper())
        model = (model or "").strip()
        if not bike_no:
            raise ValueError("Bike number is required")
        if not model:
            raise ValueError("Model is required")
        if buy_price < 0 or sell_price < 0:
            raise ValueError("Price cannot be negative")
        validate_method(method)
        bb = (bluebook_expiry or "").strip()
        if bb:
            validate_date(bb)
        with self.get_conn(write=True) as conn:
            if conn.execute("SELECT 1 FROM bikes WHERE bike_no=? COLLATE NOCASE", (bike_no,)).fetchone():
                raise ValueError(f"Bike {bike_no} already exists.")
            conn.execute("INSERT INTO bikes (bike_no, model, engine_no, chassis_no, bluebook_expiry, photo_path, "
                         "buy_price, sell_price, status, method) VALUES (?,?,?,?,?,?,?,?,'In Stock',?)",
                         (bike_no, model, (engine_no or "").strip().upper(), (chassis_no or "").strip().upper(),
                          bb, photo_path or "", buy_price, sell_price, method))
            self._add_cash_entry_with_conn(conn, today_str(), "Out", "Bike Purchase", buy_price, method, f"Buy {bike_no}")
            self._audit(conn, "BIKE_ADD", "bike", bike_no, f"{model}; buy {buy_price}; sell {sell_price}; {method}")

    def update_bike_docs(self, bike_no, engine_no, chassis_no, bluebook_expiry, photo_path=""):
        bb = (bluebook_expiry or "").strip()
        if bb:
            validate_date(bb)
        eng, chs = (engine_no or "").strip().upper(), (chassis_no or "").strip().upper()
        with self.get_conn(write=True) as conn:
            row = conn.execute("SELECT photo_path FROM bikes WHERE bike_no=?", (bike_no,)).fetchone()
            if not row:
                raise ValueError("Bike not found")
            old = row["photo_path"] or ""
            if photo_path:
                conn.execute("UPDATE bikes SET engine_no=?, chassis_no=?, bluebook_expiry=?, photo_path=? WHERE bike_no=?",
                             (eng, chs, bb, photo_path, bike_no))
            else:
                conn.execute("UPDATE bikes SET engine_no=?, chassis_no=?, bluebook_expiry=? WHERE bike_no=?",
                             (eng, chs, bb, bike_no))
            self._audit(conn, "BIKE_DOCS_UPDATE", "bike", bike_no,
                        f"engine {eng}; chassis {chs}; bb {bb}; photo {'replaced' if photo_path else 'kept'}")
            return old if photo_path else ""

    def delete_bike(self, bike_id):
        with self.get_conn(write=True) as conn:
            row = conn.execute("SELECT bike_no, photo_path, buy_price, method FROM bikes WHERE id=?",
                               (bike_id,)).fetchone()
            if not row:
                return None
            b_no = row["bike_no"]
            for t, msg in (("bills", "existing bills"), ("parts_usage", "parts usage"), ("bike_labour", "labour records")):
                if conn.execute(f"SELECT COUNT(*) FROM {t} WHERE bike_no=?", (b_no,)).fetchone()[0] > 0:
                    raise ValueError(f"Cannot delete a bike with {msg}.")
            conn.execute("DELETE FROM bikes WHERE id=?", (bike_id,))
            if row["method"] == "Cash" and (row["buy_price"] or 0) > 0:
                try:
                    self._add_cash_entry_with_conn(conn, today_str(), "In", "Bike Purchase Reversal",
                                                   row["buy_price"], "Cash", f"Deleted bike {b_no}")
                except ValueError as ex:
                    raise ValueError(
                        f"Bike '{b_no}' was NOT deleted.\nDeleting it must return {money(row['buy_price'])} "
                        f"to today's cash book, but that is blocked:\n{ex}\n\n"
                        "Fix: Cash Book -> 'Re-open Last Day', then delete the bike again.") from None
            self._audit(conn, "BIKE_DELETE", "bike", b_no, f"buy {row['buy_price']}; {row['method']}")
            return row["photo_path"] or ""

    def get_bills(self):
        with self.get_conn() as conn:
            return conn.execute("SELECT b.*, c.name AS cust_name, c.phone AS cust_phone FROM bills b "
                                "LEFT JOIN customers c ON b.customer_id = c.id "
                                "ORDER BY b.created_at DESC, b.id DESC").fetchall()

    def get_bill(self, bill_id):
        with self.get_conn() as conn:
            return conn.execute("SELECT * FROM bills WHERE id=?", (bill_id,)).fetchone()

    def get_bill_payments(self, bill_id):
        with self.get_conn() as conn:
            return conn.execute("SELECT * FROM payments WHERE bill_id=? ORDER BY id", (bill_id,)).fetchall()

    def create_bill(self, bike_no, customer_id, total, advance, method):
        if total <= 0:
            raise ValueError("Total amount must be greater than 0")
        if advance < 0:
            raise ValueError("Advance cannot be negative")
        if advance > total:
            raise ValueError("Advance cannot exceed total")
        validate_method(method)
        with self.get_conn(write=True) as conn:
            cust = conn.execute("SELECT name FROM customers WHERE id=?", (customer_id,)).fetchone()
            if not cust:
                raise ValueError("Customer not found")
            bike = conn.execute("SELECT status FROM bikes WHERE bike_no=?", (bike_no,)).fetchone()
            if not bike or bike["status"] != "In Stock":
                raise ValueError("Bike is not available in stock.")
            now = datetime.now()
            prefix = f"INV-{now:%Y%m%d}-"
            last = conn.execute("SELECT MAX(bill_no) FROM bills WHERE bill_no LIKE ?", (prefix + "%",)).fetchone()[0]
            try:
                seq = int(last.rsplit("-", 1)[1]) + 1 if last else 1
            except ValueError:
                seq = conn.execute("SELECT COUNT(*) FROM bills WHERE bill_no LIKE ?", (prefix + "%",)).fetchone()[0] + 1
            bill_no = f"{prefix}{seq:04d}"
            due = round(total - advance, 2)
            status = "Paid" if due <= 0 else ("Partial" if advance > 0 else "Unpaid")
            bid = conn.execute("INSERT INTO bills (bill_no, customer_id, buyer_name, bike_no, total, advance, due, "
                               "status, payment_method, voided, created_at) VALUES (?,?,?,?,?,?,?,?,?,0,?)",
                               (bill_no, customer_id, cust["name"], bike_no, total, advance, due, status,
                                method, now.strftime("%Y-%m-%d %H:%M:%S"))).lastrowid
            conn.execute("UPDATE bikes SET status='Sold' WHERE bike_no=?", (bike_no,))
            if advance > 0:
                conn.execute("INSERT INTO payments (bill_id, bill_no, amount, method, note, created_at) VALUES (?,?,?,?,?,?)",
                             (bid, bill_no, advance, method, "Advance", now.strftime("%Y-%m-%d %H:%M:%S")))
                self._add_cash_entry_with_conn(conn, today_str(), "In", "Bill Advance", advance, method, f"Bill {bill_no}")
            self._audit(conn, "BILL_CREATE", "bill", bill_no,
                        f"{cust['name']}; bike {bike_no}; total {total}; adv {advance}; {method}")
            return bid, bill_no

    def collect_due(self, bill_id, amount, method):
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")
        validate_method(method)
        with self.get_conn(write=True) as conn:
            row = conn.execute("SELECT bill_no, due, advance, voided FROM bills WHERE id=?", (bill_id,)).fetchone()
            if not row:
                raise ValueError("Bill not found")
            if row["voided"]:
                raise ValueError("This bill is voided. No payment can be collected.")
            if round(amount, 2) > round(row["due"], 2):
                raise ValueError("Amount is greater than the due amount")
            new_due, new_adv = round(row["due"] - amount, 2), round(row["advance"] + amount, 2)
            conn.execute("UPDATE bills SET due=?, advance=?, status=? WHERE id=?",
                         (new_due, new_adv, "Paid" if new_due <= 0 else "Partial", bill_id))
            conn.execute("INSERT INTO payments (bill_id, bill_no, amount, method, note, created_at) VALUES (?,?,?,?,?,?)",
                         (bill_id, row["bill_no"], amount, method, "Due Collection", now_str()))
            self._add_cash_entry_with_conn(conn, today_str(), "In", "Due Collection", amount, method, f"Bill {row['bill_no']}")
            self._audit(conn, "BILL_DUE_COLLECT", "bill", row["bill_no"], f"{amount} via {method}; remaining {new_due}")

    def void_bill(self, bill_id, reason):
        reason = (reason or "").strip()
        if not reason:
            raise ValueError("A void reason is required")
        with self.get_conn(write=True) as conn:
            b = conn.execute("SELECT * FROM bills WHERE id=?", (bill_id,)).fetchone()
            if not b:
                raise ValueError("Bill not found")
            if b["voided"]:
                raise ValueError("This bill is already voided.")
            cash_paid = conn.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE bill_id=? AND method='Cash'",
                                     (bill_id,)).fetchone()[0]
            if cash_paid > 0:
                try:
                    self._add_cash_entry_with_conn(conn, today_str(), "Out", "Bill Void Reversal",
                                                   cash_paid, "Cash", f"Void {b['bill_no']}")
                except ValueError as ex:
                    raise ValueError(f"Bill was NOT voided.\nVoiding must return {money(cash_paid)} from today's "
                                     f"cash book, but that is blocked:\n{ex}\n\n"
                                     "Fix: Cash Book -> 'Re-open Last Day', then void again.") from None
            conn.execute("UPDATE bills SET voided=1, status='Voided', void_reason=?, voided_at=?, voided_by=? WHERE id=?",
                         (reason, now_str(), self.current_user, bill_id))
            other = conn.execute("SELECT COUNT(*) FROM bills WHERE bike_no=? AND voided=0 AND id<>?",
                                 (b["bike_no"], bill_id)).fetchone()[0]
            if other == 0:
                conn.execute("UPDATE bikes SET status='In Stock' WHERE bike_no=?", (b["bike_no"],))
            self._audit(conn, "BILL_VOID", "bill", b["bill_no"],
                        f"reason: {reason}; cash reversed {cash_paid}; bike {b['bike_no']} restocked")
            return cash_paid

    def update_bill(self, bill_id, customer_id, total=None, advance=None, method=None):
        with self.get_conn(write=True) as conn:
            b = conn.execute("SELECT * FROM bills WHERE id=?", (bill_id,)).fetchone()
            if not b:
                raise ValueError("Bill not found")
            if b["voided"]:
                raise ValueError("A voided bill cannot be edited.")
            cust = conn.execute("SELECT name FROM customers WHERE id=?", (customer_id,)).fetchone()
            if not cust:
                raise ValueError("Customer not found")
            pays = conn.execute("SELECT * FROM payments WHERE bill_id=? ORDER BY id", (bill_id,)).fetchall()

            if total is None:
                conn.execute("UPDATE bills SET customer_id=?, buyer_name=? WHERE id=?",
                             (customer_id, cust["name"], bill_id))
                self._audit(conn, "BILL_EDIT", "bill", b["bill_no"], f"customer {b['buyer_name']} -> {cust['name']}")
                return

            if len(pays) > 1:
                raise ValueError("This bill already has due collections, so amounts cannot be edited.\n"
                                 "Please VOID this bill and create a new one instead.")
            total, advance = round(float(total), 2), round(float(advance), 2)
            if total <= 0:
                raise ValueError("Total amount must be greater than 0")
            if advance < 0 or advance > total:
                raise ValueError("Advance must be between 0 and total")
            validate_method(method)
            old_adv, old_method = b["advance"] or 0, b["payment_method"]
            if old_method == "Cash" and old_adv > 0:
                try:
                    self._add_cash_entry_with_conn(conn, today_str(), "Out", "Bill Edit Reversal", old_adv,
                                                   "Cash", f"Edit {b['bill_no']} (old advance)")
                except ValueError as ex:
                    raise ValueError(f"Bill was NOT edited.\nEditing must reverse {money(old_adv)} in today's cash "
                                     f"book, but that is blocked:\n{ex}\n\n"
                                     "Fix: Cash Book -> 'Re-open Last Day', then edit again.") from None
            due = round(total - advance, 2)
            status = "Paid" if due <= 0 else ("Partial" if advance > 0 else "Unpaid")
            conn.execute("UPDATE bills SET customer_id=?, buyer_name=?, total=?, advance=?, due=?, status=?, "
                         "payment_method=? WHERE id=?",
                         (customer_id, cust["name"], total, advance, due, status, method, bill_id))
            conn.execute("DELETE FROM payments WHERE bill_id=?", (bill_id,))
            if advance > 0:
                conn.execute("INSERT INTO payments (bill_id, bill_no, amount, method, note, created_at) VALUES (?,?,?,?,?,?)",
                             (bill_id, b["bill_no"], advance, method, "Advance (edited)", now_str()))
                self._add_cash_entry_with_conn(conn, today_str(), "In", "Bill Advance", advance, method,
                                               f"Bill {b['bill_no']} (edited)")
            self._audit(conn, "BILL_EDIT", "bill", b["bill_no"],
                        f"total {b['total']}->{total}; adv {old_adv}->{advance}; method {old_method}->{method}; "
                        f"customer -> {cust['name']}")

    def get_bill_details_for_receipt(self, bill_id):
        with self.get_conn() as conn:
            bill = conn.execute("SELECT b.*, c.name AS cust_name, c.phone AS cust_phone, c.address AS cust_address, "
                                "c.citizenship_no AS cust_id_no FROM bills b "
                                "LEFT JOIN customers c ON b.customer_id = c.id WHERE b.id=?", (bill_id,)).fetchone()
            if not bill:
                return None, None, None, None
            bike = conn.execute("SELECT * FROM bikes WHERE bike_no=?", (bill["bike_no"],)).fetchone()
            payments = conn.execute("SELECT * FROM payments WHERE bill_id=? ORDER BY created_at, id", (bill_id,)).fetchall()
            parts = conn.execute("SELECT COALESCE(p.name, '(Deleted Part)') AS name, pu.qty FROM parts_usage pu "
                                 "LEFT JOIN parts p ON pu.part_id = p.id WHERE pu.bike_no=? ORDER BY pu.id",
                                 (bill["bike_no"],)).fetchall()
            return bill, bike, payments, parts

    def get_staff(self):
        with self.get_conn() as conn:
            return conn.execute("SELECT * FROM staff WHERE active=1 ORDER BY name COLLATE NOCASE").fetchall()

    def get_staff_member(self, staff_id):
        with self.get_conn() as conn:
            return conn.execute("SELECT * FROM staff WHERE id=?", (staff_id,)).fetchone()

    def add_staff(self, name, phone, role, salary):
        name = (name or "").strip()
        if not name:
            raise ValueError("Name is required")
        if salary < 0:
            raise ValueError("Salary cannot be negative")
        with self.get_conn(write=True) as conn:
            sid = conn.execute("INSERT INTO staff (name, phone, role, monthly_salary) VALUES (?,?,?,?)",
                               (name, (phone or "").strip(), (role or "").strip(), salary)).lastrowid
            self._audit(conn, "STAFF_ADD", "staff", sid, f"{name}; salary {salary}")

    def deactivate_staff(self, staff_id):
        with self.get_conn(write=True) as conn:
            row = conn.execute("SELECT name FROM staff WHERE id=?", (staff_id,)).fetchone()
            conn.execute("UPDATE staff SET active=0 WHERE id=?", (staff_id,))
            self._audit(conn, "STAFF_DEACTIVATE", "staff", staff_id, txt(row["name"]) if row else "")

    def pay_salary(self, staff_id, month, amount, date, method, note):
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")
        validate_method(method)
        validate_month_nf(month)
        validate_date_nf(date)
        with self.get_conn(write=True) as conn:
            st = conn.execute("SELECT name FROM staff WHERE id=? AND active=1", (staff_id,)).fetchone()
            if not st:
                raise ValueError("Staff not found or inactive.")
            if conn.execute("SELECT 1 FROM salary_payments WHERE staff_id=? AND month=?", (staff_id, month)).fetchone():
                raise ValueError(f"Salary for {month} has already been paid.")
            conn.execute("INSERT INTO salary_payments (staff_id, month, amount, payment_date, method, note) "
                         "VALUES (?,?,?,?,?,?)", (staff_id, month, amount, date, method, note))
            self._add_cash_entry_with_conn(conn, date, "Out", "Salary", amount, method, f"Salary {month} - {st['name']}")
            self._audit(conn, "SALARY_PAY", "staff", staff_id, f"{st['name']}; {month}; {amount}; {method}")

    def get_salary_history(self, staff_id):
        with self.get_conn() as conn:
            return conn.execute("SELECT * FROM salary_payments WHERE staff_id=? ORDER BY month DESC",
                                (staff_id,)).fetchall()

    def get_parts(self):
        with self.get_conn() as conn:
            return conn.execute("SELECT * FROM parts ORDER BY name COLLATE NOCASE").fetchall()

    def get_part(self, part_id):
        with self.get_conn() as conn:
            return conn.execute("SELECT * FROM parts WHERE id=?", (part_id,)).fetchone()

    def add_part(self, name, category, qty, cost, threshold):
        name = (name or "").strip()
        if not name:
            raise ValueError("Name is required")
        if qty < 0 or cost < 0 or threshold < 0:
            raise ValueError("Qty, cost and threshold cannot be negative")
        with self.get_conn(write=True) as conn:
            pid = conn.execute("INSERT INTO parts (name, category, stock_qty, unit_cost, low_stock_threshold) "
                               "VALUES (?,?,?,?,?)", (name, category, qty, cost, threshold)).lastrowid
            self._audit(conn, "PART_ADD", "part", pid, f"{name}; qty {qty}; cost {cost}")

    def buy_parts(self, part_id, qty, new_cost, method):
        if qty <= 0 or new_cost < 0:
            raise ValueError("Qty must be greater than 0 and cost cannot be negative")
        validate_method(method)
        with self.get_conn(write=True) as conn:
            row = conn.execute("SELECT name, stock_qty, unit_cost FROM parts WHERE id=?", (part_id,)).fetchone()
            if not row:
                raise ValueError("Part not found")
            old_qty, old_cost = row["stock_qty"] or 0, row["unit_cost"] or 0
            new_qty = old_qty + qty
            avg = round((old_qty * old_cost + qty * new_cost) / new_qty, 2)
            conn.execute("UPDATE parts SET stock_qty=?, unit_cost=? WHERE id=?", (new_qty, avg, part_id))
            self._add_cash_entry_with_conn(conn, today_str(), "Out", "Parts Purchase", qty * new_cost, method,
                                           f"Bought {qty} x {row['name']}")
            self._audit(conn, "PART_BUY", "part", part_id, f"{row['name']}; +{qty} @ {new_cost}; {method}")

    def use_part(self, part_id, bike_no, qty, date):
        if qty <= 0:
            raise ValueError("Qty must be greater than 0")
        validate_date_nf(date)
        with self.get_conn(write=True) as conn:
            row = conn.execute("SELECT status FROM bikes WHERE bike_no=?", (bike_no,)).fetchone()
            if not row or row["status"] != "In Stock":
                raise ValueError("The bike must be in stock.")
            p = conn.execute("SELECT name, unit_cost, stock_qty FROM parts WHERE id=?", (part_id,)).fetchone()
            if not p or (p["stock_qty"] or 0) < qty:
                raise ValueError("Not enough stock.")
            conn.execute("UPDATE parts SET stock_qty = stock_qty - ? WHERE id=?", (qty, part_id))
            conn.execute("INSERT INTO parts_usage (part_id, bike_no, qty, unit_cost_at_time, usage_date) VALUES (?,?,?,?,?)",
                         (part_id, bike_no, qty, p["unit_cost"] or 0, date))
            self._audit(conn, "PART_USE", "bike", bike_no, f"{qty} x {p['name']}")

    def get_expenses(self):
        with self.get_conn() as conn:
            return conn.execute("SELECT * FROM expenses WHERE category NOT IN ('Salary','Parts','Labour') "
                                "ORDER BY expense_date DESC, id DESC").fetchall()

    def get_expense(self, eid):
        with self.get_conn() as conn:
            return conn.execute("SELECT * FROM expenses WHERE id=?", (eid,)).fetchone()

    def _validate_expense(self, title, category, amount, date, method):
        title = (title or "").strip()
        if not title:
            raise ValueError("Title is required")
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")
        if category in RESERVED_EXPENSE_CATS:
            raise ValueError("Use the dedicated page for this category.")
        validate_method(method)
        validate_date_nf(date)
        return title

    def add_expense(self, title, category, amount, date, method, note):
        title = self._validate_expense(title, category, amount, date, method)
        with self.get_conn(write=True) as conn:
            eid = conn.execute("INSERT INTO expenses (title, category, amount, expense_date, note, method) "
                               "VALUES (?,?,?,?,?,?)", (title, category, amount, date, note, method)).lastrowid
            self._add_cash_entry_with_conn(conn, date, "Out", category, amount, method, title)
            self._audit(conn, "EXPENSE_ADD", "expense", eid, f"{title}; {category}; {amount}; {date}; {method}")

    def update_expense(self, eid, title, category, amount, date, method, note):
        title = self._validate_expense(title, category, amount, date, method)
        with self.get_conn(write=True) as conn:
            old = conn.execute("SELECT * FROM expenses WHERE id=?", (eid,)).fetchone()
            if not old:
                raise ValueError("Expense not found")
            if old["method"] == "Cash" and (old["amount"] or 0) > 0:
                try:
                    self._add_cash_entry_with_conn(conn, today_str(), "In", "Expense Reversal", old["amount"],
                                                   "Cash", f"Edit expense #{eid} ({old['title']})")
                except ValueError as ex:
                    raise ValueError(f"Expense was NOT edited.\nEditing must reverse {money(old['amount'])} in today's "
                                     f"cash book, but that is blocked:\n{ex}\n\n"
                                     "Fix: Cash Book -> 'Re-open Last Day', then edit again.") from None
            conn.execute("UPDATE expenses SET title=?, category=?, amount=?, expense_date=?, note=?, method=? WHERE id=?",
                         (title, category, amount, date, note, method, eid))
            self._add_cash_entry_with_conn(conn, date, "Out", category, amount, method, title)
            self._audit(conn, "EXPENSE_EDIT", "expense", eid,
                        f"{old['title']}({old['amount']},{old['method']}) -> {title}({amount},{method}) on {date}")

    def delete_expense(self, eid):
        with self.get_conn(write=True) as conn:
            old = conn.execute("SELECT * FROM expenses WHERE id=?", (eid,)).fetchone()
            if not old:
                raise ValueError("Expense not found")
            if old["method"] == "Cash" and (old["amount"] or 0) > 0:
                try:
                    self._add_cash_entry_with_conn(conn, today_str(), "In", "Expense Reversal", old["amount"],
                                                   "Cash", f"Deleted expense #{eid} ({old['title']})")
                except ValueError as ex:
                    raise ValueError(f"Expense was NOT deleted.\nDeleting must return {money(old['amount'])} to today's "
                                     f"cash book, but that is blocked:\n{ex}\n\n"
                                     "Fix: Cash Book -> 'Re-open Last Day', then delete again.") from None
            conn.execute("DELETE FROM expenses WHERE id=?", (eid,))
            self._audit(conn, "EXPENSE_DELETE", "expense", eid,
                        f"{old['title']}; {old['amount']}; {old['expense_date']}; {old['method']}")

    def monthly_report(self, month):
        validate_month(month)
        like = f"{month}%"
        with self.get_conn() as conn:
            def one(sql):
                return conn.execute(sql, (like,)).fetchone()[0] or 0
            sold = "(SELECT bike_no FROM bills WHERE voided=0 AND created_at LIKE ?)"
            rev = one("SELECT SUM(total) FROM bills WHERE voided=0 AND created_at LIKE ?")
            bike_cost = one(f"SELECT SUM(buy_price) FROM bikes WHERE bike_no IN {sold}")
            parts_cost = one(f"SELECT SUM(qty * unit_cost_at_time) FROM parts_usage WHERE bike_no IN {sold}")
            labour_cost = one(f"SELECT SUM(amount) FROM bike_labour WHERE bike_no IN {sold}")
            op_exp = one("SELECT SUM(amount) FROM expenses WHERE expense_date LIKE ? AND category NOT IN ('Salary','Parts','Labour')")
            salary = one("SELECT SUM(amount) FROM salary_payments WHERE payment_date LIKE ?")
            gross = round(rev - bike_cost - parts_cost - labour_cost, 2)
            return {"Month": month, "Revenue": rev, "Bike Cost": bike_cost, "Parts Cost": parts_cost,
                    "Labour Cost": labour_cost, "Gross Profit": gross, "Operating Exp": op_exp,
                    "Salary Paid": salary, "Net Profit": round(gross - op_exp - salary, 2)}

    @staticmethod
    def hash_password(password):
        salt = os.urandom(16)
        h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600000)
        return f"{salt.hex()}${h.hex()}"

    @staticmethod
    def verify_password(stored_hash, password):
        try:
            salt_hex, hash_hex = stored_hash.split("$")
            calc = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 600000).hex()
            return hmac.compare_digest(calc, hash_hex)
        except Exception:
            return False

    def authenticate(self, username, password):
        with self.get_conn() as conn:
            row = conn.execute("SELECT password_hash, must_change_password FROM users WHERE username=?",
                               (username,)).fetchone()
            if row and self.verify_password(row["password_hash"], password):
                return True, int(row["must_change_password"] or 0)
            return False, 0

    def change_password(self, username, old_pwd, new_pwd):
        if len(new_pwd) < 8:
            raise ValueError("New password is too short (minimum 8 characters)")
        if new_pwd == "admin123":
            raise ValueError("Please choose a different password than the default one")
        if old_pwd == new_pwd:
            raise ValueError("New password cannot be the same as the old one")
        with self.get_conn(write=True) as conn:
            row = conn.execute("SELECT password_hash FROM users WHERE username=?", (username,)).fetchone()
            if not row or not self.verify_password(row["password_hash"], old_pwd):
                raise ValueError("Incorrect old password")
            conn.execute("UPDATE users SET password_hash=?, must_change_password=0 WHERE username=?",
                         (self.hash_password(new_pwd), username))
            self._audit(conn, "PASSWORD_CHANGE", "user", username, "Password updated")

    def backup_to(self, path):
        src = sqlite3.connect(self.db_path, timeout=30.0)
        dst = sqlite3.connect(path)
        try:
            src.backup(dst)
        finally:
            dst.close()
            src.close()

    def auto_backup(self, keep=14):
        path = os.path.join(BACKUP_DIR, f"auto_{datetime.now():%Y%m%d}.db")
        if os.path.exists(path):
            return
        self.backup_to(path)
        files = sorted(f for f in os.listdir(BACKUP_DIR) if f.startswith("auto_") and f.endswith(".db"))
        for f in files[:-keep]:
            try:
                os.remove(os.path.join(BACKUP_DIR, f))
            except OSError:
                pass


# ============================== UI HELPERS ==============================


def apply_tree_style():
    s = ttk.Style()
    try:
        s.theme_use("clam")
    except tk.TclError:
        pass
    s.configure("Treeview", background=COLORS["card"], fieldbackground=COLORS["card"], foreground=COLORS["text"],
                rowheight=28, borderwidth=0, font=(FONT, 10))
    s.configure("Treeview.Heading", background=COLORS["sidebar"], foreground=COLORS["text"],
                relief="flat", font=(FONT, 10, "bold"))
    s.map("Treeview", background=[("selected", COLORS["accent_blue"])], foreground=[("selected", "#ffffff")])
    s.map("Treeview.Heading", background=[("active", COLORS["card_hover"])])


_NUM_RE = re.compile(r"^\s*(Rs\.?\s*)?(-?[\d,]*\.?\d+)\s*%?\s*$")


def _sort_key(s):
    m = _NUM_RE.match(str(s))
    if m:
        try:
            return (0, float(m.group(2).replace(",", "")), "")
        except ValueError:
            pass
    return (1, 0.0, str(s).lower())


def sort_tree(tree, col, reverse):
    rows = [(tree.set(k, col), k) for k in tree.get_children("")]
    rows.sort(key=lambda r: _sort_key(r[0]), reverse=reverse)
    for i, (_, k) in enumerate(rows):
        tree.move(k, "", i)
    tree.heading(col, command=lambda: sort_tree(tree, col, not reverse))


def make_tree(parent, columns, height=None, expand=True, widths=None):
    box = ctk.CTkFrame(parent, fg_color="transparent")
    box.pack(fill="both" if expand else "x", expand=expand, pady=(0, 5))
    box.grid_rowconfigure(0, weight=1)
    box.grid_columnconfigure(0, weight=1)
    kw = {"height": height} if height else {}
    tree = ttk.Treeview(box, columns=columns, show="headings", selectmode="browse", **kw)
    ys = ctk.CTkScrollbar(box, orientation="vertical", command=tree.yview)
    xs = ctk.CTkScrollbar(box, orientation="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
    tree.grid(row=0, column=0, sticky="nsew")
    ys.grid(row=0, column=1, sticky="ns")
    xs.grid(row=1, column=0, sticky="ew")
    for c in columns:
        tree.heading(c, text=c, command=lambda col=c: sort_tree(tree, col, False))
        w = (widths or {}).get(c, 110)
        tree.column(c, anchor="center", width=w, minwidth=60, stretch=not bool(widths))
    return tree


def clear_tree(tree):
    tree.delete(*tree.get_children())


# ============================== MAIN APP ==============================


class ShuvamApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        global DB
        self.db = DBManager(DB_FILE)
        DB = self.db
        try:
            self.db.auto_backup()
        except Exception:
            logging.exception("Auto backup failed")
        self.title(f"{CONFIG.get('shop_name', APP_NAME)} - v{APP_VERSION}")
        try:
            import os as _os
            _ico = _os.path.join(BASE_DIR, "assets", "shuvam_icon.ico")
            if _os.path.exists(_ico):
                self.iconbitmap(_ico)
        except Exception:
            pass
        self.minsize(960, 600)
        self.configure(fg_color=COLORS["bg_main"])
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        apply_tree_style()
        self.current_frame = None
        self.show_login()

    def fit_window(self, w, h):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(w, sw - 40), min(h, sh - 90)
        self.geometry(f"{w}x{h}+{max((sw - w) // 2, 0)}+{max((sh - h) // 2 - 20, 0)}")

    def clear_frame(self):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = None

    def show_login(self):
        self.db.set_user("system")
        self.clear_frame()
        self.fit_window(900, 550)
        self.current_frame = LoginFrame(self, self.db, self.on_login_success)

    def on_login_success(self, username, must_change):
        self.db.set_user(username)
        self.clear_frame()
        self.fit_window(1280, 840)
        self.current_frame = DashboardFrame(self, self.db, username, must_change, self.on_logout)
        # silent cloud sync + auto-update check (background, no UI blocking)
        try:
            import threading
            threading.Thread(target=_silent_cloud_sync, daemon=True).start()
            self.after(1500, lambda: threading.Thread(target=_auto_update_check, args=(self, username), daemon=True).start())
            # offline retry: try sync every 90s when offline
            def _offline_retry():
                import time
                while True:
                    time.sleep(90)
                    try:
                        cfg = load_cloud_config()
                        if not cfg.get("enabled", True):
                            continue
                        cloud_push(cfg)
                    except Exception:
                        pass
            threading.Thread(target=_offline_retry, daemon=True).start()
        except Exception:
            logging.exception("boot hooks failed")

    def on_logout(self):
        self.show_login()

    def report_callback_exception(self, exc, val, tb):
        logging.error("Unhandled UI error", exc_info=(exc, val, tb))
        try:
            messagebox.showerror("Unexpected Error",
                                 f"Something went wrong:\n{val}\nDetails were saved to error.log")
        except Exception:
            pass


class LoginFrame(ctk.CTkFrame):
    MAX_TRIES = 5
    LOCK_SECONDS = 30

    def __init__(self, master, db, on_success):
        super().__init__(master, fg_color="#e0e5ec", corner_radius=0)
        self.db, self.on_success = db, on_success
        self.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        form = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=0, width=450)
        form.grid(row=0, column=0, sticky="nsew")
        form.grid_propagate(False)
        ctk.CTkLabel(form, text="User Login", font=(FONT, 32, "bold"), text_color="#1f2937").pack(pady=(80, 6))
        ctk.CTkLabel(form, text=CONFIG.get("shop_name", ""), font=(FONT, 14), text_color="#6b7280").pack(pady=(0, 28))
        self.user_entry = ctk.CTkEntry(form, placeholder_text="Username", width=300, height=45,
                                       fg_color="#e5e7eb", text_color="#000", border_width=0)
        self.user_entry.pack(pady=10)
        self.pass_entry = ctk.CTkEntry(form, placeholder_text="Password", show="*", width=300, height=45,
                                       fg_color="#e5e7eb", text_color="#000", border_width=0)
        self.pass_entry.pack(pady=10)
        ctk.CTkButton(form, text="LOGIN", width=300, height=45, font=(FONT, 14, "bold"),
                      fg_color=COLORS["login_bg"], hover_color="#1a426b", command=self.login).pack(pady=30)
        self.user_entry.bind("<Return>", lambda e: self.login())
        self.pass_entry.bind("<Return>", lambda e: self.login())
        self.after(200, self.user_entry.focus_set)
        graphic = ctk.CTkFrame(self, fg_color=COLORS["login_bg"], corner_radius=0)
        graphic.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(graphic, text="🔒", font=("Segoe UI Emoji", 120), text_color="#1e4a75").place(relx=0.5, rely=0.45, anchor="center")
        ctk.CTkLabel(graphic, text=f"Version {APP_VERSION}", font=(FONT, 14), text_color="#6495ed").place(relx=0.5, rely=0.68, anchor="center")

    def login(self):
        u, p = self.user_entry.get().strip(), self.pass_entry.get()
        if not u or not p:
            return messagebox.showerror("Error", "Please enter both username and password.")
        try:
            fails, lock = self.db.login_state(u)
            now = time.time()
            if now < lock:
                return messagebox.showwarning("Locked", f"Too many failed attempts.\n"
                                                        f"Try again in {int(lock - now) + 1} seconds.")
            ok, must_change = self.db.authenticate(u, p)
            if ok:
                self.db.login_ok(u)
                self.db.set_user(u)
                self.db.log_login(u)
                self.on_success(u, must_change)
                return
            fails, lock = self.db.login_failed(u, self.MAX_TRIES, self.LOCK_SECONDS)
        except Exception as ex:
            return messagebox.showerror("Error", str(ex))
        if lock > time.time():
            messagebox.showerror("Locked", f"Too many failed attempts.\nLogin is locked for {self.LOCK_SECONDS} seconds.")
        else:
            messagebox.showerror("Error", f"Invalid credentials ({self.MAX_TRIES - fails} attempts left)")
        self.pass_entry.delete(0, "end")


class DashboardFrame(ctk.CTkFrame):
    PAGES = [("📊 Dashboard", "Dashboard"), ("💵 Cash Book", "CashBook"), ("🚲 Bikes", "Bikes"),
             ("📋 Cost Sheet", "CostSheet"), ("👥 Customers", "Customers"), ("🧾 Bills & Dues", "Bills"),
             ("👷 Staff", "Staff"), ("🔧 Parts", "Parts"), ("💸 Expenses", "Expenses"),
             ("📈 Reports", "Reports"), ("🕵️ Audit Log", "Audit"), ("⚙️ Settings", "Settings")]
    LOADERS = {"Dashboard": "refresh_dashboard", "CashBook": "load_cashbook", "Bikes": "load_bikes",
               "CostSheet": "load_cost_sheet", "Customers": "load_customers", "Bills": "load_bills",
               "Staff": "load_staff", "Parts": "load_parts", "Expenses": "load_expenses",
               "Reports": "generate_report", "Audit": "load_audit"}

    def __init__(self, master, db, username, must_change, on_logout):
        super().__init__(master, fg_color=COLORS["bg_main"], corner_radius=0)
        self.db, self.username, self.must_change, self.on_logout = db, username, bool(must_change), on_logout
        self.chart_canvas_widget = None
        self.pages, self.nav_btns = {}, {}
        self.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.build_sidebar()
        self.build_main_area()
        if self.must_change:
            self.after(500, lambda: messagebox.showwarning(
                "Security Warning", "You are using the default password.\nPlease change it in Settings to continue."))
            self.show_page("Settings")
        else:
            self.show_page("Dashboard")

    def err(self, msg, parent=None):
        messagebox.showerror("Error", str(msg), parent=parent or self.winfo_toplevel())

    def info(self, msg, parent=None):
        messagebox.showinfo("Info", str(msg), parent=parent or self.winfo_toplevel())

    def dialog(self, title, w, h):
        d = ctk.CTkToplevel(self)
        d.title(title)
        top = self.winfo_toplevel()
        w = min(w, top.winfo_screenwidth() - 40)
        h = min(h, top.winfo_screenheight() - 80)
        x = top.winfo_rootx() + max((top.winfo_width() - w) // 2, 0)
        y = top.winfo_rooty() + max((top.winfo_height() - h) // 3, 0)
        d.geometry(f"{w}x{h}+{x}+{y}")
        d.transient(top)

        def grab():
            try:
                if d.winfo_exists():
                    d.grab_set()
                    d.focus_force()
            except tk.TclError:
                pass
        d.after(200, grab)
        d.bind("<Escape>", lambda e: d.destroy())
        return d

    @staticmethod
    def entry(parent, placeholder, width=260, default=""):
        e = ctk.CTkEntry(parent, placeholder_text=placeholder, width=width)
        if default != "":
            e.insert(0, str(default))
        e.pack(pady=5)
        return e

    @staticmethod
    def option(parent, values, default=None, width=260, command=None):
        if not values:
            raise ValueError("No options available")
        var = ctk.StringVar(value=default if default is not None else values[0])
        ctk.CTkOptionMenu(parent, values=values, variable=var, width=width, command=command).pack(pady=5)
        return var

    @staticmethod
    def action_button(d, text, command, color=None):
        ctk.CTkButton(d, text=text, command=command, **({"fg_color": color} if color else {})).pack(pady=15)
        d.bind("<Return>", lambda e: command())

    def selected(self, tree, msg="Please select a row first"):
        sel = tree.selection()
        if not sel:
            self.err(msg)
            return None
        return sel[0]

    def stat_cards(self, parent, specs, store, size=20):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=5)
        for title, color, key in specs:
            card = ctk.CTkFrame(row, fg_color=COLORS["card"], corner_radius=15, border_width=2, border_color=color)
            card.pack(side="left", fill="both", expand=True, padx=8)
            ctk.CTkLabel(card, text=title, text_color=COLORS["text_muted"]).pack(anchor="w", padx=15, pady=(10, 0))
            store[key] = ctk.CTkLabel(card, text="Rs. 0", font=(FONT, size, "bold"))
            store[key].pack(anchor="w", padx=15, pady=(0, 10))

    def refresh_current(self, pages):
        for p in pages:
            getattr(self, self.LOADERS[p])()

    def _photo_box(self, parent, filename, w=280, h=170):
        box = ctk.CTkFrame(parent, fg_color=COLORS["card"], width=w, height=h, corner_radius=10)
        box.pack(pady=6)
        box.pack_propagate(False)
        if filename:
            p = os.path.join(PHOTOS_DIR, os.path.basename(filename))
            if HAS_PIL and os.path.isfile(p):
                try:
                    img = Image.open(p)
                    img.load()
                    ratio = min((w - 12) / img.width, (h - 12) / img.height)
                    size = (max(1, int(img.width * ratio)), max(1, int(img.height * ratio)))
                    cimg = ctk.CTkImage(light_image=img, dark_image=img, size=size)
                    box._img_ref = cimg
                    ctk.CTkLabel(box, image=cimg, text="").place(relx=0.5, rely=0.5, anchor="center")
                    return
                except Exception:
                    logging.exception("Photo preview failed")
            ctk.CTkLabel(box, text="Photo attached\n(preview unavailable)",
                         text_color=COLORS["text_muted"]).place(relx=0.5, rely=0.5, anchor="center")
        else:
            ctk.CTkLabel(box, text="No bike photo attached",
                         text_color=COLORS["text_muted"]).place(relx=0.5, rely=0.5, anchor="center")

    def build_sidebar(self):
        sidebar = ctk.CTkFrame(self, fg_color=COLORS["sidebar"], width=230, corner_radius=0)
        sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        sidebar.grid_propagate(False)
        ctk.CTkLabel(sidebar, text="SRH", font=(FONT, 22, "bold"), fg_color="#353542", width=50, height=50,
                     corner_radius=25).pack(pady=(20, 4))
        ctk.CTkLabel(sidebar, text=f"User: {self.username}", font=(FONT, 12),
                     text_color=COLORS["text_muted"]).pack(pady=(0, 8))
        for text, page in self.PAGES:
            btn = ctk.CTkButton(sidebar, text=text, fg_color="transparent", anchor="w", font=(FONT, 14),
                                height=32, hover_color=COLORS["card_hover"],
                                command=lambda p=page: self.show_page(p))
            btn.pack(fill="x", padx=10, pady=1)
            self.nav_btns[page] = btn
        ctk.CTkButton(sidebar, text="🚪 Logout", fg_color="transparent", border_width=1,
                      border_color=COLORS["text_muted"], hover_color=COLORS["accent_pink"],
                      command=self.on_logout).pack(side="bottom", fill="x", padx=20, pady=16)

    def build_main_area(self):
        top_bar = ctk.CTkFrame(self, fg_color="transparent", height=60)
        top_bar.grid(row=0, column=1, sticky="ew", padx=20, pady=10)
        self.page_title = ctk.CTkLabel(top_bar, text="Dashboard", font=(FONT, 24, "bold"), text_color=COLORS["text"])
        self.page_title.pack(side="left")
        ctk.CTkLabel(top_bar, text=f"{today_str()}   v{APP_VERSION}", text_color=COLORS["text_muted"]).pack(side="right")
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=1, column=1, sticky="nsew", padx=20, pady=(0, 10))
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)
        for _, p in self.PAGES:
            self.pages[p] = ctk.CTkFrame(self.content, fg_color="transparent")
            self.pages[p].grid(row=0, column=0, sticky="nsew")
        self.build_dashboard_ui(); self.build_cashbook_ui(); self.build_bikes_ui(); self.build_cost_sheet_ui()
        self.build_customers_ui(); self.build_bills_ui(); self.build_staff_ui(); self.build_parts_ui()
        self.build_expenses_ui(); self.build_reports_ui(); self.build_audit_ui(); self.build_settings_ui()

    def show_page(self, name):
        if self.must_change and name != "Settings":
            return messagebox.showwarning("Blocked", "You must change the default password in Settings first.")
        self.page_title.configure(text={"CashBook": "Cash Book", "CostSheet": "Cost Sheet",
                                        "Bills": "Bills & Dues"}.get(name, name))
        for p, btn in self.nav_btns.items():
            btn.configure(fg_color=COLORS["accent_blue"] if p == name else "transparent")
        self.pages[name].tkraise()
        loader = self.LOADERS.get(name)
        if loader:
            getattr(self, loader)()

    # ================= DASHBOARD =================
    def build_dashboard_ui(self):
        pg = self.pages["Dashboard"]
        self.cash_cards, self.cards = {}, {}
        self.stat_cards(pg, [("Today Cash In", COLORS["accent_blue"], "in"),
                             ("Today Cash Out", COLORS["accent_orange"], "out"),
                             ("Today Closing Cash", COLORS["accent_green"], "closing")], self.cash_cards)
        self.stat_cards(pg, [("Total Revenue", COLORS["accent_blue"], "revenue"),
                             ("Gross Profit", COLORS["accent_green"], "gross"),
                             ("Total Due", COLORS["accent_pink"], "due")], self.cards)
        self.stat_cards(pg, [("Op Expenses", COLORS["accent_orange"], "op"),
                             ("Salary Paid", COLORS["accent_orange"], "salary"),
                             ("Net Profit", COLORS["accent_pink"], "net")], self.cards)
        self.top_debtors_lbl = ctk.CTkLabel(pg, text="Top Debtors: None", font=(FONT, 14, "bold"),
                                            text_color=COLORS["accent_orange"])
        self.top_debtors_lbl.pack(anchor="w", padx=15, pady=8)
        self.chart_frame = ctk.CTkFrame(pg, fg_color=COLORS["card"], corner_radius=15)
        self.chart_frame.pack(fill="both", expand=True, padx=8, pady=8)

    def refresh_dashboard(self):
        s = self.db.get_stats()
        pos = lambda v: COLORS["accent_green"] if v >= 0 else COLORS["accent_pink"]
        self.cash_cards["in"].configure(text=money(s["cash_in"]))
        self.cash_cards["out"].configure(text=money(s["cash_out"]))
        self.cash_cards["closing"].configure(text=money(s["cash_closing"]), text_color=pos(s["cash_closing"]))
        self.cards["revenue"].configure(text=money(s["revenue"]))
        self.cards["gross"].configure(text=money(s["gross"]), text_color=pos(s["gross"]))
        self.cards["due"].configure(text=money(s["total_due"]))
        self.cards["op"].configure(text=money(s["op_exp"]))
        self.cards["salary"].configure(text=money(s["salary"]))
        self.cards["net"].configure(text=money(s["net"]), text_color=pos(s["net"]))
        debtors = self.db.get_top_debtors()
        self.top_debtors_lbl.configure(text="Top Debtors: " + (
            ", ".join(f"{d['name']} ({money(d['total_due'])})" for d in debtors) if debtors else "None"))
        if self.chart_canvas_widget:
            self.chart_canvas_widget.destroy()
            self.chart_canvas_widget = None
        dates, sales, costs = self.db.get_last_7_days_data()
        fig = Figure(figsize=(8, 3), dpi=80, facecolor=COLORS["card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(COLORS["card"])
        x = list(range(len(dates)))
        ax.bar([i - 0.2 for i in x], sales, width=0.4, label="Sales", color=COLORS["accent_blue"])
        ax.bar([i + 0.2 for i in x], costs, width=0.4, label="Total Costs", color=COLORS["accent_pink"])
        ax.set_xticks(x)
        ax.set_xticklabels(dates, color=COLORS["text_muted"])
        ax.set_title("Last 7 days", color=COLORS["text_muted"], fontsize=10)
        ax.tick_params(colors=COLORS["text_muted"])
        ax.legend(facecolor=COLORS["card"], labelcolor=COLORS["text"], framealpha=0)
        for spine in ax.spines.values():
            spine.set_color(COLORS["card_hover"])
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.chart_canvas_widget = canvas.get_tk_widget()
        self.chart_canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        canvas.draw()

    # ================= CASH BOOK =================
    def build_cashbook_ui(self):
        pg = self.pages["CashBook"]
        bar = ctk.CTkFrame(pg, fg_color="transparent")
        bar.pack(fill="x", pady=(5, 0))
        ctk.CTkLabel(bar, text="Date (YYYY-MM-DD):").pack(side="left")
        ctk.CTkButton(bar, text="◀", width=32, command=lambda: self.shift_cb_day(-1)).pack(side="left", padx=(8, 2))
        self.cb_date = ctk.CTkEntry(bar, width=110)
        self.cb_date.insert(0, today_str())
        self.cb_date.pack(side="left", padx=2)
        self.cb_date.bind("<Return>", lambda e: self.load_cashbook())
        ctk.CTkButton(bar, text="▶", width=32, command=lambda: self.shift_cb_day(1)).pack(side="left", padx=(2, 8))
        ctk.CTkButton(bar, text="Load Day", width=80, command=self.load_cashbook).pack(side="left", padx=5)
        ctk.CTkButton(bar, text="➕ Manual Cash In", fg_color=COLORS["accent_green"],
                      command=lambda: self.open_manual_cash("In")).pack(side="left", padx=5)
        ctk.CTkButton(bar, text="➖ Manual Cash Out", fg_color=COLORS["accent_pink"],
                      command=lambda: self.open_manual_cash("Out")).pack(side="left", padx=5)
        bar2 = ctk.CTkFrame(pg, fg_color="transparent")
        bar2.pack(fill="x", pady=8)
        ctk.CTkButton(bar2, text="🔒 Close Day", fg_color=COLORS["accent_orange"], command=self.close_day).pack(side="left", padx=5)
        ctk.CTkButton(bar2, text="🔓 Re-open Last Day", fg_color="transparent", border_width=1,
                      command=self.reopen_day).pack(side="left", padx=5)
        ctk.CTkButton(bar2, text="📜 Past Closures", command=self.show_closures).pack(side="left", padx=5)
        ctk.CTkButton(bar2, text="🖨️ Print Report", command=self.print_cash_report).pack(side="left", padx=5)
        self.cb_cards = {}
        self.stat_cards(pg, [("Opening", COLORS["text_muted"], "open"), ("Cash In", COLORS["accent_green"], "in"),
                             ("Cash Out", COLORS["accent_pink"], "out"), ("Closing", COLORS["accent_blue"], "close")],
                        self.cb_cards, size=18)
        self.cb_status_lbl = ctk.CTkLabel(pg, text="", font=(FONT, 12, "bold"))
        self.cb_status_lbl.pack(anchor="w", padx=15)
        self.cb_tree = make_tree(pg, ("Type", "Category", "Amount", "Method", "Note"),
                                 widths={"Type": 70, "Category": 170, "Amount": 130, "Method": 100, "Note": 380})
        self.cb_tree.tag_configure("green", foreground=COLORS["accent_green"])
        self.cb_tree.tag_configure("red", foreground=COLORS["accent_pink"])

    def _cb_day(self):
        return validate_date(self.cb_date.get().strip())

    def shift_cb_day(self, delta):
        try:
            d = datetime.strptime(self._cb_day(), "%Y-%m-%d") + timedelta(days=delta)
        except ValueError as ex:
            return self.err(ex)
        self.cb_date.delete(0, "end")
        self.cb_date.insert(0, d.strftime("%Y-%m-%d"))
        self.load_cashbook()

    def load_cashbook(self):
        try:
            d = self._cb_day()
            s = self.db.get_cash_summary(d)
            moves = self.db.get_cash_movements(d)
        except ValueError as ex:
            return self.err(ex)
        self.cb_cards["open"].configure(text=money(s["opening"]))
        self.cb_cards["in"].configure(text=money(s["in"]), text_color=COLORS["accent_green"])
        self.cb_cards["out"].configure(text=money(s["out"]), text_color=COLORS["accent_pink"])
        self.cb_cards["close"].configure(text=money(s["closing"]), text_color=COLORS["accent_blue"])
        self.cb_status_lbl.configure(
            text=f"🔒 CLOSED. Note: {s['closure_note'] or 'None'}" if s["is_closed"] else "🔓 OPEN FOR ENTRIES",
            text_color=COLORS["accent_orange"] if s["is_closed"] else COLORS["accent_green"])
        clear_tree(self.cb_tree)
        for m in moves:
            self.cb_tree.insert("", "end", values=(m["type"], txt(m["category"]), money(m["amount"]),
                                                   txt(m["method"]), txt(m["note"])),
                                tags=("green" if m["type"] == "In" else "red",))

    def open_manual_cash(self, c_type):
        d = self.dialog(f"Manual Cash {c_type}", 320, 260)
        ctk.CTkLabel(d, text=f"Manual Cash {c_type}  ({self.cb_date.get().strip()})",
                     font=(FONT, 15, "bold")).pack(pady=12)
        e_amt = self.entry(d, "Amount (Rs)")
        e_note = self.entry(d, "Note / Reason (required)")

        def save():
            try:
                amt = parse_amount(e_amt.get())
                note = e_note.get().strip()
                if not note:
                    raise ValueError("Please write a note / reason")
                self.db.add_cash_entry(self._cb_day(), c_type, "Manual", amt, "Cash", note)
            except Exception as ex:
                return self.err(ex, d)
            d.destroy()
            self.load_cashbook()
        self.action_button(d, "Save", save)

    def close_day(self):
        try:
            day = self._cb_day()
        except ValueError as ex:
            return self.err(ex)
        dial = self.dialog("Close Day", 340, 230)
        ctk.CTkLabel(dial, text=f"Close cash book for {day}", font=(FONT, 14, "bold")).pack(pady=12)
        e_note = self.entry(dial, "Any mismatch notes?", 280)

        def save():
            if not messagebox.askyesno("Confirm", f"Close {day}?\nNo more cash entries will be allowed for this date.",
                                       parent=dial):
                return
            try:
                self.db.close_day(day, e_note.get(), self.username)
            except Exception as ex:
                return self.err(ex, dial)
            dial.destroy()
            self.load_cashbook()
            self.info("Day closed successfully.")
        self.action_button(dial, "Close Day", save, COLORS["accent_orange"])

    def reopen_day(self):
        if not messagebox.askyesno("Confirm", "Re-open the most recently closed day?"):
            return
        try:
            d = self.db.reopen_last_closure()
        except Exception as ex:
            return self.err(ex)
        self.load_cashbook()
        self.info(f"{d} has been re-opened.")

    def show_closures(self):
        d = self.dialog("Past Closures", 820, 440)
        tree = make_tree(d, ("Date", "Opening", "In", "Out", "Closing", "By", "Note"),
                         widths={"Date": 110, "Opening": 120, "In": 110, "Out": 110,
                                 "Closing": 120, "By": 100, "Note": 220})
        for c in self.db.get_previous_closures():
            tree.insert("", "end", values=(c["date"], money(c["opening"]), money(c["cash_in"]),
                                           money(c["cash_out"]), money(c["closing"]),
                                           txt(c["closed_by"]), txt(c["note"])))

    def print_cash_report(self):
        try:
            day = self._cb_day()
            s = self.db.get_cash_summary(day)
            moves = self.db.get_cash_movements(day)
        except ValueError as ex:
            return self.err(ex)
        rows = "".join(
            f"<tr><td>{escape_html(m['type'])}</td><td>{escape_html(m['category'])}</td><td>{escape_html(m['note'])}</td>"
            f"<td style='color:{'green' if m['type'] == 'In' else 'red'}'>{money(m['amount'])}</td></tr>" for m in moves)
        body = (f"<h2>Cash Report - {escape_html(CONFIG.get('shop_name'))}</h2>"
                f"<p><b>Date:</b> {escape_html(day)} | <b>Status:</b> {'CLOSED' if s['is_closed'] else 'OPEN'}</p>"
                f"<p>Opening: {money(s['opening'])} | In: {money(s['in'])} | Out: {money(s['out'])} | "
                f"<b>Closing: {money(s['closing'])}</b></p>"
                f"<table><tr><th>Type</th><th>Category</th><th>Note</th><th>Amount</th></tr>"
                f"{rows or '<tr><td colspan=4>No entries on this date</td></tr>'}</table>"
                f"<br><br><p>Verified By: ____________________</p>")
        open_html("cash_report", day, body, "Cash Report")

    # ================= COST SHEET =================
    def build_cost_sheet_ui(self):
        pg = self.pages["CostSheet"]
        bar = ctk.CTkFrame(pg, fg_color="transparent")
        bar.pack(fill="x", pady=10)
        ctk.CTkLabel(bar, text="Filter:").pack(side="left")
        self.cs_filter = ctk.CTkOptionMenu(bar, values=["All", "In Stock", "Sold"], width=110,
                                           command=lambda e: self.load_cost_sheet())
        self.cs_filter.pack(side="left", padx=5)
        self.cs_search = ctk.CTkEntry(bar, placeholder_text="Search Bike No / Model", width=220)
        self.cs_search.pack(side="left", padx=10)
        self.cs_search.bind("<KeyRelease>", lambda e: self.load_cost_sheet())
        ctk.CTkButton(bar, text="➕ Add Labour", fg_color=COLORS["accent_orange"],
                      command=self.open_add_labour_dialog).pack(side="right", padx=5)
        ctk.CTkButton(bar, text="📥 Export CSV", fg_color=COLORS["accent_green"],
                      command=self.export_cost_sheet_csv).pack(side="right", padx=5)
        ctk.CTkLabel(pg, text="Double-click a row for full details & documents",
                     text_color=COLORS["text_muted"]).pack(side="bottom", anchor="w")
        self.cs_tree = make_tree(pg, ("Bike No", "Model", "Bluebook Exp", "Buy", "Parts", "Labour",
                                      "True Cost", "Sell", "Profit", "Margin %"),
                                 widths={"Bike No": 150, "Model": 160, "Bluebook Exp": 120, "Buy": 110,
                                         "Parts": 100, "Labour": 100, "True Cost": 120, "Sell": 110,
                                         "Profit": 110, "Margin %": 90})
        self.cs_tree.tag_configure("profit", foreground=COLORS["accent_green"])
        self.cs_tree.tag_configure("loss", foreground=COLORS["accent_pink"])
        self.cs_tree.bind("<Double-1>", self.open_cost_sheet_details)
        self._cs_data = {}

    def load_cost_sheet(self):
        clear_tree(self.cs_tree)
        self._cs_data = {}
        q, flt = self.cs_search.get().strip().lower(), self.cs_filter.get()
        for i, b in enumerate(self.db.get_bike_cost_sheet()):
            if flt != "All" and b["status"] != flt:
                continue
            if q and q not in b["bike_no"].lower() and q not in b["model"].lower():
                continue
            iid = f"b{i}"
            self._cs_data[iid] = b
            self.cs_tree.insert("", "end", iid=iid, tags=("profit" if b["profit"] >= 0 else "loss",), values=(
                b["bike_no"], b["model"], b["bluebook_expiry"] or "-", money(b["buy"]), money(b["parts"]),
                money(b["labour"]), money(b["true_cost"]), money(b["sell"]), money(b["profit"]), f"{b['margin']:.1f}%"))

    def open_add_labour_dialog(self):
        bikes = self.db.get_stock_bikes()
        if not bikes:
            return self.err("No bikes in stock")
        d = self.dialog("Add Labour", 340, 400)
        ctk.CTkLabel(d, text="Add Repair / Labour Cost", font=(FONT, 15, "bold")).pack(pady=8)
        b_var = self.option(d, [b["bike_no"] for b in bikes], width=260)
        e_desc = self.entry(d, "Description (e.g. Engine Repair)")
        e_mech = self.entry(d, "Mechanic Name")
        e_amt = self.entry(d, "Amount (Rs)")
        cash_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(d, text="Paid in Cash today?", variable=cash_var).pack(pady=10)

        def save():
            try:
                self.db.add_labour(b_var.get(), today_str(), e_desc.get(), e_mech.get(),
                                   parse_amount(e_amt.get()), cash_var.get())
            except Exception as ex:
                return self.err(ex, d)
            d.destroy()
            self.refresh_current(("CostSheet", "Bikes"))
            self.info("Labour added")
        self.action_button(d, "Save Labour", save, COLORS["accent_orange"])

    def open_cost_sheet_details(self, event=None):
        sel = self.cs_tree.selection()
        if not sel:
            return
        b = self._cs_data.get(sel[0])
        if not b:
            return
        bike_no = b["bike_no"]
        bike_info, parts, labour, bill = self.db.get_bike_details(bike_no)
        d = self.dialog(f"Cost Sheet & Documents - {bike_no}", 700, 740)
        ctk.CTkLabel(d, text=f"Bike: {bike_no}  ({b['model']})", font=(FONT, 18, "bold")).pack(pady=(10, 2))
        if bike_info:
            ctk.CTkLabel(d, text=f"Engine: {bike_info['engine_no'] or 'N/A'} | Chassis: {bike_info['chassis_no'] or 'N/A'} "
                                 f"| Bluebook Exp: {bike_info['bluebook_expiry'] or 'N/A'}",
                         font=(FONT, 12), text_color=COLORS["text_muted"]).pack(pady=2)
            self._photo_box(d, bike_info["photo_path"], w=280, h=150)
        if bill:
            ctk.CTkLabel(d, text=f"Sold to: {txt(bill['cust_name'])} ({txt(bill['cust_phone']) or 'N/A'}) | "
                                 f"Bill: {bill['bill_no']} | Total: {money(bill['total'])}",
                         text_color=COLORS["accent_green"], font=(FONT, 12)).pack(pady=3)
        ctk.CTkLabel(d, text="Parts Used", font=(FONT, 14, "bold")).pack(pady=(8, 3))
        p_tree = make_tree(d, ("Part", "Qty", "Rate", "Total"), height=4, expand=False)
        for p in parts:
            p_tree.insert("", "end", values=(p["name"], p["qty"], money(p["unit_cost_at_time"]),
                                             money(p["qty"] * p["unit_cost_at_time"])))
        ctk.CTkLabel(d, text="Labour Jobs", font=(FONT, 14, "bold")).pack(pady=(8, 3))
        l_tree = make_tree(d, ("Date", "Description", "Mechanic", "Amount"), height=4, expand=False)
        for l in labour:
            l_tree.insert("", "end", values=(l["labour_date"], l["description"], l["mechanic"], money(l["amount"])))
        ctk.CTkLabel(d, text=f"True Cost: {money(b['true_cost'])}   |   Sell: {money(b['sell'])}   |   "
                             f"Profit: {money(b['profit'])} ({b['margin']:.1f}%)", font=(FONT, 13, "bold"),
                     text_color=COLORS["accent_green"] if b["profit"] >= 0 else COLORS["accent_pink"]).pack(pady=10)
        ctk.CTkButton(d, text="🖨️ Print Cost Sheet", command=lambda: self.print_cost_sheet(bike_no)).pack(pady=5)

    def print_cost_sheet(self, bike_no):
        _, parts, labour, bill = self.db.get_bike_details(bike_no)
        b = next((x for x in self.db.get_bike_cost_sheet() if x["bike_no"] == bike_no), None)
        if not b:
            return self.err("Bike not found")
        uri = photo_data_uri(b["photo_path"])
        photo_html = f"<div style='text-align:center;margin:15px 0'><img class='photo' src='{uri}'></div>" if uri else ""
        p_rows = "".join(f"<tr><td>{escape_html(p['name'])}</td><td>{p['qty']}</td><td>{money(p['unit_cost_at_time'])}</td>"
                         f"<td>{money(p['qty'] * p['unit_cost_at_time'])}</td></tr>" for p in parts) \
                 or "<tr><td colspan='4'>No parts used</td></tr>"
        l_rows = "".join(f"<tr><td>{escape_html(l['labour_date'])}</td><td>{escape_html(l['description'])}</td>"
                         f"<td>{escape_html(l['mechanic'])}</td><td>{money(l['amount'])}</td></tr>" for l in labour) \
                 or "<tr><td colspan='4'>No labour jobs</td></tr>"
        color = "green" if b["profit"] >= 0 else "red"
        body = (f"<h2>Bike Cost Sheet & Documents - {escape_html(CONFIG.get('shop_name'))}</h2>"
                f"<p><b>Bike:</b> {escape_html(bike_no)} ({escape_html(b['model'])}) | <b>Status:</b> {escape_html(b['status'])}</p>"
                f"<p><b>Engine No:</b> {escape_html(b['engine_no'] or 'N/A')} | <b>Chassis No:</b> {escape_html(b['chassis_no'] or 'N/A')} "
                f"| <b>Bluebook Expiry:</b> {escape_html(b['bluebook_expiry'] or 'N/A')}</p>"
                f"<p><b>Buy Price:</b> {money(b['buy'])} | <b>Sell Price:</b> {money(b['sell'])}</p>{photo_html}<hr>"
                f"<h3>Parts Used</h3><table><tr><th>Part</th><th>Qty</th><th>Rate</th><th>Total</th></tr>{p_rows}</table>"
                f"<h3>Labour Jobs</h3><table><tr><th>Date</th><th>Description</th><th>Mechanic</th><th>Amount</th></tr>{l_rows}</table>"
                f"<div class='total-box'><p>True Total Cost: {money(b['true_cost'])}</p><p>Selling Price: {money(b['sell'])}</p>"
                f"<p style='color:{color}'><b>Net Profit/Loss: {money(b['profit'])} ({b['margin']:.1f}%)</b></p></div>"
                + (f"<p>Sold to: {escape_html(bill['cust_name'])} on {escape_html(bill['created_at'][:10])}</p>" if bill else ""))
        open_html("cost_sheet", bike_no, body, "Cost Sheet")

    def export_cost_sheet_csv(self):
        rows = list(self._cs_data.values())
        if not rows:
            return self.info("No data to export")
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")],
                                            initialfile="cost_sheet.csv")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["Bike No", "Model", "Engine No", "Chassis No", "Bluebook Expiry", "Status",
                            "Buy Price", "Parts Cost", "Labour Cost", "True Cost", "Sell Price", "Profit", "Margin %"])
                for b in rows:
                    w.writerow([sanitize_csv(b["bike_no"]), sanitize_csv(b["model"]), sanitize_csv(b["engine_no"]),
                                sanitize_csv(b["chassis_no"]), sanitize_csv(b["bluebook_expiry"]), b["status"],
                                b["buy"], b["parts"], b["labour"], b["true_cost"], b["sell"], b["profit"],
                                f"{b['margin']:.2f}"])
        except OSError as ex:
            return self.err(f"Could not save file: {ex}")
        self.info("Exported")

    # ================= CUSTOMERS =================
    def build_customers_ui(self):
        pg = self.pages["Customers"]
        bar = ctk.CTkFrame(pg, fg_color="transparent")
        bar.pack(fill="x", pady=10)
        ctk.CTkButton(bar, text="➕ Add Customer", command=self.open_add_customer_dialog).pack(side="left", padx=5)
        self.cust_search = ctk.CTkEntry(bar, placeholder_text="Search Name / Phone / ID...", width=260)
        self.cust_search.pack(side="left", padx=15)
        self.cust_search.bind("<KeyRelease>", lambda e: self.load_customers())
        btn_bar = ctk.CTkFrame(pg, fg_color="transparent")
        btn_bar.pack(side="bottom", fill="x", pady=5)
        ctk.CTkButton(btn_bar, text="📜 View Ledger", fg_color=COLORS["accent_blue"], command=self.open_ledger).pack(side="left", padx=5)
        ctk.CTkButton(btn_bar, text="📩 Copy Due Reminder", fg_color=COLORS["accent_orange"], command=self.copy_reminder).pack(side="left", padx=5)
        ctk.CTkButton(btn_bar, text="❌ Delete", fg_color=COLORS["accent_pink"], command=self.delete_customer).pack(side="left", padx=5)
        self.cust_tree = make_tree(pg, ("Name", "Phone", "Citizenship/ID", "Bills", "Total Bought", "Total Paid", "Total Due"),
                                   widths={"Name": 180, "Phone": 130, "Citizenship/ID": 150, "Bills": 70,
                                           "Total Bought": 130, "Total Paid": 130, "Total Due": 130})

    def load_customers(self):
        clear_tree(self.cust_tree)
        q = self.cust_search.get().strip().lower()
        for c in self.db.get_customers():
            blob = f"{c['name'] or ''} {c['phone'] or ''} {c['citizenship_no'] or ''}".lower()
            if q and q not in blob:
                continue
            self.cust_tree.insert("", "end", iid=str(c["id"]), values=(
                c["name"], txt(c["phone"]), txt(c["citizenship_no"]) or "-", c["bill_count"],
                money(c["total_bought"]), money(c["total_paid"]), money(c["total_due"])))

    def open_add_customer_dialog(self):
        d = self.dialog("Add Customer", 340, 360)
        ctk.CTkLabel(d, text="New Customer & Documents", font=(FONT, 15, "bold")).pack(pady=8)
        e_name = self.entry(d, "Full Name", 260)
        e_phone = self.entry(d, "Phone (family can share)", 260)
        e_addr = self.entry(d, "Address", 260)
        e_cit = self.entry(d, "Citizenship / License / ID No", 260)

        def save():
            try:
                _, actual, is_new = self.db.get_or_create_customer(e_name.get(), e_phone.get(), e_addr.get(), e_cit.get())
            except Exception as ex:
                return self.err(ex, d)
            if not is_new:
                messagebox.showinfo("Already exists", f"A customer with this phone/name already exists ({actual}).\n"
                                                      "No duplicate was created.", parent=d)
            d.destroy()
            self.load_customers()
        self.action_button(d, "Save", save)

    def delete_customer(self):
        iid = self.selected(self.cust_tree, "Select a customer")
        if iid and messagebox.askyesno("Confirm", "Delete this customer?"):
            try:
                self.db.delete_customer(int(iid))
            except Exception as ex:
                return self.err(ex)
            self.load_customers()

    def open_ledger(self):
        iid = self.selected(self.cust_tree, "Select a customer")
        if not iid:
            return
        cust = self.db.get_customer(int(iid))
        bills, payments = self.db.get_customer_ledger(int(iid))
        d = self.dialog(f"Ledger - {cust['name']}", 700, 660)
        ctk.CTkLabel(d, text="Bills (double-click to print invoice)", font=(FONT, 15, "bold")).pack(pady=(10, 3))
        b_tree = make_tree(d, ("Bill", "Bike", "Total", "Due", "Date", "State"), height=7, expand=False)
        b_tree.tag_configure("void", foreground=COLORS["text_muted"])
        for b in bills:
            b_tree.insert("", "end", iid=str(b["id"]), tags=("void",) if b["voided"] else (), values=(
                b["bill_no"], b["bike_no"], money(b["total"]), money(b["due"]), b["created_at"][:10],
                "VOIDED" if b["voided"] else b["status"]))
        b_tree.bind("<Double-1>", lambda e: b_tree.selection() and self.print_receipt(int(b_tree.selection()[0])))
        ctk.CTkLabel(d, text="Payments", font=(FONT, 15, "bold")).pack(pady=(12, 3))
        p_tree = make_tree(d, ("Bill", "Amount", "Method", "Date"), height=7, expand=False)
        for p in payments:
            p_tree.insert("", "end", values=(p["b_no"], money(p["amount"]), txt(p["method"]), p["created_at"][:10]))

    def copy_reminder(self):
        iid = self.selected(self.cust_tree, "Select a customer")
        if not iid:
            return
        cust = self.db.get_customer(int(iid))
        bills, _ = self.db.get_customer_ledger(int(iid))
        pending = [b for b in bills if b["due"] > 0 and not b["voided"]]
        if not pending:
            return self.info("No due for this customer")
        total = sum(b["due"] for b in pending)
        lines = "\n".join(f"- {b['bill_no']}: {money(b['due'])}" for b in pending)
        msg = (f"Namaste {cust['name']} ji,\n{CONFIG.get('shop_name')} ma tapaiko total baki {money(total)} xa.\n"
               f"Kripaya chhittai bhuktani garnuhola.\nBills:\n{lines}\n"
               + (f"Contact: {CONFIG.get('shop_phone')}\n" if CONFIG.get("shop_phone") else "") + "Dhanyabad!")
        self.clipboard_clear()
        self.clipboard_append(msg)
        self.info("Reminder copied to clipboard!")

    # ================= BIKES =================
    def build_bikes_ui(self):
        pg = self.pages["Bikes"]
        bar = ctk.CTkFrame(pg, fg_color="transparent")
        bar.pack(fill="x", pady=10)
        ctk.CTkButton(bar, text="➕ Add Bike", command=self.open_add_bike_dialog).pack(side="left", padx=5)
        ctk.CTkButton(bar, text="📄 Bluebook / Photo", fg_color=COLORS["accent_blue"],
                      command=self.open_bike_docs_dialog).pack(side="left", padx=5)
        ctk.CTkButton(bar, text="🔧 Add Labour", fg_color=COLORS["accent_orange"],
                      command=self.open_add_labour_dialog).pack(side="left", padx=5)
        ctk.CTkButton(bar, text="❌ Delete Selected", fg_color=COLORS["accent_pink"],
                      command=self.delete_bike).pack(side="left", padx=5)
        ctk.CTkLabel(pg, text="Orange = bluebook expiring within 30 days / expired. Double-click for documents.",
                     text_color=COLORS["text_muted"]).pack(side="bottom", anchor="w")
        self.bike_tree = make_tree(pg, ("Bike No", "Model", "Bluebook Exp", "Buy Price", "Sell Price", "Status"),
                                   widths={"Bike No": 160, "Model": 180, "Bluebook Exp": 130,
                                           "Buy Price": 130, "Sell Price": 130, "Status": 110})
        self.bike_tree.tag_configure("sold", foreground=COLORS["text_muted"])
        self.bike_tree.tag_configure("expwarn", foreground=COLORS["accent_orange"])
        self.bike_tree.bind("<Double-1>", lambda e: self.open_bike_docs_dialog())

    def load_bikes(self):
        clear_tree(self.bike_tree)
        for b in self.db.get_bikes():
            bb = b["bluebook_expiry"] or ""
            tags = ()
            if b["status"] == "Sold":
                tags = ("sold",)
            elif bb:
                try:
                    if datetime.strptime(bb, "%Y-%m-%d") <= datetime.now() + timedelta(days=30):
                        tags = ("expwarn",)
                except ValueError:
                    pass
            self.bike_tree.insert("", "end", iid=str(b["id"]), tags=tags, values=(
                b["bike_no"], txt(b["model"]), bb or "-", money(b["buy_price"]), money(b["sell_price"]), b["status"]))

    def open_add_bike_dialog(self):
        d = self.dialog("Add Bike", 360, 600)
        ctk.CTkLabel(d, text="Add Bike, Bluebook & Photo", font=(FONT, 15, "bold")).pack(pady=8)
        e_no = self.entry(d, "Bike Number (e.g. BA 90 PA 1234)", 280)
        e_mod = self.entry(d, "Model (e.g. Pulsar 220F)", 280)
        e_eng = self.entry(d, "Engine No (optional)", 280)
        e_chs = self.entry(d, "Chassis No (optional)", 280)
        e_bb = self.entry(d, "Bluebook Expiry YYYY-MM-DD (optional)", 280)
        e_buy = self.entry(d, "Buy Price (Rs)", 280)
        e_sell = self.entry(d, "Target Sell Price (Rs)", 280)
        ctk.CTkLabel(d, text="Purchase paid by:").pack()
        m_var = self.option(d, PAYMENT_METHODS, "Cash", 280)
        picked = {"path": ""}
        p_lbl = ctk.CTkLabel(d, text="No photo selected", font=(FONT, 11), text_color=COLORS["text_muted"])
        p_lbl.pack(pady=2)

        def pick():
            p = filedialog.askopenfilename(title="Select Bike Photo",
                                           filetypes=[("Images", "*.jpg *.jpeg *.png *.webp")], parent=d)
            if p:
                picked["path"] = p
                p_lbl.configure(text=os.path.basename(p), text_color=COLORS["accent_green"])
        ctk.CTkButton(d, text="📷 Choose Bike Photo", fg_color=COLORS["card_hover"], height=28, command=pick).pack(pady=4)

        def save():
            photo = ""
            try:
                bno = re.sub(r"\s+", " ", e_no.get().strip().upper())
                if not bno:
                    raise ValueError("Bike number is required")
                buy = parse_amount(e_buy.get(), allow_zero=True, label="Buy price")
                sell = parse_amount(e_sell.get(), allow_zero=True, label="Sell price")
                if picked["path"]:
                    photo = save_bike_photo(picked["path"], bno)
                try:
                    self.db.add_bike(bno, e_mod.get(), buy, sell, m_var.get(),
                                     e_eng.get(), e_chs.get(), e_bb.get(), photo)
                except Exception:
                    remove_photo(photo)
                    raise
            except Exception as ex:
                return self.err(ex, d)
            d.destroy()
            self.load_bikes()
        self.action_button(d, "Save Bike", save)

    def open_bike_docs_dialog(self):
        iid = self.selected(self.bike_tree, "Select a bike to view/update documents")
        if not iid:
            return
        bike_row = next((b for b in self.db.get_bikes() if b["id"] == int(iid)), None)
        if not bike_row:
            return self.err("Bike not found")
        bike_no = bike_row["bike_no"]
        d = self.dialog(f"Bluebook & Photo - {bike_no}", 380, 580)
        ctk.CTkLabel(d, text=f"{bike_no} ({bike_row['model']})", font=(FONT, 16, "bold")).pack(pady=(10, 2))
        self._photo_box(d, bike_row["photo_path"], w=280, h=150)
        e_eng = self.entry(d, "Engine No", 280, bike_row["engine_no"] or "")
        e_chs = self.entry(d, "Chassis No", 280, bike_row["chassis_no"] or "")
        e_bb = self.entry(d, "Bluebook Expiry (YYYY-MM-DD)", 280, bike_row["bluebook_expiry"] or "")
        picked = {"path": ""}
        p_lbl = ctk.CTkLabel(d, text="Keep existing photo", font=(FONT, 11), text_color=COLORS["text_muted"])
        p_lbl.pack(pady=2)

        def pick():
            p = filedialog.askopenfilename(title="Select New Bike Photo",
                                           filetypes=[("Images", "*.jpg *.jpeg *.png *.webp")], parent=d)
            if p:
                picked["path"] = p
                p_lbl.configure(text=os.path.basename(p), text_color=COLORS["accent_green"])
        ctk.CTkButton(d, text="📷 Replace Photo", fg_color=COLORS["card_hover"], height=28, command=pick).pack(pady=4)

        def save():
            new_photo = ""
            try:
                if picked["path"]:
                    new_photo = save_bike_photo(picked["path"], bike_no)
                old_photo = self.db.update_bike_docs(bike_no, e_eng.get(), e_chs.get(), e_bb.get(), new_photo)
            except Exception as ex:
                remove_photo(new_photo)
                return self.err(ex, d)
            if new_photo and old_photo:
                remove_photo(old_photo)
            d.destroy()
            self.refresh_current(("Bikes", "CostSheet"))
            self.info("Bluebook & document details saved.")
        self.action_button(d, "Save Details", save, COLORS["accent_blue"])

    def delete_bike(self):
        iid = self.selected(self.bike_tree, "Select a bike")
        if iid and messagebox.askyesno("Confirm", "Delete this bike?\n(Cash purchase amount will be reversed in the cash book.)"):
            try:
                photo = self.db.delete_bike(int(iid))
            except Exception as ex:
                return self.err(ex)
            remove_photo(photo)
            self.refresh_current(("Bikes", "CostSheet"))

    # ================= BILLS =================
    def build_bills_ui(self):
        pg = self.pages["Bills"]
        bar = ctk.CTkFrame(pg, fg_color="transparent")
        bar.pack(fill="x", pady=(10, 0))
        ctk.CTkButton(bar, text="➕ Create Bill", command=self.open_new_bill_dialog).pack(side="left", padx=5)
        ctk.CTkButton(bar, text="💵 Collect Due", fg_color=COLORS["accent_green"],
                      command=self.open_collect_due_dialog).pack(side="left", padx=5)
        ctk.CTkButton(bar, text="✏️ Edit Bill", fg_color=COLORS["accent_blue"],
                      command=self.open_edit_bill_dialog).pack(side="left", padx=5)
        ctk.CTkButton(bar, text="🚫 Void Bill", fg_color=COLORS["accent_pink"],
                      command=self.open_void_bill_dialog).pack(side="left", padx=5)
        ctk.CTkButton(bar, text="🖨️ Print Invoice", command=self.open_print_receipt).pack(side="left", padx=5)
        bar2 = ctk.CTkFrame(pg, fg_color="transparent")
        bar2.pack(fill="x", pady=8)
        ctk.CTkLabel(bar2, text="Show:").pack(side="left")
        self.bill_filter = ctk.CTkOptionMenu(bar2, values=["Active", "Voided", "All"], width=110,
                                             command=lambda e: self.load_bills())
        self.bill_filter.pack(side="left", padx=5)
        self.bill_search = ctk.CTkEntry(bar2, placeholder_text="Search Bill No / Customer / Bike...", width=280)
        self.bill_search.pack(side="right", padx=5)
        self.bill_search.bind("<KeyRelease>", lambda e: self.load_bills())
        self.bill_tree = make_tree(pg, ("Bill No", "Customer", "Phone", "Bike", "Total", "Due", "Status"),
                                   widths={"Bill No": 165, "Customer": 170, "Phone": 125, "Bike": 140,
                                           "Total": 120, "Due": 120, "Status": 100})
        self.bill_tree.tag_configure("due", foreground=COLORS["accent_orange"])
        self.bill_tree.tag_configure("paid", foreground=COLORS["accent_green"])
        self.bill_tree.tag_configure("void", foreground=COLORS["text_muted"])
        self.bill_tree.bind("<Double-1>", lambda e: self.open_print_receipt())

    def load_bills(self):
        clear_tree(self.bill_tree)
        q, flt = self.bill_search.get().strip().lower(), self.bill_filter.get()
        for b in self.db.get_bills():
            if flt == "Active" and b["voided"]:
                continue
            if flt == "Voided" and not b["voided"]:
                continue
            blob = f"{b['bill_no']} {txt(b['cust_name'])} {txt(b['cust_phone'])} {txt(b['bike_no'])}".lower()
            if q and q not in blob:
                continue
            tags = ("void",) if b["voided"] else (("due",) if b["due"] > 0 else ("paid",))
            self.bill_tree.insert("", "end", iid=str(b["id"]), tags=tags, values=(
                b["bill_no"], txt(b["cust_name"]), txt(b["cust_phone"]), txt(b["bike_no"]),
                money(b["total"]), money(b["due"]), "Voided" if b["voided"] else b["status"]))

    def open_new_bill_dialog(self):
        bikes = self.db.get_stock_bikes()
        if not bikes:
            return self.err("No bikes in stock")
        customers = self.db.get_customers()
        d = self.dialog("Create Bill", 430, 700)
        b_dict = {f"{b['bike_no']} - {txt(b['model'])} (Rs. {b['sell_price']:,.0f})": b for b in bikes}
        c_dict = {f"{c['name']} ({c['phone'] or 'no phone'}) - #{c['id']}": c["id"] for c in customers}
        ctk.CTkLabel(d, text="1. Select Bike", font=(FONT, 12, "bold")).pack(pady=(8, 0))
        e_total = ctk.CTkEntry(d, placeholder_text="Final Selling Total (Rs)", width=330)

        def on_bike(choice):
            e_total.delete(0, "end")
            sp = b_dict[choice]["sell_price"]
            if sp:
                e_total.insert(0, f"{sp:g}")
        b_var = self.option(d, list(b_dict.keys()), width=330, command=on_bike)
        ctk.CTkLabel(d, text="2. Select Existing Customer", font=(FONT, 12, "bold")).pack(pady=(6, 0))
        c_var = ctk.StringVar(value=list(c_dict.keys())[0] if c_dict else "No customers yet")
        c_menu = ctk.CTkOptionMenu(d, values=list(c_dict.keys()) if c_dict else ["No customers yet"],
                                   variable=c_var, width=330)
        c_menu.pack(pady=5)
        ctk.CTkLabel(d, text="--- OR Quick Add New Customer ---", text_color=COLORS["text_muted"]).pack(pady=2)
        n_name = self.entry(d, "New Customer Name", 330)
        n_phone = self.entry(d, "Phone", 330)
        n_cit = self.entry(d, "Citizenship / ID No (optional)", 330)

        def add_inline():
            try:
                cid, actual, is_new = self.db.get_or_create_customer(n_name.get(), n_phone.get(), "", n_cit.get())
                if not is_new:
                    messagebox.showinfo("Existing customer", f"Using existing customer: {actual}", parent=d)
                key = f"{actual} ({re.sub(r'[\\s\\-]', '', n_phone.get()) or 'no phone'}) - #{cid}"
                c_dict[key] = cid
                c_menu.configure(values=list(c_dict.keys()))
                c_var.set(key)
                n_name.delete(0, "end"); n_phone.delete(0, "end"); n_cit.delete(0, "end")
            except Exception as ex:
                return self.err(ex, d)
        ctk.CTkButton(d, text="Add & Select Customer", height=28, command=add_inline).pack(pady=4)
        ctk.CTkLabel(d, text="3. Billing Details", font=(FONT, 12, "bold")).pack(pady=(6, 0))
        e_total.pack(pady=5)
        on_bike(b_var.get())
        e_adv = self.entry(d, "Advance / Paid Amount (0 if unpaid)", 330)
        ctk.CTkLabel(d, text="Payment Method:").pack()
        m_var = self.option(d, PAYMENT_METHODS, "Cash", 330)

        def save():
            try:
                total = parse_amount(e_total.get(), label="Total")
                adv = parse_amount(e_adv.get() or "0", allow_zero=True, label="Advance")
                if n_name.get().strip():
                    cust_id, actual, is_new = self.db.get_or_create_customer(n_name.get(), n_phone.get(), "", n_cit.get())
                    if not is_new:
                        messagebox.showinfo("Existing customer", f"Using existing customer: {actual}", parent=d)
                elif c_var.get() in c_dict:
                    cust_id = c_dict[c_var.get()]
                else:
                    raise ValueError("Please select a customer or enter a new customer name.")
                bill_id, bill_no = self.db.create_bill(b_dict[b_var.get()]["bike_no"], cust_id, total, adv, m_var.get())
            except Exception as ex:
                return self.err(ex, d)
            d.destroy()
            self.refresh_current(("Bills", "Bikes", "Customers"))
            if messagebox.askyesno("Bill created", f"Bill {bill_no} created.\nPrint receipt now?"):
                self.print_receipt(bill_id)
        self.action_button(d, "Create & Save Bill", save, COLORS["accent_blue"])

    def open_edit_bill_dialog(self):
        iid = self.selected(self.bill_tree, "Select a bill to edit")
        if not iid:
            return
        bill = self.db.get_bill(int(iid))
        if not bill:
            return self.err("Bill not found")
        if bill["voided"]:
            return self.err("A voided bill cannot be edited.")
        pays = self.db.get_bill_payments(bill["id"])
        can_amounts = len(pays) <= 1
        customers = self.db.get_customers()
        if not customers:
            return self.err("No customers available")
        d = self.dialog(f"Edit Bill - {bill['bill_no']}", 420, 520)
        ctk.CTkLabel(d, text=f"Bike: {bill['bike_no']}  (bike cannot be changed)",
                     font=(FONT, 12), text_color=COLORS["text_muted"]).pack(pady=(10, 4))
        c_dict = {f"{c['name']} ({c['phone'] or 'no phone'}) - #{c['id']}": c["id"] for c in customers}
        cur_key = next((k for k, v in c_dict.items() if v == bill["customer_id"]), list(c_dict.keys())[0])
        ctk.CTkLabel(d, text="Customer").pack()
        c_var = self.option(d, list(c_dict.keys()), cur_key, 330)
        ctk.CTkLabel(d, text="Total Amount (Rs)").pack()
        e_total = self.entry(d, "Total", 330, f"{bill['total']:g}")
        ctk.CTkLabel(d, text="Advance / Paid (Rs)").pack()
        e_adv = self.entry(d, "Advance", 330, f"{bill['advance']:g}")
        ctk.CTkLabel(d, text="Payment Method").pack()
        m_var = self.option(d, PAYMENT_METHODS, bill["payment_method"] or "Cash", 330)
        if not can_amounts:
            e_total.configure(state="disabled")
            e_adv.configure(state="disabled")
            ctk.CTkLabel(d, text="Due collections exist → amounts locked.\nOnly customer can be changed.\n"
                                 "To change amounts: Void this bill and create a new one.",
                         text_color=COLORS["accent_orange"], font=(FONT, 11)).pack(pady=6)

        def save():
            try:
                cid = c_dict[c_var.get()]
                if can_amounts:
                    total = parse_amount(e_total.get(), label="Total")
                    adv = parse_amount(e_adv.get() or "0", allow_zero=True, label="Advance")
                    self.db.update_bill(bill["id"], cid, total, adv, m_var.get())
                else:
                    self.db.update_bill(bill["id"], cid)
            except Exception as ex:
                return self.err(ex, d)
            d.destroy()
            self.refresh_current(("Bills", "Customers"))
            self.info("Bill updated.")
        self.action_button(d, "Save Changes", save, COLORS["accent_blue"])

    def open_void_bill_dialog(self):
        iid = self.selected(self.bill_tree, "Select a bill to void")
        if not iid:
            return
        bill = self.db.get_bill(int(iid))
        if not bill:
            return self.err("Bill not found")
        if bill["voided"]:
            return self.err("This bill is already voided.")
        pays = self.db.get_bill_payments(bill["id"])
        cash_paid = sum(p["amount"] for p in pays if p["method"] == "Cash")
        d = self.dialog(f"Void Bill - {bill['bill_no']}", 420, 380)
        ctk.CTkLabel(d, text=f"Void {bill['bill_no']}  ({money(bill['total'])})",
                     font=(FONT, 15, "bold"), text_color=COLORS["accent_pink"]).pack(pady=(12, 4))
        ctk.CTkLabel(d, text=f"Cash to be returned today: {money(cash_paid)}\n"
                             f"Bike {bill['bike_no']} will go back to stock.\n"
                             "The bill stays in records but is excluded from all totals.",
                     text_color=COLORS["text_muted"], font=(FONT, 11)).pack(pady=4)
        e_reason = self.entry(d, "Void reason (required)", 330)

        def save():
            try:
                reason = e_reason.get().strip()
                if not reason:
                    raise ValueError("Please write a void reason")
                if not messagebox.askyesno("Confirm Void", f"Void {bill['bill_no']}?\nThis cannot be undone.", parent=d):
                    return
                self.db.void_bill(bill["id"], reason)
            except Exception as ex:
                return self.err(ex, d)
            d.destroy()
            self.refresh_current(("Bills", "Bikes", "Customers"))
            self.info("Bill voided.")
        self.action_button(d, "Void Bill", save, COLORS["accent_pink"])

    def open_collect_due_dialog(self):
        iid = self.selected(self.bill_tree, "Select a bill")
        if not iid:
            return
        bill = self.db.get_bill(int(iid))
        if not bill:
            return self.err("Bill not found")
        if bill["voided"]:
            return self.err("This bill is voided. No payment can be collected.")
        if bill["due"] <= 0:
            return self.info("Already paid")
        d = self.dialog("Collect Due", 320, 300)
        ctk.CTkLabel(d, text=f"{bill['bill_no']}\nRemaining Due: {money(bill['due'])}",
                     font=(FONT, 14, "bold"), text_color=COLORS["accent_orange"]).pack(pady=10)
        e_amt = self.entry(d, "Amount to Collect", 220, f"{bill['due']:g}")
        m_var = self.option(d, PAYMENT_METHODS, "Cash", 220)

        def save():
            try:
                self.db.collect_due(bill["id"], parse_amount(e_amt.get()), m_var.get())
            except Exception as ex:
                return self.err(ex, d)
            d.destroy()
            self.refresh_current(("Bills", "Customers"))
            self.info("Due payment recorded.")
        self.action_button(d, "Confirm Payment", save, COLORS["accent_green"])

    def open_print_receipt(self):
        iid = self.selected(self.bill_tree, "Select a bill to print")
        if iid:
            self.print_receipt(int(iid))

    def print_receipt(self, bill_id):
        bill, bike, payments, parts = self.db.get_bill_details_for_receipt(bill_id)
        if not bill:
            return self.err("Bill not found")
        photo_html, specs_html = "", ""
        if bike:
            uri = photo_data_uri(bike["photo_path"])
            if uri:
                photo_html = f"<img src='{uri}' style='max-height:110px;border:1px solid #ddd;border-radius:4px'>"
            specs_html = (f"<p class='specs'><b>Model:</b> {escape_html(bike['model'])} | "
                          f"<b>Engine No:</b> {escape_html(bike['engine_no'] or 'N/A')} | "
                          f"<b>Chassis No:</b> {escape_html(bike['chassis_no'] or 'N/A')} | "
                          f"<b>Bluebook Expiry:</b> {escape_html(bike['bluebook_expiry'] or 'N/A')}</p>")
        void_html = ""
        if bill["voided"]:
            void_html = (f"<div class='voidbanner'>*** VOIDED / CANCELLED ***<br>"
                         f"Reason: {escape_html(bill['void_reason'])}<br>"
                         f"By: {escape_html(bill['voided_by'])} at {escape_html(bill['voided_at'])}</div>")
        parts_rows = "".join(f"<tr><td>{escape_html(p['name'])}</td><td>{p['qty']}</td></tr>" for p in parts)
        pay_rows = "".join(f"<tr><td>{escape_html(p['created_at'][:10])}</td><td>{escape_html(p['note'])}</td>"
                           f"<td>{escape_html(p['method'])}</td><td>{money(p['amount'])}</td></tr>" for p in payments)
        body = (f"<div class='header'><div><h1>{escape_html(CONFIG.get('shop_name'))}</h1>"
                f"<p style='margin:4px 0 0 0'>{escape_html(CONFIG.get('shop_address'))} | {escape_html(CONFIG.get('shop_phone'))}</p></div>"
                f"{photo_html}</div>{void_html}"
                f"<div class='details'><div><b>Invoice No:</b> {escape_html(bill['bill_no'])}<br>"
                f"<b>Date:</b> {escape_html(bill['created_at'][:10])}<br>"
                f"<b>Status:</b> {'VOIDED' if bill['voided'] else escape_html(bill['status'])}</div>"
                f"<div><b>Customer:</b> {escape_html(bill['cust_name'])}<br><b>Phone:</b> {escape_html(bill['cust_phone'] or 'N/A')}<br>"
                f"<b>ID / Citizenship:</b> {escape_html(bill['cust_id_no'] or 'N/A')}<br>"
                f"<b>Address:</b> {escape_html(bill['cust_address'] or 'N/A')}</div></div>"
                f"<table><tr><th>Item Description</th><th>Amount</th></tr>"
                f"<tr><td><b>Vehicle Sale - {escape_html(bill['bike_no'])}</b>{specs_html}</td>"
                f"<td><b>{money(bill['total'])}</b></td></tr></table>"
                + (f"<h3>Refurbishment Parts Included</h3><table><tr><th>Part</th><th>Qty</th></tr>{parts_rows}</table>" if parts else "")
                + (f"<h3>Payment History</h3><table><tr><th>Date</th><th>Note</th><th>Method</th><th>Amount</th></tr>{pay_rows}</table>" if payments else "")
                + f"<div class='total-box'><p><b>Grand Total:</b> {money(bill['total'])}</p>"
                  f"<p><b>Total Paid:</b> {money(bill['advance'])}</p>"
                  f"<p style='color:{'#dc2626' if bill['due'] > 0 and not bill['voided'] else '#16a34a'}'>"
                  f"<b>Balance Due:</b> {money(0 if bill['voided'] else bill['due'])}</p></div>"
                  f"<div class='footer'><p>Thank you for choosing {escape_html(CONFIG.get('shop_name'))}!</p>"
                  f"<br><br><p>_________________________<br>Authorized Signature</p></div>")
        open_html("invoice", bill["bill_no"], body, f"Invoice {bill['bill_no']}")

    # ================= STAFF =================
    def build_staff_ui(self):
        pg = self.pages["Staff"]
        bar = ctk.CTkFrame(pg, fg_color="transparent")
        bar.pack(fill="x", pady=10)
        ctk.CTkButton(bar, text="➕ Add Staff", command=self.open_add_staff_dialog).pack(side="left", padx=5)
        ctk.CTkButton(bar, text="💰 Pay Salary", fg_color=COLORS["accent_green"],
                      command=self.open_pay_salary_dialog).pack(side="left", padx=5)
        ctk.CTkButton(bar, text="📜 Salary History", fg_color=COLORS["accent_blue"],
                      command=self.open_salary_history).pack(side="left", padx=5)
        ctk.CTkButton(bar, text="🚫 Deactivate", fg_color=COLORS["accent_pink"],
                      command=self.deactivate_staff).pack(side="left", padx=5)
        self.staff_tree = make_tree(pg, ("Name", "Phone", "Role", "Salary"))

    def load_staff(self):
        clear_tree(self.staff_tree)
        for s in self.db.get_staff():
            self.staff_tree.insert("", "end", iid=str(s["id"]), values=(
                s["name"], txt(s["phone"]), txt(s["role"]), money(s["monthly_salary"])))

    def open_add_staff_dialog(self):
        d = self.dialog("Add Staff", 320, 350)
        ctk.CTkLabel(d, text="Add New Staff Member", font=(FONT, 15, "bold")).pack(pady=8)
        e_name = self.entry(d, "Full Name", 240)
        e_phone = self.entry(d, "Phone", 240)
        e_role = self.entry(d, "Role (e.g. Mechanic, Sales)", 240)
        e_sal = self.entry(d, "Monthly Salary (Rs)", 240)

        def save():
            try:
                self.db.add_staff(e_name.get(), e_phone.get(), e_role.get(),
                                  parse_amount(e_sal.get(), allow_zero=True, label="Salary"))
            except Exception as ex:
                return self.err(ex, d)
            d.destroy()
            self.load_staff()
        self.action_button(d, "Save Staff", save)

    def open_pay_salary_dialog(self):
        iid = self.selected(self.staff_tree, "Select a staff member")
        if not iid:
            return
        st = self.db.get_staff_member(int(iid))
        d = self.dialog("Pay Salary", 320, 380)
        ctk.CTkLabel(d, text=f"Pay Salary: {st['name']}", font=(FONT, 15, "bold")).pack(pady=8)
        e_month = self.entry(d, "Month (YYYY-MM)", 240, datetime.now().strftime("%Y-%m"))
        e_amt = self.entry(d, "Amount (Rs)", 240, f"{st['monthly_salary']:g}")
        e_date = self.entry(d, "Payment Date (YYYY-MM-DD)", 240, today_str())
        m_var = self.option(d, PAYMENT_METHODS, "Cash", 240)

        def save():
            try:
                self.db.pay_salary(st["id"], e_month.get().strip(), parse_amount(e_amt.get()),
                                   e_date.get().strip(), m_var.get(), "Monthly Salary")
            except Exception as ex:
                return self.err(ex, d)
            d.destroy()
            self.info("Salary payment recorded.")
        self.action_button(d, "Confirm Pay", save, COLORS["accent_green"])

    def open_salary_history(self):
        iid = self.selected(self.staff_tree, "Select a staff member")
        if not iid:
            return
        st = self.db.get_staff_member(int(iid))
        d = self.dialog(f"Salary History - {st['name']}", 600, 400)
        tree = make_tree(d, ("Month", "Amount", "Date", "Method"))
        for p in self.db.get_salary_history(st["id"]):
            tree.insert("", "end", values=(p["month"], money(p["amount"]), p["payment_date"], txt(p["method"])))

    def deactivate_staff(self):
        iid = self.selected(self.staff_tree, "Select a staff member")
        if iid and messagebox.askyesno("Confirm", "Deactivate this staff member?\n(Past salary records are kept.)"):
            self.db.deactivate_staff(int(iid))
            self.load_staff()

    # ================= PARTS =================
    def build_parts_ui(self):
        pg = self.pages["Parts"]
        bar = ctk.CTkFrame(pg, fg_color="transparent")
        bar.pack(fill="x", pady=10)
        ctk.CTkButton(bar, text="➕ Add Part", command=self.open_add_part_dialog).pack(side="left", padx=5)
        ctk.CTkButton(bar, text="📦 Buy Stock", fg_color=COLORS["accent_blue"],
                      command=self.open_buy_parts_dialog).pack(side="left", padx=5)
        ctk.CTkButton(bar, text="🔧 Use on Bike", fg_color=COLORS["accent_orange"],
                      command=self.open_use_part_dialog).pack(side="left", padx=5)
        self.parts_tree = make_tree(pg, ("Name", "Category", "Stock", "Unit Cost", "Alert At"))
        self.parts_tree.tag_configure("low", foreground=COLORS["accent_pink"])

    def load_parts(self):
        clear_tree(self.parts_tree)
        for p in self.db.get_parts():
            low = (p["stock_qty"] or 0) <= (p["low_stock_threshold"] or 0)
            self.parts_tree.insert("", "end", iid=str(p["id"]), tags=("low",) if low else (), values=(
                p["name"], txt(p["category"]), p["stock_qty"], money(p["unit_cost"]), p["low_stock_threshold"]))

    def open_add_part_dialog(self):
        d = self.dialog("Add Part", 320, 430)
        ctk.CTkLabel(d, text="New Spare Part", font=(FONT, 15, "bold")).pack(pady=8)
        e_name = self.entry(d, "Part Name", 240)
        cat_var = self.option(d, PART_CATEGORIES, "General", 240)
        e_qty = self.entry(d, "Opening Stock Qty", 240)
        e_cost = self.entry(d, "Unit Cost (Rs)", 240)
        e_thresh = self.entry(d, "Low Stock Alert Threshold", 240, "5")

        def save():
            try:
                self.db.add_part(e_name.get(), cat_var.get(), parse_int(e_qty.get(), "Stock"),
                                 parse_amount(e_cost.get(), allow_zero=True, label="Cost"),
                                 parse_int(e_thresh.get(), "Threshold"))
            except Exception as ex:
                return self.err(ex, d)
            d.destroy()
            self.load_parts()
        self.action_button(d, "Save Part", save)

    def open_buy_parts_dialog(self):
        iid = self.selected(self.parts_tree, "Select a part")
        if not iid:
            return
        p = self.db.get_part(int(iid))
        d = self.dialog("Buy Stock", 320, 330)
        ctk.CTkLabel(d, text=f"Restock: {p['name']}", font=(FONT, 14, "bold")).pack(pady=8)
        e_qty = self.entry(d, "Quantity Purchased", 240)
        e_cost = self.entry(d, "Unit Purchase Cost (Rs)", 240, f"{(p['unit_cost'] or 0):g}")
        m_var = self.option(d, PAYMENT_METHODS, "Cash", 240)

        def save():
            try:
                self.db.buy_parts(p["id"], parse_int(e_qty.get(), "Qty"),
                                  parse_amount(e_cost.get(), allow_zero=True, label="Cost"), m_var.get())
            except Exception as ex:
                return self.err(ex, d)
            d.destroy()
            self.load_parts()
            self.info("Stock updated.")
        self.action_button(d, "Confirm Purchase", save)

    def open_use_part_dialog(self):
        parts = [p for p in self.db.get_parts() if (p["stock_qty"] or 0) > 0]
        bikes = self.db.get_stock_bikes()
        if not parts or not bikes:
            return self.err("You need parts in stock and bikes in stock")
        d = self.dialog("Use Part on Bike", 360, 320)
        ctk.CTkLabel(d, text="Assign Part to Bike", font=(FONT, 14, "bold")).pack(pady=8)
        p_dict = {f"{p['name']} (Stock: {p['stock_qty']}) [#{p['id']}]": p for p in parts}
        p_var = self.option(d, list(p_dict.keys()), width=300)
        b_var = self.option(d, [b["bike_no"] for b in bikes], width=300)
        e_qty = self.entry(d, "Quantity Used", 300)

        def save():
            try:
                self.db.use_part(p_dict[p_var.get()]["id"], b_var.get(), parse_int(e_qty.get(), "Qty"), today_str())
            except Exception as ex:
                return self.err(ex, d)
            d.destroy()
            self.refresh_current(("Parts", "CostSheet"))
            self.info("Part assigned to bike cost sheet.")
        self.action_button(d, "Assign Part", save, COLORS["accent_orange"])

    # ================= EXPENSES (Edit / Delete) =================
    def build_expenses_ui(self):
        pg = self.pages["Expenses"]
        bar = ctk.CTkFrame(pg, fg_color="transparent")
        bar.pack(fill="x", pady=10)
        ctk.CTkButton(bar, text="➕ Add Expense", command=self.open_add_expense_dialog).pack(side="left", padx=5)
        ctk.CTkButton(bar, text="✏️ Edit", fg_color=COLORS["accent_blue"],
                      command=self.open_edit_expense_dialog).pack(side="left", padx=5)
        ctk.CTkButton(bar, text="❌ Delete", fg_color=COLORS["accent_pink"],
                      command=self.delete_expense).pack(side="left", padx=5)
        self.exp_total_lbl = ctk.CTkLabel(bar, text="", text_color=COLORS["text_muted"])
        self.exp_total_lbl.pack(side="right", padx=10)
        self.exp_tree = make_tree(pg, ("Date", "Title", "Category", "Method", "Amount"),
                                  widths={"Date": 110, "Title": 260, "Category": 130, "Method": 110, "Amount": 130})

    def load_expenses(self):
        clear_tree(self.exp_tree)
        total = 0
        for e in self.db.get_expenses():
            total += e["amount"] or 0
            self.exp_tree.insert("", "end", iid=str(e["id"]), values=(
                e["expense_date"], e["title"], txt(e["category"]), txt(e["method"]), money(e["amount"])))
        self.exp_total_lbl.configure(text=f"Total: {money(total)}")

    def open_add_expense_dialog(self):
        d = self.dialog("Add Expense", 320, 410)
        ctk.CTkLabel(d, text="New Operating Expense", font=(FONT, 15, "bold")).pack(pady=8)
        e_title = self.entry(d, "Expense Title", 240)
        cat_var = self.option(d, EXPENSE_CATEGORIES, "Rent", 240)
        e_amt = self.entry(d, "Amount (Rs)", 240)
        e_date = self.entry(d, "Date (YYYY-MM-DD)", 240, today_str())
        m_var = self.option(d, PAYMENT_METHODS, "Cash", 240)

        def save():
            try:
                self.db.add_expense(e_title.get(), cat_var.get(), parse_amount(e_amt.get()),
                                    e_date.get().strip(), m_var.get(), "")
            except Exception as ex:
                return self.err(ex, d)
            d.destroy()
            self.load_expenses()
        self.action_button(d, "Save Expense", save)

    def open_edit_expense_dialog(self):
        iid = self.selected(self.exp_tree, "Select an expense to edit")
        if not iid:
            return
        e = self.db.get_expense(int(iid))
        if not e:
            return self.err("Expense not found")
        d = self.dialog(f"Edit Expense #{e['id']}", 340, 470)
        ctk.CTkLabel(d, text="Edit Operating Expense", font=(FONT, 15, "bold")).pack(pady=8)
        ctk.CTkLabel(d, text="Cash effect will be re-adjusted automatically.",
                     font=(FONT, 11), text_color=COLORS["text_muted"]).pack()
        e_title = self.entry(d, "Expense Title", 260, e["title"])
        cat_var = self.option(d, EXPENSE_CATEGORIES,
                              e["category"] if e["category"] in EXPENSE_CATEGORIES else "Other", 260)
        e_amt = self.entry(d, "Amount (Rs)", 260, f"{(e['amount'] or 0):g}")
        e_date = self.entry(d, "Date (YYYY-MM-DD)", 260, e["expense_date"])
        m_var = self.option(d, PAYMENT_METHODS, e["method"] if e["method"] in PAYMENT_METHODS else "Cash", 260)
        e_note = self.entry(d, "Note (optional)", 260, e["note"] or "")

        def save():
            try:
                self.db.update_expense(e["id"], e_title.get(), cat_var.get(), parse_amount(e_amt.get()),
                                       e_date.get().strip(), m_var.get(), e_note.get().strip())
            except Exception as ex:
                return self.err(ex, d)
            d.destroy()
            self.load_expenses()
            self.info("Expense updated.")
        self.action_button(d, "Save Changes", save, COLORS["accent_blue"])

    def delete_expense(self):
        iid = self.selected(self.exp_tree, "Select an expense to delete")
        if not iid:
            return
        e = self.db.get_expense(int(iid))
        if not e:
            return self.err("Expense not found")
        if not messagebox.askyesno("Confirm", f"Delete '{e['title']}' ({money(e['amount'])})?\n"
                                              "Cash amount will be returned to today's cash book."):
            return
        try:
            self.db.delete_expense(e["id"])
        except Exception as ex:
            return self.err(ex)
        self.load_expenses()
        self.info("Expense deleted.")

    # ================= REPORTS =================
    def build_reports_ui(self):
        pg = self.pages["Reports"]
        bar = ctk.CTkFrame(pg, fg_color="transparent")
        bar.pack(fill="x", pady=10)
        ctk.CTkLabel(bar, text="Month (YYYY-MM):").pack(side="left")
        self.rep_month = ctk.CTkEntry(bar, width=100)
        self.rep_month.insert(0, datetime.now().strftime("%Y-%m"))
        self.rep_month.pack(side="left", padx=5)
        self.rep_month.bind("<Return>", lambda e: self.generate_report())
        ctk.CTkButton(bar, text="Generate Report", command=self.generate_report).pack(side="left", padx=10)
        ctk.CTkButton(bar, text="📥 Export CSV", fg_color=COLORS["accent_green"],
                      command=self.export_csv).pack(side="right", padx=5)
        self.report_text = ctk.CTkTextbox(pg, font=("Courier New", 14))
        self.report_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.rep_data = {}

    def generate_report(self):
        try:
            r = self.db.monthly_report(self.rep_month.get().strip())
        except ValueError as ex:
            return self.err(ex)
        self.rep_data = r
        f = lambda v: f"Rs. {v:,.2f}"
        text = f"""
==================================================
PROFIT & LOSS STATEMENT - {r['Month']}
{CONFIG.get('shop_name')}
(voided bills are excluded)
==================================================
Total Sales Revenue    : {f(r['Revenue'])}
Bike Purchase Cost     : {f(r['Bike Cost'])}
Parts Used Cost (COGS) : {f(r['Parts Cost'])}
Labour Cost (COGS)     : {f(r['Labour Cost'])}
--------------------------------------------------
GROSS PROFIT           : {f(r['Gross Profit'])}
==================================================
Operating Expenses     : {f(r['Operating Exp'])}
Staff Salary Paid      : {f(r['Salary Paid'])}
--------------------------------------------------
TRUE NET PROFIT        : {f(r['Net Profit'])}
==================================================
"""
        self.report_text.configure(state="normal")
        self.report_text.delete("1.0", "end")
        self.report_text.insert("1.0", text)

    def export_csv(self):
        if not self.rep_data:
            return self.info("Generate a report first")
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")],
                                            initialfile=f"report_{self.rep_data['Month']}.csv")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["Metric", "Value"])
                for k, v in self.rep_data.items():
                    w.writerow([k, f"{v:.2f}" if isinstance(v, (int, float)) else sanitize_csv(v)])
        except OSError as ex:
            return self.err(f"Could not save file: {ex}")
        self.info("Exported")

    # ================= AUDIT LOG =================
    def build_audit_ui(self):
        pg = self.pages["Audit"]
        bar = ctk.CTkFrame(pg, fg_color="transparent")
        bar.pack(fill="x", pady=10)
        ctk.CTkLabel(bar, text="Action:").pack(side="left")
        self.au_action = ctk.CTkOptionMenu(bar, values=["All"], width=190, command=lambda e: self.load_audit())
        self.au_action.pack(side="left", padx=5)
        self.au_search = ctk.CTkEntry(bar, placeholder_text="Search user / entity / details...", width=280)
        self.au_search.pack(side="left", padx=10)
        self.au_search.bind("<KeyRelease>", lambda e: self.load_audit())
        ctk.CTkButton(bar, text="🔄 Refresh", command=self.load_audit).pack(side="left", padx=5)
        ctk.CTkButton(bar, text="📥 Export CSV", fg_color=COLORS["accent_green"],
                      command=self.export_audit_csv).pack(side="right", padx=5)
        ctk.CTkLabel(pg, text=f"Latest {AUDIT_LIMIT} entries (newest first). Every change is recorded automatically.",
                     text_color=COLORS["text_muted"]).pack(side="bottom", anchor="w")
        self.au_tree = make_tree(pg, ("Time", "User", "Action", "Entity", "ID", "Details"),
                                 widths={"Time": 150, "User": 110, "Action": 170, "Entity": 100,
                                         "ID": 150, "Details": 420})
        self._au_rows = []

    def load_audit(self):
        try:
            actions = ["All"] + self.db.get_audit_actions()
            cur = self.au_action.get()
            self.au_action.configure(values=actions)
            if cur not in actions:
                self.au_action.set("All")
            rows = self.db.get_audit(self.au_search.get().strip(), self.au_action.get())
        except Exception as ex:
            return self.err(ex)
        clear_tree(self.au_tree)
        self._au_rows = rows
        for r in rows:
            self.au_tree.insert("", "end", values=(r["ts"], txt(r["username"]), r["action"],
                                                   txt(r["entity"]), txt(r["entity_id"]), txt(r["details"])))

    def export_audit_csv(self):
        if not self._au_rows:
            return self.info("No audit entries to export")
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")],
                                            initialfile=f"audit_{datetime.now():%Y%m%d_%H%M}.csv")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["Time", "User", "Action", "Entity", "Entity ID", "Details"])
                for r in self._au_rows:
                    w.writerow([r["ts"], sanitize_csv(r["username"]), sanitize_csv(r["action"]),
                                sanitize_csv(r["entity"]), sanitize_csv(r["entity_id"]), sanitize_csv(r["details"])])
        except OSError as ex:
            return self.err(f"Could not save file: {ex}")
        self.info("Exported")

    # ================= SETTINGS =================
    def build_settings_ui(self):
        card = ctk.CTkScrollableFrame(self.pages["Settings"], fg_color=COLORS["card"], corner_radius=15)
        card.pack(pady=10, padx=40, fill="both", expand=True)
        ctk.CTkLabel(card, text="Shop Information", font=(FONT, 16, "bold")).pack(pady=(20, 10))
        self.shop_name_entry = self.entry(card, "Shop Name", 320, CONFIG.get("shop_name", ""))
        self.shop_addr_entry = self.entry(card, "Address", 320, CONFIG.get("shop_address", ""))
        self.shop_phone_entry = self.entry(card, "Phone", 320, CONFIG.get("shop_phone", ""))
        self.shop_pan_entry = self.entry(card, "PAN / VAT No.", 320, CONFIG.get("shop_pan", ""))
        ctk.CTkButton(card, text="Save Shop Info", command=self.save_shop_info).pack(pady=10)
        ctk.CTkLabel(card, text="Change Password", font=(FONT, 16, "bold")).pack(pady=(25, 10))
        self.old_pwd = ctk.CTkEntry(card, placeholder_text="Current Password", show="*", width=320)
        self.old_pwd.pack(pady=3)
        self.new_pwd = ctk.CTkEntry(card, placeholder_text="New Password (min 8 characters)", show="*", width=320)
        self.new_pwd.pack(pady=3)
        ctk.CTkButton(card, text="Update Password", fg_color=COLORS["accent_orange"],
                      command=self.change_pwd).pack(pady=10)
        ctk.CTkLabel(card, text="Database Backup", font=(FONT, 16, "bold")).pack(pady=(25, 5))
        ctk.CTkLabel(card, text=f"Automatic daily backups are kept in:\n{BACKUP_DIR}",
                     text_color=COLORS["text_muted"]).pack()
        ctk.CTkButton(card, text="Safe Backup (choose location)", fg_color=COLORS["accent_blue"],
                      command=self.backup_db).pack(pady=10)

        ctk.CTkLabel(card, text="Cloud Sync & Updates", font=(FONT, 16, "bold")).pack(pady=(25, 5))
        cfg = load_cloud_config()
        self.cloud_status_lbl = ctk.CTkLabel(card, text=f"Last sync: {cfg.get('last_sync') or 'never'}",
                                            text_color=COLORS["text_muted"])
        self.cloud_status_lbl.pack(pady=(0, 6))
        self.auto_sync_var = ctk.BooleanVar(value=bool(cfg.get("enabled", True)))
        ctk.CTkCheckBox(card, text="Auto-sync (silent, background)", variable=self.auto_sync_var,
                        command=self._toggle_auto_sync).pack(pady=4)

        def _sync_now():
            def work():
                try:
                    ts = cloud_push(load_cloud_config())
                    self.after(0, lambda: self.cloud_status_lbl.configure(text=f"Last sync: {ts}"))
                    self.after(0, lambda: self.info("Cloud sync complete."))
                except Exception as ex:
                    self.after(0, lambda: self.err(f"Sync failed: {ex}"))
            import threading
            threading.Thread(target=work, daemon=True).start()

        def _check_update():
            def work():
                try:
                    info = check_for_update()
                    if info:
                        self.after(0, lambda: self.info(f"New version {info.get('version')} available.\n"
                                                       "Use auto-update to install."))
                    else:
                        self.after(0, lambda: self.info("You are on the latest version."))
                except Exception as ex:
                    self.after(0, lambda: self.err(f"Update check failed: {ex}"))
            import threading
            threading.Thread(target=work, daemon=True).start()

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(pady=6)
        ctk.CTkButton(btn_row, text="Sync now", fg_color=COLORS["accent_green"],
                      command=_sync_now).pack(side="left", padx=5)
        ctk.CTkButton(btn_row, text="Check for updates", fg_color=COLORS["accent_blue"],
                      command=_check_update).pack(side="left", padx=5)

        ctk.CTkLabel(card, text=f"App Version: {APP_VERSION}", text_color=COLORS["text_muted"]).pack(pady=15)

    def save_shop_info(self):
        name = self.shop_name_entry.get().strip()
        if not name:
            return self.err("Shop Name cannot be empty")
        CONFIG["shop_name"] = name
        CONFIG["shop_address"] = self.shop_addr_entry.get().strip()
        CONFIG["shop_phone"] = self.shop_phone_entry.get().strip()
        CONFIG["shop_pan"] = self.shop_pan_entry.get().strip()
        try:
            save_config(CONFIG)
        except OSError as ex:
            return self.err(f"Could not save settings: {ex}")
        self.winfo_toplevel().title(f"{name} - v{APP_VERSION}")
        self.info("Shop info saved")

    def change_pwd(self):
        try:
            self.db.change_password(self.username, self.old_pwd.get(), self.new_pwd.get())
        except Exception as ex:
            return self.err(ex)
        self.info("Password changed")
        self.old_pwd.delete(0, "end")
        self.new_pwd.delete(0, "end")
        if self.must_change:
            self.must_change = False
            self.show_page("Dashboard")

    def _toggle_auto_sync(self):
        try:
            cfg = load_cloud_config()
            cfg["enabled"] = bool(self.auto_sync_var.get())
            save_cloud_config(cfg)
        except Exception as ex:
            self.err(ex)

    def backup_db(self):
        path = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("SQLite DB", "*.db")],
                                            initialfile=f"shuvam_backup_{datetime.now():%Y%m%d_%H%M}.db")
        if not path:
            return
        if os.path.normcase(os.path.abspath(path)) == os.path.normcase(os.path.abspath(DB_FILE)):
            return self.err("Cannot overwrite the current active database.")
        try:
            self.db.backup_to(path)
        except Exception as ex:
            return self.err(f"Backup failed: {ex}")
        self.info("Safe backup created")


def main():
    if "--version" in sys.argv:
        print(f"{APP_NAME} v{APP_VERSION}"); return
    if "--test" in sys.argv:
        ok = run_self_tests()
        sys.exit(0 if ok else 1)
    try:
        app = ShuvamApp()
    except Exception as ex:
        logging.exception("Startup failed")
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Startup error", f"The application could not start:\n{ex}\nSee error.log for details.")
        return
    app.mainloop()




# ======================= CLOUD + AUTO-UPDATE (v9) =======================
import urllib.request as _ur, ctypes as _ct, struct as _st

TURSO_URL_BUILTIN = "libsql://shuvam-recondition-house-khemraj73-coder.aws-ap-south-1.turso.io"
TURSO_TOKEN_BUILTIN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3OTUyMTM3NzgsImlkIjoiMDFhMWZhYTItYzUwMS03ZjNlLWEwMjctZmY0YWQ4YTBlOWVmIiwia2lkIjoiTUFONElfcXVPMVBzLXZMNm9SY3BnVjRIMlV4cG4tWm9mNHJ4NnNvN2lpYyIsInJpZCI6ImE3Mjc1MWUyLTQ3NTEtNGZmNC1iMTFiLTI4Zjg4MGUwMzhmMSJ9.OuI33n3uQL_1XrydzTK-yqpYcR3TJpbG81t0jyGhClQfh5RpfNZP_5ThxY8_e4-j3mOjjBvV2U9hZUEUJgNWAA"
GITHUB_REPO_URL = "https://github.com/khemraj73-coder/shuvam-recondition-house"
GITHUB_RAW_URL = "https://raw.githubusercontent.com/khemraj73-coder/shuvam-recondition-house/main"
UPDATE_VERSION_URL = GITHUB_RAW_URL + "/version_v9.json"
SNAPSHOT_TABLES = ("settings", "users", "bikes", "customers", "bills", "payments", "expenses",
                   "staff", "salary_payments", "parts", "parts_usage", "bike_labour",
                   "cash_book", "cash_closures", "audit_log")
CLOUD_FILE = os.path.join(DATA_DIR, "shuvam_cloud.json")
TURSO_VAULT_TABLE = "shuvam_vault"

def _http_get(url, timeout=15):
    req = _ur.Request(url, headers={"User-Agent": f"SHUVAM/{APP_VERSION}", "Cache-Control": "no-cache"})
    with _ur.urlopen(req, timeout=timeout) as r:
        return r.read()

def version_tuple(v):
    out = []
    for part in str(v or "0").split("."):
        try: out.append(int("".join(c for c in part if c.isdigit()) or 0))
        except ValueError: out.append(0)
    return tuple((out + [0, 0, 0])[:4])

# ---- DPAPI ----
def _dpapi_protect(data: bytes) -> bytes:
    class DATA_BLOB(_ct.Structure):
        _fields_ = [("cbData", _ct.c_uint), ("pbData", _ct.POINTER(_ct.c_char))]
    inblob = DATA_BLOB(len(data), _ct.cast(_ct.create_string_buffer(data), _ct.POINTER(_ct.c_char)))
    outblob = DATA_BLOB()
    ok = _ct.windll.crypt32.CryptProtectData(_ct.byref(inblob), None, None, None, None, 0, _ct.byref(outblob))
    if not ok:
        raise OSError("CryptProtectData failed")
    return _ct.string_at(outblob.pbData, outblob.cbData)

def _dpapi_unprotect(data: bytes) -> bytes:
    class DATA_BLOB(_ct.Structure):
        _fields_ = [("cbData", _ct.c_uint), ("pbData", _ct.POINTER(_ct.c_char))]
    inblob = DATA_BLOB(len(data), _ct.cast(_ct.create_string_buffer(data), _ct.POINTER(_ct.c_char)))
    outblob = DATA_BLOB()
    ok = _ct.windll.crypt32.CryptUnprotectData(_ct.byref(inblob), None, None, None, None, 0, _ct.byref(outblob))
    if not ok:
        raise OSError("CryptUnprotectData failed")
    return _ct.string_at(outblob.pbData, outblob.cbData)

def dpapi_protect_text(text):
    return base64.b64encode(_dpapi_protect(text.encode("utf-8"))).decode("ascii")

def dpapi_unprotect_text(tok):
    return _dpapi_unprotect(base64.b64decode(tok)).decode("utf-8")

# ---- Turso client ----
class TursoClient:
    def __init__(self, url, token):
        self.url = (url or "").strip().replace("libsql://", "https://")
        if self.url.endswith("/"):
            self.url = self.url[:-1]
        self.token = (token or "").strip()
        self.pipeline = self.url + "/v2/pipeline"

    def _post(self, body):
        import urllib.request
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(self.pipeline, data=data,
                                    headers={"Authorization": "Bearer " + self.token,
                                             "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))

    def ping(self):
        r = self._post({"requests": [{"type": "execute", "stmt": {"sql": "SELECT 1"}}]})
        return r

    def execute(self, sql, args=None):
        stmt = {"sql": sql}
        if args:
            stmt["args"] = [{"type": "text", "value": str(a)} for a in args]
        r = self._post({"requests": [{"type": "execute", "stmt": stmt}]})
        return r

# ---- snapshot export/restore ----
def export_snapshot(db=None):
    global DB
    if db is None:
        if DB is None:
            DB = DBManager(DB_FILE)
        db = DB
    tables = {}
    with db.get_conn() as conn:
        for t in SNAPSHOT_TABLES:
            try:
                tables[t] = [dict(r) for r in conn.execute(f"SELECT * FROM {t}").fetchall()]
            except sqlite3.Error:
                tables[t] = []
    return {"format": 1, "app": APP_NAME, "version": APP_VERSION,
            "created_at": datetime.now().isoformat(timespec="seconds"), "tables": tables}

def restore_snapshot(data, db=None, actor="cloud"):
    global DB
    if db is None:
        if DB is None:
            DB = DBManager(DB_FILE)
        db = DB
    if not isinstance(data, dict) or data.get("format") != 1 or not isinstance(data.get("tables"), dict):
        raise ValueError("Snapshot format invalid")
    tables = data["tables"]
    backup = os.path.join(BACKUP_DIR, f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
    try:
        db.backup_to(backup)
    except Exception:
        pass
    count = 0
    with db.get_conn(write=True) as conn:
        for t in SNAPSHOT_TABLES:
            rows = tables.get(t)
            if not isinstance(rows, list):
                continue
            conn.execute(f"DELETE FROM {t}")
            for row in rows:
                if not isinstance(row, dict) or not row:
                    continue
                cols = [c for c in row.keys() if all(ch.isalnum() or ch == "_" for ch in str(c))]
                if not cols:
                    continue
                conn.execute(f"INSERT INTO {t}({','.join(cols)}) VALUES({','.join('?'*len(cols))})",
                             tuple(row[c] for c in cols))
                count += 1
        db._audit(conn, actor, "RESTORE_CLOUD", "", f"{count} rows | {os.path.basename(backup)}")
    logging.info("Cloud restore done: %s rows", count)
    return count

# ---- cloud config ----
def load_cloud_config():
    cfg = {"url": TURSO_URL_BUILTIN, "token": TURSO_TOKEN_BUILTIN, "enabled": True, "last_sync": ""}
    try:
        if os.path.exists(CLOUD_FILE):
            raw = json.load(open(CLOUD_FILE, encoding="utf-8"))
            cfg.update({k: raw.get(k, cfg[k]) for k in ("url", "enabled", "last_sync")})
            if raw.get("token_enc"):
                try:
                    cfg["token"] = dpapi_unprotect_text(raw["token_enc"])
                except Exception:
                    pass
            if not cfg.get("token"):
                cfg["token"] = TURSO_TOKEN_BUILTIN
            if not cfg.get("url"):
                cfg["url"] = TURSO_URL_BUILTIN
    except Exception:
        logging.exception("Cloud config load failed")
    if not cfg.get("token"):
        cfg["token"] = TURSO_TOKEN_BUILTIN
    if not cfg.get("url"):
        cfg["url"] = TURSO_URL_BUILTIN
    return cfg

def save_cloud_config(cfg):
    out = {"url": cfg.get("url") or TURSO_URL_BUILTIN,
           "enabled": bool(cfg.get("enabled", True)),
           "last_sync": cfg.get("last_sync") or ""}
    token = (cfg.get("token") or "").strip() or TURSO_TOKEN_BUILTIN
    out["token_enc"] = dpapi_protect_text(token)
    tmp = CLOUD_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    os.replace(tmp, CLOUD_FILE)

def cloud_push(cfg=None, db=None):
    cfg = cfg or load_cloud_config()
    client = TursoClient(cfg.get("url"), cfg.get("token"))
    snap = export_snapshot(db)
    # store snapshot as encrypted-ish JSON in vault table (create if missing)
    try:
        client.execute(f"CREATE TABLE IF NOT EXISTS {TURSO_VAULT_TABLE} (id INTEGER PRIMARY KEY, payload TEXT)")
    except Exception:
        pass
    payload = json.dumps(snap, ensure_ascii=False)
    res = client.execute(f"INSERT INTO {TURSO_VAULT_TABLE} (payload) VALUES (?)", (payload,))
    # surface Turso errors
    try:
        if isinstance(res, dict) and res.get("results") and res["results"][0].get("type") == "error":
            raise RuntimeError(res["results"][0].get("error", {}).get("message", "Turso insert failed"))
    except RuntimeError:
        raise
    cfg["last_sync"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_cloud_config(cfg)
    return cfg["last_sync"]

def cloud_pull(cfg=None, db=None):
    cfg = cfg or load_cloud_config()
    db = db or DB
    client = TursoClient(cfg.get("url"), cfg.get("token"))
    r = client.execute(f"SELECT payload FROM {TURSO_VAULT_TABLE} ORDER BY id DESC LIMIT 1")
    # parse result
    rows = []
    try:
        res = r["results"][0]["response"]["result"]
        rows = res.get("rows", [])
    except Exception:
        rows = []
    if not rows:
        raise ValueError("No cloud snapshot found")
    row0 = rows[0]
    if isinstance(row0, list):
        cell = row0[0] if row0 else None
    elif isinstance(row0, dict):
        cell = row0.get("payload") or row0.get("value")
    else:
        cell = row0
    if isinstance(cell, dict):
        cell = cell.get("value", cell)
    payload = cell
    if isinstance(payload, (bytes, bytearray)):
        payload = payload.decode("utf-8", "replace")
    payload = str(payload or "").strip()
    # payload may be DPAPI-encrypted (legacy glass app) -> try decrypt
    try:
        payload = dpapi_unprotect_text(payload)
    except Exception:
        pass
    data = json.loads(payload)
    n = restore_snapshot(data, db, actor="cloud")
    cfg["last_sync"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_cloud_config(cfg)
    return n, cfg["last_sync"]

# ---- auto-update ----
def check_for_update(timeout=12):
    try:
        raw = json.loads(_http_get(UPDATE_VERSION_URL, timeout=timeout).decode("utf-8"))
        remote = str(raw.get("version") or "")
        if remote and version_tuple(remote) > version_tuple(APP_VERSION):
            raw["version"] = remote
            try:
                rel = json.loads(_http_get("https://api.github.com/repos/khemraj73-coder/shuvam-recondition-house/releases/latest",
                                          timeout=timeout).decode("utf-8"))
                for asset in (rel.get("assets") or []):
                    if str(asset.get("name") or "").lower().endswith(".exe"):
                        raw["exe_url"] = asset.get("browser_download_url")
                        break
            except Exception:
                pass
            return raw
    except Exception as exc:
        logging.info("Update check failed: %s", exc)
    return None

def install_update(info):
    info = info or {}
    url = info.get("exe_url") if getattr(sys, "frozen", False) else (info.get("url") or GITHUB_RAW_URL + "/shuvam_v9.py")
    expected = (info.get("sha256") or "").strip().lower()
    try:
        data = _http_get(url, timeout=60)
        if expected and hashlib.sha256(data).hexdigest() != expected:
            return False, "Download checksum mismatch - update stopped"
        if getattr(sys, "frozen", False):
            target = pathlib.Path(sys.executable)
            new_file = target.with_suffix(".new.exe")
            new_file.write_bytes(data)
            bat = pathlib.Path(tempfile.gettempdir()) / f"shuvam_update_{int(time.time())}.bat"
            bat.write_text("@echo off\r\ntimeout /t 2 /nobreak >nul\r\n"
                           f'copy /y "{new_file}" "{target}" >nul\r\n'
                           f'start "" "{target}"\r\n'
                           'del "%~f0"\r\n', encoding="ascii", errors="ignore")
            import subprocess
            subprocess.Popen(["cmd", "/c", str(bat)], creationflags=0x08000008, close_fds=True)
            return True, "Update downloaded - app will restart"
        target = pathlib.Path(__file__).resolve()
        backup = target.with_suffix(f".bak-{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
        backup.write_bytes(target.read_bytes())
        tmp = target.with_suffix(".update.tmp")
        tmp.write_bytes(data)
        os.replace(tmp, target)
        return True, f"v{info.get('version', '?')} installed - restart the app"
    except Exception as exc:
        logging.warning("Update install failed: %s", exc)
        return False, f"Update failed: {exc}"

# ---- silent auto-sync hook (call after login) ----
def _silent_cloud_sync():
    try:
        cfg = load_cloud_config()
        if not cfg.get("enabled", True):
            return
        cloud_push(cfg)
        logging.info("silent cloud sync ok")
    except Exception:
        logging.exception("silent cloud sync failed")

# ---- auto-update check hook (background) ----
def _auto_update_check(root, username):
    try:
        info = check_for_update()
        if not info:
            return
        def prompt():
            if messagebox.askyesno("Update available",
                                   f"New version {info.get('version')} is available.\nInstall now?"):
                ok, msg = install_update(info)
                messagebox.showinfo("Update", msg)
        root.after(0, prompt)
    except Exception:
        logging.exception("auto-update check failed")

# ---- headless --test mode ----
def run_self_tests():
    import traceback
    passed, failed = [], []
    def check(name, fn):
        try:
            fn(); passed.append(name); print(f"  [PASS] {name}")
        except Exception as exc:
            failed.append((name, exc)); print(f"  [FAIL] {name} -> {exc}")
            if os.environ.get("SHUVAM_TEST_VERBOSE"):
                traceback.print_exc()
    print("=" * 60)
    print("Shuvam v9 - self test")
    print("=" * 60)
    def t1():
        assert APP_VERSION.startswith("9.")
        assert APP_NAME == "SHUVAM RECONDITION HOUSE"
        assert len(PAYMENT_METHODS) >= 9
        for m in ("Cash", "eSewa", "Khalti", "ConnectIPS", "Bank Transfer", "Fonepay", "IME Pay", "Cheque", "Other"):
            assert m in PAYMENT_METHODS, m
    check("1. Branding + payment methods", t1)
    def t2():
        assert version_tuple("9.0.1") > version_tuple("9.0.0")
        assert version_tuple("9.0.0") > version_tuple("8.2.0")
    check("2. Version compare", t2)
    def t3():
        tok = dpapi_protect_text("shuvam-test-token")
        assert dpapi_unprotect_text(tok) == "shuvam-test-token"
    check("3. DPAPI roundtrip", t3)
    tmp_db = os.path.join(tempfile.mkdtemp(prefix="shuvam_v9_test_"), "t.db")
    db = DBManager(tmp_db)
    def t4():
        assert db.authenticate("admin", "admin123")[0] is True
        assert db.authenticate("admin", "wrong") == (False, 0)
    check("4. Auth (admin/admin123)", t4)
    def t5():
        snap = export_snapshot(db)
        assert isinstance(snap, dict) and snap.get("format") == 1
        db2 = DBManager(os.path.join(os.path.dirname(tmp_db), "t2.db"))
        n = restore_snapshot(snap, db2, actor="tester")
        assert n >= 0
    check("5. Snapshot export/restore", t5)
    def t6():
        cfg = load_cloud_config()
        assert cfg.get("token") and cfg.get("url")
        c = TursoClient(cfg["url"], cfg["token"])
        r = c.ping()
        assert r is not None
    check("6. Turso ping", t6)
    print("-" * 60)
    print(f"RESULT: {len(passed)} passed, {len(failed)} failed")
    print("=" * 60)
    for name, exc in failed:
        print(f"  FAILED -> {name}: {exc}")
    return not failed


if __name__ == "__main__":
    main()
