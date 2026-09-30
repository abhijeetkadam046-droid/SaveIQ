from datetime import datetime, timedelta
from backend.database import get_db

def seed_initial_data():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM goals")
        count = cursor.fetchone()["cnt"]

        if count > 0:
            return  # Already seeded

        today = datetime.now().date()
        
        sample_goals = [
            (
                "Emergency Fund",
                "Emergency Fund",
                15000.0,
                9200.0,
                (today + timedelta(days=120)).strftime("%Y-%m-%d"),
                1,
                "saver@saveiq.ai",
                "6-month living expenses buffer for financial resilience",
                "High",
                "Active"
            ),
            (
                "M3 Max Laptop Upgrade",
                "Tech & Gadgets",
                2800.0,
                2100.0,
                (today + timedelta(days=21)).strftime("%Y-%m-%d"),
                1,
                "saver@saveiq.ai",
                "High-performance workstation for AI software development",
                "High",
                "Active"
            ),
            (
                "Bali Summer Vacation",
                "Travel & Vacation",
                3500.0,
                1400.0,
                (today + timedelta(days=75)).strftime("%Y-%m-%d"),
                1,
                "saver@saveiq.ai",
                "Flights, villa accommodation, and travel itinerary",
                "Medium",
                "Active"
            ),
            (
                "FinTech Masters Cert.",
                "Education",
                5000.0,
                1250.0,
                (today + timedelta(days=180)).strftime("%Y-%m-%d"),
                1,
                "saver@saveiq.ai",
                "Advanced FinTech and quantitative engineering credentials",
                "Medium",
                "Active"
            ),
            (
                "Used Car Down Payment",
                "Vehicle",
                6000.0,
                6000.0,
                (today - timedelta(days=10)).strftime("%Y-%m-%d"),
                0,
                "saver@saveiq.ai",
                "Reliable commuter vehicle down payment",
                "Low",
                "Completed"
            )
        ]

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for g in sample_goals:
            cursor.execute("""
                INSERT INTO goals (name, category, target_amount, current_amount, deadline, email_alerts, user_email, purpose, priority, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (*g, now_str, now_str))
            
            goal_id = cursor.lastrowid
            
            # Initial deposits
            if g[3] > 0:
                cursor.execute("""
                    INSERT INTO deposits (goal_id, amount, note, date)
                    VALUES (?, ?, ?, ?)
                """, (goal_id, g[3] * 0.6, "Initial base deposit", (today - timedelta(days=45)).strftime("%Y-%m-%d")))
                cursor.execute("""
                    INSERT INTO deposits (goal_id, amount, note, date)
                    VALUES (?, ?, ?, ?)
                """, (goal_id, g[3] * 0.4, "Monthly disciplined savings addition", (today - timedelta(days=15)).strftime("%Y-%m-%d")))

        # Seed initial audit alert
        cursor.execute("""
            INSERT INTO audit_alerts (goal_id, goal_name, alert_type, message, recipient_email, sent_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            2,
            "M3 Max Laptop Upgrade",
            "WARNING",
            "Approaching deadline in 21 days for 'M3 Max Laptop Upgrade'. Gap remaining: $700.00.",
            "saver@saveiq.ai",
            now_str,
            "Sent"
        ))

        conn.commit()
