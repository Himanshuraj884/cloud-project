"""Task 7 cost + SLO worksheet. Prints every step.
  python scripts/cost.py results/loadtest_stats.csv --replicas 2 --cpu-limit 1 --mem-limit-gib 1 [--slo 99]
Uses the 'Aggregated' (or only) row of Locust's *_stats.csv and data/rate_card.json."""
import argparse
import csv
import json

ap = argparse.ArgumentParser()
ap.add_argument("stats")
ap.add_argument("--replicas", type=int, required=True)
ap.add_argument("--cpu-limit", type=float, default=1.0)
ap.add_argument("--mem-limit-gib", type=float, default=1.0)
ap.add_argument("--slo", type=float, default=99.0, help="target success percentage")
ap.add_argument("--rate-card", default="data/rate_card.json")
a = ap.parse_args()

rows = list(csv.DictReader(open(a.stats, encoding="utf-8")))
row = next((r for r in rows if r["Name"] == "Aggregated"), rows[-1])
reqs, fails = int(row["Request Count"]), int(row["Failure Count"])
rps = float(row["Requests/s"])
rate = json.load(open(a.rate_card))

per_replica = a.cpu_limit * rate["vcpu_hour"] + a.mem_limit_gib * rate["gib_memory_hour"]
hourly = a.replicas * per_replica
per_hour = rps * 3600
cost = hourly / per_hour * 1000
print(f"Per replica per hour = {a.cpu_limit} vCPU x {rate['vcpu_hour']} + {a.mem_limit_gib} GiB x "
      f"{rate['gib_memory_hour']} = {per_replica:.4f} {rate['currency']}")
print(f"Hourly cost of {a.replicas} replicas = {a.replicas} x {per_replica:.4f} = "
      f"{hourly:.4f} {rate['currency']}")
print(f"Requests served per hour = {rps:.3f} req/s x 3600 = {per_hour:.1f}")
print(f"Cost per 1,000 requests = {hourly:.4f} / {per_hour:.1f} x 1000 = {cost:.4f} {rate['currency']}")
budget = reqs * (100 - a.slo) / 100
print(f"\nSLO: {a.slo}% of requests succeed, window = one load-test run ({reqs} requests)")
print(f"Error budget = {reqs} x (1 - {a.slo / 100}) = {budget:.1f} requests")
print(f"Failures = {fails} -> budget used = {fails / budget * 100 if budget else 0:.1f}% "
      f"(error rate {fails / reqs * 100 if reqs else 0:.3f}%)")
