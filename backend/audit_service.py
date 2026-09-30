import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any, List
from backend.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS

logger = logging.getLogger("saveiq.audit")

def send_email_alert(recipient: str, subject: str, html_body: str) -> bool:
    """Sends an email via SMTP or records simulation if credentials are not configured."""
    if not SMTP_USER or not SMTP_PASS:
        logger.info(f"[SIMULATED EMAIL] To: {recipient} | Subject: {subject}")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"SaveIQ Alerts <{SMTP_USER}>"
        msg["To"] = recipient

        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, recipient, msg.as_string())
        
        logger.info(f"Successfully sent live email alert to {recipient}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {recipient}: {e}")
        return False

def run_daily_financial_audit(conn) -> Dict[str, Any]:
    """
    Automated Daily Financial Audit Engine.
    Scans all goals, checks approaching deadlines, evaluates completion pace,
    updates statuses, records audit alerts, and triggers email notifications.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM goals")
    goals = [dict(row) for row in cursor.fetchall()]

    today = datetime.now().date()
    alerts_created = []

    for g in goals:
        target = float(g.get("target_amount", 0))
        current = float(g.get("current_amount", 0))
        deadline_str = g.get("deadline", "")
        email_alerts = bool(g.get("email_alerts", 1))
        recipient = g.get("user_email", "saver@saveiq.ai")
        goal_id = g["id"]
        goal_name = g["name"]
        status = g.get("status", "Active")

        # Parse deadline
        try:
            deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d").date()
            days_left = (deadline_date - today).days
        except Exception:
            days_left = 30

        progress_pct = (current / target * 100) if target > 0 else 100
        remaining = max(0.0, target - current)

        alert_type = None
        message = ""
        new_status = status

        # Status & Condition Evaluation
        if current >= target:
            if status != "Completed":
                new_status = "Completed"
                alert_type = "CONGRATULATIONS"
                message = f"🎉 Goal Achieved! You reached 100% of your target for '{goal_name}' (${target:,.2f}). Fantastic discipline!"
        elif days_left < 0:
            if status != "Overdue":
                new_status = "Overdue"
            alert_type = "OVERDUE"
            message = f"⚠️ Goal Overdue! '{goal_name}' deadline passed on {deadline_str}. You have ${remaining:,.2f} left to reach target."
        elif days_left <= 7:
            alert_type = "URGENT"
            daily_req = round(remaining / max(1, days_left), 2)
            message = f"🚨 Urgent Deadline in {days_left} days for '{goal_name}'! Gap: ${remaining:,.2f} (Need ${daily_req:,.2f}/day to finish)."
        elif days_left <= 30 and progress_pct < 60:
            alert_type = "WARNING"
            message = f"⏳ Approaching Deadline ({days_left} days left) for '{goal_name}'. Current progress is {progress_pct:.1f}%. Consider a booster deposit."

        # Update goal status if changed
        if new_status != status:
            cursor.execute(
                "UPDATE goals SET status = ?, updated_at = ? WHERE id = ?",
                (new_status, datetime.now().isoformat(), goal_id)
            )

        # Record alert if triggered
        if alert_type and email_alerts:
            now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO audit_alerts (goal_id, goal_name, alert_type, message, recipient_email, sent_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (goal_id, goal_name, alert_type, message, recipient, now_iso, "Sent"))

            # Send Email (Live or Simulation)
            email_html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
                <h2 style="color: #4f46e5; margin-bottom: 8px;">SaveIQ Financial Alert: {alert_type}</h2>
                <p style="font-size: 16px; color: #1e293b;">{message}</p>
                <div style="background-color: #f8fafc; padding: 12px; border-radius: 6px; margin: 15px 0;">
                    <p style="margin: 4px 0;"><b>Goal:</b> {goal_name}</p>
                    <p style="margin: 4px 0;"><b>Target:</b> ${target:,.2f}</p>
                    <p style="margin: 4px 0;"><b>Saved:</b> ${current:,.2f} ({progress_pct:.1f}%)</p>
                    <p style="margin: 4px 0;"><b>Deadline:</b> {deadline_str} ({days_left} days remaining)</p>
                </div>
                <p style="font-size: 12px; color: #64748b;">Powered by SaveIQ AI Personal Finance Engine.</p>
            </div>
            """
            send_email_alert(recipient, f"SaveIQ Alert: {goal_name} ({alert_type})", email_html)

            alerts_created.append({
                "goal_id": goal_id,
                "goal_name": goal_name,
                "alert_type": alert_type,
                "message": message,
                "recipient": recipient,
                "timestamp": now_iso
            })

    conn.commit()

    return {
        "audited_count": len(goals),
        "alerts_created": len(alerts_created),
        "details": alerts_created
    }
