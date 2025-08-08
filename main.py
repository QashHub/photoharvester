from flask import Flask, render_template, request, send_file, flash
from dotenv import load_dotenv
load_dotenv()
import os
import requests
import zipfile
from io import BytesIO

app = Flask(__name__)
app.secret_key = "secret-key"  

SAVE_FOLDER = 'images'
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

if not os.path.exists(SAVE_FOLDER):
    os.mkdir(SAVE_FOLDER)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        query = request.form["query"].strip()
        num_images = int(request.form["num_images"])

        if not query:
            flash("Search term cannot be empty!", "danger")
            return render_template("index.html")

        flash("Fetching images, please wait...", "info")

        # Clear old images
        for f in os.listdir(SAVE_FOLDER):
            os.remove(os.path.join(SAVE_FOLDER, f))

        # Call SerpAPI
        params = {
            "engine": "google",
            "q": query,
            "tbm": "isch",
            "ijn": "0",
            "api_key": SERPAPI_KEY
        }
        response = requests.get("https://serpapi.com/search", params=params).json()
        images_results = response.get("images_results", [])[:num_images]

        if not images_results:
            flash("No images found. Try another search term.", "danger")
            return render_template("index.html")

        for i, img in enumerate(images_results):
            img_url = img.get("original")
            if img_url:
                img_data = requests.get(img_url).content
                with open(f"{SAVE_FOLDER}/{query}_{i+1}.jpg", "wb") as f:
                    f.write(img_data)

        # Zip images
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for filename in os.listdir(SAVE_FOLDER):
                zf.write(os.path.join(SAVE_FOLDER, filename), filename)
        zip_buffer.seek(0)

        return send_file(zip_buffer, as_attachment=True, download_name=f"{query}_images.zip")

    return render_template("index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)

