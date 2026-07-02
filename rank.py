import json, csv, argparse, heapq

KEYWORDS = [
    "embedding","embeddings","retrieval","vector","faiss","qdrant","weaviate","milvus",
    "elasticsearch","opensearch","rag","ranking","nlp","information retrieval",
    "llm","fine-tuning","lora","qlora","peft","transformers","bert","pytorch","tensorflow","python","search"
]
SERVICE = ["tcs","infosys","wipro","accenture","cognizant","capgemini","hcl","tech mahindra","mphasis","hexaware"]

def txt(c):
    p = c.get("profile", {})
    skills = " ".join(str(s.get("name","")) for s in c.get("skills", []))
    roles = " ".join(str(r.get("title","")) for r in c.get("career_history", []))
    summ = str(p.get("summary",""))[:300]
    return f"{p.get('headline','')} {p.get('current_title','')} {summ} {skills} {roles}".lower()

def score(c, t):
    s = 0
    for k in KEYWORDS:
        if k in t:
            s += 1
    yoe = float(c.get("profile", {}).get("years_of_experience", 0) or 0)
    if 5 <= yoe <= 9: s += 5
    elif 4 <= yoe <= 12: s += 2
    notice = float(c.get("redrob_signals", {}).get("notice_period_days", 90) or 90)
    if notice <= 30: s += 2
    companies = " ".join(str(r.get("company","")).lower() for r in c.get("career_history", []))
    if not any(x in companies for x in SERVICE): s += 2
    if c.get("redrob_signals", {}).get("open_to_work_flag"): s += 1
    return s

def reasoning(c):
    p = c.get("profile", {})
    sig = c.get("redrob_signals", {})
    skills = [str(s.get("name","")) for s in c.get("skills", []) if str(s.get("name","")).strip()][:3]
    return f"{p.get('current_title','Engineer')} with {float(p.get('years_of_experience',0) or 0):.1f} yrs; {', '.join(skills) if skills else 'relevant skills'}; notice {int(float(sig.get('notice_period_days',90) or 90))}d"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    heap = []
    with open(args.candidates, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                c = json.loads(line)
            except:
                continue
            cid = c.get("candidate_id")
            if not cid:
                continue
            t = txt(c)
            s = score(c, t)
            heapq.heappush(heap, (s, cid, c))
            if len(heap) > 200:
                heapq.heappop(heap)
            if i % 10000 == 0:
                print(f"Scanned {i} candidates", flush=True)

    top = sorted(heap, reverse=True)[:100]
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["candidate_id","rank","score","reasoning"])
        for rank, (s, cid, c) in enumerate(top, start=1):
            w.writerow([cid, rank, s, reasoning(c)])
    print(f"Done. Wrote {len(top)} rows to {args.out}", flush=True)

if __name__ == "__main__":
    main()
