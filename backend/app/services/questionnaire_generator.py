"""
Questionnaire → workbook JSON generator.

Converts questionnaire answers stored in the DB into the normalized workbook_json dict
that ingest_from_workbook_json can consume to create Plan + TaskTemplate + RotationDay
+ Screening records. No LLM required — all logic is deterministic Python.
"""
import json
from datetime import datetime, date, timezone

from sqlalchemy.orm import Session

from app.db.models import QuestionnaireAnswer


# Standard supplement list — determines active vs review status
_STANDARD_SUPPLEMENTS = [
    "Creatine",
    "Omega-3 fish oil",
    "Vitamin D",
    "Magnesium",
    "Psyllium husk fiber",
    "Curcumin",
    "Protein powder",
]


def _build_supplements_status(supplements: list) -> dict[str, str]:
    """Map each standard supplement to 'active' or 'review' based on user answers."""
    active_lower = {s.lower() for s in supplements}
    result: dict[str, str] = {}
    for supp in _STANDARD_SUPPLEMENTS:
        matched = any(supp.lower() in s for s in active_lower)
        result[supp] = "active" if matched else "review"
    return result


def _build_tasks(answers: dict, sex: str) -> list[dict]:
    """Return a hardcoded list of representative daily tasks drawn from the template."""
    preferred_time = answers.get("q34_preferred_exercise_time", "Flexible")
    protein_target = answers.get("_protein_target", 120)

    return [
        {
            "pillar": "brief_today",
            "name": "Morning Activation",
            "description": "Wake the body and prime movement patterns for the day.",
            "schedule": "daily",
            "timing": "Morning",
            "target_value": "8 min: nasal breathing + shoulder circles + cat-cow",
            "benefit_tags": "posture,energy,nervous_system",
            "source_key": "brief_today_morning",
            "is_reference": False,
        },
        {
            "pillar": "brief_today",
            "name": "Strength Training (Upper Back + Core)",
            "description": "Build structural resilience with compound pulling and core anti-rotation.",
            "schedule": "3x/week",
            "timing": preferred_time,
            "target_value": "2 rounds: band row, wall slide, dead bug/bird dog",
            "benefit_tags": "strength,posture,longevity",
            "source_key": "brief_today_strength",
            "is_reference": False,
        },
        {
            "pillar": "brief_today",
            "name": "Zone 2 Cardio",
            "description": "Aerobic base training — maintain nasal breathing throughout.",
            "schedule": "2x/week",
            "timing": preferred_time,
            "target_value": "30–45 min easy walk or cycle, RPE 4–5",
            "benefit_tags": "cardiovascular,metabolic,longevity",
            "source_key": "brief_today_zone2",
            "is_reference": False,
        },
        {
            "pillar": "nutrition",
            "name": f"Protein Target ({protein_target} g/day)",
            "description": "Maintain muscle mass and support recovery with adequate protein.",
            "schedule": "daily",
            "timing": "All meals",
            "target_value": f"{protein_target} g protein spread across 4 meals (~{protein_target // 4} g each)",
            "benefit_tags": "muscle_mass,recovery,satiety",
            "source_key": "nutrition_protein",
            "is_reference": True,
        },
        {
            "pillar": "supplements",
            "name": "Creatine Monohydrate",
            "description": "Supports ATP regeneration, muscle power, and cognitive function.",
            "schedule": "daily",
            "timing": "Any time",
            "target_value": "5 g",
            "benefit_tags": "strength,cognition,muscle_mass",
            "source_key": "supp_creatine",
            "is_reference": False,
        },
        {
            "pillar": "supplements",
            "name": "Omega-3 Fish Oil",
            "description": "Reduces systemic inflammation; supports cardiovascular and brain health.",
            "schedule": "daily",
            "timing": "With a meal",
            "target_value": "2–4 g EPA+DHA",
            "benefit_tags": "inflammation,cardiovascular,brain",
            "source_key": "supp_omega3",
            "is_reference": False,
        },
        {
            "pillar": "sleep_recovery",
            "name": "Sleep Hygiene Protocol",
            "description": "Consistent sleep/wake time anchors circadian rhythm.",
            "schedule": "daily",
            "timing": "Evening",
            "target_value": "Dim lights 90 min before bed; no screens in bedroom",
            "benefit_tags": "recovery,hormone_balance,longevity",
            "source_key": "sleep_hygiene",
            "is_reference": True,
        },
        {
            "pillar": "cognitive_social",
            "name": "Cognitive Challenge",
            "description": "Maintain neural plasticity through deliberate cognitive training.",
            "schedule": "daily",
            "timing": "Morning or Evening",
            "target_value": "20 min: reading, puzzle, music practice, or learning",
            "benefit_tags": "brain_health,plasticity,longevity",
            "source_key": "cognitive_daily",
            "is_reference": True,
        },
        {
            "pillar": "brief_today",
            "name": "Mobility + Cool-Down",
            "description": "Reduce injury risk and restore range of motion after training.",
            "schedule": "3x/week",
            "timing": "Post-workout",
            "target_value": "5 min: hip flexor stretch, thoracic rotation, ankle circles",
            "benefit_tags": "mobility,recovery,injury_prevention",
            "source_key": "brief_today_cooldown",
            "is_reference": False,
        },
        {
            "pillar": "brief_today",
            "name": "Hydration Check",
            "description": "Adequate hydration maintains performance and cognitive function.",
            "schedule": "daily",
            "timing": "Throughout day",
            "target_value": "2.4 L water; start with 500 ml upon waking",
            "benefit_tags": "hydration,performance,cognition",
            "source_key": "brief_today_hydration",
            "is_reference": False,
        },
    ]


def _build_rotation_days(answers: dict) -> list[dict]:
    """Return 4 representative rotation days (Mon–Thu pattern)."""
    preferred_time = answers.get("q34_preferred_exercise_time", "Flexible")

    return [
        {
            "day_number": 1,
            "week_number": 1,
            "block_name": "Strength A — Upper Back + Core",
            "morning_time": preferred_time if preferred_time != "Flexible" else "6:00 AM",
            "warm_up_min": "8",
            "upper_back_core_min": "20",
            "secondary_min": "12",
            "cool_down_min": "5",
            "total_min": "45",
            "fits_60": "Yes",
            "priority_exercises": "Band row, Wall slide, Dead bug",
            "secondary_exercises": "Glute bridge, Pallof press",
            "week_rule": "Week 1: Easy / RPE 5–6",
        },
        {
            "day_number": 2,
            "week_number": 1,
            "block_name": "Zone 2 Cardio",
            "morning_time": preferred_time if preferred_time != "Flexible" else "6:00 AM",
            "warm_up_min": "5",
            "upper_back_core_min": "0",
            "secondary_min": "35",
            "cool_down_min": "5",
            "total_min": "45",
            "fits_60": "Yes",
            "priority_exercises": "Easy walk or cycle (nasal breathing only)",
            "secondary_exercises": None,
            "week_rule": "RPE 4–5, conversational pace",
        },
        {
            "day_number": 3,
            "week_number": 1,
            "block_name": "Strength B — Lower Body + Carry",
            "morning_time": preferred_time if preferred_time != "Flexible" else "6:00 AM",
            "warm_up_min": "8",
            "upper_back_core_min": "0",
            "secondary_min": "22",
            "cool_down_min": "5",
            "total_min": "35",
            "fits_60": "Yes",
            "priority_exercises": "Sit-to-stand, Glute bridge, Farmer carry",
            "secondary_exercises": "Calf raise, Terminal knee extension",
            "week_rule": "Week 1: Easy / RPE 5–6",
        },
        {
            "day_number": 4,
            "week_number": 1,
            "block_name": "Recovery + Mobility",
            "morning_time": preferred_time if preferred_time != "Flexible" else "6:00 AM",
            "warm_up_min": "5",
            "upper_back_core_min": "0",
            "secondary_min": "20",
            "cool_down_min": "5",
            "total_min": "30",
            "fits_60": "Yes",
            "priority_exercises": "Hip flexor stretch, Thoracic rotation, Cat-cow",
            "secondary_exercises": "Ankle circles, Child's pose",
            "week_rule": "Active recovery — no pain, no aggression",
        },
    ]


def _build_screenings(sex: str) -> list[dict]:
    """Return sex-appropriate screenings."""
    screenings = [
        {
            "pillar": "screenings_safety",
            "name": "Colonoscopy",
            "description": "Colorectal cancer screening; adenoma detection.",
            "frequency_months": 120,  # 10 years if clear
            "target_value": None,
        },
        {
            "pillar": "screenings_safety",
            "name": "Blood Pressure Check",
            "description": "Cardiovascular risk assessment.",
            "frequency_months": 12,
            "target_value": "<120/80 mmHg",
        },
        {
            "pillar": "blood_markers",
            "name": "HbA1c",
            "description": "3-month average blood glucose — metabolic health proxy.",
            "frequency_months": 12,
            "target_value": "<5.7%",
        },
        {
            "pillar": "blood_markers",
            "name": "Lipid Panel",
            "description": "LDL-C, HDL-C, TG, non-HDL-C for cardiovascular risk.",
            "frequency_months": 12,
            "target_value": "LDL-C <70 mg/dL (longevity target)",
        },
        {
            "pillar": "blood_markers",
            "name": "Vitamin D (25-OH)",
            "description": "Bone density, immune function, and mood regulation.",
            "frequency_months": 12,
            "target_value": "40–60 ng/mL",
        },
    ]

    if sex == "F":
        screenings.append({
            "pillar": "screenings_safety",
            "name": "Mammogram",
            "description": "Breast cancer screening.",
            "frequency_months": 12,
            "target_value": None,
        })
    elif sex == "M":
        screenings.append({
            "pillar": "screenings_safety",
            "name": "PSA (Prostate-Specific Antigen)",
            "description": "Prostate cancer screening marker.",
            "frequency_months": 12,
            "target_value": "<4.0 ng/mL",
        })

    return screenings


def _safe_float(value: object, default: float) -> float:
    """Safely convert a value to float, returning *default* on error."""
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _parse_age(dob_str: str) -> int:
    """Return age from a date-of-birth string, or 0 if unparseable."""
    if not dob_str:
        return 0
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"):
        try:
            dob = datetime.strptime(dob_str, fmt).date()
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return max(0, age)
        except ValueError:
            continue
    return 0


def build_workbook_json(session_id: str, db: Session) -> dict:
    """
    Query all QuestionnaireAnswer rows for *session_id* and build the workbook_json dict.

    Returns a dict that is compatible with ingest_from_workbook_json.
    """
    rows = (
        db.query(QuestionnaireAnswer)
        .filter(QuestionnaireAnswer.session_id == session_id)
        .all()
    )

    # Build flat answers dict: {question_id: parsed value}
    answers: dict[str, object] = {}
    for row in rows:
        try:
            answers[row.question_id] = json.loads(row.answer_json)
        except (json.JSONDecodeError, TypeError):
            answers[row.question_id] = row.answer_json

    # Extract key fields with safe defaults
    name: str = str(answers.get("q1_full_name", ""))
    dob_str: str = str(answers.get("q2_date_of_birth", ""))
    sex_raw: str = str(answers.get("q3_sex_at_birth", ""))
    sex = "M" if sex_raw == "Male" else ("F" if sex_raw == "Female" else sex_raw)
    height_cm = _safe_float(answers.get("q4_height_cm", 170), 170.0)
    weight_kg = _safe_float(answers.get("q5_weight_kg", 75), 75.0)
    wake_time: str = str(answers.get("q22_wake_time", "06:00"))
    bed_time: str = str(answers.get("q23_bed_time", "22:00"))
    dietary_pattern: str = str(answers.get("q16_dietary_pattern", "Omnivore"))
    supplements_raw = answers.get("q19_current_supplements", [])
    supplements: list = supplements_raw if isinstance(supplements_raw, list) else []
    preferred_exercise_time: str = str(answers.get("q34_preferred_exercise_time", "Flexible"))
    cognitive_activities: str = str(answers.get("q26_detail", ""))

    # Computed values
    age = _parse_age(dob_str)
    height_m = height_cm / 100.0
    bmi = round(weight_kg / (height_m ** 2), 1) if height_m > 0 else 0.0
    protein_target = round(weight_kg * 1.6)

    # Make protein_target available to sub-builders via answers dict
    answers["_protein_target"] = protein_target

    supplements_status = _build_supplements_status(supplements)

    return {
        "format_version": "questionnaire_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "questionnaire_session_id": session_id,
        "user_profile": {
            "name": name,
            "date_of_birth": dob_str,
            "sex": sex,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "age": age,
            "bmi": bmi,
            "protein_target_g": protein_target,
            "wake_time": wake_time,
            "bed_time": bed_time,
            "dietary_pattern": dietary_pattern,
            "preferred_exercise_time": preferred_exercise_time,
        },
        "personal_settings": {
            "name": name,
            "date_of_birth": dob_str,
            "sex": sex,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
        },
        "nutrition_targets": {
            "protein_g_per_day": protein_target,
            "protein_g_per_meal": protein_target // 4,
            "water_l_per_day": 2.4,
            "dietary_pattern": dietary_pattern,
        },
        "sleep_schedule": {
            "wake_time": wake_time,
            "bed_time": bed_time,
            "target_hours": 7.5,
        },
        "supplements_status": supplements_status,
        "cognitive_activities": cognitive_activities,
        "tasks": _build_tasks(answers, sex),
        "rotation_days": _build_rotation_days(answers),
        "screenings": _build_screenings(sex),
    }
