from flask import Flask, render_template, request, jsonify
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
import os
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

MODEL_NAME = "llama-3.1-8b-instant"

CSV_PATH = os.path.join(os.path.dirname(__file__), "AI_interview_questions.csv")

def load_questions():
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip().str.lower()
    return df

df_questions = load_questions()

@app.route("/")
def index():
    topics = sorted(df_questions["topic"].dropna().unique().tolist())
    difficulties = sorted(
        df_questions["difficulty"].dropna().unique().tolist(),
        key=lambda x: {"Easy": 0, "Medium": 1, "Hard": 2}.get(x, 9)
    )
    total = len(df_questions)
    return render_template("index.html", topics=topics, difficulties=difficulties, total=total)

@app.route("/api/questions")
def get_questions():
    topic = request.args.get("topic", "all")
    difficulty = request.args.get("difficulty", "all")
    search = request.args.get("search", "").strip().lower()
    shuffle = request.args.get("shuffle", "false") == "true"

    filtered = df_questions.copy()

    if topic != "all":
        filtered = filtered[filtered["topic"] == topic]
    if difficulty != "all":
        filtered = filtered[filtered["difficulty"] == difficulty]
    if search:
        filtered = filtered[
            filtered["question"].str.lower().str.contains(search, na=False) |
            filtered["topic"].str.lower().str.contains(search, na=False)
        ]

    if shuffle:
        filtered = filtered.sample(frac=1)

    questions = filtered.to_dict(orient="records")
    return jsonify({"questions": questions, "total": len(questions)})

@app.route("/api/random")
def get_random():
    topic = request.args.get("topic", "all")
    difficulty = request.args.get("difficulty", "all")

    filtered = df_questions.copy()

    if topic != "all":
        filtered = filtered[filtered["topic"] == topic]
    if difficulty != "all":
        filtered = filtered[filtered["difficulty"] == difficulty]

    if filtered.empty:
        return jsonify({"error": "No questions match the selected filters."}), 404

    q = filtered.sample(1).iloc[0].to_dict()
    return jsonify(q)

def ask_groq(prompt, temperature=0.3):
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Respond ONLY in valid JSON when asked."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise e

@app.route("/api/evaluate", methods=["POST"])
def evaluate_answer():
    data = request.get_json()
    question = data.get("question", "")
    user_answer = data.get("user_answer", "").strip()
    correct_answer = data.get("correct_answer", "")

    if not user_answer:
        return jsonify({"error": "Please provide an answer to evaluate."}), 400

    prompt = f"""You are an expert ML interviewer evaluating a candidate's answer.

Question: {question}

Candidate's Answer: {user_answer}

Reference Answer: {correct_answer}

Evaluate the candidate's answer and respond in this EXACT JSON format:
{{
  "score": <integer 0-10>,
  "grade": "<Excellent|Good|Partial|Poor>",
  "strengths": "<1-2 sentences>",
  "improvements": "<1-2 sentences>",
  "tip": "<one concise tip>"
}}

Be fair but rigorous. A score of 8-10 means interview-ready."""

    try:
        raw = ask_groq(prompt)

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        result = json.loads(raw)
        return jsonify(result)

    except json.JSONDecodeError:
        return jsonify({
            "score": 5,
            "grade": "Partial",
            "strengths": "Could not fully parse evaluation.",
            "improvements": "Please try again.",
            "tip": raw[:300]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/hint", methods=["POST"])
def get_hint():
    data = request.get_json()
    question = data.get("question", "")

    prompt = f"""Give a concise interview hint for this ML question (2-3 sentences max, no full answer):

Question: {question}

Hint:"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )

        hint = response.choices[0].message.content.strip()
        return jsonify({"hint": hint})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/stats")
def get_stats():
    topic_counts = df_questions["topic"].value_counts().to_dict()
    difficulty_counts = df_questions["difficulty"].value_counts().to_dict()

    return jsonify({
        "total": len(df_questions),
        "by_topic": topic_counts,
        "by_difficulty": difficulty_counts
    })

@app.route("/upload", methods=["POST"])
def upload_csv():
    global df_questions

    file = request.files.get("file")

    if not file or not file.filename.endswith(".csv"):
        return jsonify({"error": "Please upload a valid CSV file."}), 400

    try:
        df_new = pd.read_csv(file)
        df_new.columns = df_new.columns.str.strip().str.lower()

        required = {"question", "answer"}
        if not required.issubset(set(df_new.columns)):
            return jsonify({
                "error": f"CSV must include 'question' and 'answer'. Found: {list(df_new.columns)}"
            }), 400

        if "topic" not in df_new.columns:
            df_new["topic"] = "General"

        if "difficulty" not in df_new.columns:
            df_new["difficulty"] = "Medium"

        df_new.to_csv(CSV_PATH, index=False)
        df_questions = df_new

        return jsonify({"success": True, "loaded": len(df_new)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)