

A Flask-based ML interview preparation app powered by Google Gemini AI.

## Features
- 📚 **Browse Mode** — Filter questions by topic, difficulty, or keyword search
- ⚡ **Quiz Mode** — Random question drill with AI-powered answer evaluation
- 📊 **Stats** — Dataset breakdown by topic and difficulty
- 🤖 **AI Evaluation** — Gemini grades your answer with score, strengths, improvements & tip
- 💡 **Hints** — Get a hint without revealing the full answer
- 📁 **Upload CSV** — Replace the dataset with your own questions anytime

## Setup

### 1. Install dependencies
```bash
# Using Anaconda (recommended for your setup):
C:\Users\ELITEBOOK\Downloads\Anaconda\Scripts\pip.exe install flask pandas google-generativeai
```

### 2. Set your Gemini API key
Open `app.py` and replace `YOUR_API_KEY_HERE`:
```python
genai.configure(api_key="YOUR_ACTUAL_GEMINI_API_KEY")
```
Or set it as an environment variable:
```bash
set GEMINI_API_KEY=your_key_here   # Windows CMD
```

### 3. (Optional) Replace dataset
Drop your `ml_interview_questions.csv` into the project folder.
Required columns: `question`, `answer`
Optional columns: `topic`, `difficulty`

### 4. Run the app
```bash
cd C:\Users\ELITEBOOK\Desktop\contentai\ml_interview_prep
python app.py
```
Then open **http://127.0.0.1:5000** in your browser.

## CSV Format
```csv
question,answer,topic,difficulty
What is overfitting?,Overfitting occurs when...,Model Evaluation,Medium
```

## Project Structure
```
ml_interview_prep/
├── app.py                  ← Flask backend + Gemini API
├── requirements.txt
├── ml_interview_questions.csv
├── templates/
│   └── index.html          ← Main UI
└── static/
    ├── css/style.css       ← Dark terminal aesthetic
    └── js/app.js           ← All frontend logic
```
