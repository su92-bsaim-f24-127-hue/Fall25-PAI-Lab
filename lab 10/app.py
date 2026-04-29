from flask import Flask, render_template, request, jsonify
import re
import math
from collections import Counter

app = Flask(__name__)

STOP_WORDS = {
    "a","an","the","is","it","in","on","at","to","for","of","and","or",
    "but","not","with","this","that","do","i","you","me","my","we","can",
    "how","what","when","why","which","should","would","could","will","be",
    "are","was","were","has","have","had","am","tell","give","please","about",
    "some","any","if","also","just","get","need","want","help","make","use",
}

STEMMER_RULES = [
    ("nesses", ""), ("ments", ""), ("ations", "ate"), ("ings", ""),
    ("ness",  ""), ("ment",  ""), ("ation", "ate"), ("ing",  ""),
    ("ers",   ""), ("ies",   "y"), ("es",   ""),    ("ed",   ""),
    ("er",    ""), ("ly",    ""),  ("s",    ""),
]

def stem(word):
    for suffix, replacement in STEMMER_RULES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: len(word) - len(suffix)] + replacement
    return word

def tokenize(text):
    """Lowercase → split on non-alpha → remove stop words → stem."""
    tokens = re.findall(r"[a-z]+", text.lower())
    return [stem(t) for t in tokens if t not in STOP_WORDS and len(t) > 2]

def tfidf_score(query_tokens, doc_tokens):
    """Simple TF-IDF–inspired cosine similarity between two token lists."""
    if not query_tokens or not doc_tokens:
        return 0.0
    q_freq = Counter(query_tokens)
    d_freq = Counter(doc_tokens)
    vocab  = set(q_freq) | set(d_freq)
    dot, q_norm, d_norm = 0.0, 0.0, 0.0
    for w in vocab:
        q_val = q_freq.get(w, 0)
        d_val = d_freq.get(w, 0)
        dot    += q_val * d_val
        q_norm += q_val ** 2
        d_norm += d_val ** 2
    denom = math.sqrt(q_norm) * math.sqrt(d_norm)
    return dot / denom if denom else 0.0


QA_PAIRS = [
    {
        "tags": ["lose weight", "fat loss", "weight loss", "slim down",
                 "burn fat", "reduce weight", "get lean", "cut fat"],
        "answer": (
            "🔥 <b>Weight Loss Strategy</b><br>"
            "• Create a 300–500 kcal daily calorie deficit.<br>"
            "• Do 150–300 min of moderate cardio per week (brisk walk, cycling, swimming).<br>"
            "• Prioritise protein (1.2–1.6 g/kg body weight) to preserve muscle.<br>"
            "• Minimise ultra-processed foods, sugary drinks, and alcohol.<br>"
            "• Sleep 7–9 hrs — sleep deprivation spikes hunger hormones (ghrelin).<br>"
            "• Track food with apps like MyFitnessPal for accountability."
        ),
    },
    {
        "tags": ["intermittent fasting", "fasting", "16 8", "eat window",
                 "time restricted eating", "if diet"],
        "answer": (
            "⏰ <b>Intermittent Fasting (IF)</b><br>"
            "• Most popular protocol: <b>16:8</b> — fast 16 hrs, eat within an 8-hr window.<br>"
            "• Helps reduce calorie intake naturally and improves insulin sensitivity.<br>"
            "• During the fast: water, black coffee, and plain tea are allowed.<br>"
            "• Break your fast with a protein-rich meal to protect muscle.<br>"
            "• <i>Not recommended</i> for people with a history of eating disorders or diabetes without medical supervision."
        ),
    },
    {
        "tags": ["calorie deficit", "calories", "calorie counting",
                 "how many calories", "kcal", "tdee"],
        "answer": (
            "📊 <b>Calorie Deficit Explained</b><br>"
            "• Your TDEE (Total Daily Energy Expenditure) = BMR × activity multiplier.<br>"
            "• A deficit of <b>500 kcal/day ≈ 0.5 kg fat loss per week</b>.<br>"
            "• Never drop below 1,200 kcal (women) or 1,500 kcal (men) without medical guidance.<br>"
            "• Use the Mifflin-St Jeor formula to estimate your BMR:<br>"
            "  Men: 10×weight(kg) + 6.25×height(cm) − 5×age + 5<br>"
            "  Women: 10×weight(kg) + 6.25×height(cm) − 5×age − 161"
        ),
    },
    {
        "tags": ["gain muscle", "muscle gain", "build muscle", "bulk up",
                 "hypertrophy", "get bigger", "mass gain", "put on muscle"],
        "answer": (
            "💪 <b>Muscle Building (Hypertrophy)</b><br>"
            "• Train each muscle group 2× per week with 10–20 sets total per week.<br>"
            "• Rep range: 6–12 reps at 65–85% of your 1-rep max for hypertrophy.<br>"
            "• <b>Progressive overload</b> — add weight or reps every 1–2 weeks.<br>"
            "• Eat in a 200–300 kcal surplus and consume 1.6–2.2 g protein/kg body weight.<br>"
            "• Rest 48–72 hrs between training the same muscle group.<br>"
            "• Key exercises: Squat, Deadlift, Bench Press, Pull-Up, Overhead Press, Rows."
        ),
    },
    {
        "tags": ["protein", "protein intake", "how much protein",
                 "protein foods", "protein sources", "whey"],
        "answer": (
            "🥩 <b>Protein for Muscle & Health</b><br>"
            "• Muscle building: <b>1.6–2.2 g/kg</b> body weight/day.<br>"
            "• Weight loss (preserve muscle): 1.2–1.6 g/kg/day.<br>"
            "• Best whole-food sources: chicken breast, eggs, Greek yogurt, lentils, tuna, cottage cheese, tofu.<br>"
            "• Whey protein shakes are a convenient supplement — not a necessity if diet is adequate.<br>"
            "• Spread protein across 3–5 meals; body can optimally use ~40 g per meal."
        ),
    },
    {
        "tags": ["creatine", "supplement", "supplements", "pre workout",
                 "bcaa", "mass gainer", "protein powder"],
        "answer": (
            "💊 <b>Fitness Supplements</b><br>"
            "• <b>Creatine monohydrate</b> — most researched supplement; boosts strength & muscle mass. 3–5 g/day.<br>"
            "• <b>Whey protein</b> — convenient protein source post-workout.<br>"
            "• <b>Caffeine</b> — proven performance enhancer; 3–6 mg/kg body weight pre-workout.<br>"
            "• <b>Vitamin D & Omega-3</b> — widely deficient; support hormones & recovery.<br>"
            "• <i>Skip</i>: BCAAs (redundant if protein intake is adequate), fat burners, and most 'proprietary blends'."
        ),
    },
    {
        "tags": ["diet", "nutrition", "eating", "food plan",
                 "healthy eating", "what to eat", "balanced diet"],
        "answer": (
            "🥗 <b>Balanced Diet Blueprint</b><br>"
            "• <b>Protein</b> (25–35%): chicken, fish, eggs, legumes, dairy.<br>"
            "• <b>Carbohydrates</b> (40–50%): oats, brown rice, sweet potato, fruits, vegetables.<br>"
            "• <b>Fats</b> (20–30%): avocado, nuts, olive oil, fatty fish.<br>"
            "• Follow the 80/20 rule — 80% whole foods, 20% flexibility prevents burnout.<br>"
            "• Eat 3–5 meals/day; don't skip breakfast if it causes binge-eating later."
        ),
    },
    {
        "tags": ["meal plan", "meal prep", "weekly meal", "meal schedule",
                 "what should i eat", "daily meals"],
        "answer": (
            "📅 <b>Sample Weekly Meal Plan</b><br>"
            "• <b>Breakfast</b>: Oats + banana + whey OR eggs + whole-grain toast + avocado.<br>"
            "• <b>Lunch</b>: Grilled chicken + brown rice + steamed broccoli.<br>"
            "• <b>Snack</b>: Greek yogurt + almonds OR apple + peanut butter.<br>"
            "• <b>Dinner</b>: Salmon + sweet potato + salad OR lentil soup + whole-grain bread.<br>"
            "• Prep proteins and grains in bulk on Sunday to save weekday time."
        ),
    },
    {
        "tags": ["carbs", "carbohydrates", "carb", "carbohydrate",
                 "sugar", "bread", "rice pasta"],
        "answer": (
            "🍞 <b>Carbohydrates — The Truth</b><br>"
            "• Carbs are the body's <b>primary fuel source</b> — don't fear them.<br>"
            "• Choose complex carbs: oats, brown rice, quinoa, sweet potato, whole-grain bread.<br>"
            "• Limit simple/refined carbs: white bread, pastries, sugary cereals, sodas.<br>"
            "• Time carbs around workouts for best energy and recovery.<br>"
            "• Fibre-rich carbs (vegetables, legumes) support gut health and satiety."
        ),
    },
    {
        "tags": ["healthy fats", "fat", "fats", "good fat", "omega 3",
                 "avocado", "nuts", "olive oil"],
        "answer": (
            "🥑 <b>Healthy Fats</b><br>"
            "• <b>Monounsaturated</b>: olive oil, avocado, almonds — heart-healthy.<br>"
            "• <b>Polyunsaturated (Omega-3)</b>: salmon, walnuts, flaxseed — anti-inflammatory.<br>"
            "• <b>Saturated fats</b>: limit to <10% of calories (butter, red meat, coconut oil).<br>"
            "• <b>Trans fats</b>: avoid completely — found in fried fast food and margarine.<br>"
            "• Fat is essential for hormone production, vitamin absorption (A, D, E, K), and brain health."
        ),
    },
    {
        "tags": ["hydration", "water", "drink water", "how much water",
                 "dehydration", "electrolytes"],
        "answer": (
            "💧 <b>Hydration</b><br>"
            "• General guideline: <b>~35 ml per kg</b> body weight per day.<br>"
            "• During exercise: 500 ml before, 150–250 ml every 15–20 min during, 500 ml after.<br>"
            "• Signs of dehydration: dark urine, fatigue, headache, reduced performance.<br>"
            "• Electrolytes (sodium, potassium, magnesium) matter during long sessions >60 min.<br>"
            "• Coffee and tea count towards daily fluid intake — contrary to popular myth."
        ),
    },
    {
        "tags": ["vitamins", "minerals", "micronutrients", "vitamin d",
                 "iron", "calcium", "zinc", "magnesium"],
        "answer": (
            "🌿 <b>Key Micronutrients for Athletes</b><br>"
            "• <b>Vitamin D</b>: bone health, testosterone, immunity — supplement 1,000–2,000 IU/day if limited sun.<br>"
            "• <b>Iron</b>: oxygen transport — low in endurance athletes; sources: red meat, spinach, lentils.<br>"
            "• <b>Calcium</b>: bone density — 1,000 mg/day from dairy, fortified plant milk, broccoli.<br>"
            "• <b>Magnesium</b>: muscle relaxation & sleep — nuts, seeds, dark chocolate, leafy greens.<br>"
            "• <b>Zinc</b>: immune function & testosterone — meat, shellfish, pumpkin seeds."
        ),
    },
    {
        "tags": ["gym routine", "training plan", "workout plan",
                 "fitness routine", "weekly workout", "training schedule"],
        "answer": (
            "🏋️ <b>Weekly Workout Blueprint</b><br>"
            "• <b>Day 1</b>: Chest + Triceps (Bench Press, Dips, Cable Fly)<br>"
            "• <b>Day 2</b>: Back + Biceps (Pull-Up, Row, Curl)<br>"
            "• <b>Day 3</b>: Active Rest — 30 min walk or yoga<br>"
            "• <b>Day 4</b>: Legs (Squat, Romanian Deadlift, Leg Press, Calf Raise)<br>"
            "• <b>Day 5</b>: Shoulders + Core (OHP, Lateral Raises, Plank)<br>"
            "• <b>Day 6</b>: Cardio / HIIT — 20–30 min<br>"
            "• <b>Day 7</b>: Full Rest"
        ),
    },
    {
        "tags": ["beginner", "start fitness", "new to gym", "first time",
                 "starting workout", "fitness beginner", "gym beginner"],
        "answer": (
            "🌱 <b>Beginner Fitness Guide</b><br>"
            "• Start with 3 full-body workouts per week (Mon / Wed / Fri).<br>"
            "• Learn the 5 fundamental movements: squat, hinge (deadlift), push, pull, carry.<br>"
            "• Master bodyweight first: push-ups, bodyweight squats, lunges, planks, glute bridges.<br>"
            "• Progress slowly — add 2.5–5 kg to the bar each week (linear progression).<br>"
            "• Great beginner programs: <i>StrongLifts 5×5</i>, <i>GZCLP</i>, <i>PPL (Push-Pull-Legs)</i>.<br>"
            "• Consistency > intensity in the first 3 months."
        ),
    },
    {
        "tags": ["home workout", "no gym", "no equipment", "home exercise",
                 "bodyweight", "workout at home"],
        "answer": (
            "🏠 <b>Effective Home Workout (No Equipment)</b><br>"
            "• <b>Upper Body</b>: Push-ups (5 variants), Diamond push-ups, Pike push-ups, Dips on chair.<br>"
            "• <b>Lower Body</b>: Squats, Bulgarian split squats, Lunges, Glute bridges, Wall sit.<br>"
            "• <b>Core</b>: Plank, Side plank, Dead bug, Bicycle crunches, Mountain climbers.<br>"
            "• <b>Cardio</b>: Jump squats, Burpees, High knees, Jump rope (if available).<br>"
            "• Structure: 4 rounds × 40 sec work / 20 sec rest — total 30 min."
        ),
    },
    {
        "tags": ["hiit", "hiit workout", "high intensity", "interval training",
                 "tabata", "circuit training", "fat burning cardio"],
        "answer": (
            "⚡ <b>HIIT (High-Intensity Interval Training)</b><br>"
            "• Burns <b>25–30% more calories</b> than steady-state cardio in less time.<br>"
            "• Classic protocol: 20 sec max effort → 10 sec rest × 8 rounds (Tabata).<br>"
            "• Or: 40 sec work / 20 sec rest for 20–30 min (easier for beginners).<br>"
            "• Exercises: sprints, burpees, jump squats, kettlebell swings, battle ropes.<br>"
            "• Limit to <b>2–3 HIIT sessions/week</b> — central nervous system recovery is crucial.<br>"
            "• EPOC effect keeps metabolism elevated for 24–48 hrs post-session."
        ),
    },
    {
        "tags": ["cardio", "running", "cycling", "aerobic", "endurance",
                 "jogging", "swimming", "cardio exercise"],
        "answer": (
            "🏃 <b>Cardio Training</b><br>"
            "• <b>Zone 2 (low intensity)</b>: 60–70% max HR — best for fat oxidation & heart health.<br>"
            "• <b>Zone 4–5 (high intensity)</b>: 85–95% max HR — improves VO₂ max.<br>"
            "• WHO recommends 150 min moderate OR 75 min vigorous cardio per week.<br>"
            "• Running tip: build mileage no faster than 10% per week to prevent injury.<br>"
            "• Best calorie-burning cardio: rowing, swimming, cycling, running (in that order).<br>"
            "• Fasted cardio offers marginal benefits over fed cardio for most people."
        ),
    },
    {
        "tags": ["push up", "pushup", "chest exercise", "chest workout",
                 "pectoral", "bench press"],
        "answer": (
            "🤲 <b>Push-Up Mastery & Chest Training</b><br>"
            "• Perfect push-up form: hands shoulder-width, body straight, chest touches ground.<br>"
            "• Variations: Wide (outer chest), Narrow/Diamond (triceps), Decline (upper chest), Archer push-up (advanced).<br>"
            "• Gym progression: Dumbbell Fly → Incline Bench → Flat Bench → Weighted Dips.<br>"
            "• Chest grows best with a mix of heavy compound lifts (3–6 reps) and isolation work (10–15 reps).<br>"
            "• Train chest 2× per week for optimal hypertrophy."
        ),
    },
    {
        "tags": ["squat", "leg workout", "leg exercise", "quadriceps",
                 "glutes", "hamstring", "lower body"],
        "answer": (
            "🦵 <b>Leg Training</b><br>"
            "• <b>Squat</b>: King of lower-body movements — full depth, knees tracking over toes.<br>"
            "• <b>Romanian Deadlift</b>: Best hamstring exercise — hinge at hips, soft knee bend.<br>"
            "• <b>Bulgarian Split Squat</b>: Brutal but highly effective for quads & glutes.<br>"
            "• <b>Hip Thrust</b>: Superior glute activation vs squats.<br>"
            "• <b>Calf Raises</b>: Often neglected — do seated (soleus) and standing (gastrocnemius).<br>"
            "• Don't skip leg day! Legs = 60% of muscle mass — huge metabolic impact."
        ),
    },
    {
        "tags": ["deadlift", "back exercise", "back workout", "lat",
                 "pull up", "row", "back muscles"],
        "answer": (
            "🏗️ <b>Back & Deadlift Training</b><br>"
            "• <b>Deadlift</b>: Engages entire posterior chain — master hip hinge pattern first.<br>"
            "• Form cues: bar over mid-foot, neutral spine, push the floor away, lockout at top.<br>"
            "• <b>Pull-Up</b>: Best lat developer — full hang to chin above bar, control the descent.<br>"
            "• <b>Barbell Row</b>: Overhand grip targets lats; underhand grip targets lower traps & biceps.<br>"
            "• <b>Face Pulls</b>: Essential for rear delts and rotator cuff health.<br>"
            "• Aim for a 2:1 pull-to-push ratio for balanced shoulder health."
        ),
    },
    {
        "tags": ["abs", "core", "core workout", "six pack", "abdominal",
                 "plank", "crunch", "belly"],
        "answer": (
            "🎯 <b>Core & Abs Training</b><br>"
            "• <b>Myth</b>: Crunches alone won't give you a six-pack — body fat % is the key.<br>"
            "• Best core exercises: Plank, Dead Bug, Pallof Press, Ab Wheel Rollout, Hanging Leg Raise.<br>"
            "• Train core 3×/week — it recovers faster than other muscle groups.<br>"
            "• Anti-rotation and anti-extension exercises (Pallof press, plank) are more functional than crunches.<br>"
            "• Compound lifts (squat, deadlift, overhead press) are among the best core exercises."
        ),
    },
    {
        "tags": ["recovery", "rest day", "muscle recovery", "soreness",
                 "doms", "overtraining", "rest"],
        "answer": (
            "🔄 <b>Recovery & Rest</b><br>"
            "• Muscles grow during rest, not during training — don't neglect recovery.<br>"
            "• DOMS (Delayed Onset Muscle Soreness) peaks 24–72 hrs post-workout; light movement helps.<br>"
            "• Signs of overtraining: persistent fatigue, declining performance, mood changes, insomnia.<br>"
            "• Recovery toolkit: adequate sleep, nutrition, foam rolling, contrast showers, light yoga.<br>"
            "• Deload week (reduced volume/intensity) every 4–6 weeks for advanced trainees."
        ),
    },
    {
        "tags": ["sleep", "sleep fitness", "sleep recovery", "how much sleep",
                 "rest sleep", "sleep muscle"],
        "answer": (
            "😴 <b>Sleep & Fitness</b><br>"
            "• Growth hormone (GH) — the #1 muscle-building hormone — peaks during deep sleep.<br>"
            "• Sleep deprivation raises cortisol and ghrelin (hunger hormone), sabotaging fat loss.<br>"
            "• Aim for <b>7–9 hrs</b> per night; athletes may need up to 10 hrs.<br>"
            "• Optimise sleep: dark/cool room (18–20°C), no screens 1 hr before bed, consistent schedule.<br>"
            "• Naps of 10–20 min improve performance; longer naps can cause grogginess."
        ),
    },
    {
        "tags": ["stretching", "flexibility", "mobility", "stretch",
                 "yoga", "foam roll", "cool down"],
        "answer": (
            "🧘 <b>Flexibility & Mobility</b><br>"
            "• <b>Dynamic stretching</b> before workout: leg swings, arm circles, hip circles — improves performance.<br>"
            "• <b>Static stretching</b> after workout: hold 30–60 sec/muscle — improves flexibility over time.<br>"
            "• <b>Foam rolling</b>: reduces muscle tightness (myofascial release) — roll slowly over tender spots.<br>"
            "• Yoga 1–2×/week significantly improves mobility and reduces injury risk.<br>"
            "• Key tight areas for gym-goers: hip flexors, thoracic spine, hamstrings, ankles, pec minor."
        ),
    },
    {
        "tags": ["bmi", "body mass index", "healthy weight", "overweight",
                 "obese", "underweight", "body fat"],
        "answer": (
            "📏 <b>BMI & Body Composition</b><br>"
            "• BMI = weight(kg) ÷ height(m)² | Ranges: Underweight <18.5, Normal 18.5–24.9, Overweight 25–29.9, Obese ≥30.<br>"
            "• BMI is a screening tool, <b>not</b> a health verdict — it ignores muscle mass.<br>"
            "• <b>Body fat %</b> is more meaningful: Athletic males 6–13%, Fitness 14–17%; Athletic females 14–20%, Fitness 21–24%.<br>"
            "• Better metrics: waist circumference <94 cm (men) / <80 cm (women), waist-to-height ratio <0.5.<br>"
            "• DEXA scan or hydrostatic weighing give the most accurate body composition data."
        ),
    },
    {
        "tags": ["running plan", "5k", "10k", "marathon", "running training",
                 "run faster", "improve running"],
        "answer": (
            "🏅 <b>Running Training Plans</b><br>"
            "• <b>Couch to 5K (C25K)</b>: 8-week walk/run program — perfect for absolute beginners.<br>"
            "• <b>5K to 10K</b>: Add 10% mileage per week; add one tempo run per week.<br>"
            "• <b>Half Marathon</b>: 12-week plan; long run increases by 1–2 km/week.<br>"
            "• Speed work: Strides (20 sec accelerations), Tempo runs (comfortably hard pace), Intervals (800 m repeats).<br>"
            "• Strength training 2×/week (squats, hip thrusts, single-leg work) improves running economy."
        ),
    },
    {
        "tags": ["abs diet", "six pack diet", "get abs", "reveal abs",
                 "low body fat", "shredded", "ripped"],
        "answer": (
            "✂️ <b>Getting Abs / Getting Shredded</b><br>"
            "• Six-pack is revealed at ~10–12% body fat (men) or ~18–20% (women).<br>"
            "• 1 kg of fat loss requires a deficit of ~7,700 kcal — patience is essential.<br>"
            "• High-protein + high-fibre diet is the most effective for fat loss with muscle retention.<br>"
            "• Track daily steps — 8,000–10,000 steps/day adds significant calorie burn without stress.<br>"
            "• Avoid crash diets — they cause muscle loss and metabolic adaptation."
        ),
    },
    {
        "tags": ["women fitness", "female fitness", "women workout",
                 "female workout", "women strength", "ladies gym"],
        "answer": (
            "👩 <b>Fitness for Women</b><br>"
            "• Women benefit from strength training just as much as men — won't get 'bulky' without specific effort.<br>"
            "• Strength training increases metabolism, improves bone density (crucial for preventing osteoporosis), and enhances body composition.<br>"
            "• Training around menstrual cycle: follicular phase (Days 1–14) — higher strength & recovery; luteal phase (Days 15–28) — focus on endurance & lighter loads.<br>"
            "• Iron intake is especially important for menstruating women (18 mg/day).<br>"
            "• Great starter programs: PHUL, Strong Curves, 3-day full-body split."
        ),
    },
    {
        "tags": ["senior fitness", "older adult", "fitness over 50",
                 "elderly exercise", "60 years", "aging fitness"],
        "answer": (
            "👴 <b>Fitness for Older Adults (50+)</b><br>"
            "• Resistance training twice a week is the #1 recommendation to combat sarcopenia (muscle loss).<br>"
            "• Low-impact cardio: swimming, cycling, walking, elliptical — easy on joints.<br>"
            "• Balance training (single-leg stand, Tai Chi) reduces fall risk significantly.<br>"
            "• Protein needs increase with age: aim for 1.2–1.6 g/kg/day.<br>"
            "• Focus on mobility and posture; yoga and Pilates are excellent options.<br>"
            "• Always get medical clearance before starting a new program."
        ),
    },
    {
        "tags": ["posture", "back pain", "lower back", "back pain exercise",
                 "spine health", "hunchback", "neck pain"],
        "answer": (
            "🪑 <b>Posture & Back Pain</b><br>"
            "• Most back pain is caused by weak glutes, tight hip flexors, and poor thoracic mobility.<br>"
            "• <b>Key corrective exercises</b>: Glute Bridge, Dead Bug, Bird-Dog, Cat-Cow, Face Pull, Thoracic Extension.<br>"
            "• Ergonomics: monitor at eye level, hips at 90°, feet flat — stand up every 45 min.<br>"
            "• Avoid sit-ups/crunches if you have lower-back pain; plank and dead bug are safer.<br>"
            "• Strengthening the posterior chain (glutes, hamstrings, back) is the long-term fix."
        ),
    },
    {
        "tags": ["injury prevention", "injury", "prevent injury",
                 "workout injury", "knee pain", "shoulder pain", "joint pain"],
        "answer": (
            "🩹 <b>Injury Prevention</b><br>"
            "• <b>Warm up</b>: 5–10 min light cardio + dynamic stretching before every session.<br>"
            "• <b>Progressive overload</b>: increase load by no more than 5–10% per week.<br>"
            "• <b>Form first</b>: ego lifting is the leading cause of gym injuries.<br>"
            "• Knee pain: strengthen VMO (terminal knee extensions), improve ankle mobility.<br>"
            "• Shoulder pain: strengthen rotator cuff (band external rotations), reduce forward head posture.<br>"
            "• If pain is sharp or persistent >2 weeks, consult a physiotherapist."
        ),
    },
    {
        "tags": ["stress", "mental health fitness", "anxiety exercise",
                 "depression workout", "fitness mental health", "mood exercise"],
        "answer": (
            "🧠 <b>Exercise & Mental Health</b><br>"
            "• Exercise is clinically proven to reduce symptoms of depression and anxiety.<br>"
            "• Aerobic exercise boosts BDNF (brain-derived neurotrophic factor) — a 'miracle-gro' for the brain.<br>"
            "• Even a 10-min brisk walk improves mood via endorphin release.<br>"
            "• Consistent exercise improves sleep quality, self-esteem, and stress resilience.<br>"
            "• Mind-body practices: yoga, tai chi, and meditation amplify benefits further."
        ),
    },
    {
        "tags": ["motivation", "stay motivated", "no motivation", "lazy",
                 "consistency", "discipline", "habit"],
        "answer": (
            "🔥 <b>Staying Motivated & Building Habits</b><br>"
            "• Motivation is temporary — build <b>systems and habits</b> instead of relying on it.<br>"
            "• Start with the <b>2-Minute Rule</b>: commit to just 2 minutes of exercise; momentum follows.<br>"
            "• Use implementation intentions: 'I will train at [TIME] at [PLACE] on [DAYS].'<br>"
            "• Track progress visually — photos every 4 weeks reveal changes the mirror hides.<br>"
            "• Find a training partner or join a community — accountability doubles adherence.<br>"
            "• Celebrate small wins: 5 extra push-ups, 1 more kg, 5 mins longer run = real progress 🏆"
        ),
    },
    {
        "tags": ["plateau", "stuck plateau", "progress stopped",
                 "no progress", "same weight", "performance plateau"],
        "answer": (
            "📈 <b>Breaking Through Plateaus</b><br>"
            "• Training plateau: apply a <b>deload week</b>, then return with changed rep ranges or new exercises.<br>"
            "• Weight loss plateau: re-calculate TDEE (metabolism adapts), reduce calories by 100–150 kcal, or add 2,000 steps/day.<br>"
            "• Try <b>periodisation</b>: cycle between hypertrophy (8–12 reps), strength (3–6 reps), and endurance (15–20 reps) phases.<br>"
            "• Audit sleep, stress, and nutrition — often the fix isn't more training but better recovery.<br>"
            "• Change training stimulus: new exercises, tempo manipulation (slow eccentric), drop sets."
        ),
    },
    {
        "tags": ["warm up", "warmup", "pre workout warmup",
                 "before training", "activation", "prime"],
        "answer": (
            "🔥 <b>Warm-Up Protocol</b><br>"
            "• Phase 1 (5 min): Light cardio — jog, row, jump rope to raise core temperature.<br>"
            "• Phase 2 (5 min): Dynamic mobility — leg swings, hip circles, shoulder dislocations, thoracic rotations.<br>"
            "• Phase 3 (3 min): Muscle activation — glute bridges, band pull-aparts, hollow body holds.<br>"
            "• Phase 4: Movement-specific warm-up sets — e.g., 50%, 70%, 90% of working weight × 5–8 reps before first working set.<br>"
            "• A proper warm-up reduces injury risk and can improve performance by 10–20%."
        ),
    },
    {
        "tags": ["weight gain", "skinny", "underweight", "hard gainer",
                 "ectomorph", "eat more", "gain weight"],
        "answer": (
            "🍽️ <b>Gaining Weight (Hardgainer Guide)</b><br>"
            "• Eat in a <b>300–500 kcal daily surplus</b> — track diligently as hardgainers often underestimate intake.<br>"
            "• Calorie-dense foods: nuts, nut butters, whole milk, oats, avocado, olive oil, dried fruit, granola.<br>"
            "• Liquid calories are easier to consume when appetite is low: smoothies, milk, weight-gainer shakes.<br>"
            "• Lift heavy — progressive overload (compound lifts) signals the body to build muscle, not just fat.<br>"
            "• Eat every 3–4 hrs; don't skip meals; add an evening high-protein snack before bed."
        ),
    },
    {
        "tags": ["vegetarian fitness", "vegan fitness", "plant based",
                 "vegan protein", "vegan protein sources", "vegetarian protein",
                 "no meat fitness", "plant protein"],
        "answer": (
            "🌱 <b>Plant-Based Fitness</b><br>"
            "• Complete plant proteins: soy (tofu, tempeh, edamame), quinoa, hemp seeds.<br>"
            "• Combine incomplete proteins: rice + lentils, peanut butter + whole wheat toast.<br>"
            "• Aim for 10–20% more protein than meat-eaters to compensate for lower digestibility (PDCAAS).<br>"
            "• Key nutrients to monitor: B12, creatine, iron, zinc, omega-3 (algae-based DHA/EPA), iodine.<br>"
            "• Plant-based athletes perform at elite levels — diet composition matters more than food source."
        ),
    },
    {
        "tags": ["sport specific", "football training", "basketball fitness",
                 "cricket fitness", "tennis training", "sports conditioning"],
        "answer": (
            "⚽ <b>Sport-Specific Conditioning</b><br>"
            "• All sports benefit from a base of: strength, power, speed, endurance, and mobility.<br>"
            "• <b>Football/Soccer</b>: Sprint intervals, agility ladders, hip mobility, single-leg strength.<br>"
            "• <b>Basketball</b>: Vertical jump training (plyometrics), lateral quickness, core strength.<br>"
            "• <b>Cricket</b>: Rotational power (landmine rotations), shoulder stability, speed off the mark.<br>"
            "• <b>Tennis</b>: Lateral bounds, wrist strength, shoulder external rotation, aerobic base.<br>"
            "• Prioritise sport practice > gym; gym is supplementary."
        ),
    },
    {
        "tags": ["how long see results", "when see results", "results time",
                 "how long workout results", "fitness results"],
        "answer": (
            "⏳ <b>When Will You See Results?</b><br>"
            "• <b>2–4 weeks</b>: Better energy, improved mood, reduced bloating — changes you <i>feel</i>.<br>"
            "• <b>4–8 weeks</b>: Noticeable strength gains (neural adaptations), clothes fitting better.<br>"
            "• <b>8–12 weeks</b>: Visible body composition changes in photos.<br>"
            "• <b>6–12 months</b>: Significant transformation if consistent.<br>"
            "• The scale is a poor short-term metric — muscle gain can mask fat loss. Use measurements and photos."
        ),
    },
    {
        "tags": ["faq", "hello", "hi", "hey", "start", "help me",
                 "what can you do", "who are you"],
        "answer": (
            "👋 <b>Welcome to FitBot!</b><br>"
            "I'm your AI-powered fitness assistant using NLP to understand your questions.<br><br>"
            "I can help you with:<br>"
            "• 🔥 Weight loss & calorie deficit strategies<br>"
            "• 💪 Muscle building & hypertrophy programmes<br>"
            "• 🥗 Diet, nutrition & meal planning<br>"
            "• 🏋️ Workout routines for all levels<br>"
            "• ⚡ HIIT, cardio & endurance training<br>"
            "• 😴 Recovery, sleep & injury prevention<br>"
            "• 🧠 Motivation, mental health & habit building<br><br>"
            "Just type your question naturally!"
        ),
    },
]

for qa in QA_PAIRS:
    qa["_tokens"] = tokenize(" ".join(qa["tags"]))


def find_best_match(user_input: str):
    """
    Multi-stage NLP pipeline:
      1. Exact substring match on raw tags (fast path)
      2. TF-IDF cosine similarity on stemmed tokens
      3. Fallback response
    """
    # Stage 1 – exact phrase match (longest matching tag wins → avoids
    #           short tags like "workout" shadowing "home workout")
    low = user_input.lower()
    best_tag_len = 0
    best_exact   = None
    for qa in QA_PAIRS:
        for tag in qa["tags"]:
            if tag in low and len(tag) > best_tag_len:
                best_tag_len = len(tag)
                best_exact   = qa["answer"]
    if best_exact:
        return best_exact

    # Stage 2 – TF-IDF cosine similarity
    q_tokens = tokenize(user_input)
    if q_tokens:
        best_score = 0.0
        best_answer = None
        for qa in QA_PAIRS:
            score = tfidf_score(q_tokens, qa["_tokens"])
            if score > best_score:
                best_score = score
                best_answer = qa["answer"]
        if best_score > 0.05:
            return best_answer

    # Stage 3 – fallback
    return (
        "🤔 I'm not sure about that. Try asking about:<br>"
        "<i>weight loss, muscle gain, diet, workout, cardio, HIIT, sleep, "
        "supplements, stretching, injury prevention, or motivation.</i>"
    )


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get", methods=["POST"])
def get_bot_response():
    user_msg = request.form.get("msg", "").strip()
    if not user_msg:
        return jsonify({"reply": "Please type a message!"})
    response = find_best_match(user_msg)
    return jsonify({"reply": response})

if __name__ == "__main__":
    app.run(debug=True)
