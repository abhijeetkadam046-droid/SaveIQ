import csv
import io
from typing import List, Dict, Any

def export_goals_to_csv(goals: List[Dict[str, Any]]) -> str:
    """Exports goals into Google Sheets compatible CSV structure."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Google Sheets Schema Header
    writer.writerow([
        "Goal ID", "Goal Name", "Category", "Target Amount ($)",
        "Current Saved ($)", "Progress (%)", "Remaining ($)",
        "Deadline", "Days Remaining", "Daily Required ($)",
        "Email Alerts", "User Email", "Priority", "Status", "Purpose", "Created At"
    ])

    for g in goals:
        target = float(g.get("target_amount", 0))
        current = float(g.get("current_amount", 0))
        progress = round((current / target * 100), 2) if target > 0 else 0
        remaining = max(0.0, target - current)
        days = g.get("days_remaining", 0)
        daily = round(remaining / max(1, days), 2)

        writer.writerow([
            g.get("id"),
            g.get("name"),
            g.get("category"),
            target,
            current,
            f"{progress}%",
            remaining,
            g.get("deadline"),
            days,
            daily,
            "Yes" if g.get("email_alerts") else "No",
            g.get("user_email"),
            g.get("priority"),
            g.get("status"),
            g.get("purpose", ""),
            g.get("created_at")
        ])

    return output.getvalue()
