import threading
import uvicorn
import os
import sys

# Ensure SSL certs exist
from generate_ssl_certs import generate_self_signed_cert
cert_path, key_path = generate_self_signed_cert()

def run_http():
    print("[Server 1] Starting HTTP Server on http://0.0.0.0:8000 ...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, log_level="warning")

def run_https():
    print(f"[Server 2] Starting Secure HTTPS Server on https://0.0.0.0:8443 (SSL active for Mobile Camera) ...")
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8443, 
        ssl_keyfile=key_path, 
        ssl_certfile=cert_path,
        log_level="warning"
    )

if __name__ == "__main__":
    from init_db import seed_database
    seed_database()

    t1 = threading.Thread(target=run_http, daemon=True)
    t2 = threading.Thread(target=run_https, daemon=True)

    t1.start()
    t2.start()

    print("\n" + "="*60)
    print(" 🏛️ LUNAR AURORA DUAL SERVERS ARE LIVE!")
    print("="*60)
    print(" • HTTP (Desktop & USB):  http://localhost:8000/app/")
    print(" • HTTPS (Mobile Camera): https://localhost:8443/app/")
    print(" • QR Code Generator:    http://localhost:8000/qr")
    print("="*60 + "\n")

    t1.join()
    t2.join()

