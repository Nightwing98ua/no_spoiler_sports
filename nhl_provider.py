import requests
from config import NHL_BASE_URL
from scoring import hockey_score


def fetch_hockey_games(date_str):
    """
    date_str: "YYYY-MM-DD"
    Повертає список нормалізованих матчів для цієї дати.
    """
    url = f"{NHL_BASE_URL}/score/{date_str}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    games = []
    for g in data.get("games", []):
        home = g["homeTeam"]
        away = g["awayTeam"]

        status = g.get("gameState", "")  # напр. "FUT", "LIVE", "FINAL"
        finished = status in ("FINAL", "OFF")

        home_goals = home.get("score", 0)
        away_goals = away.get("score", 0)
        shots_total = home.get("sog", 0) + away.get("sog", 0)
        is_ot = g.get("periodDescriptor", {}).get("periodType") == "OT"

        rating = None
        if finished:
            rating = hockey_score(home_goals, away_goals, shots_total, is_ot)

        games.append({
            "id": f"nhl-{g.get('id')}",
            "sport": "hockey",
            "date": date_str,
            "league": "NHL",
            "status": status,
            "finished": finished,
            "home": home.get("abbrev"),
            "away": away.get("abbrev"),
            "score_home": home_goals,
            "score_away": away_goals,
            "rating": rating,
            "stats": {
                "shots_total": shots_total,
                "overtime": is_ot,
            },
        })

    return games
