# 🕵️ ARP Spoofer + MITM Traffic Interceptor

> ⚠️ **For educational use only. Run ONLY on networks you own or have explicit permission to test.**

---

## 📁 Project Structure

```
arp_mitm/
├── arp_spoofer.py     ← Poisons ARP tables (MITM position)
├── sniffer.py         ← Captures & logs HTTP, DNS, credentials
└── README.md
```

---

## 🛠️ Requirements

```bash
pip install scapy
```

Also need root/sudo access on Kali Linux.

---

## 🧪 Lab Setup (Recommended)

| Machine        | Role          | Example IP     |
|----------------|---------------|----------------|
| Kali Linux     | Attacker      | 192.168.1.100  |
| Windows VM     | Victim        | 192.168.1.105  |
| Router         | Gateway       | 192.168.1.1    |

Use VirtualBox/VMware — set both VMs to **Bridged Adapter** so they're on the same network.

---

## 🚀 How to Run

### Step 1 — Find victim & gateway IPs
```bash
# Scan your network
sudo arp-scan --localnet
# or
ip route   # shows your gateway
nmap -sn 192.168.1.0/24
```

### Step 2 — Start ARP Spoofer (Terminal 1)
```bash
sudo python3 arp_spoofer.py <victim_ip> <gateway_ip>

# Example:
sudo python3 arp_spoofer.py 192.168.1.105 192.168.1.1
```

You'll see packets being sent every 1.5 seconds.

### Step 3 — Start Sniffer (Terminal 2)
```bash
sudo python3 sniffer.py <interface> <victim_ip>

# Example:
sudo python3 sniffer.py eth0 192.168.1.105
```

### Step 4 — Browse on Victim Machine
On the victim (Windows VM), open a browser and visit any **HTTP** (not HTTPS) site.
Watch the terminal light up with DNS queries, HTTP requests, and any credentials! 👀

### Step 5 — Stop & Restore
Hit `CTRL+C` on arp_spoofer.py — it will automatically:
- Restore the victim's ARP table
- Restore the router's ARP table  
- Disable IP forwarding

---

## 📊 What Gets Captured

| Type         | What You See                              |
|--------------|-------------------------------------------|
| 🌐 DNS       | Every domain the victim looks up          |
| 🔗 HTTP GET  | Full URLs being visited                   |
| 🔑 HTTP POST | Form data, login credentials (HTTP only)  |
| 📥 HTTP Resp | Server response codes                     |
| 🔑 FTP       | FTP username and passwords                |

> ⚠️ HTTPS traffic is **encrypted** — you won't see plaintext credentials from HTTPS sites. That's why HTTP test sites (like http://testphp.vulnweb.com) are used in labs.

---

## 🧠 Key Concepts You'll Learn

- How ARP protocol works (and why it has no authentication)
- Layer 2 attacks (ARP poisoning)
- Man-in-the-Middle attack flow
- Packet crafting with Scapy
- Network traffic analysis
- Why HTTPS matters for defense

---

## 🛡️ Defense (Blue Team)

To **detect** ARP spoofing:
```bash
# Watch for duplicate MACs in ARP table
arp -a
# Use arpwatch tool
sudo apt install arpwatch
```

To **prevent** it:
- Use static ARP entries for critical devices
- Enable Dynamic ARP Inspection (DAI) on managed switches
- Use HTTPS everywhere (HSTS)

---

## 📺 YouTube Video Idea

1. Explain ARP protocol + vulnerability (whiteboard/slides)
2. Show lab setup (VMs)
3. Run arp_spoofer.py — show ARP table before/after on victim
4. Run sniffer.py — browse HTTP site on victim, show captured traffic
5. Show HTTPS protection (nothing captured)
6. Restore & explain defense

---

*Built with Python + Scapy | Kali Linux*
