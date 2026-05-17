from pathlib import Path

BENEFIT_CONFIG_PATH = Path(__file__).parent.parent / "benefit_config.json"

# Default user ID for Phase 1 single-user POC
# Phase 2: replace with real authenticated user IDs
DEFAULT_USER_ID = "default"

# Flexible column header hints for Excel parsing — edit to support more header names.
# Keys are canonical DB field names; values are all column headers that map to them.
COLUMN_HINTS: dict[str, list[str]] = {
    "name": [
        # generic
        "name", "task", "item", "action",
        # this workbook
        "do now",           # 02_Brief_Today
        "element",          # 12_Sleep_Recovery
        "pillar",           # 08_Nutrition  (row content = task name)
        "activity",         # 13_Cognitive_Social
        "exercise",         # 07_Exercise_Library
        "supplement",       # 09_Supplements
        "screening",        # 11_Screenings_Safety
        "marker",           # 10_Blood_Markers
        "protocol",         # 04_Deep_Protocol
        "block",            # 03_Guided_Steps, 06_Weekly_Plan, 16_Progression_Weeks
        "food",
    ],
    "description": [
        "description", "notes", "details", "instructions", "info",
        # this workbook
        "why", "why it matters", "why (mechanism)",
        "mechanism", "mechanism (why it works)",
        "how", "how to do it", "steps to complete",
        "exact method", "examples",
        "how to know it is right",
    ],
    "schedule": [
        "schedule", "frequency", "days", "recurrence", "repeat",
        "frequency (yrs)",  # 11_Screenings_Safety
    ],
    "timing": [
        "timing", "time of day", "take with", "best time",
        "timing / food", "timing/food",    # 09_Supplements
        "time",                             # 13_Cognitive_Social
        "when",                             # 03_Guided_Steps, 04_Deep_Protocol
        "best time/place",                  # 07_Exercise_Library v4
    ],
    "target_value": [
        "target", "goal", "amount", "dosage", "quantity", "reps", "sets",
        "dose",                     # 09_Supplements
        "week 1 dosage",            # 02_Brief_Today, 07_Exercise_Library
        "dose / target",            # 03_Guided_Steps
        "progression / target",     # 04_Deep_Protocol
        "duration",                 # 02_Brief_Today
        "week 1 easy version",      # 06_Weekly_Plan
        "week 1: easy start",       # 16_Progression_Weeks
        "optimal range (longevity)",# 10_Blood_Markers
        "reps / time", "reps/time", # 07_Exercise_Library v4
    ],
    "unit": ["unit", "units", "measure", "units"],
    "benefit_tags": ["benefits", "benefit_tags", "health benefits", "outcomes", "tags"],
    "source_key":   ["source key", "source", "source_key", "ref", "reference"],
    "link":         ["link", "url", "resource link", "learn more",
                     "animated gif/reference search", "gif/reference search"],  # 07_Exercise_Library v4
    "video_link":   ["video", "video link", "video url", "watch", "demo",
                     "youtube demo search"],                                     # 07_Exercise_Library v4
    "safety_notes": ["safety", "safety notes", "caution", "warning", "contraindications",
                     "safety stop / pain rule", "safety stop/pain rule"],        # 07_Exercise_Library v4
    "how_to":       ["how to do it", "how-to", "instructions", "steps", "method", "technique",
                     "how to", "exact method",
                     "step-by-step execution", "step by step execution"],        # 07_Exercise_Library v4
    "why_mechanism":["why (mechanism)", "mechanism (why it works)", "mechanism", "science",
                     "rationale", "reason"],
}

# Sheets to skip from regular daily-todo generation.
# exercise_library → reference only; daily exercise comes from 30-day rotation
# progression_weeks, weekly_plan, guided_steps, deep_protocol → planning reference
# 30day_rotation → parsed into RotationDay table separately (see upload router)
# blood_markers, screenings_safety → parsed into Screening table separately
SKIP_SHEETS: set[str] = {
    "readme", "dashboard", "sources", "personal_settings",
    # exercise_library moved to REFERENCE_PILLARS — parsed as reference, not skipped
    "blood_markers",
    "screenings_safety",
    "progression_weeks",
    "weekly_plan",
    "guided_steps",
    "deep_protocol",
    "30day_rotation",
    "time_audit",          # workout time-budget planning sheet — not user tasks
    "demo_link_guide",     # link usage guide — not user tasks
}

# Sheets that are parsed into the Screening table instead of task_templates
SCREENING_SHEETS: set[str] = {"blood_markers", "screenings_safety"}

# Pillars whose rows are reference material — parsed as TaskTemplates with is_reference=True.
# They never generate daily todos but appear in the Reference tab.
REFERENCE_PILLARS: set[str] = {"nutrition", "sleep_recovery", "cognitive_social", "exercise_library"}
