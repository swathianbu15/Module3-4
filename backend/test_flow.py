"""Quick end-to-end smoke test — not a formal test suite, just a sanity check."""
import sys
sys.path.insert(0, '.')
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=" * 60)
print("1. Create personalization (Module 3)")
print("=" * 60)
r = client.post("/api/personalization", json={
    "user_id": 25,
    "roadmap_id": 101,
    "learning_goal": "Become job ready",
    "hours_per_day": 2,
    "available_days": ["Monday", "Tuesday", "Wednesday", "Friday", "Saturday"],
    "target_date": "2026-11-30",
    "skill_level": "intermediate"
})
print(r.status_code)
assert r.status_code == 201, r.text
prefs = r.json()
print(prefs)

print("\n" + "=" * 60)
print("2. Get personalization back")
print("=" * 60)
r = client.get("/api/personalization/25/101")
print(r.status_code)
assert r.status_code == 200
print(r.json())

print("\n" + "=" * 60)
print("3. Generate learning plan (Module 4)")
print("=" * 60)
r = client.post("/api/learning-plans/generate", json={
    "user_id": 25,
    "roadmap_id": 101,
    "use_ai": False
})
print(r.status_code)
assert r.status_code == 201, r.text
plan = r.json()
print(f"Plan ID: {plan['plan_id']}")
print(f"Status: {plan['status']}")
print(f"Total days: {len(plan['days'])}")
print(f"\nFirst 3 days:")
for day in plan['days'][:3]:
    print(f"\n  Day {day['day']} ({day['date']}) - {day['total_minutes']} min")
    for task in day['tasks']:
        print(f"    [{task['task_type']}] {task['task_title']} ({task['estimated_minutes']} min)")
        print(f"      -> {task['description']}")

print(f"\nLast day:")
last = plan['days'][-1]
print(f"  Day {last['day']} ({last['date']}) - {last['total_minutes']} min")
for task in last['tasks']:
    print(f"    [{task['task_type']}] {task['task_title']} ({task['estimated_minutes']} min)")

print("\n" + "=" * 60)
print("4. Get plan by ID")
print("=" * 60)
r = client.get(f"/api/learning-plans/{plan['plan_id']}")
print(r.status_code)
assert r.status_code == 200

print("\n" + "=" * 60)
print("5. Adapt plan — mark day 1 tasks completed, day 2 missed")
print("=" * 60)
day1_task_ids = [t['id'] for t in plan['days'][0]['tasks']]
day2_task_ids = [t['id'] for t in plan['days'][1]['tasks']] if len(plan['days']) > 1 else []

updates = [{"task_id": tid, "status": "completed"} for tid in day1_task_ids]
updates += [{"task_id": tid, "status": "missed"} for tid in day2_task_ids]

r = client.post(f"/api/learning-plans/{plan['plan_id']}/adapt", json={
    "task_updates": updates
})
print(r.status_code)
assert r.status_code == 200, r.text
adapted = r.json()
print(f"Total days after adaptation: {len(adapted['days'])}")
print(f"Day 1 task statuses preserved: {[t['status'] for t in adapted['days'][0]['tasks']]}")

print("\n" + "=" * 60)
print("6. Validation error test — bad day name")
print("=" * 60)
r = client.post("/api/personalization", json={
    "user_id": 99,
    "roadmap_id": 101,
    "learning_goal": "test",
    "hours_per_day": 2,
    "available_days": ["Funday"],
    "target_date": "2026-11-30",
    "skill_level": "intermediate"
})
print(r.status_code, "(expect 422)")
assert r.status_code == 422

print("\n" + "=" * 60)
print("7. Missing preferences error test")
print("=" * 60)
r = client.post("/api/learning-plans/generate", json={
    "user_id": 999,
    "roadmap_id": 101,
    "use_ai": False
})
print(r.status_code, "(expect 404)")
assert r.status_code == 404

print("\n" + "=" * 60)
print("ALL TESTS PASSED")
print("=" * 60)
