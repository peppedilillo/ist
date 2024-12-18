from datetime import datetime
from math import log10

arbitrary_date = datetime.fromisoformat("2024-01-01T00:00:00Z")
day_seconds = 24 * 60 * 60


def compute_score(nlikes: int, creation_date, days_modifier: int = 1):
    lapse = creation_date - arbitrary_date
    return log10(nlikes + 1) + (lapse.days + lapse.seconds / day_seconds) / days_modifier
