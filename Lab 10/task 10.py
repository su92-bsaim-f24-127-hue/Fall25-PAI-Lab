from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

def chatbot_response(msg):
    msg = msg.lower()

    if "lose weight" in msg or "fat loss" in msg:
        return "For weight loss: Do cardio (running, cycling) 30 mins daily + eat low-calorie foods like vegetables, fruits, and lean protein."

    elif "gain muscle" in msg or "muscle" in msg:
        return "For muscle gain: Do strength training (gym, push-ups, weights) + eat high-protein foods like eggs, chicken, milk."

    elif "diet" in msg:
        return "Balanced diet: Breakfast (eggs, oats), Lunch (rice, chicken, vegetables), Dinner (light meal like salad or soup)."

    elif "workout" in msg or "exercise" in msg:
        return "Basic workout: Push-ups, squats, plank, and jogging for 20-30 minutes daily."

    elif "motivation" in msg:
        return "Stay consistent! Small progress every day leads to big results 💪"

    else:
        return "Ask me about weight loss, muscle gain, diet, or workouts."

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get", methods=["POST"])
def get_bot_response():
    user_msg = request.form["msg"]
    response = chatbot_response(user_msg)
    return jsonify({"reply": response})

if __name__ == "__main__":
    app.run(debug=True)