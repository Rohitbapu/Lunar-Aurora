import json
import os
import re
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.config import settings
from app.database import SessionLocal
from app.main import app
from app.services.routing_service import routing_service
from app.services.tts_service import tts_service
from init_db import seed_database


def measure(label: str, fn, iterations: int = 20):
    # Single unmeasured warmup so first-call lazy init does not skew 20 measured runs
    fn()
    latencies_ms = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        fn()
        latencies_ms.append((time.perf_counter() - t0) * 1000.0)
    latencies_ms.sort()
    p95_idx = min(len(latencies_ms) - 1, max(0, int(0.95 * len(latencies_ms)) - 1))
    return {
        "operation": label,
        "status": "MEASURED",
        "iterations": iterations,
        "mean_ms": round(statistics.mean(latencies_ms), 2),
        "p95_ms": round(latencies_ms[p95_idx], 2),
        "min_ms": round(min(latencies_ms), 2),
        "max_ms": round(max(latencies_ms), 2),
    }


def run_api_test_suite() -> dict:
    t0 = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, "test_suite.py"],
        capture_output=True,
        text=True,
        check=False,
    )
    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    output = proc.stdout + "\n" + proc.stderr
    ok_steps = len(re.findall(r"-> OK", output))
    return {
        "status": "MEASURED",
        "exit_code": proc.returncode,
        "passed_steps": ok_steps,
        "total_steps": 9,
        "pass_rate_pct": round((ok_steps / 9.0) * 100.0, 1) if proc.returncode == 0 else 0.0,
        "duration_ms": elapsed_ms,
    }


def main():
    seed_database(force_reset=True)
    client = TestClient(app)
    db = SessionLocal()

    try:
        ticket = client.post(
            "/api/ticket/create",
            json={"customer_name": "Benchmark Guest", "preferred_language": "en"},
        ).json()
        sid = ticket["session_id"]

        client.post(
            "/api/session/start",
            json={"session_id": sid, "customer_name": "Benchmark Guest", "generate_audio": False},
        )

        # Verify precached audio sample exists
        cached_rel_url = tts_service.resolve_precached_url("stop_1", "en")
        if not cached_rel_url:
            raise RuntimeError("Missing precached stop_1_en.mp3 in static/audio_cache")

        benchmarks = [
            measure(
                "Dijkstra shaded-route compute (direct DB graph)",
                lambda: routing_service.find_path(
                    db, start_id=1, target_id=7, mode="shaded", hour=12.0, date_str="2027-01-11"
                ),
                iterations=20,
            ),
            measure(
                "NOAA solar calculation (2027-01-11 12:00 IST)",
                lambda: routing_service.calculate_solar_position_details(
                    hour=12.0, date_str="2027-01-11"
                ),
                iterations=20,
            ),
            measure(
                f"Cached-audio hit (GET {cached_rel_url})",
                lambda: client.get(cached_rel_url),
                iterations=20,
            ),
        ]

        groq_key = (os.getenv("GROQ_API_KEY") or settings.GROQ_API_KEY or "").strip()
        if not groq_key:
            benchmarks.append(
                {
                    "operation": "Online AI latency (Groq + Edge-TTS)",
                    "status": "NOT MEASURED - no API key",
                    "iterations": 0,
                    "mean_ms": None,
                    "p95_ms": None,
                    "min_ms": None,
                    "max_ms": None,
                }
            )
        else:
            benchmarks.append(
                measure(
                    "Online AI latency (Groq + Edge-TTS)",
                    lambda: client.post(
                        "/api/chat",
                        json={
                            "message": "Where is Shore Temple?",
                            "customer_name": "Benchmark Guest",
                            "current_step": 2,
                            "session_id": sid,
                            "language": "en",
                            "generate_audio": True,
                        },
                    ),
                    iterations=20,
                )
            )

        benchmarks.extend(
            [
                measure(
                    "Vision metadata lookup (POST /api/vision/identify)",
                    lambda: client.post(
                        "/api/vision/identify",
                        json={
                            "detected_labels": ["shore_temple_vimana"],
                            "current_step": 2,
                            "session_id": sid,
                            "language": "en",
                        },
                    ),
                    iterations=20,
                ),
                measure(
                    "Dual-route NOAA telemetry (GET /api/site/telemetry)",
                    lambda: client.get(
                        "/api/site/telemetry?start_id=1&target_id=7&hour=12.0&date=2027-01-11"
                    ),
                    iterations=20,
                ),
                measure(
                    "PDF Travel Journal export (POST /api/tour/{sid}/journal)",
                    lambda: client.post(f"/api/tour/{sid}/journal", json={}),
                    iterations=20,
                ),
            ]
        )
    finally:
        db.close()

    api_tests = run_api_test_suite()

    device_hardware_kpis = {
        "mobile_fps": "MEASURE ON DEVICE",
        "qr_to_ar_launch_ms": "MEASURE ON DEVICE",
        "vision_on_device_ms": "MEASURE ON DEVICE",
        "unity_frame_time_ms": "MEASURE ON DEVICE",
    }

    timestamp_utc = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = f"benchmark_results_{timestamp_utc}.json"

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "site": "Mahabalipuram (12.6165 N, 80.19 E)",
        "default_demo_date": "2027-01-11",
        "backend_benchmarks": benchmarks,
        "api_test_suite": api_tests,
        "device_hardware_kpis": device_hardware_kpis,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print("\n" + "=" * 86)
    print(" LUNAR AURORA - MEASURED KPI BENCHMARK (20 ITERATIONS)")
    print("=" * 86)
    print(f"{'Operation':50} | {'Mean':>10} | {'P95':>10} | {'Status'}")
    print("-" * 86)
    for row in benchmarks:
        mean_str = f"{row['mean_ms']:.2f}ms" if row["mean_ms"] is not None else "N/A"
        p95_str = f"{row['p95_ms']:.2f}ms" if row["p95_ms"] is not None else "N/A"
        print(f"{row['operation'][:50]:50} | {mean_str:>10} | {p95_str:>10} | {row['status']}")
    print("-" * 86)
    print(
        f"API Test Pass Rate: {api_tests['passed_steps']}/{api_tests['total_steps']} "
        f"({api_tests['pass_rate_pct']}%) in {api_tests['duration_ms']}ms"
    )
    print("\nDevice / Hardware KPIs (pending field hardware profiling):")
    for k, v in device_hardware_kpis.items():
        print(f"  - {k}: {v}")
    print("=" * 86)
    print(f"Saved timestamped JSON report to {out_path}")


if __name__ == "__main__":
    main()
