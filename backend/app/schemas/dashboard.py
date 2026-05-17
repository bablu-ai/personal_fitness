from datetime import date
from pydantic import BaseModel


class DailyRow(BaseModel):
    date: date
    total: int
    completed: int
    completion_pct: float


class WeeklyRow(BaseModel):
    week_start: date
    total: int
    completed: int
    completion_pct: float
    days_tracked: int


class MonthlyRow(BaseModel):
    month: str  # "YYYY-MM"
    total: int
    completed: int
    completion_pct: float
    days_tracked: int


class DashboardResponse(BaseModel):
    rows: list[DailyRow] | list[WeeklyRow] | list[MonthlyRow]
