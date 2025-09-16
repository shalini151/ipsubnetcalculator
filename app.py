import streamlit as st
import ipaddress
import pandas as pd
import sqlite3
import datetime

DB_FILE = "ip_history.db"

# ---------------- Database Setup ----------------

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_input TEXT,
            network_address TEXT,
            broadcast_address TEXT,
            netmask TEXT,
            wildcard_mask TEXT,
            prefixlen INTEGER,
            total_ips INTEGER,
            usable_hosts INTEGER,
            first_usable_ip TEXT,
            last_usable_ip TEXT,
            is_private TEXT,
            is_multicast TEXT,
            is_reserved TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_to_db(info):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO history (
            ip_input, network_address, broadcast_address, netmask, wildcard_mask,
            prefixlen, total_ips, usable_hosts, first_usable_ip, last_usable_ip,
            is_private, is_multicast, is_reserved, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        info["ip_input"], info["network_address"], info["broadcast_address"], info["netmask"], info["wildcard_mask"],
        info["prefixlen"], info["total_ips"], info["usable_hosts"], info["first_usable_ip"], info["last_usable_ip"],
        info["is_private"], info["is_multicast"], info["is_reserved"], datetime.datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def load_history(limit=500)_
