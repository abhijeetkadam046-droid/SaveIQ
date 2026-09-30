import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from backend.config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger("saveiq.ai")

def calculate_pace_metrics(goal: Dict[str, Any]) -> Dict[str, Any]:
    target = float(goal.get("target_amount", 0.0))
    current = float(goal.get("current_amount", 0.0))
    deadline_str = goal.get("deadline", "")
    remaining = max(0.0, target - current)
    
    days_left = 1
    if deadline_str:
        try:
            deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d").date()
            today = datetime.now().date()
            diff = (deadline_date - today).days
            days_left = max(1, diff)
        except Exception:
            days_left = 30
            
    daily_req = round(remaining / days_left, 2)
    weekly_req = round(daily_req * 7, 2)
    monthly_req = round(daily_req * 30, 2)
    progress_pct = round((current / target * 100), 1) if target > 0 else 100.0

    # Feasibility score (0-100) based on progress and pacing
    if progress_pct >= 100:
        feasibility = 100
    elif daily_req <= 15:
        feasibility = 95
    elif daily_req <= 50:
        feasibility = 85
    elif daily_req <= 150:
        feasibility = 70
    elif daily_req <= 350:
        feasibility = 50
    else:
        feasibility = 35

    return {
        "remaining": remaining,
        "days_left": days_left,
        "daily_req": daily_req,
        "weekly_req": weekly_req,
        "monthly_req": monthly_req,
        "progress_pct": progress_pct,
        "feasibility": feasibility
    }

def get_heuristic_advice(goal: Dict[str, Any], metrics: Dict[str, Any]) -> Dict[str, Any]:
    """High-quality algorithmic financial advisory engine when Groq API key is not configured."""
    name = goal.get("name", "Goal")
    category = goal.get("category", "General")
    progress = metrics["progress_pct"]
    daily = metrics["daily_req"]
    weekly = metrics["weekly_req"]
    days = metrics["days_left"]
    feasibility = metrics["feasibility"]

    if progress >= 100:
        return {
            "goal_name": name,
            "recommendation": f"🎉 Congratulations! You have fully achieved your '{name}' target of ${goal.get('target_amount', 0):,.2f}. Your financial discipline is commendable!",
            "daily_saving_target": 0.0,
            "weekly_saving_target": 0.0,
            "feasibility_score": 100,
            "strategies": [
                "Lock in your savings into a high-yield liquid account or execute your planned purchase.",
                "Roll over the habit: redirect your future surplus contributions to an Emergency or Investment fund.",
                "Review your next prioritized goal on the SaveIQ dashboard to maintain momentum."
            ],
            "motivational_quote": "Financial freedom is not about having more money; it is about having control over your choices.",
            "source_model": "SaveIQ Heuristic FinTech Engine"
        }

    strategies = [
        f"Automate a weekly recurring transfer of ${weekly:,.2f} right after payday to eliminate temptation.",
        f"Apply the 50/30/20 rule: Trim non-essential leisure or dining subscriptions by 10-15% to easily fund ${daily:,.2f}/day.",
        f"Redirect upcoming windfalls (tax refunds, bonuses, cashback) directly toward '{name}'.",
        f"Micro-saving challenge: Save spare change round-ups daily to shave {min(days, 15)} days off your deadline."
    ]

    if days < 14 and progress < 70:
        strategies[0] = f"⚠️ Critical sprint: Allocate a one-time booster deposit to narrow the ${metrics['remaining']:,.2f} gap or consider extending the deadline by 30 days."

    rec_text = (
        f"For your '{name}' ({category}) goal, you are currently at {progress}% with ${metrics['remaining']:,.2f} remaining. "
        f"To successfully hit your target by the deadline in {days} days, your optimal contribution velocity is ${daily:,.2f}/day "
        f"or ${weekly:,.2f}/week. With focused budget pacing, your feasibility index stands at a confident {feasibility}%."
    )

    quotes = [
        "A budget is telling your money where to go instead of wondering where it went.",
        "Small daily savings compound into monumental financial security.",
        "Discipline is choosing between what you want now and what you want most."
    ]

    return {
        "goal_name": name,
        "recommendation": rec_text,
        "daily_saving_target": daily,
        "weekly_saving_target": weekly,
        "feasibility_score": feasibility,
        "strategies": strategies,
        "motivational_quote": quotes[len(name) % len(quotes)],
        "source_model": "SaveIQ AI Engine (Heuristic Mode - Add Groq Key for LLaMA 3.3-70B Live Analysis)"
    }

def generate_ai_recommendation(goal: Dict[str, Any], user_context: str = "") -> Dict[str, Any]:
    """Generates personalized financial guidance using Groq LLaMA 3.3-70B Versatile, falling back to heuristic."""
    metrics = calculate_pace_metrics(goal)
    
    if not GROQ_API_KEY or GROQ_API_KEY.strip() == "":
        logger.info("GROQ_API_KEY not found. Using SaveIQ FinTech Heuristic Engine.")
        return get_heuristic_advice(goal, metrics)

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        prompt = f"""
You are the senior AI Financial Advisor of SaveIQ (an AI-powered personal finance & savings goal tracker).
Analyze the following user savings goal and generate actionable, encouraging, and data-driven financial advice.

Goal Profile:
- Goal Name: {goal.get('name')}
- Category: {goal.get('category')}
- Target Amount: ${goal.get('target_amount', 0):,.2f}
- Current Savings: ${goal.get('current_amount', 0):,.2f} ({metrics['progress_pct']}%)
- Remaining Amount: ${metrics['remaining']:,.2f}
- Days Remaining to Deadline: {metrics['days_left']} days (Deadline: {goal.get('deadline')})
- Daily Required Savings: ${metrics['daily_req']:,.2f}
- Weekly Required Savings: ${metrics['weekly_req']:,.2f}
- User Purpose / Note: {goal.get('purpose', 'Not specified')}
- Additional Context: {user_context or 'Standard savings optimization'}

Respond strictly with a valid JSON object matching this schema:
{{
  "recommendation": "A 2-3 sentence personalized executive evaluation of the user's progress, pacing, and realistic path forward.",
  "daily_saving_target": {metrics['daily_req']},
  "weekly_saving_target": {metrics['weekly_req']},
  "feasibility_score": {metrics['feasibility']},
  "strategies": [
    "Concrete actionable tactic 1 tailored to category and deadline",
    "Concrete actionable tactic 2 (budget trimming / automation)",
    "Concrete actionable tactic 3 (windfalls / milestone acceleration)"
  ],
  "motivational_quote": "A powerful quote about financial discipline and goal attainment."
}}
Do NOT output markdown backticks around JSON if possible. Return only JSON.
"""

        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are SaveIQ's expert FinTech AI advisor powered by LLaMA 3.3-70B. Output purely valid JSON."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=800,
            response_format={"type": "json_object"}
        )

        content = completion.choices[0].message.content
        data = json.loads(content)
        data["goal_name"] = goal.get("name")
        data["source_model"] = f"Groq LLaMA 3.3-70B ({GROQ_MODEL})"
        
        # Ensure fallback values if keys are missing
        data.setdefault("daily_saving_target", metrics["daily_req"])
        data.setdefault("weekly_saving_target", metrics["weekly_req"])
        data.setdefault("feasibility_score", metrics["feasibility"])
        data.setdefault("strategies", [
            f"Save ${metrics['daily_req']:,.2f} daily via automated transfer.",
            "Review variable utility and dining expenses.",
            "Celebrate intermediate 25% checkpoints."
        ])
        data.setdefault("motivational_quote", "Consistency today buys freedom tomorrow.")
        return data

    except Exception as e:
        logger.warning(f"Groq API call failed or timed out: {e}. Falling back to heuristic advisor.")
        fallback = get_heuristic_advice(goal, metrics)
        fallback["source_model"] = f"SaveIQ FinTech Engine (Fallback: {str(e)[:40]}...)"
        return fallback
