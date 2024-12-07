from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import requests
import json
import os

app = Flask(__name__)
app.secret_key = "2001"  # Replace with your secret key
USER_DATA_FILE = "users.json"

# File to store user data
def load_users():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as file:
            return json.load(file)
    return {}

def save_users(users):
    with open(USER_DATA_FILE, "w") as file:
        json.dump(users, file)

def get_weather(lat, lon):
    api_key = "02e9d888d330497fa9f9b9a7a7e7d0d8"  # Fixed OpenWeatherMap API key
    base_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = requests.get(base_url)
    if response.status_code == 200:
        data = response.json()
        return {
            "temp": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "description": data["weather"][0]["description"]
        }
    return None

def get_geocode(location):
    geocode_token = "9493d33e04c04b108c0b5a83d52bc7dc"  # Fixed OpenCage API key
    base_url = f"https://api.opencagedata.com/geocode/v1/json?q={location}&key={geocode_token}"
    response = requests.get(base_url)
    if response.status_code == 200:
        data = response.json()
        if data["results"]:
            result = data["results"][0]
            return {
                "lat": result["geometry"]["lat"],
                "lon": result["geometry"]["lng"],
                "district": result["components"].get("district", "N/A"),
                "country": result["components"].get("country", "N/A")
            }
    return None

def predict_malaria_risk(temp, humidity):
    if temp > 25 and humidity > 60:
        return "High Risk of Malaria"
    elif 20 < temp <= 25 and 50 < humidity <= 60:
        return "Moderate Risk of Malaria"
    else:
        return "Low Risk of Malaria"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]
    users = load_users()
    if username in users:
        return jsonify({"error": "User already exists."}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long."}), 400
    users[username] = password
    save_users(users)
    return jsonify({"success": "User registered successfully."}), 200

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    users = load_users()
    if users.get(username) == password:
        session["username"] = username
        return jsonify({"success": f"Welcome, {username}!"}), 200
    return jsonify({"error": "Invalid username or password."}), 400

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("username", None)
    return jsonify({"success": "Logged out successfully."}), 200

@app.route("/weather", methods=["POST"])
def weather():
    if "username" not in session:
        return jsonify({"error": "Please log in to access weather data."}), 401
    location = request.form["location"]
    geocode_data = get_geocode(location)
    if not geocode_data:
        return jsonify({"error": "Invalid location."}), 400
    weather_info = get_weather(geocode_data["lat"], geocode_data["lon"])
    if not weather_info:
        return jsonify({"error": "Unable to fetch weather data."}), 500
    malaria_risk = predict_malaria_risk(weather_info["temp"], weather_info["humidity"])
    return jsonify({
        "weather": weather_info,
        "location": geocode_data,
        "malaria_risk": malaria_risk
    }), 200

if __name__ == "__main__":
    app.run(port=5008, debug=True)
