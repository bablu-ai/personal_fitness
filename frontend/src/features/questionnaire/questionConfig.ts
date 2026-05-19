import type { Question, SectionMeta } from './types'

export const SECTIONS: SectionMeta[] = [
  { number: 1, title: 'Personal Information',    questionCount: 5, iconName: 'User',     estimatedMinutes: 2 },
  { number: 2, title: 'Health & Medical',        questionCount: 5, iconName: 'Heart',    estimatedMinutes: 3 },
  { number: 3, title: 'Activity & Fitness',      questionCount: 5, iconName: 'Activity', estimatedMinutes: 2 },
  { number: 4, title: 'Nutrition & Supplements', questionCount: 6, iconName: 'Apple',    estimatedMinutes: 3 },
  { number: 5, title: 'Lifestyle & Schedule',    questionCount: 5, iconName: 'Clock',    estimatedMinutes: 2 },
  { number: 6, title: 'Monitoring & Tracking',   questionCount: 5, iconName: 'Monitor',  estimatedMinutes: 2 },
  { number: 7, title: 'Additional Information',  questionCount: 9, iconName: 'Info',     estimatedMinutes: 4 },
]

export const QUESTIONS: Question[] = [
  // SECTION 1 — Personal Information
  { id: 'q1_full_name',    section: 1, number: 1,  type: 'text',          text: 'What is your full name?',          required: true,  placeholder: 'Enter your full name' },
  { id: 'q2_date_of_birth', section: 1, number: 2, type: 'date',          text: 'Date of birth (YYYY-MM-DD)',        required: true },
  { id: 'q3_sex_at_birth', section: 1, number: 3,  type: 'single_choice', text: 'Sex at birth',                     required: true,  options: ['Male', 'Female', 'Intersex', 'Prefer not to say'] },
  { id: 'q4_height_cm',   section: 1, number: 4,  type: 'number',        text: 'Height (cm)',                      required: true,  placeholder: 'e.g. 175', validation: { min: 50, max: 300 } },
  { id: 'q5_weight_kg',   section: 1, number: 5,  type: 'number',        text: 'Weight (kg)',                      required: true,  placeholder: 'e.g. 80',  validation: { min: 20, max: 500 } },

  // SECTION 2 — Health & Medical
  {
    id: 'q6_chronic_conditions', section: 2, number: 6, type: 'multi_choice',
    text: 'Do you have any diagnosed chronic conditions? (select all that apply)',
    required: false,
    options: ['Hypertension', 'Diabetes', 'Cardiovascular disease', 'Osteoporosis', 'Arthritis', 'None', 'Other'],
    conditional: { triggerOption: 'Other', placeholder: 'Please describe', fieldId: 'q6_other' },
  },
  {
    id: 'q7_medications', section: 2, number: 7, type: 'conditional_text',
    text: 'Are you currently taking any medications that affect heart rate, blood pressure or exercise tolerance?',
    required: false, options: ['Yes', 'No'],
    conditional: { triggerOption: 'Yes', placeholder: 'Please specify medications', fieldId: 'q7_detail' },
  },
  {
    id: 'q8_mobility_limitations', section: 2, number: 8, type: 'conditional_text',
    text: 'Do you have any movement or mobility limitations?',
    required: false, options: ['Yes', 'No'],
    conditional: { triggerOption: 'Yes', placeholder: 'Please describe your limitations', fieldId: 'q8_detail' },
  },
  {
    id: 'q9_surgeries_injuries', section: 2, number: 9, type: 'conditional_text',
    text: 'Have you had any surgeries or injuries that affect your ability to exercise?',
    required: false, options: ['Yes', 'No'],
    conditional: { triggerOption: 'Yes', placeholder: 'Please describe', fieldId: 'q9_detail' },
  },
  {
    id: 'q10_last_physical_exam', section: 2, number: 10, type: 'single_choice',
    text: 'When was your most recent physical exam or exercise clearance?',
    required: true,
    options: ['Within the last 3 months', '3–6 months ago', 'More than 6 months ago', "Never / don't recall"],
  },

  // SECTION 3 — Activity & Fitness
  {
    id: 'q11_activity_level', section: 3, number: 11, type: 'single_choice',
    text: 'How would you describe your current activity level?',
    required: true, options: ['Sedentary', 'Lightly active', 'Moderately active', 'Very active'],
  },
  {
    id: 'q12_daily_exercise_minutes', section: 3, number: 12, type: 'single_choice',
    text: 'How many minutes per day can you consistently commit to exercise?',
    required: true, options: ['Less than 30 minutes', '30–60 minutes', '60–90 minutes', 'More than 90 minutes'],
  },
  {
    id: 'q13_fitness_goals', section: 3, number: 13, type: 'multi_choice',
    text: 'What are your primary fitness goals? (select all that apply)',
    required: false,
    options: ['Build muscle strength', 'Improve cardiovascular endurance', 'Enhance mobility/flexibility', 'Improve balance and fall prevention', 'Weight loss or weight management', 'Maintain independence for daily activities', 'Other'],
    conditional: { triggerOption: 'Other', placeholder: 'Please describe', fieldId: 'q13_other' },
  },
  {
    id: 'q14_equipment_access', section: 3, number: 14, type: 'multi_choice',
    text: 'Which exercise equipment do you have access to? (select all that apply)',
    required: false,
    options: ['Resistance bands', 'Dumbbells/kettlebells', 'Barbell/weight machines', 'Cardio machine (treadmill, bike, rowing machine)', 'None (bodyweight only)'],
  },
  {
    id: 'q15_bodyweight_comfortable', section: 3, number: 15, type: 'single_choice',
    text: 'Are you comfortable using body-weight exercises (e.g. squats, planks, bridges)?',
    required: true, options: ['Yes', 'No'],
  },

  // SECTION 4 — Nutrition & Supplements
  {
    id: 'q16_dietary_pattern', section: 4, number: 16, type: 'single_choice',
    text: 'Describe your usual dietary pattern',
    required: true, options: ['Omnivore', 'Vegetarian', 'Vegan', 'Pescatarian', 'Other'],
    conditional: { triggerOption: 'Other', placeholder: 'Please describe', fieldId: 'q16_other' },
  },
  {
    id: 'q17_dietary_restrictions', section: 4, number: 17, type: 'conditional_text',
    text: 'Do you have any dietary restrictions or food allergies?',
    required: false, options: ['Yes', 'No'],
    conditional: { triggerOption: 'Yes', placeholder: 'Please list your restrictions or allergies', fieldId: 'q17_detail' },
  },
  {
    id: 'q18_meals_per_day', section: 4, number: 18, type: 'single_choice',
    text: 'How many meals do you typically eat per day?',
    required: true, options: ['1–2', '3', '4', 'More than 4'],
  },
  {
    id: 'q19_current_supplements', section: 4, number: 19, type: 'multi_choice',
    text: 'Are you currently taking any supplements? (select all that apply)',
    required: false,
    options: ['Creatine', 'Omega-3 fish oil', 'Psyllium husk fiber', 'Curcumin', 'Vitamin D', 'Magnesium', 'Protein powder', 'None', 'Other'],
    conditional: { triggerOption: 'Other', placeholder: 'Please list', fieldId: 'q19_other' },
  },
  {
    id: 'q20_nutrient_deficiencies', section: 4, number: 20, type: 'conditional_text',
    text: 'Do you have known nutrient deficiencies (e.g. vitamin D, iron)?',
    required: false, options: ['Yes', 'No'],
    conditional: { triggerOption: 'Yes', placeholder: 'Please describe', fieldId: 'q20_detail' },
  },
  {
    id: 'q21_track_macros', section: 4, number: 21, type: 'single_choice',
    text: 'Do you plan to track macros (protein, fat, carbs) daily?',
    required: true, options: ['Yes', 'No'],
  },

  // SECTION 5 — Lifestyle & Schedule
  { id: 'q22_wake_time', section: 5, number: 22, type: 'time', text: 'What time do you usually wake up?',     required: true, placeholder: '05:30' },
  { id: 'q23_bed_time',  section: 5, number: 23, type: 'time', text: 'What time do you usually go to bed?',  required: true, placeholder: '22:00' },
  {
    id: 'q24_shift_work', section: 5, number: 24, type: 'single_choice',
    text: 'Do you work shifts or have a variable schedule?',
    required: true, options: ['Yes', 'No'],
  },
  {
    id: 'q25_include_balance_training', section: 5, number: 25, type: 'single_choice',
    text: 'Are you willing to include balance and mobility training in your routine?',
    required: true, options: ['Yes', 'No'],
  },
  {
    id: 'q26_cognitive_social', section: 5, number: 26, type: 'conditional_text',
    text: 'Would you like cognitive and social-health activities included?',
    required: false, options: ['Yes', 'No'],
    conditional: { triggerOption: 'Yes', placeholder: 'Preferred activities (language learning, music, journaling, meditation, etc.)', fieldId: 'q26_detail' },
  },

  // SECTION 6 — Monitoring & Tracking
  {
    id: 'q27_measure_bp_at_home', section: 6, number: 27, type: 'single_choice',
    text: 'Are you comfortable measuring your blood pressure and weight at home?',
    required: true, options: ['Yes', 'No'],
  },
  {
    id: 'q28_wearable_devices', section: 6, number: 28, type: 'conditional_text',
    text: 'Do you use any wearable devices to track heart rate, steps or sleep?',
    required: false, options: ['Yes', 'No'],
    conditional: { triggerOption: 'Yes', placeholder: 'Devices used (Garmin, Apple Watch, Oura, Whoop, etc.)', fieldId: 'q28_detail' },
  },
  {
    id: 'q29_quarterly_blood_tests', section: 6, number: 29, type: 'single_choice',
    text: 'Are you willing to obtain quarterly blood tests to track biomarkers (e.g. HbA1c, ApoB, vitamin D)?',
    required: true, options: ['Yes', 'No'],
  },
  {
    id: 'q30_screening_reminders', section: 6, number: 30, type: 'single_choice',
    text: 'Would you like reminders for regular cancer screenings and health check-ups (colonoscopy, mammogram, PSA, etc.)?',
    required: true, options: ['Yes', 'No'],
  },
  {
    id: 'q31_open_to_trainer', section: 6, number: 31, type: 'single_choice',
    text: 'Are you open to working with a certified trainer or physical therapist for form and safety review?',
    required: true, options: ['Yes', 'No'],
  },

  // SECTION 7 — Additional Information
  { id: 'q32_other_goals',       section: 7, number: 32, type: 'text', text: 'Do you have any other specific goals or concerns we should be aware of?', required: false, placeholder: 'Optional — share anything else' },
  { id: 'q33_exercises_to_avoid', section: 7, number: 33, type: 'text', text: 'Are there any exercises you particularly enjoy or wish to avoid?',         required: false, placeholder: 'Optional' },
  {
    id: 'q34_preferred_exercise_time', section: 7, number: 34, type: 'single_choice',
    text: 'Is there a preferred time of day for exercise?',
    required: true, options: ['Early morning (e.g. 5:40–6:40)', 'Late morning/afternoon', 'Evening', 'Flexible', 'Other'],
    conditional: { triggerOption: 'Other', placeholder: 'Please specify', fieldId: 'q34_other' },
  },
  {
    id: 'q35_current_routine', section: 7, number: 35, type: 'conditional_text',
    text: 'Do you currently follow any exercise routine or program?',
    required: false, options: ['Yes', 'No'],
    conditional: { triggerOption: 'Yes', placeholder: 'Please describe your current routine', fieldId: 'q35_detail' },
  },
  {
    id: 'q36_medical_devices', section: 7, number: 36, type: 'conditional_text',
    text: 'Do you require modifications because of medical devices (e.g. pacemaker, joint replacement)?',
    required: false, options: ['Yes', 'No'],
    conditional: { triggerOption: 'Yes', placeholder: 'Please specify', fieldId: 'q36_detail' },
  },
  {
    id: 'q37_daily_metrics', section: 7, number: 37, type: 'conditional_text',
    text: 'Are there specific metrics you would like to record daily (e.g. weight, step count, mood, energy levels)?',
    required: false, options: ['Yes', 'No'],
    conditional: { triggerOption: 'Yes', placeholder: 'Please list your preferred metrics', fieldId: 'q37_detail' },
  },
  {
    id: 'q38_video_review', section: 7, number: 38, type: 'single_choice',
    text: 'Would you like the option of submitting video clips for form review by a coach or trainer?',
    required: true, options: ['Yes', 'No'],
  },
  {
    id: 'q39_comfortable_with_tech', section: 7, number: 39, type: 'single_choice',
    text: 'Are you comfortable using a smartphone or spreadsheet software daily for tracking?',
    required: true, options: ['Yes', 'No'],
  },
  {
    id: 'q40_privacy', section: 7, number: 40, type: 'conditional_text',
    text: 'Do you require privacy or data-anonymization measures?',
    required: false, options: ['Yes', 'No'],
    conditional: { triggerOption: 'Yes', placeholder: 'Please specify your privacy preferences', fieldId: 'q40_detail' },
  },
]

export const QUESTION_BY_ID: Record<string, Question> = Object.fromEntries(
  QUESTIONS.map(q => [q.id, q])
)

export const SECTION_QUESTIONS = (sectionNum: number): Question[] =>
  QUESTIONS.filter(q => q.section === sectionNum)

export const FIRST_QUESTION_OF_SECTION = (sectionNum: number): Question =>
  QUESTIONS.find(q => q.section === sectionNum)!
