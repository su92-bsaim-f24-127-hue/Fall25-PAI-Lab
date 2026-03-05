from flask import Flask, jsonify, render_template
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/fact")
def fact():
    response = requests.get("https://uselessfacts.jsph.pl/api/v2/facts/random")
    data = response.json()
    return jsonify({"fact": data["text"]})

if __name__ == "__main__":
    app.run(debug=True)