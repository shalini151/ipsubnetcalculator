# ip_calculator_ml_db.py

import streamlit as st
import ipaddress
import pandas as pd
import sqlite3
import datetime
import joblib
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures
import os

DB_FILE = "ip_history.db"
MODEL_FILE = "subnet_predictor.pkl"

# ------------------- Database -------------------

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_input TEXT,
            network_address TEXT,
            prefixlen INTEGER,
            total_ips INTEGER,
            usable_hosts INTEGER,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_to_db(ip_input, info):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO history (ip_input, network_address, prefixlen, total_ips, usable_hosts, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        ip_input, info["network_address"], info["prefixlen"],
        info["total_ips"], info["usable_hosts"],
        datetime.datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def load_history(limit=1000):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM history ORDER BY timestamp DESC LIMIT ?", conn, params=(limit,))
    conn.close()
    return df

# ------------------- Subnet Logic -------------------

def classify_subnet(network):
    if network.version == 4:
        first_octet = int(str(network.network_address).split('.')[0])
        if 0 <= first_octet <= 127:
            return "Class A"
        elif 128 <= first_octet <= 191:
            return "Class B"
        elif 192 <= first_octet <= 223:
            return "Class C"
        elif 224 <= first_octet <= 239:
            return "Multicast"
        else:
            return "Experimental"
    else:
        return "IPv6 (Various)"

def parse_network(ip_str):
    try:
        net = ipaddress.ip_network(ip_str, strict=False)
        return net, None
    except Exception as e:
        return None, str(e)

def calculate_subnet_info(net):
    info = {
        "network_address": str(net.network_address),
        "prefixlen": net.prefixlen,
        "total_ips": net.num_addresses,
        "usable_hosts": net.num_addresses - 2 if net.version == 4 and net.prefixlen < 31 else net.num_addresses,
        "class": classify_subnet(net)
    }
    return info

# ------------------- ML Model -------------------

def train_model_from_history():
    df = load_history()
    df = df[df["usable_hosts"] > 0]
    if len(df) < 10:
        return None, "Not enough data to train model"
    X = df[["usable_hosts"]]
    y = df["prefixlen"]
    model = make_pipeline(PolynomialFeatures(2), LinearRegression())
    model.fit(X, y)
    joblib.dump(model, MODEL_FILE)
    return model, "Model trained successfully"

def load_model():
    if os.path.exists(MODEL_FILE):
        return joblib.load(MODEL_FILE)
    return None

def predict_prefixlen(usable_hosts, model):
    try:
        prediction = int(round(model.predict([[usable_hosts]])[0]))
        return max(0, min(prediction, 32))
    except:
        return None

# ------------------- Streamlit App -------------------

st.set_page_config("IP Calculator + ML", layout="wide")
init_db()

st.title("📡 IP/Subnet Calculator with ML Suggestions & History")

mode = st.sidebar.radio("Choose Mode", ["Calculator", "History", "ML Suggestion", "Train Model"])
model = load_model()

# ------------------- Calculator -------------------

if mode == "Calculator":
    st.subheader("🔍 IP/Subnet Calculator")
    ip_input = st.text_input("Enter IP/Subnet (e.g. 192.168.0.0/24)")

    if st.button("Calculate"):
        net, err = parse_network(ip_input)
        if err:
            st.error(f"Error: {err}")
        else:
            info = calculate_subnet_info(net)
            save_to_db(ip_input, info)

            st.success("✅ Subnet Info Calculated:")
            st.markdown(f"""
- **Network Address:** `{info['network_address']}`
- **Prefix Length:** `/{info['prefixlen']}`
- **Total IPs:** `{info['total_ips']}`
- **Usable Hosts:** `{info['usable_hosts']}`
- **Class:** `{info['class']}`
            """)

# ------------------- History -------------------

elif mode == "History":
    st.subheader("📜 Calculation History")
    df = load_history()
    if df.empty:
        st.info("No history yet.")
    else:
        st.dataframe(df)

# ------------------- ML Suggestion -------------------

elif mode == "ML Suggestion":
    st.subheader("💡 Subnet Suggestion (via ML)")
    host_count = st.number_input("Expected Number of Hosts", min_value=1)

    if st.button("Suggest Subnet Size"):
        if model is None:
            st.warning("No model trained yet. Please train the model in the 'Train Model' tab.")
        else:
            pred = predict_prefixlen(host_count, model)
            if pred:
                total_ips = 2 ** (32 - pred)
                usable = total_ips - 2 if pred < 31 else total_ips
                st.success(f"📐 Suggested Prefix Length: /{pred}")
                st.info(f"Total IPs: {total_ips}, Usable Hosts: {usable}")
            else:
                st.error("Prediction failed.")

# ------------------- Train Model -------------------

elif mode == "Train Model":
    st.subheader("🔁 Train Model")
    if st.button("Train from History"):
        model, msg = train_model_from_history()
        st.info(msg)
