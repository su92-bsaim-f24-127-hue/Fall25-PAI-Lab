import os
import json
import requests
import numpy as np
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

DATASET_URL = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"

EMBEDDINGS_FILE = "fitness_embeddings.npy"
INDEX_FILE      = "faiss_index.index"
DATA_FILE       = "exercises_data.json"

def load_dataset():
    if os.path.exists(DATA_FILE):
        print("Loading cached dataset...")
        with open(DATA_FILE, "r") as f:
            exercises = json.load(f)
    else:
        print("Downloading dataset from GitHub...")
        response = requests.get(DATASET_URL, timeout=30)
        response.raise_for_status()
        exercises = response.json()
        with open(DATA_FILE, "w") as f:
            json.dump(exercises, f)
        print(f"Downloaded {len(exercises)} exercises.")

    rows = []
    for ex in exercises:
        instructions = " ".join(ex.get("instructions", []))
        muscles      = ", ".join(ex.get("primaryMuscles", []))
        secondary    = ", ".join(ex.get("secondaryMuscles", []))
        equipment    = ex.get("equipment", "none")
        category     = ex.get("category", "")
        name         = ex.get("name", "")
        level        = ex.get("level", "")
        mechanic     = ex.get("mechanic", "") or ""
        force        = ex.get("force", "") or ""

        cleaned = (
            f"{name}. Category: {category}. Level: {level}. "
            f"Equipment: {equipment}. Primary muscles: {muscles}. "
            f"Secondary muscles: {secondary}. Mechanic: {mechanic}. Force: {force}. "
            f"{instructions}"
        )

        rows.append({
            "name":        name,
            "category":    category,
            "level":       level,
            "equipment":   equipment,
            "muscles":     muscles,
            "secondary":   secondary,
            "mechanic":    mechanic,
            "force":       force,
            "instructions": instructions,
            "cleaned":     cleaned
        })

    df = pd.DataFrame(rows)
    print(f"Dataset shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    return df

def build_embeddings(df, model):
    if os.path.exists(EMBEDDINGS_FILE):
        print("Loading cached embeddings...")
        embeddings = np.load(EMBEDDINGS_FILE)
    else:
        print("Encoding exercises with sentence-transformers...")
        embeddings = model.encode(df["cleaned"].values, show_progress_bar=True)
        embeddings = np.array(embeddings)
        np.save(EMBEDDINGS_FILE, embeddings)
        print(f"Embeddings saved. Shape: {embeddings.shape}")
    return embeddings

def build_faiss_index(embeddings):
    if os.path.exists(INDEX_FILE):
        print("Loading cached FAISS index...")
        index = faiss.read_index(INDEX_FILE)
    else:
        print("Building FAISS index...")
        dimensions  = embeddings.shape[1]
        index       = faiss.IndexFlatL2(dimensions)
        index.add(embeddings)
        faiss.write_index(index, INDEX_FILE)
        print("FAISS index saved.")
    return index

def get_similar_exercises(query, count=3, model=None, index=None, df=None):
    query_embedding = model.encode([query])
    distances, indices = index.search(query_embedding, count)

    results = []
    for i in range(count):
        idx  = indices[0][i]
        dist = distances[0][i]
        row  = df.iloc[idx]
        instructions = row["instructions"] or ""
        results.append({
            "name":         (row["name"]      or "Unknown").title(),
            "category":     (row["category"]  or "General").title(),
            "level":        (row["level"]     or "N/A").title(),
            "equipment":    (row["equipment"] or "None").title(),
            "muscles":      row["muscles"]    or "N/A",
            "instructions": instructions[:400] + ("..." if len(instructions) > 400 else ""),
            "distance":     round(float(dist), 4)
        })
    return results

print("Starting FitnessBot...")
print("Loading model (sentence-transformers)...")
model = SentenceTransformer("all-MiniLM-L6-v2")

df          = load_dataset()
embeddings  = build_embeddings(df, model)
faiss_index = build_faiss_index(embeddings)

print("FitnessBot is ready!\n")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get", methods=["POST"])
def get_bot_response():
    user_msg = request.form.get("msg", "").strip()
    if not user_msg:
        return jsonify({"error": "Empty message"}), 400

    results = get_similar_exercises(
        query=user_msg,
        count=3,
        model=model,
        index=faiss_index,
        df=df
    )
    return jsonify({"query": user_msg, "results": results})

if __name__ == "__main__":
    app.run(debug=True)