import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="SDG3 — Health & Wellbeing Recommender", layout="centered")

# ---------- Helper functions ----------

def calc_bmi(weight_kg, height_cm):
    h_m = height_cm / 100.0
    if h_m <= 0:
        return None
    return weight_kg / (h_m ** 2)

def bmi_category(bmi):
    if bmi is None:
        return "Unknown"
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal weight"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obesity"

def bmr_mifflin(weight, height, age, gender):
    # weight in kg, height in cm, age in years
    if gender.lower() == "male":
        return 10*weight + 6.25*height - 5*age + 5
    else:
        return 10*weight + 6.25*height - 5*age - 161

def activity_multiplier(level):
    mapping = {
        "sedentary": 1.2,       # little or no exercise
        "light": 1.375,         # light exercise 1-3 days/week
        "moderate": 1.55,       # moderate 3-5 days/week
        "active": 1.725,        # hard exercise 6-7 days/week
        "very active": 1.9      # very hard exercise / physical job
    }
    return mapping.get(level, 1.2)

def calorie_target(tdee, goal):
    if goal == 'lose':
        # Conservative safe deficit ~500 kcal/day for ~0.45 kg/week
        return max(1200, tdee - 500)
    elif goal == 'gain':
        return tdee + 300
    else:
        return tdee

def macro_split(calories, protein_g_per_kg, weight):
    # Calculate macros based on protein target (g/kg), then split remaining calories to fats and carbs
    protein_g = protein_g_per_kg * weight
    protein_cals = protein_g * 4
    # target: 25-30% calories from fat (we'll pick 30% as default)
    fat_cals = calories * 0.30
    fat_g = fat_cals / 9
    carb_cals = calories - protein_cals - fat_cals
    carb_g = max(0, carb_cals / 4)
    return {
        'protein_g': round(protein_g),
        'fat_g': round(fat_g),
        'carb_g': round(carb_g)
    }

# ---------- UI ----------

st.title("SDG 3 — Good Health & Wellbeing: Diet & Exercise Recommender")
st.markdown(
    "This tool calculates BMI, estimates calorie needs, and gives a personalized diet and exercise plan aligned with Sustainable Development Goal 3: Good Health and Wellbeing."
)

with st.form("inputs"):
    st.header("Enter your details")
    col1, col2 = st.columns(2)
    with col1:
        weight = st.number_input("Weight (kg)", min_value=20.0, max_value=300.0, value=70.0, step=0.1)
        age = st.number_input("Age (years)", min_value=10, max_value=100, value=25, step=1)
        water_cups = st.number_input("Water intake (cups per day, 1 cup = ~250 ml)", min_value=0, max_value=20, value=6)
    with col2:
        height = st.number_input("Height (cm)", min_value=80.0, max_value=250.0, value=170.0, step=0.1)
        gender = st.selectbox("Gender", options=["male", "female", "other"], index=0)
        exercise_level = st.selectbox(
            "Exercise level",
            options=["sedentary", "light", "moderate", "active", "very active"],
            index=1
        )

    st.write("\n")
    goal = st.radio("What's your primary short-term goal?", options=["maintain", "lose", "gain"], index=0)

    submitted = st.form_submit_button("Get recommendation")

if not submitted:
    st.info("Fill the form and click 'Get recommendation' to see personalized suggestions.")
    st.stop()

# ---------- Calculations ----------

bmi = calc_bmi(weight, height)
bmi_text = f"{bmi:.1f}" if bmi is not None else "—"
category = bmi_category(bmi)

bmr = bmr_mifflin(weight, height, age, gender if gender in ['male','female'] else 'female')
mult = activity_multiplier(exercise_level)
tdee = bmr * mult
cal_target = calorie_target(tdee, goal)

# protein recommendation based on goal
if goal == 'lose':
    protein_g_per_kg = 1.6  # higher protein to preserve muscle during deficit
elif goal == 'gain':
    protein_g_per_kg = 1.6
else:
    protein_g_per_kg = 1.2

macros = macro_split(cal_target, protein_g_per_kg, weight)

# ---------- Output ----------

st.subheader("Body metrics & energy needs")
col1, col2 = st.columns(2)
with col1:
    st.metric("BMI", bmi_text)
    st.write(f"Category: *{category}*")
    st.write(f"BMR (Mifflin-St Jeor): *{round(bmr)} kcal/day*")
with col2:
    st.write(f"Activity multiplier: *{mult}* ({exercise_level})")
    st.write(f"Estimated TDEE: *{round(tdee)} kcal/day*")
    st.write(f"Recommended daily calories ({goal}): *{round(cal_target)} kcal/day*")

# BMI gauge visualization
fig, ax = plt.subplots(figsize=(6,1.2))
ax.set_xlim(10,40)
ax.set_ylim(0,1)
ax.axis('off')
# rectangles for BMI ranges
ranges = [(10,18.5,'Under'), (18.5,25,'Normal'), (25,30,'Over'), (30,40,'Obese')]
colors = ['#ffd1dc','#c8f7c5','#fff2b2','#ffb3b3']
for (start,end,_),c in zip(ranges,colors):
    ax.fill_betweenx([0,1],[start],[end], color=c)
ax.plot([bmi,bmi],[0,1], color='black')
ax.text(10,0.5,'',)
st.pyplot(fig)

st.subheader("Hydration check")
recommended_water_ml = 30 * weight  # rough: 30 ml per kg bodyweight
recommended_cups = round(recommended_water_ml / 250)
st.write(f"You reported *{water_cups} cups ({water_cups*250} ml)* per day.")
st.write(f"General recommendation: *~{recommended_cups} cups ({recommended_water_ml:.0f} ml)* per day (approx. 30 ml/kg).")
if water_cups < recommended_cups:
    st.warning("You're drinking less than the general recommendation — try increasing water gradually.")
else:
    st.success("Your reported water intake meets or exceeds the general guideline.")

st.subheader("Personalized diet recommendation")
st.write(f"Daily calorie target: *{round(cal_target)} kcal*")
st.write(f"Macronutrient targets (approx.): Protein *{macros['protein_g']} g, Fat *{macros['fat_g']} g*, Carbs *{macros['carb_g']} g**")

st.markdown("*Nutrition guidance & sample meals*")

# Sample meal plan generator (simple templates)

def sample_meal_plan(calories):
    # Simple heuristic: 20% breakfast, 30% lunch, 15% snack, 35% dinner
    b = int(calories * 0.20)
    l = int(calories * 0.30)
    s = int(calories * 0.15)
    d = int(calories * 0.35)
    return {
        'Breakfast': (b, ["Oats or wholegrain cereal (1 bowl)", "1 serving fruit", "6-8 egg whites or 1 whole egg + 2 whites or paneer/tofu"]),
        'Lunch': (l, ["1 cup cooked whole grains (rice/quinoa)", "Large serving vegetables/salad", "100-150 g lean protein (chicken/fish/legumes)"]),
        'Snack': (s, ["Greek yogurt or a handful of nuts + fruit"]),
        'Dinner': (d, ["Vegetable stir-fry or salad with protein", "Smaller portion of carbs than lunch"])
    }

plan = sample_meal_plan(round(cal_target))
for meal, (cals, items) in plan.items():
    st.write(f"*{meal} — ~{cals} kcal*")
    for it in items:
        st.write("- ", it)

st.markdown("*Practical nutrition tips*")
st.write("- Prefer whole foods over ultra-processed foods.\n- Prioritise lean protein, whole grains, legumes, vegetables, and healthy fats.\n- Watch portion sizes and use a food scale/app if precise tracking is needed.\n- If trying to lose weight, aim for a modest calorie deficit and maintain protein intake to preserve muscle.")

st.subheader("Personalized exercise recommendation")

# Exercise suggestions based on BMI and exercise level

def exercise_plan(bmi, level):
    plans = {}
    # Base aerobic recommendations
    if level in ['sedentary','light']:
        cardio = "Start with 20-30 minutes brisk walking 4-5x/week. Gradually increase intensity to include 2 sessions of 20-30 minutes of jogging or cycling."
    elif level == 'moderate':
        cardio = "Maintain 30-45 minutes of moderate cardio 4-5x/week; include 1-2 higher-intensity intervals per week."
    else:
        cardio = "Keep varied cardio 4-6x/week, include intervals or sports for intensity and enjoyment."

    # Strength training
    if bmi is None:
        strength = "General strength training 2-3x/week focusing on all major muscle groups."
    elif bmi < 18.5:
        strength = "Focus on progressive resistance training 3x/week to build muscle mass; use compound lifts and ensure calorie surplus if trying to gain."
    elif bmi < 25:
        strength = "Balanced strength training 2-4x/week to preserve muscle and support metabolism; combine full-body sessions."
    else:
        strength = "Begin with low-impact strength and mobility work 2-3x/week, gradually increase intensity; combine with aerobic work for fat loss."

    mobility = "Include mobility and flexibility work (10-15 min) after workouts or on rest days — yoga or dynamic stretching." 

    return {
        'cardio': cardio,
        'strength': strength,
        'mobility': mobility
    }

ex_plan = exercise_plan(bmi, exercise_level)
st.write("*Cardio:*", ex_plan['cardio'])
st.write("*Strength training:*", ex_plan['strength'])
st.write("*Mobility & recovery:*", ex_plan['mobility'])

st.markdown("*Safety & notes*")
st.write("- Consult a doctor before starting any new intense program, especially if you have existing medical conditions.\n- Start slow and progress gradually.\n- Sleep, stress management and consistent hydration are essential for health and fitness goals.\n- This tool provides general guidance — for a detailed clinical or therapeutic plan, consult a registered dietitian or certified trainer.")

st.markdown("---")
st.caption("This app is aligned with Sustainable Development Goal 3 (Good Health and Wellbeing): promoting healthy lives and well-being for all ages.")

# Offer download of summary as CSV
summary = {
    'metric': ['BMI','BMI_category','BMR_kcal','TDEE_kcal','Calorie_target_kcal','Protein_g','Fat_g','Carb_g','Water_cups_reported','Water_cups_recommended','Exercise_level'],
    'value': [round(bmi,1) if bmi else '', category, round(bmr), round(tdee), round(cal_target), macros['protein_g'], macros['fat_g'], macros['carb_g'], water_cups, recommended_cups, exercise_level]
}