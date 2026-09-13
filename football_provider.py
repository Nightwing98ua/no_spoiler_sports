import requests
from config import API_FOOTBALL_BASE_URL, API_FOOTBALL_KEY, ALLOWED_FOOTBALL_LEAGUES
from scoring import football_score_with_stats, football_score_fallback

HEADERS = {"x-apisports-key": API_FOOTBALL_KEY}


def _safe_num(stat_dict, name):
    val = stat_dict.get(name, 0)
    if val is None:
        return 0
    if isinstance(val, str):
        val = val.replace("%", "")
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0


def _fetch_fixture_stats(fixture_id):
    resp = requests.get(
        f"{API_FOOTBALL_BASE_URL}/fixtures/statistics",
        headers=HEADERS,
        params={"fixture": fixture_id},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("response", [])


def fetch_football_games(date_str):
    """
    date_str: "YYYY-MM-DD"
    Робить 1 запит на список матчів дня + по 1 запиту статистики
    ЛИШЕ для завершених матчів (щоб не витрачати денний ліміт
    на матчі, що ще не почались чи йдуть наживо).
    """
    resp = requests.get(
        f"{API_FOOTBALL_BASE_URL}/fixtures",
        headers=HEADERS,
        params={"date": date_str},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    # API-Football повертає HTTP 200 навіть коли вичерпано ліміт запитів —
    # у такому разі помилка лежить у полі "errors", а "response" просто порожній.
    # Без цієї перевірки сайт мовчки показував би "матчів немає" замість
    # справжньої причини.
    api_errors = data.get("errors")
    if api_errors:
        raise RuntimeError(f"API-Football повернув помилку: {api_errors}")

    games = []

    for m in data.get("response", []):
        if m["league"]["id"] not in ALLOWED_FOOTBALL_LEAGUES:
            continue

        fixture_id = m["fixture"]["id"]
        status = m["fixture"]["status"]["short"]  # напр. "FT", "NS", "1H"
        finished = status == "FT"

        home = m["teams"]["home"]["name"]
        away = m["teams"]["away"]["name"]
        gh = m["goals"]["home"] or 0
        ga = m["goals"]["away"] or 0

        rating = None
        stats_payload = {}

        if finished:
            stats_resp = _fetch_fixture_stats(fixture_id)

            if stats_resp:
                home_stats, away_stats = {}, {}
                for team in stats_resp:
                    values = {s["type"]: s["value"] for s in team["statistics"]}
                    if team["team"]["name"] == home:
                        home_stats = values
                    else:
                        away_stats = values

                shots = _safe_num(home_stats, "Total Shots") + _safe_num(away_stats, "Total Shots")
                xg = _safe_num(home_stats, "Expected Goals") + _safe_num(away_stats, "Expected Goals")
                fouls = _safe_num(home_stats, "Fouls") + _safe_num(away_stats, "Fouls")

                rating = football_score_with_stats(gh, ga, shots, xg, fouls)
                stats_payload = {"shots_total": shots, "xg_total": xg, "fouls_total": fouls}
            else:
                rating = football_score_fallback(gh, ga)

        games.append({
            "id": f"fb-{fixture_id}",
            "sport": "football",
            "date": date_str,
            "league": m["league"]["name"],
            "status": status,
            "finished": finished,
            "home": home,
            "away": away,
            "score_home": gh,
            "score_away": ga,
            "rating": rating,
            "stats": stats_payload,
        })

    return games
