from flask import Flask, render_template, jsonify
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("API_KEY", "DEMO_KEY")

# ── Home ────────────────────────────────────────────────────────────────────
@app.route('/')
def home():
    return render_template("index.html")


# ── APOD ────────────────────────────────────────────────────────────────────
@app.route('/apod')
@app.route('/apod/<date>')
def apod(date=None):
    params = {"api_key": API_KEY, "hd": "True"}
    if date:
        params["date"] = date
    data = requests.get("https://api.nasa.gov/planetary/apod", params=params).json()
    return render_template("apod.html", data=data, now=datetime.utcnow())


# ── Mars Rovers ─────────────────────────────────────────────────────────────
@app.route('/mars')
@app.route('/mars/<rover>/<int:sol>')
def mars(rover="curiosity", sol=1000):
    url = (
        f"https://api.nasa.gov/mars-photos/api/v1/rovers/{rover}/photos"
        f"?sol={sol}&api_key={API_KEY}"
    )
    response = requests.get(url)
    try:
        data = response.json()
    except Exception:
        data = {}
    photos = data.get("photos", [])[:20]
    for p in photos:
        p["img_src"] = p["img_src"].replace("http://", "https://")

    # Get rover manifest for metadata
    manifest_url = f"https://api.nasa.gov/mars-photos/api/v1/manifests/{rover}?api_key={API_KEY}"
    try:
        manifest = requests.get(manifest_url).json().get("photo_manifest", {})
    except Exception:
        manifest = {}

    rovers = ["curiosity", "opportunity", "perseverance", "spirit"]
    return render_template(
        "mars.html",
        photos=photos,
        rover=rover,
        sol=sol,
        manifest=manifest,
        rovers=rovers,
    )


# ── ISS Tracker ─────────────────────────────────────────────────────────────
@app.route('/iss')
def iss():
    return render_template("iss.html")

@app.route('/api/iss')
def api_iss():
    pos = requests.get("http://api.open-notify.org/iss-now.json").json()
    crew = requests.get("http://api.open-notify.org/astros.json").json()
    iss_crew = [p for p in crew.get("people", []) if p.get("craft") == "ISS"]
    return jsonify({
        "latitude": float(pos["iss_position"]["latitude"]),
        "longitude": float(pos["iss_position"]["longitude"]),
        "timestamp": pos["timestamp"],
        "crew": iss_crew,
        "crew_count": len(iss_crew),
    })


# ── Near-Earth Objects ──────────────────────────────────────────────────────
@app.route('/asteroids')
def asteroids():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    end   = (datetime.utcnow() + timedelta(days=6)).strftime("%Y-%m-%d")
    url   = (
        f"https://api.nasa.gov/neo/rest/v1/feed"
        f"?start_date={today}&end_date={end}&api_key={API_KEY}"
    )
    data  = requests.get(url).json()
    all_neos = []
    for day_neos in data.get("near_earth_objects", {}).values():
        all_neos.extend(day_neos)
    all_neos.sort(
        key=lambda x: float(x["close_approach_data"][0]["miss_distance"]["kilometers"])
    )
    hazardous = [n for n in all_neos if n["is_potentially_hazardous_asteroid"]]
    return render_template(
        "asteroids.html",
        neos=all_neos[:30],
        hazardous_count=len(hazardous),
        total=data.get("element_count", 0),
        start_date=today,
        end_date=end,
    )


# ── Space News ──────────────────────────────────────────────────────────────
@app.route('/news')
def news():
    url  = "https://api.spaceflightnewsapi.net/v4/articles/?limit=20&ordering=-published_at"
    data = requests.get(url).json()
    return render_template("news.html", articles=data.get("results", []))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))