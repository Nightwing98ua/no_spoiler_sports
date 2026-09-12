from datetime import datetime

from flask import Flask, jsonify, request

from cache import get_or_fetch
from nhl_provider import fetch_hockey_games
from football_provider import fetch_football_games

app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    # Дозволяє фронтенду з іншого домену звертатись до цього API
    # без окремої залежності flask-cors.
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/api/matches")
def matches():
    sport = request.args.get("sport", "football")
    date_str = request.args.get("date", datetime.utcnow().strftime("%Y-%m-%d"))

    if sport not in ("football", "hockey"):
        return jsonify({"error": "sport має бути 'football' або 'hockey'"}), 400

    cache_key = f"{sport}:{date_str}"

    try:
        if sport == "football":
            games = get_or_fetch(cache_key, lambda: fetch_football_games(date_str))
        else:
            games = get_or_fetch(cache_key, lambda: fetch_hockey_games(date_str))
    except Exception as e:
        return jsonify({"error": f"Не вдалось отримати дані: {e}"}), 502

    games_sorted = sorted(
        games,
        key=lambda g: (g["rating"] is None, -(g["rating"] or 0)),
    )

    return jsonify({"sport": sport, "date": date_str, "games": games_sorted})


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # Локально: http://localhost:5000/api/matches?sport=football&date=2026-09-10
    app.run(host="0.0.0.0", port=5000, debug=True)
