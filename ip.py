import streamlit as st
import ipaddress

st.set_page_config(page_title="Advanced IP Range Calculator", layout="centered")

st.title("🌐 Advanced IP Range Calculator")

mode = st.radio("Choose mode:", ["Single IP", "Batch IP"])

def calculate_subnet_info(ip_input):
    try:
        network = ipaddress.ip_network(ip_input, strict=False)
        usable_hosts = network.num_addresses - 2 if network.num_addresses > 2 else network.num_addresses
        hosts = list(network.hosts())
        first_usable = hosts[0] if hosts else "N/A"
        last_usable = hosts[-1] if hosts else "N/A"

        result = f"""
**IP Address:** {ip_input}  
**Network Address:** {network.network_address}  
**Broadcast Address:** {network.broadcast_address}  
**Subnet Mask:** {network.netmask}  
**Wildcard Mask:** {ipaddress.IPv4Address(int(network.hostmask))}  
**CIDR Notation:** /{network.prefixlen}  
**IP Version:** IPv{network.version}  
**Total IPs:** {network.num_addresses}  
**Usable Hosts:** {usable_hosts}  
**First Usable IP:** {first_usable}  
**Last Usable IP:** {last_usable}  
**Is Private:** {"Yes" if network.is_private else "No"}  
---
"""
        return result
    except ValueError as e:
        return f"❌ Error with `{ip_input}`: {str(e)}\n---"

if mode == "Single IP":
    ip_input = st.text_input("Enter IP address with CIDR (e.g. 192.168.1.0/24):")
    if st.button("Calculate"):
        if ip_input:
            st.markdown(calculate_subnet_info(ip_input))
        else:
            st.warning("Please enter a valid IP/CIDR.")

else:  # Batch Mode
    batch_input = st.text_area("Enter one IP/CIDR per line:", height=200)
    if st.button("Run Batch Calculation"):
        lines = batch_input.strip().splitlines()
        for line in lines:
            st.markdown(calculate_subnet_info(line.strip()))
