import logging
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path

from backend.config import APP_NAME, APP_VERSION, BASE_DIR
from backend.database import init_db, get_db
from backend.models import (
    GoalCreate, GoalUpdate, DepositCreate, GoalResponse,
    DashboardSummary, AIAdviceRequest, AIAdviceResponse, AuditRunResponse
)
from backend.ai_service import generate_ai_recommendation
from backend.pdf_service import generate_savings_pdf
from backend.audit_service import run_daily_financial_audit
from backend.sheets_service import export_goals_to_csv
from backend.seed_data import seed_initial_data

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("saveiq.main")

# Initialize App
app = FastAPI(title=APP_NAME, version=APP_VERSION, description="AI-Powered Personal Finance & Savings Goal Tracker")

# Enable CORS for cross-origin or local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure DB & Seed data are created immediately
init_db()
seed_initial_data()

# Startup event to ensure DB and initial seeds
@app.on_event("startup")
def on_startup():
    init_db()
    seed_initial_data()
    logger.info("SaveIQ backend initialized successfully.")

# Helper to enrich goal dictionary
def enrich_goal(g: dict) -> dict:
    target = float(g.get("target_amount", 0.0))
    current = float(g.get("current_amount", 0.0))
    remaining = max(0.0, target - current)
    progress = round((current / target * 100), 1) if target > 0 else 100.0

    today = datetime.now().date()
    days_left = 30
    deadline_str = g.get("deadline", "")
    if deadline_str:
        try:
            deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d").date()
            diff = (deadline_date - today).days
            days_left = diff
        except Exception:
            days_left = 30

    daily_req = round(remaining / max(1, days_left), 2) if days_left > 0 else remaining

    # Determine status badge
    status = g.get("status", "Active")
    if current >= target:
        status_badge = "Completed"
    elif days_left < 0:
        status_badge = "Overdue"
    elif days_left <= 7:
        status_badge = "Urgent"
    else:
        status_badge = status

    return {
        **g,
        "email_alerts": bool(g.get("email_alerts", 1)),
        "progress_percentage": progress,
        "remaining_amount": remaining,
        "days_remaining": days_left,
        "daily_required": daily_req,
        "status_badge": status_badge
    }

# ----------------- Goal Endpoints -----------------

@app.get("/api/goals", response_model=List[GoalResponse])
def get_all_goals(category: Optional[str] = None, status: Optional[str] = None):
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM goals WHERE 1=1"
        params = []
        if category and category != "All":
            query += " AND category = ?"
            params.append(category)
        if status and status != "All":
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY id DESC"
        cursor.execute(query, params)
        raw_goals = [dict(row) for row in cursor.fetchall()]
        return [enrich_goal(g) for g in raw_goals]

@app.post("/api/goals", response_model=GoalResponse)
def create_goal(goal: GoalCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "Completed" if goal.initial_savings >= goal.target_amount else "Active"

        cursor.execute("""
            INSERT INTO goals (
                name, category, target_amount, current_amount, deadline,
                email_alerts, user_email, purpose, priority, status,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            goal.name, goal.category, goal.target_amount, goal.initial_savings,
            goal.deadline, 1 if goal.email_alerts else 0, goal.user_email,
            goal.purpose or "", goal.priority or "Medium", status,
            now_str, now_str
        ))
        goal_id = cursor.lastrowid

        if goal.initial_savings > 0:
            cursor.execute("""
                INSERT INTO deposits (goal_id, amount, note, date)
                VALUES (?, ?, ?, ?)
            """, (goal_id, goal.initial_savings, "Initial Savings Balance", datetime.now().strftime("%Y-%m-%d")))

        cursor.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
        created = dict(cursor.fetchone())
        return enrich_goal(created)

@app.get("/api/goals/{goal_id}")
def get_goal(goal_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Goal not found")
        goal_data = enrich_goal(dict(row))

        cursor.execute("SELECT * FROM deposits WHERE goal_id = ? ORDER BY id DESC", (goal_id,))
        deposits = [dict(d) for d in cursor.fetchall()]

        cursor.execute("SELECT * FROM ai_insights WHERE goal_id = ? ORDER BY id DESC LIMIT 5", (goal_id,))
        insights = [dict(i) for i in cursor.fetchall()]

        return {
            "goal": goal_data,
            "deposits": deposits,
            "insights": insights
        }

@app.put("/api/goals/{goal_id}", response_model=GoalResponse)
def update_goal(goal_id: int, updates: GoalUpdate):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
        current = cursor.fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="Goal not found")

        current_dict = dict(current)
        up_dict = updates.model_dump(exclude_unset=True)
        if "email_alerts" in up_dict and up_dict["email_alerts"] is not None:
            up_dict["email_alerts"] = 1 if up_dict["email_alerts"] else 0

        up_dict["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        fields = [f"{k} = ?" for k in up_dict.keys()]
        values = list(up_dict.values()) + [goal_id]

        cursor.execute(f"UPDATE goals SET {', '.join(fields)} WHERE id = ?", values)
        cursor.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
        return enrich_goal(dict(cursor.fetchone()))

@app.delete("/api/goals/{goal_id}")
def delete_goal(goal_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM deposits WHERE goal_id = ?", (goal_id,))
        cursor.execute("DELETE FROM ai_insights WHERE goal_id = ?", (goal_id,))
        cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Goal not found")
        return {"success": True, "message": "Goal successfully deleted"}

@app.post("/api/goals/{goal_id}/deposit")
def add_deposit(goal_id: int, deposit: DepositCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
        goal = cursor.fetchone()
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")

        goal_dict = dict(goal)
        deposit_date = deposit.date or datetime.now().strftime("%Y-%m-%d")

        # Insert deposit record
        cursor.execute("""
            INSERT INTO deposits (goal_id, amount, note, date)
            VALUES (?, ?, ?, ?)
        """, (goal_id, deposit.amount, deposit.note or "Savings Deposit", deposit_date))

        # Update goal current amount
        new_amount = float(goal_dict["current_amount"]) + deposit.amount
        target = float(goal_dict["target_amount"])
        new_status = "Completed" if new_amount >= target else goal_dict["status"]

        cursor.execute("""
            UPDATE goals SET current_amount = ?, status = ?, updated_at = ?
            WHERE id = ?
        """, (new_amount, new_status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), goal_id))

        cursor.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
        return {
            "success": True,
            "goal": enrich_goal(dict(cursor.fetchone())),
            "added_amount": deposit.amount
        }

# ----------------- Dashboard Summary -----------------

@app.get("/api/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM goals")
        raw_goals = [dict(row) for row in cursor.fetchall()]
        enriched = [enrich_goal(g) for g in raw_goals]

        total_goals = len(enriched)
        active_goals = len([g for g in enriched if g["status"] == "Active"])
        completed_goals = len([g for g in enriched if g["status"] == "Completed"])
        overdue_goals = len([g for g in enriched if g["days_remaining"] < 0 and g["status"] != "Completed"])

        total_target = sum(g["target_amount"] for g in enriched)
        total_saved = sum(g["current_amount"] for g in enriched)
        overall_progress = round((total_saved / total_target * 100), 1) if total_target > 0 else 0.0

        # Discipline score calculation
        if total_goals == 0:
            discipline_score = 100
        else:
            on_track = len([g for g in enriched if g["status"] == "Completed" or (g["days_remaining"] >= 0 and g["progress_percentage"] >= 40)])
            discipline_score = min(100, max(20, int((on_track / total_goals) * 85 + (overall_progress * 0.15))))

        # Category breakdown
        category_breakdown = {}
        for g in enriched:
            cat = g["category"]
            category_breakdown[cat] = category_breakdown.get(cat, 0.0) + g["current_amount"]

        # Urgent goals (< 30 days and not completed)
        urgent = [
            g for g in enriched
            if g["status"] != "Completed" and 0 <= g["days_remaining"] <= 30
        ]
        urgent.sort(key=lambda x: x["days_remaining"])

        # Recent alerts
        cursor.execute("SELECT * FROM audit_alerts ORDER BY id DESC LIMIT 5")
        recent_alerts = [dict(a) for a in cursor.fetchall()]

        return DashboardSummary(
            total_goals=total_goals,
            active_goals=active_goals,
            completed_goals=completed_goals,
            overdue_goals=overdue_goals,
            total_target=total_target,
            total_saved=total_saved,
            overall_progress=overall_progress,
            discipline_score=discipline_score,
            category_breakdown=category_breakdown,
            urgent_goals=urgent[:4],
            recent_alerts=recent_alerts
        )

# ----------------- AI Financial Advisory -----------------

@app.post("/api/ai/recommendation/{goal_id}", response_model=AIAdviceResponse)
def get_ai_goal_recommendation(goal_id: int, req: Optional[AIAdviceRequest] = None):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Goal not found")

        goal = dict(row)
        user_prompt = req.prompt if req else ""
        advice = generate_ai_recommendation(goal, user_prompt)

        # Store insight in DB history
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO ai_insights (goal_id, goal_name, recommendation, daily_saving_target, feasibility_score, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            goal_id,
            goal["name"],
            advice.get("recommendation", ""),
            advice.get("daily_saving_target", 0.0),
            advice.get("feasibility_score", 85),
            now_str
        ))
        conn.commit()

        return AIAdviceResponse(**advice)

# ----------------- Automated Audit & Alerts -----------------

@app.post("/api/audit/run", response_model=AuditRunResponse)
def trigger_audit():
    with get_db() as conn:
        result = run_daily_financial_audit(conn)
        return AuditRunResponse(**result)

@app.get("/api/alerts")
def get_alerts(limit: int = Query(20, ge=1, le=100)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_alerts ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in cursor.fetchall()]

# ----------------- PDF & CSV Generation Reports -----------------

@app.get("/api/reports/download-pdf")
def download_pdf_report():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM goals ORDER BY id DESC")
        goals = [enrich_goal(dict(r)) for r in cursor.fetchall()]

        cursor.execute("SELECT * FROM ai_insights ORDER BY id DESC LIMIT 5")
        insights = [dict(r) for r in cursor.fetchall()]

        # Compute summary
        total_target = sum(g["target_amount"] for g in goals)
        total_saved = sum(g["current_amount"] for g in goals)
        progress = (total_saved / total_target * 100) if total_target > 0 else 0.0

        summary = {
            "total_target": total_target,
            "total_saved": total_saved,
            "overall_progress": progress,
            "active_goals": len([g for g in goals if g["status"] == "Active"]),
            "completed_goals": len([g for g in goals if g["status"] == "Completed"])
        }

        pdf_bytes = generate_savings_pdf(goals, summary, insights)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=SaveIQ_Financial_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
            }
        )

@app.get("/api/export/sheets-csv")
def download_sheets_csv():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM goals ORDER BY id ASC")
        goals = [enrich_goal(dict(r)) for r in cursor.fetchall()]
        csv_data = export_goals_to_csv(goals)

        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=SaveIQ_GoogleSheets_Export_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        )

# ----------------- Frontend Static Files Mounting -----------------

frontend_dir = BASE_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

@app.get("/")
def serve_index():
    index_path = BASE_DIR / "frontend" / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": f"Welcome to {APP_NAME} API v{APP_VERSION}. Visit /docs for Swagger documentation."}

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": APP_NAME,
        "version": APP_VERSION,
        "timestamp": datetime.now().isoformat()
    }
