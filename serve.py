"""Run Range Drill on the local network (Wi-Fi / LAN).

    python serve.py              # port 8000
    python serve.py --port 8080

Uses Waitress, a production-grade WSGI server that works on Windows, macOS and Linux.
On start it prints the addresses other devices can open, plus a QR code for phones.
"""
import argparse
import os
import socket
import sys


def lan_addresses():
    """Best-effort list of this computer's IPv4 addresses in the local network."""
    found = []
    # The address of the interface used for outgoing traffic (no packets are actually sent)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            found.append(s.getsockname()[0])
    except OSError:
        pass
    try:
        for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
            if ip not in found:
                found.append(ip)
    except OSError:
        pass
    private = [ip for ip in found if ip.startswith(("192.168.", "10.")) or
               (ip.startswith("172.") and 16 <= int(ip.split(".")[1]) <= 31)]
    return private or [ip for ip in found if not ip.startswith("127.")]


def print_qr(url):
    try:
        import qrcode
    except ImportError:
        return
    qr = qrcode.QRCode(border=2)
    qr.add_data(url)
    qr.make(fit=True)
    try:
        qr.print_ascii(invert=True)
    except UnicodeEncodeError:  # old Windows consoles without UTF-8
        pass


def main():
    parser = argparse.ArgumentParser(description="Run Range Drill in the local network")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    parser.add_argument("--host", default="0.0.0.0", help="0.0.0.0 = reachable from other devices")
    parser.add_argument("--threads", type=int, default=8)
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            pass

    from waitress import serve
    from app import app

    addresses = lan_addresses()
    line = "=" * 60
    print(line)
    print("  RANGE DRILL is running")
    print(line)
    print(f"  On this computer:   http://localhost:{args.port}")
    for ip in addresses:
        print(f"  In the network:     http://{ip}:{args.port}")
    try:
        print(f"  By computer name:   http://{socket.gethostname()}.local:{args.port}  (may not work on every phone)")
    except OSError:
        pass
    print(line)
    if addresses:
        print("  Scan with a phone camera:")
        print_qr(f"http://{addresses[0]}:{args.port}")
    print("  Keep this window open. Press Ctrl+C to stop the server.")
    print(line, flush=True)

    serve(app, host=args.host, port=args.port, threads=args.threads, ident="RangeDrill")


if __name__ == "__main__":
    main()
