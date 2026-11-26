import os
import socket
import argparse
import datetime
import ipaddress
from typing import Optional, List
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def auto_detect_lan_ip() -> Optional[str]:
    """Detects this machine's active LAN IPv4 address (preferring 192.168/10/172 subnets)."""
    candidates: List[str] = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith("127.") and ip != "0.0.0.0":
                candidates.append(ip)
    except Exception:
        pass

    for prefix in ("192.168.", "10.", "172."):
        for ip in candidates:
            if ip.startswith(prefix):
                return ip

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass

    return candidates[0] if candidates else None


def generate_self_signed_cert(
    cert_file: str = "cert.pem",
    key_file: str = "key.pem",
    extra_ip: Optional[str] = None,
    force_rotate: bool = False,
):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cert_path = os.path.join(base_dir, cert_file)
    key_path = os.path.join(base_dir, key_file)

    if not force_rotate and os.path.exists(cert_path) and os.path.exists(key_path):
        print(f"[SSL] Certificates already exist: {cert_path}")
        return cert_path, key_path

    print("[SSL] Generating self-signed SSL certificate for Mobile WebXR...")
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Tamil Nadu"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Mahabalipuram"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Lunar Aurora"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])

    san_entries = [
        x509.DNSName("localhost"),
        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
    ]

    lan_ip = extra_ip or auto_detect_lan_ip()
    if lan_ip:
        try:
            ip_obj = ipaddress.IPv4Address(lan_ip)
            if str(ip_obj) != "127.0.0.1":
                san_entries.append(x509.IPAddress(ip_obj))
        except ValueError:
            san_entries.append(x509.DNSName(lan_ip))

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365))
        .add_extension(x509.SubjectAlternativeName(san_entries), critical=False)
        .sign(key, hashes.SHA256())
    )

    with open(key_path, "wb") as f:
        f.write(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    san_ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    print(f"[SSL] Certificate created: {cert_path} and {key_path}")
    print(f"[SSL] Serial: {hex(cert.serial_number)}")
    print(f"[SSL] SANs: {[str(entry.value) for entry in san_ext]}")
    return cert_path, key_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate or rotate self-signed SSL certificates for Lunar Aurora.")
    parser.add_argument("--ip", type=str, default=None, help="Optional LAN IPv4 address to include in SANs")
    parser.add_argument("--rotate", action="store_true", help="Force regeneration even if cert.pem/key.pem exist")
    args = parser.parse_args()
    generate_self_signed_cert(extra_ip=args.ip, force_rotate=True if (args.rotate or args.ip) else True)
