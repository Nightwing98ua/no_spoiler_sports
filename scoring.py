"""
Формули оцінки матчів — перенесені без змін з ваших телеграм-ботів
(nhl_bot2.py та Football_bot.py), лише оформлені як функції,
що повертають число замість друку в чат.
"""


def hockey_score(home_goals, away_goals, shots_total, is_ot):
    goals = home_goals + away_goals
    diff = abs(home_goals - away_goals)
    score = (
        shots_total * 0.2
        + goals * 1.7
        + (3 if is_ot else 0)
        - diff ** 1.6
    )
    return round(score, 2)


def football_score_with_stats(home_goals, away_goals, shots_total, xg_total, fouls_total):
    goals = home_goals + away_goals
    diff = abs(home_goals - away_goals)
    xg_factor = xg_total if xg_total > 0 else 1
    score = (
        shots_total * 0.1 * xg_factor
        + goals * 1.7
        - diff ** 1.6
        - fouls_total * 0.05
    )
    return round(score, 2)


def football_score_fallback(home_goals, away_goals):
    """Використовується, якщо для матчу ще немає детальної статистики."""
    goals = home_goals + away_goals
    diff = abs(home_goals - away_goals)
    score = goals * 1.7 - diff ** 1.3
    return round(score, 2)
