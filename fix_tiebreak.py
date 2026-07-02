import csv

with open("submission.csv", "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

rows.sort(key=lambda x: (-float(x["score"]), x["candidate_id"]))

for i, row in enumerate(rows, start=1):
    row["rank"] = i

with open("submission.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["candidate_id","rank","score","reasoning"])
    w.writeheader()
    w.writerows(rows)

print("Fixed! Tie-break applied.")
