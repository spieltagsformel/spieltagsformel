"""Kurznamen der Teams für Grafiken (gleiche Liste wie auf der Website)."""
KURZ = {
    "SV 07 Elversberg": "Elversberg", "1. FSV Mainz 05": "Mainz", "Bayer 04 Leverkusen": "Leverkusen",
    "VfB Stuttgart": "Stuttgart", "FC Augsburg": "Augsburg", "SC Freiburg": "Freiburg",
    "Borussia Mönchengladbach": "Gladbach", "SC Paderborn 07": "Paderborn", "SV Werder Bremen": "Bremen",
    "TSG Hoffenheim": "Hoffenheim", "FC Schalke 04": "Schalke", "RB Leipzig": "Leipzig",
    "FC Bayern München": "Bayern", "Borussia Dortmund": "Dortmund", "1. FC Union Berlin": "Union",
    "1. FC Köln": "Köln", "Eintracht Frankfurt": "Frankfurt", "Hamburger SV": "HSV",
    "VfL Wolfsburg": "Wolfsburg", "1. FC Heidenheim 1846": "Heidenheim", "FC St. Pauli": "St. Pauli",
    "VfL Bochum": "Bochum", "Holstein Kiel": "Kiel", "SV Darmstadt 98": "Darmstadt",
    "TSG 1899 Hoffenheim": "Hoffenheim", "1. FC Heidenheim": "Heidenheim",
}
TAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def kurz(name):
    return KURZ.get(name, name)


def anstoss(lokal):
    """'2026-10-30T20:30:00' -> 'Fr 20:30'"""
    from datetime import datetime
    if not lokal:
        return ""
    t = datetime.fromisoformat(lokal)
    return f"{TAGE[t.weekday()]} {t:%H:%M}"
