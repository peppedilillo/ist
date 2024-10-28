from datetime import datetime
from math import log10

arbitrary_date = datetime.fromisoformat('2024-01-01T00:00:00Z')


def compute_score(nlikes: int, creation_date, days_modifier: int = 1):
    lapse = creation_date - arbitrary_date
    return log10(max(nlikes, 1)) + (lapse.days / days_modifier)
