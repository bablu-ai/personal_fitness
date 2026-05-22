"""Canonical questionnaire catalog for persisted question snapshots."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import QuestionnaireQuestion

QUESTIONNAIRE_VERSION = 1


@dataclass(frozen=True)
class QuestionDef:
    id: str
    section: int
    number: int
    type: str
    text: str
    required: bool
    options: list[str] | None = None
    placeholder: str | None = None
    conditional: dict[str, Any] | None = None
    validation: dict[str, Any] | None = None


QUESTIONS: list[QuestionDef] = [
    QuestionDef("q1_full_name", 1, 1, "text", "What is your full name?", True, placeholder="Enter your full name"),
    QuestionDef("q2_date_of_birth", 1, 2, "date", "Date of birth (YYYY-MM-DD)", True),
    QuestionDef("q3_sex_at_birth", 1, 3, "single_choice", "Sex at birth", True, options=["Male", "Female", "Intersex", "Prefer not to say"]),
    QuestionDef("q4_height_cm", 1, 4, "number", "Height (cm)", True, placeholder="e.g. 175", validation={"min": 50, "max": 300}),
    QuestionDef("q5_weight_kg", 1, 5, "number", "Weight (kg)", True, placeholder="e.g. 80", validation={"min": 20, "max": 500}),
    QuestionDef("q6_chronic_conditions", 2, 6, "multi_choice", "Do you have any diagnosed chronic conditions? (select all that apply)", False, options=["Hypertension", "Diabetes", "Cardiovascular disease", "Osteoporosis", "Arthritis", "None", "Other"], conditional={"triggerOption": "Other", "placeholder": "Please describe", "fieldId": "q6_other"}),
    QuestionDef("q7_medications", 2, 7, "conditional_text", "Are you currently taking any medications that affect heart rate, blood pressure or exercise tolerance?", False, options=["Yes", "No"], conditional={"triggerOption": "Yes", "placeholder": "Please specify medications", "fieldId": "q7_detail"}),
    QuestionDef("q8_mobility_limitations", 2, 8, "conditional_text", "Do you have any movement or mobility limitations?", False, options=["Yes", "No"], conditional={"triggerOption": "Yes", "placeholder": "Please describe your limitations", "fieldId": "q8_detail"}),
    QuestionDef("q9_surgeries_injuries", 2, 9, "conditional_text", "Have you had any surgeries or injuries that affect your ability to exercise?", False, options=["Yes", "No"], conditional={"triggerOption": "Yes", "placeholder": "Please describe", "fieldId": "q9_detail"}),
    QuestionDef("q10_last_physical_exam", 2, 10, "single_choice", "When was your most recent physical exam or exercise clearance?", True, options=["Within the last 3 months", "3-6 months ago", "More than 6 months ago", "Never / don't recall"]),
    QuestionDef("q11_activity_level", 3, 11, "single_choice", "How would you describe your current activity level?", True, options=["Sedentary", "Lightly active", "Moderately active", "Very active"]),
    QuestionDef("q12_daily_exercise_minutes", 3, 12, "single_choice", "How many minutes per day can you consistently commit to exercise?", True, options=["Less than 30 minutes", "30-60 minutes", "60-90 minutes", "More than 90 minutes"]),
    QuestionDef("q13_fitness_goals", 3, 13, "multi_choice", "What are your primary fitness goals? (select all that apply)", False, options=["Build muscle strength", "Improve cardiovascular endurance", "Enhance mobility/flexibility", "Improve balance and fall prevention", "Weight loss or weight management", "Maintain independence for daily activities", "Other"], conditional={"triggerOption": "Other", "placeholder": "Please describe", "fieldId": "q13_other"}),
    QuestionDef("q14_equipment_access", 3, 14, "multi_choice", "Which exercise equipment do you have access to? (select all that apply)", False, options=["Resistance bands", "Dumbbells/kettlebells", "Barbell/weight machines", "Cardio machine (treadmill, bike, rowing machine)", "None (bodyweight only)"]),
    QuestionDef("q15_bodyweight_comfortable", 3, 15, "single_choice", "Are you comfortable using body-weight exercises (e.g. squats, planks, bridges)?", True, options=["Yes", "No"]),
    QuestionDef("q16_dietary_pattern", 4, 16, "single_choice", "Describe your usual dietary pattern", True, options=["Omnivore", "Vegetarian", "Vegan", "Pescatarian", "Other"], conditional={"triggerOption": "Other", "placeholder": "Please describe", "fieldId": "q16_other"}),
    QuestionDef("q17_dietary_restrictions", 4, 17, "conditional_text", "Do you have any dietary restrictions or food allergies?", False, options=["Yes", "No"], conditional={"triggerOption": "Yes", "placeholder": "Please list your restrictions or allergies", "fieldId": "q17_detail"}),
    QuestionDef("q18_meals_per_day", 4, 18, "single_choice", "How many meals do you typically eat per day?", True, options=["1-2", "3", "4", "More than 4"]),
    QuestionDef("q19_current_supplements", 4, 19, "multi_choice", "Are you currently taking any supplements? (select all that apply)", False, options=["Creatine", "Omega-3 fish oil", "Psyllium husk fiber", "Curcumin", "Vitamin D", "Magnesium", "Protein powder", "None", "Other"], conditional={"triggerOption": "Other", "placeholder": "Please list", "fieldId": "q19_other"}),
    QuestionDef("q20_nutrient_deficiencies", 4, 20, "conditional_text", "Do you have known nutrient deficiencies (e.g. vitamin D, iron)?", False, options=["Yes", "No"], conditional={"triggerOption": "Yes", "placeholder": "Please describe", "fieldId": "q20_detail"}),
    QuestionDef("q21_track_macros", 4, 21, "single_choice", "Do you plan to track macros (protein, fat, carbs) daily?", True, options=["Yes", "No"]),
    QuestionDef("q22_wake_time", 5, 22, "time", "What time do you usually wake up?", True, placeholder="05:30"),
    QuestionDef("q23_bed_time", 5, 23, "time", "What time do you usually go to bed?", True, placeholder="22:00"),
    QuestionDef("q24_shift_work", 5, 24, "single_choice", "Do you work shifts or have a variable schedule?", True, options=["Yes", "No"]),
    QuestionDef("q25_include_balance_training", 5, 25, "single_choice", "Are you willing to include balance and mobility training in your routine?", True, options=["Yes", "No"]),
    QuestionDef("q26_cognitive_social", 5, 26, "conditional_text", "Would you like cognitive and social-health activities included?", False, options=["Yes", "No"], conditional={"triggerOption": "Yes", "placeholder": "Preferred activities (language learning, music, journaling, meditation, etc.)", "fieldId": "q26_detail"}),
    QuestionDef("q27_measure_bp_at_home", 6, 27, "single_choice", "Are you comfortable measuring your blood pressure and weight at home?", True, options=["Yes", "No"]),
    QuestionDef("q28_wearable_devices", 6, 28, "conditional_text", "Do you use any wearable devices to track heart rate, steps or sleep?", False, options=["Yes", "No"], conditional={"triggerOption": "Yes", "placeholder": "Devices used (Garmin, Apple Watch, Oura, Whoop, etc.)", "fieldId": "q28_detail"}),
    QuestionDef("q29_quarterly_blood_tests", 6, 29, "single_choice", "Are you willing to obtain quarterly blood tests to track biomarkers (e.g. HbA1c, ApoB, vitamin D)?", True, options=["Yes", "No"]),
    QuestionDef("q30_screening_reminders", 6, 30, "single_choice", "Would you like reminders for regular cancer screenings and health check-ups (colonoscopy, mammogram, PSA, etc.)?", True, options=["Yes", "No"]),
    QuestionDef("q31_open_to_trainer", 6, 31, "single_choice", "Are you open to working with a certified trainer or physical therapist for form and safety review?", True, options=["Yes", "No"]),
    QuestionDef("q32_other_goals", 7, 32, "text", "Do you have any other specific goals or concerns we should be aware of?", False, placeholder="Optional - share anything else"),
    QuestionDef("q33_exercises_to_avoid", 7, 33, "text", "Are there any exercises you particularly enjoy or wish to avoid?", False, placeholder="Optional"),
    QuestionDef("q34_preferred_exercise_time", 7, 34, "single_choice", "Is there a preferred time of day for exercise?", True, options=["Early morning (e.g. 5:40-6:40)", "Late morning/afternoon", "Evening", "Flexible", "Other"], conditional={"triggerOption": "Other", "placeholder": "Please specify", "fieldId": "q34_other"}),
    QuestionDef("q35_current_routine", 7, 35, "conditional_text", "Do you currently follow any exercise routine or program?", False, options=["Yes", "No"], conditional={"triggerOption": "Yes", "placeholder": "Please describe your current routine", "fieldId": "q35_detail"}),
    QuestionDef("q36_medical_devices", 7, 36, "conditional_text", "Do you require modifications because of medical devices (e.g. pacemaker, joint replacement)?", False, options=["Yes", "No"], conditional={"triggerOption": "Yes", "placeholder": "Please specify", "fieldId": "q36_detail"}),
    QuestionDef("q37_daily_metrics", 7, 37, "conditional_text", "Are there specific metrics you would like to record daily (e.g. weight, step count, mood, energy levels)?", False, options=["Yes", "No"], conditional={"triggerOption": "Yes", "placeholder": "Please list your preferred metrics", "fieldId": "q37_detail"}),
    QuestionDef("q38_video_review", 7, 38, "single_choice", "Would you like the option of submitting video clips for form review by a coach or trainer?", True, options=["Yes", "No"]),
    QuestionDef("q39_comfortable_with_tech", 7, 39, "single_choice", "Are you comfortable using a smartphone or spreadsheet software daily for tracking?", True, options=["Yes", "No"]),
    QuestionDef("q40_privacy", 7, 40, "conditional_text", "Do you require privacy or data-anonymization measures?", False, options=["Yes", "No"], conditional={"triggerOption": "Yes", "placeholder": "Please specify your privacy preferences", "fieldId": "q40_detail"}),
]


def _json_or_none(value: Any) -> str | None:
    return json.dumps(value) if value is not None else None


def ensure_questionnaire_questions(db: Session, version: int = QUESTIONNAIRE_VERSION) -> None:
    """Seed missing question snapshot rows for the current questionnaire version."""
    existing = {
        question_id
        for (question_id,) in db.query(QuestionnaireQuestion.question_id)
        .filter(QuestionnaireQuestion.version == version)
        .all()
    }
    for q in QUESTIONS:
        if q.id in existing:
            continue
        db.add(QuestionnaireQuestion(
            question_id=q.id,
            version=version,
            section_number=q.section,
            question_number=q.number,
            question_text=q.text,
            question_type=q.type,
            options_json=_json_or_none(q.options),
            required=q.required,
            placeholder=q.placeholder,
            conditional_json=_json_or_none(q.conditional),
            validation_json=_json_or_none(q.validation),
        ))
    db.flush()


def get_question_snapshot(
    db: Session,
    question_id: str,
    version: int = QUESTIONNAIRE_VERSION,
) -> QuestionnaireQuestion | None:
    ensure_questionnaire_questions(db, version)
    return (
        db.query(QuestionnaireQuestion)
        .filter(
            QuestionnaireQuestion.question_id == question_id,
            QuestionnaireQuestion.version == version,
        )
        .first()
    )
