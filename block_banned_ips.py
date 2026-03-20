import urllib.request
import json
import subprocess
import threading

# URL to fetch banned IPs
BAN_LIST_URL = "https://bcsservers.ballistica.workers.dev/fetchbannedips"


def fetch_banned_ips():
    """Fetch the list of banned IPs from the server using urllib."""
    try:
        with urllib.request.urlopen(BAN_LIST_URL) as response:
            data = response.read().decode('utf-8')
            return json.loads(data)
    except urllib.error.URLError as e:
        print(f"Error fetching banned IPs: {e}")
        return {}


def is_ip_blocked(ip):
    """Check if the IP is already blocked in iptables."""
    try:
        result = subprocess.run(
            ["iptables", "-L", "-n", "-v"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return ip in result.stdout
    except Exception as e:
        print(f"Error checking iptables for IP {ip}: {e}")
        return False


def block_ip(ip):
    """Block the given IP for UDP traffic using iptables."""
    try:
        subprocess.run(
            ["iptables", "-A", "INPUT", "-s", ip, "-p", "udp", "-j", "DROP"],
            check=True,
        )
        print(f"Blocked IP: {ip}")
    except subprocess.CalledProcessError as e:
        print(f"Error blocking IP {ip}: {e}")


def main():
    """Main function to fetch banned IPs and block them."""
    banned_ips = fetch_banned_ips()
    for ip, details in banned_ips.items():
        if not is_ip_blocked(ip):
            print(
                f"Blocking IP: {ip} (Reason: {details.get('reason', 'No reason provided')})")
            block_ip(ip)
        else:
            print(f"IP {ip} is already blocked.")


def schedule_main():
    """Schedule the main function to run every hour."""
    main()
    print("Scheduled to run again in 1 hour...")
    # Schedule to run after 1 hour
    threading.Timer(3600, schedule_main).start()
