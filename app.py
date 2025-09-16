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

def load_history(limit=500):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(f"""
        SELECT * FROM history ORDER BY timestamp DESC LIMIT {limit}
    """, conn)
    conn.close()
    return df

# ---------------- IP/Subnet Calculation ----------------

def calculate_subnet_info(ip_input):
    try:
        network = ipaddress.ip_network(ip_input, strict=False)
    except ValueError as e:
        return None, f"Invalid IP/Network: {e}"

    # Calculate usable hosts for IPv4 only and if prefix < 31
    total_ips = network.num_addresses
    if network.version == 4 and network.prefixlen < 31:
        usable_hosts = total_ips - 2
        hosts = list(network.hosts())
        first_usable_ip = str(hosts[0]) if hosts else "N/A"
        last_usable_ip = str(hosts[-1]) if hosts else "N/A"
    else:
        usable_hosts = total_ips
        first_usable_ip = "N/A"
        last_usable_ip = "N/A"

    wildcard_mask = ipaddress.IPv4Address(int(network.hostmask)) if network.version == 4 else "N/A"

    info = {
        "ip_input": ip_input,
        "network_address": str(network.network_address),
        "broadcast_address": str(network.broadcast_address) if network.version == 4 else "N/A",
        "netmask": str(network.netmask) if network.version == 4 else str(network.netmask),
        "wildcard_mask": str(wildcard_mask),
        "prefixlen": network.prefixlen,
        "total_ips": total_ips,
        "usable_hosts": usable_hosts,
        "first_usable_ip": first_usable_ip,
        "last_usable_ip": last_usable_ip,
        "is_private": "Yes" if network.is_private else "No",
        "is_multicast": "Yes" if network.is_multicast else "No",
        "is_reserved": "Yes" if network.is_reserved else "No",
    }
    return info, None

# ---------------- Streamlit UI ----------------

st.set_page_config(page_title="IP Range Calculator", layout="centered")
init_db()

st.title("🌐 Advanced IP Range Calculator")

mode = st.radio("Choose mode:", ["Single IP", "Batch IP", "View History"])

# ---------- Single IP Mode ----------

if mode == "Single IP":
    ip_input = st.text_input("Enter IP address with CIDR (e.g. 192.168.1.0/24):")

    if st.button("Calculate"):
        if not ip_input.strip():
            st.warning("Please enter a valid IP/CIDR")
        else:
            info, err = calculate_subnet_info(ip_input.strip())
            if err:
                st.error(err)
            else:
                save_to_db(info)
                st.success("Subnet info calculated and saved to history!")
                st.markdown(f"""
**IP Input:** `{info['ip_input']}`  
**Network Address:** `{info['network_address']}`  
**Broadcast Address:** `{info['broadcast_address']}`  
**Subnet Mask:** `{info['netmask']}`  
**Wildcard Mask:** `{info['wildcard_mask']}`  
**Prefix Length:** /{info['prefixlen']}  
**Total IPs:** {info['total_ips']}  
**Usable Hosts:** {info['usable_hosts']}  
**First Usable IP:** `{info['first_usable_ip']}`  
**Last Usable IP:** `{info['last_usable_ip']}`  
**Is Private:** {info['is_private']}  
**Is Multicast:** {info['is_multicast']}  
**Is Reserved:** {info['is_reserved']}  
""")

# ---------- Batch IP Mode ----------

elif mode == "Batch IP":
    batch_input = st.text_area("Enter one IP/CIDR per line:", height=300)

    if st.button("Run Batch Calculation"):
        lines = batch_input.strip().splitlines()
        if not lines:
            st.warning("Please enter at least one IP/CIDR")
        else:
            results = []
            errors = []
            for line in lines:
                ip_line = line.strip()
                if not ip_line:
                    continue
                info, err = calculate_subnet_info(ip_line)
                if err:
                    errors.append(f"❌ {ip_line}: {err}")
                else:
                    save_to_db(info)
                    results.append(info)

            if results:
                st.success(f"Processed {len(results)} IPs:")
                for info in results:
                    st.markdown(f"""
**IP Input:** `{info['ip_input']}`  
**Network Address:** `{info['network_address']}`  
**Broadcast Address:** `{info['broadcast_address']}`  
**Subnet Mask:** `{info['netmask']}`  
**Wildcard Mask:** `{info['wildcard_mask']}`  
**Prefix Length:** /{info['prefixlen']}  
**Total IPs:** {info['total_ips']}  
**Usable Hosts:** {info['usable_hosts']}  
**First Usable IP:** `{info['first_usable_ip']}`  
**Last Usable IP:** `{info['last_usable_ip']}`  
**Is Private:** {info['is_private']}  
**Is Multicast:** {info['is_multicast']}  
**Is Reserved:** {info['is_reserved']}  
---  
""")
            if errors:
                st.error("\n".join(errors))

# ---------- View History Mode ----------

elif mode == "View History":
    st.subheader("📜 Previously Calculated IP Ranges")
    df = load_history()
    if df.empty:
        st.info("No history found yet.")
    else:
        # Format timestamp
        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        st.dataframe(df, height=600)

# ---------- Extra: Clear History ----------

st.sidebar.markdown("---")
if st.sidebar.button("Clear History"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM history")
    conn.commit()
    conn.close()
    st.sidebar.success("History cleared!")

# ---------- About ----------

st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.markdown("""
This app calculates subnet information for IPv4 and IPv6 addresses with CIDR notation.  
It stores the results in a local SQLite database and allows you to review the calculation history.  
No machine learning or external dependencies required beyond standard Python libraries.
""")

