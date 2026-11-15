"""Real HTTP checks; start FastAPI and Vite (real mode) first. No private data output."""
import json
import os
from urllib.request import Request, urlopen

api = os.getenv("SMOKE_API_URL", "http://127.0.0.1:8000")
frontend = os.getenv("SMOKE_FRONTEND_URL", "http://127.0.0.1:5173")

def get(path):
    with urlopen(path, timeout=15) as response:
        return json.load(response)

def post(profile=None, history=None, limit=5):
    body = {"user_profile": profile or {}, "history": history or [], "limit": limit}
    request = Request(frontend + "/api/v1/recommendations", data=json.dumps(body).encode(),
                      headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=15) as response:
        result = json.load(response)
    assert result["metadata"]["returned"] == len(result["recommendations"])
    assert all(item["reasons"] and item["next_step"] for item in result["recommendations"])
    return result

assert get(api + "/health") == {"status": "ok"}
schema = get(api + "/openapi.json")
assert "user_profile" in schema["components"]["schemas"]["RecommendationRequest"]["properties"]
assert "reasons" in schema["components"]["schemas"]["RecommendationItem"]["properties"]
assert post()["metadata"]["cold_start"] is True
for goal in ("marketing", "finance", "team"):
    result = post({"current_goal": goal})
    if result["metadata"]["catalog_source"] == "sample":
        assert result["recommendations"][0]["topic"] in {"marketing": {"marketing"}, "finance": {"finance", "accounting"}, "team": {"operations", "team"}}[goal]
    print(goal, "source=" + result["metadata"]["catalog_source"], "strategy=" + result["metadata"]["strategy"], "returned=" + str(result["metadata"]["returned"]))
assert post({"industry": "retail"})["recommendations"]
assert post({"preferred_formats": ["course"]})["recommendations"][0]["material_type"] == "course"
first = post({"current_goal": "marketing"})["recommendations"][0]["material_id"]
assert first not in {r["material_id"] for r in post({"current_goal": "marketing"}, [{"material_id": first, "event_type": "view"}])["recommendations"]}
all_items = post(limit=50)["recommendations"]
assert post(history=[{"material_id": r["material_id"]} for r in all_items])["recommendations"] == []
print("HTTP health, OpenAPI, Vite proxy, goals, cold/partial profile, formats, history and empty response: OK")
