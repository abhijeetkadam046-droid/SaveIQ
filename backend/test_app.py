import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from backend.main import app

def run_tests():
    client = TestClient(app)
    print("Testing SaveIQ Endpoints...")

    # 1. Health
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("[PASS] Health check passed")

    # 2. Dashboard Summary
    res = client.get("/api/dashboard/summary")
    assert res.status_code == 200, f"Dashboard summary failed: {res.text}"
    summary = res.json()
    assert summary["total_goals"] >= 5, "Initial goals were not seeded properly"
    print(f"[PASS] Dashboard summary passed: {summary['total_goals']} goals, ${summary['total_saved']:,.2f} saved")

    # 3. Create Goal
    new_goal_payload = {
        "name": "Japan Cherry Blossom Trip",
        "category": "Travel & Vacation",
        "target_amount": 4500.0,
        "initial_savings": 1500.0,
        "deadline": "2026-11-30",
        "email_alerts": True,
        "user_email": "test@saveiq.ai",
        "purpose": "Spring trip across Tokyo & Kyoto",
        "priority": "High"
    }
    res = client.post("/api/goals", json=new_goal_payload)
    assert res.status_code == 200, f"Goal creation failed: {res.text}"
    created = res.json()
    assert created["name"] == "Japan Cherry Blossom Trip"
    goal_id = created["id"]
    print(f"[PASS] Goal creation passed (ID: {goal_id})")

    # 4. Record Deposit
    deposit_payload = {
        "amount": 500.0,
        "note": "Paycheck contribution"
    }
    res = client.post(f"/api/goals/{goal_id}/deposit", json=deposit_payload)
    assert res.status_code == 200, f"Deposit failed: {res.text}"
    updated_goal = res.json()["goal"]
    assert updated_goal["current_amount"] == 2000.0
    print(f"[PASS] Deposit recorded successfully (New Balance: ${updated_goal['current_amount']})")

    # 5. AI Financial Recommendation
    res = client.post(f"/api/ai/recommendation/{goal_id}")
    assert res.status_code == 200, f"AI Recommendation failed: {res.text}"
    ai_data = res.json()
    assert "recommendation" in ai_data
    assert "strategies" in ai_data
    print(f"[PASS] AI Advisor recommendation passed (Score: {ai_data['feasibility_score']}%, Daily: ${ai_data['daily_saving_target']}/d)")

    # 6. Automated Financial Audit
    res = client.post("/api/audit/run")
    assert res.status_code == 200, f"Audit failed: {res.text}"
    audit_data = res.json()
    print(f"[PASS] Automated audit engine passed ({audit_data['audited_count']} audited, {audit_data['alerts_created']} alerts)")

    # 7. PDF Report Generation
    res = client.get("/api/reports/download-pdf")
    assert res.status_code == 200, f"PDF generation failed: {res.text}"
    assert res.headers["content-type"] == "application/pdf"
    assert len(res.content) > 1000, "PDF content is too small"
    print(f"[PASS] ReportLab PDF report generation passed ({len(res.content)} bytes)")

    # 8. Google Sheets CSV Export
    res = client.get("/api/export/sheets-csv")
    assert res.status_code == 200, f"CSV export failed: {res.text}"
    assert "Goal ID,Goal Name" in res.text
    print("[PASS] Google Sheets CSV export passed")

    # 9. Frontend HTML Serving
    res = client.get("/")
    assert res.status_code == 200
    assert "SaveIQ" in res.text
    print("[PASS] Frontend HTML serving passed")

    print("\n>>> ALL 9 TEST SUITES PASSED FLAWLESSLY! <<<")

if __name__ == "__main__":
    run_tests()
