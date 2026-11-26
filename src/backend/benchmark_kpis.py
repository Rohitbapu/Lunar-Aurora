import time
import json
import statistics
from fastapi.testclient import TestClient
from app.main import app
from init_db import seed_database

def measure(label: str, fn, iterations: int = 20):
    latencies_ms = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        fn()
        latencies_ms.append((time.perf_counter() - t0) * 1000.0)
    latencies_ms.sort()
    p95_idx = min(len(latencies_ms) - 1, int(0.95 * len(latencies_ms)))
    return {
        "operation": label,
        "iterations": iterations,
        "mean_ms": round(statistics.mean(latencies_ms), 2),
        "p95_ms": round(latencies_ms[p95_idx], 2),
        "min_ms": round(min(latencies_ms), 2),
        "max_ms": round(max(latencies_ms), 2),
    }

def main():
    seed_database(force_reset=False)
    client = TestClient(app)

    ticket = client.post("/api/ticket/create", json={"customer_name": "Benchmark Guest", "preferred_language": "en"}).json()
    sid = ticket["session_id"]

    results = [
        measure(
            "Solar Dual-Route Telemetry (GET /api/site/telemetry)",
            lambda: client.get("/api/site/telemetry?start_id=1&target_id=7&hour=13.0"),
        ),
        measure(
            "Vision Relic Identification + Offline Audio Lookup (POST /api/vision/identify)",
            lambda: client.post("/api/vision/identify", json={"detected_labels": ["yali_pillar"], "current_step": 2, "session_id": sid, "language": "en"}),
        ),
        measure(
            "Personalized Session Start with Pre-Cached Audio (POST /api/session/start)",
            lambda: client.post("/api/session/start", json={"session_id": sid, "generate_audio": True}),
        ),
        measure(
            "Riddle Submission & XP Evaluation (POST /api/session/riddle)",
            lambda: client.post("/api/session/riddle", json={"session_id": sid, "step_number": 1, "answer": "Narasimhavarman II (Rajasimha)"}),
        ),
        measure(
            "PDF Travel Journal Generation (POST /api/tour/{session_id}/journal)",
            lambda: client.post(f"/api/tour/{sid}/journal", json={}),
        ),
    ]

    out_path = "benchmark_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 78)
    print(" LUNAR AURORA - 20-ITERATION LATENCY & KPI BENCHMARK")
    print("=" * 78)
    print(f"{'Operation':56} | {'Mean':>8} | {'P95':>8}")
    print("-" * 78)
    for row in results:
        print(f"{row['operation'][:56]:56} | {row['mean_ms']:6.2f}ms | {row['p95_ms']:6.2f}ms")
    print("=" * 78)
    print(f"Saved JSON report to {out_path}")

if __name__ == "__main__":
    main()
