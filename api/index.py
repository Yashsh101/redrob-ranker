import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from ranker.engine import score_candidate, is_disqualified, normalise_scores  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def _send(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(200, {"ok": True})

    def do_GET(self):
        self._send(200, {"name": "Red Rob Ranker API", "status": "ready"})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            candidates = payload.get("candidates", [])
            as_of = __import__("datetime").date.fromisoformat(payload.get("as_of_date", "2026-05-31"))
            scored = []
            for candidate in candidates:
                cid = str(candidate.get("candidate_id", ""))
                if cid and not is_disqualified(candidate):
                    raw, features = score_candidate(candidate, as_of)
                    scored.append((raw, cid, candidate, features))
            ranked = sorted(scored, key=lambda item: (-item[0], item[1]))[:100]
            rows = []
            for rank, (raw, cid, candidate, features, normalized) in enumerate(normalise_scores(ranked), 1):
                rows.append({"candidate_id": cid, "rank": rank, "score": round(normalized, 6), "features": features})
            self._send(200, {"count": len(rows), "results": rows})
        except Exception as exc:
            self._send(400, {"error": str(exc)})
