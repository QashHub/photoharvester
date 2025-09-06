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
        images_results = response.get("images_results", [])

        if not images_results:
            flash("No images found. Try another search term.", "danger")
            return render_template("index.html")

        saved_count = 0
        i = 0

        # Keep trying images until we get the number requested
        while saved_count < num_images and i < len(images_results):
            img_url = images_results[i].get("original")
            i += 1
            if not img_url:
                continue
            try:
                img_data = requests.get(img_url, timeout=5).content
                # Skip tiny or empty images
                if len(img_data) < 1024:
                    continue
                with open(f"{SAVE_FOLDER}/{query}_{saved_count+1}.jpg", "wb") as f:
                    f.write(img_data)
                saved_count += 1
            except:
                continue

        if saved_count == 0:
            flash("Could not download any images. Try another search term.", "danger")
            return render_template("index.html")
        elif saved_count < num_images:
            flash(f"Only {saved_count} images could be downloaded.", "warning")

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

