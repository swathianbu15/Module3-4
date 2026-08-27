"""Smoke test for the 'skip known topics' feature (Module 3 + 4)."""
import sys
sys.path.insert(0, '.')
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("Create preferences with known_topic_ids=[1, 2] (HTML, CSS already known)")
r = client.post("/api/personalization", json={
    "user_id": 77,
    "roadmap_id": 101,
    "learning_goal": "Become job ready",
    "hours_per_day": 2,
    "available_days": ["Monday", "Tuesday", "Wednesday", "Friday", "Saturday"],
    "target_date": "2026-11-30",
    "skill_level": "intermediate",
    "known_topic_ids": [1, 2]
})
assert r.status_code == 201, r.text
print(r.json())
assert r.json()["known_topic_ids"] == [1, 2]

print("\nGenerate plan — HTML/CSS should be skipped entirely")
r = client.post("/api/learning-plans/generate", json={
    "user_id": 77,
    "roadmap_id": 101,
    "use_ai": False
})
assert r.status_code == 201, r.text
plan = r.json()

all_topics = set()
for day in plan["days"]:
    for task in day["tasks"]:
        all_topics.add(task["topic_title"])

print(f"Topics scheduled: {sorted(all_topics)}")
assert "HTML" not in all_topics, "HTML should have been skipped!"
assert "CSS" not in all_topics, "CSS should have been skipped!"
assert "JavaScript" in all_topics, "JavaScript should still be scheduled"

print(f"\nTotal days needed: {len(plan['days'])} (should be fewer than the full-roadmap 60)")
assert len(plan["days"]) < 60

print("\nPASSED — known topics correctly skipped")
