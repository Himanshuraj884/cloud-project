"""Task 4 step 7: delete all Pods, measure Pod creation -> Ready, 3 runs, median.
  python scripts/coldstart.py [runs]   (writes results/coldstart.json)"""
import json
import statistics
import subprocess
import sys
import time
from datetime import datetime


def kubectl(*a):
    return subprocess.run(["kubectl", "-n", "app", *a], check=True, capture_output=True, text=True).stdout


def ts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").timestamp()


runs, times = int(sys.argv[1]) if len(sys.argv) > 1 else 3, []
for r in range(1, runs + 1):
    kubectl("delete", "pods", "-l", "app=parser", "--wait=true")
    want = int(json.loads(kubectl("get", "deploy", "parser", "-o", "json"))["spec"]["replicas"])
    while True:
        pods = json.loads(kubectl("get", "pods", "-l", "app=parser", "-o", "json"))["items"]
        ready = [p for p in pods if any(c["type"] == "Ready" and c["status"] == "True"
                                        for c in p["status"].get("conditions", []))]
        if len(ready) >= want:
            break
        time.sleep(1)
    for p in ready:
        created = ts(p["metadata"]["creationTimestamp"])
        rdy = next(ts(c["lastTransitionTime"]) for c in p["status"]["conditions"] if c["type"] == "Ready")
        times.append(rdy - created)
        print(f"run {r}: {p['metadata']['name']} created->Ready {rdy - created:.0f}s")
    print(kubectl("logs", ready[0]["metadata"]["name"]).strip().splitlines()[-3:])
med = statistics.median(times)
print("median seconds:", med)
json.dump({"times_s": times, "median_s": med}, open("results/coldstart.json", "w"), indent=2)
