import time

import requests
from scoring import football_score_fallback

# Неофіційне, але стабільне й багато років використовуване API ESPN.
# Не потребує ключа й реєстрації.
ESPN_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer"

# Код ліги ESPN -> назва для показу на сайті
LEAGUES = {
    "eng.1": "Premier League",
    "esp.1": "La Liga",
    "ita.1": "Serie A",
    "ger.1": "Bundesliga",
    "fra.1": "Ligue 1",
    "uefa.champions": "Champions League",
}


def _fetch_league_scoreboard(league_code, date_str_espn):
    url = f"{ESPN_BASE_URL}/{league_code}/scoreboard"
    resp = requests.get(url, params={"dates": date_str_espn}, timeout=10)
    resp.raise_for_status()
    return resp.json()


def fetch_football_games(date_str):
    """
    date_str: "YYYY-MM-DD"

    ESPN не дає детальної статистики (удари, xG) через цей ендпоінт,
    тому оцінка рахується спрощено — за голами й різницею рахунку,
    так само як для матчів без статистики раніше.
    """
    date_str_espn = date_str.replace("-", "")  # ESPN хоче формат YYYYMMDD
    games = []

    for league_code, league_name in LEAGUES.items():
        try:
            data = _fetch_league_scoreboard(league_code, date_str_espn)
        except requests.RequestException:
            # Якщо одна ліга тимчасово недоступна — не валимо весь запит,
            # просто пропускаємо її для цього дня.
            continue

        for event in data.get("events", []):
            status = event.get("status", {}).get("type", {})
            finished = bool(status.get("completed"))

            competitions = event.get("competitions", [])
            if not competitions:
                continue
            competitors = competitions[0].get("competitors", [])

            home = next((c for c in competitors if c.get("homeAway") == "home"), None)
            away = next((c for c in competitors if c.get("homeAway") == "away"), None)
            if not home or not away:
                continue

            home_name = home.get("team", {}).get("displayName", "")
            away_name = away.get("team", {}).get("displayName", "")

            try:
                gh = int(home.get("score", 0) or 0)
                ga = int(away.get("score", 0) or 0)
            except (TypeError, ValueError):
                gh, ga = 0, 0

            rating = football_score_fallback(gh, ga) if finished else None

            games.append({
                "id": f"fb-{event.get('id')}",
                "sport": "football",
                "date": date_str,
                "league": league_name,
                "status": status.get("name", ""),
                "finished": finished,
                "home": home_name,
                "away": away_name,
                "score_home": gh,
                "score_away": ga,
                "rating": rating,
                "stats": {},
            })

        time.sleep(0.3)  # ввічлива пауза між запитами до різних ліг

    return games
