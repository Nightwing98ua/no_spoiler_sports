import json
import re
import time
import unicodedata
from datetime import datetime, timezone

import requests

UNDERSTAT_BASE_URL = "https://understat.com/league"
UNDERSTAT_MATCH_URL = "https://understat.com/match"

# ESPN-код ліги -> назва ліги на Understat.
# Understat НЕ покриває Лігу чемпіонів (тільки національні чемпіонати).
LEAGUE_SLUGS = {
    "eng.1": "EPL",
    "esp.1": "La_liga",
    "ita.1": "Serie_A",
    "ger.1": "Bundesliga",
    "fra.1": "Ligue_1",
}

_LEAGUE_CACHE_TTL = 60 * 60  # 1 година для списку матчів ліги
_league_cache = {}  # slug -> {"ts": ..., "matches": [...]}

# Дані по завершеному матчу (удари) не змінюються заднім числом —
# кешуємо їх без обмеження часу в межах роботи процесу.
_shots_cache = {}  # match_id -> shots_total

_HEADERS = {"User-Agent": "Mozilla/5.0"}

# Пауза між запитами окремих матчів, щоб не "довбати" сайт занадто швидко.
_MIN_SECONDS_BETWEEN_REQUESTS = 1.5
_last_request_time = 0.0


def _throttle():
    global _last_request_time
    elapsed = time.time() - _last_request_time
    wait = _MIN_SECONDS_BETWEEN_REQUESTS - elapsed
    if wait > 0:
        time.sleep(wait)
    _last_request_time = time.time()


def _current_season_key():
    now = datetime.now(timezone.utc)
    return str(now.year if now.month >= 7 else now.year - 1)


def _normalize_name(name):
    if not name:
        return ""
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_name = "".join(c for c in nfkd if not unicodedata.combining(c))
    ascii_name = ascii_name.lower()
    for junk in [" fc", " cf", " afc", ".", "-"]:
        ascii_name = ascii_name.replace(junk, " ")
    return " ".join(ascii_name.split())


def _decode_understat_json(raw_js_string):
    decoded = raw_js_string.encode("utf-8").decode("unicode_escape")
    decoded = decoded.encode("latin1").decode("utf-8")
    return json.loads(decoded)


def _parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")


def _fetch_league_matches(slug):
    now = time.time()
    cached = _league_cache.get(slug)
    if cached and (now - cached["ts"]) < _LEAGUE_CACHE_TTL:
        return cached["matches"]

    season = _current_season_key()
    _throttle()
    resp = requests.get(f"{UNDERSTAT_BASE_URL}/{slug}/{season}", timeout=10, headers=_HEADERS)
    resp.raise_for_status()

    match = re.search(r"var\s+datesData\s*=\s*JSON\.parse\('(.+?)'\);", resp.text)
    matches = []
    if match:
        raw = _decode_understat_json(match.group(1))
        for m in raw:
            if not m.get("isResult"):
                continue
            matches.append({
                "id": m.get("id"),
                "date": (m.get("datetime") or "")[:10],
                "home": m.get("h", {}).get("title", ""),
                "away": m.get("a", {}).get("title", ""),
                "xg_home": float(m.get("xG", {}).get("h", 0) or 0),
                "xg_away": float(m.get("xG", {}).get("a", 0) or 0),
            })

    _league_cache[slug] = {"ts": now, "matches": matches}
    return matches


def get_understat_match(espn_league_code, date_str, home_name, away_name):
    """Повертає запис матчу (з id та xG) або None, якщо не знайдено."""
    slug = LEAGUE_SLUGS.get(espn_league_code)
    if not slug:
        return None

    try:
        matches = _fetch_league_matches(slug)
    except (requests.RequestException, ValueError):
        return None

    target_home = _normalize_name(home_name)
    target_away = _normalize_name(away_name)

    for m in matches:
        if _normalize_name(m["home"]) == target_home and _normalize_name(m["away"]) == target_away:
            if abs((_parse_date(m["date"]) - _parse_date(date_str)).days) <= 1:
                return m

    return None


def get_shots_for_match(match_id):
    """Повертає загальну кількість ударів по воротах для матчу, або None."""
    if match_id is None:
        return None
    if match_id in _shots_cache:
        return _shots_cache[match_id]

    try:
        _throttle()
        resp = requests.get(f"{UNDERSTAT_MATCH_URL}/{match_id}", timeout=10, headers=_HEADERS)
        resp.raise_for_status()

        match = re.search(r"var\s+shotsData\s*=\s*JSON\.parse\('(.+?)'\);", resp.text)
        if not match:
            return None

        raw = _decode_understat_json(match.group(1))
        shots_total = len(raw.get("h", [])) + len(raw.get("a", []))
        _shots_cache[match_id] = shots_total
        return shots_total
    except (requests.RequestException, ValueError):
        return None
