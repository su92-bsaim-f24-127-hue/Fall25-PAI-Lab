from flask import Flask, render_template, request, send_file
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def extract_emails(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text()

        emails = re.findall(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            text
        )
        return list(set(emails))
    except:
        return []

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")

        if not file:
            return "No file uploaded"

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        # Read Excel
        df = pd.read_excel(file_path)

        # Use FIRST column automatically
        url_column = df.columns[0]

        all_data = []

        for url in df[url_column]:
            if pd.isna(url):
                continue

            emails = extract_emails(str(url))

            for email in emails:
                all_data.append({
                    "Website": url,
                    "Email": email
                })

        if not all_data:
            return "❌ No emails found from given URLs"

        output_df = pd.DataFrame(all_data)
        output_path = os.path.join(OUTPUT_FOLDER, "scraped_emails.xlsx")
        output_df.to_excel(output_path, index=False)

        return send_file(output_path, as_attachment=True)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
