from datetime import datetime
from math import log

arbitrary_date = datetime.fromisoformat('2024-01-01T00:00:00Z')


def compute_score(nvotes: int, creation_date, days_modifier: int = 1):
    lapse = creation_date - arbitrary_date
    return log(max(nvotes, 1), base=2) + (lapse.days / days_modifier)
