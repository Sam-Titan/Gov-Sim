"""Start-up time and peak memory of the API, for the Render free plan (512 MB).

Run from the repo root (as Render does) or from backend/:
    cd backend && uv run python -m scripts.check_memory
It loads the API (629 districts x 500 agents), sends every scheme through /simulate,
/simulate/state and /compare, and prints the start-up seconds and the peak resident memory.
Exit code 1 if the peak is over the limit.
"""

import resource
import sys
import time

from fastapi.testclient import TestClient

LIMIT_MB = 350  # Render free = 512 MB; leaves room for the OS and a request spike
SCHEMES = ("pmjay", "pmuy", "jsy", "sbm")


def peak_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # Linux: KiB


def main() -> int:
    from app.main import app

    t = time.perf_counter()
    with TestClient(app) as client:  # runs the lifespan = Service() load
        startup = time.perf_counter() - t
        after_load = peak_mb()
        districts = [d for d in client.get("/api/districts").json() if d["has_data"]]
        states = sorted({d["state"] for d in districts})
        n = 0
        for scheme in SCHEMES:
            for d in districts[:: max(1, len(districts) // 40)]:
                client.post("/api/simulate", json={"district_id": d["id"], "scheme": scheme})
                n += 1
            client.post("/api/simulate/state", json={"state": states[0], "scheme": scheme})
            d0 = districts[0]["id"]
            client.post(
                "/api/compare",
                json={"district_id": d0, "a": {"scheme": scheme}, "b": {"scheme": scheme}},
            )
        peak = peak_mb()
    print(f"districts with data: {len(districts)}  requests: {n}")
    print(f"start-up: {startup:.2f} s")
    print(f"peak memory after load: {after_load:.0f} MB, after requests: {peak:.0f} MB")
    print(f"limit {LIMIT_MB} MB: {'OK' if peak < LIMIT_MB else 'OVER'}")
    return 0 if peak < LIMIT_MB else 1


if __name__ == "__main__":
    sys.exit(main())
