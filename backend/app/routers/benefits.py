from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.benefit_scorer import calculate_benefit_scores
from app.schemas.benefits import BenefitScoresResponse

router = APIRouter()


@router.get("/benefits/today", response_model=BenefitScoresResponse)
def get_today_benefits(db: Session = Depends(get_db)):
    return calculate_benefit_scores(db, date.today())


@router.get("/benefits/{target_date}", response_model=BenefitScoresResponse)
def get_benefits_for_date(target_date: date, db: Session = Depends(get_db)):
    return calculate_benefit_scores(db, target_date)
