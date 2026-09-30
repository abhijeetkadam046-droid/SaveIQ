from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class GoalCreate(BaseModel):
    name: str = Field(..., example="Emergency Fund")
    category: str = Field("General", example="Emergency Fund")
    target_amount: float = Field(..., gt=0, example=50000.0)
    initial_savings: float = Field(0.0, ge=0, example=10000.0)
    deadline: str = Field(..., example="2026-12-31")
    email_alerts: bool = Field(True, example=True)
    user_email: str = Field("user@example.com", example="user@example.com")
    purpose: Optional[str] = Field(None, example="Safety net for 6 months living expenses")
    priority: Optional[str] = Field("Medium", example="High")

class GoalUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    target_amount: Optional[float] = None
    current_amount: Optional[float] = None
    deadline: Optional[str] = None
    email_alerts: Optional[bool] = None
    user_email: Optional[str] = None
    purpose: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None

class DepositCreate(BaseModel):
    amount: float = Field(..., gt=0, example=2500.0)
    note: Optional[str] = Field("Monthly contribution", example="Monthly contribution")
    date: Optional[str] = None

class GoalResponse(BaseModel):
    id: int
    name: str
    category: str
    target_amount: float
    current_amount: float
    deadline: str
    email_alerts: bool
    user_email: str
    purpose: Optional[str]
    priority: str
    status: str
    created_at: str
    updated_at: str
    progress_percentage: float
    remaining_amount: float
    days_remaining: int
    daily_required: float
    status_badge: str

class DashboardSummary(BaseModel):
    total_goals: int
    active_goals: int
    completed_goals: int
    overdue_goals: int
    total_target: float
    total_saved: float
    overall_progress: float
    discipline_score: int
    category_breakdown: Dict[str, float]
    urgent_goals: List[Dict[str, Any]]
    recent_alerts: List[Dict[str, Any]]

class AIAdviceRequest(BaseModel):
    goal_id: Optional[int] = None
    prompt: Optional[str] = None
    financial_persona: Optional[str] = "Balanced Saver"

class AIAdviceResponse(BaseModel):
    goal_name: Optional[str]
    recommendation: str
    daily_saving_target: float
    weekly_saving_target: float
    feasibility_score: int
    strategies: List[str]
    motivational_quote: str
    source_model: str

class AuditRunResponse(BaseModel):
    audited_count: int
    alerts_created: int
    details: List[Dict[str, Any]]
