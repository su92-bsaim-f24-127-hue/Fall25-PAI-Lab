from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

API_URL = "https://uselessfacts.jsph.pl/api/v2/facts/random"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get-fact")
def get_fact():
    try:
        response = requests.get(API_URL)
        data = response.json()
        return jsonify({
            "fact": data["text"],
            "source": data["source"]
        })
    except:
        return jsonify({"fact": "Oops! Something went wrong.", "source": "Server"})

if __name__ == "__main__":
    app.run(debug=True)