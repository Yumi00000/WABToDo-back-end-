from datetime import datetime


def change_date_format(date: datetime) -> str | None:
    try:
        old_format = date
        valid_format = old_format.strftime("%Y-%m-%d")
        return valid_format

    except (ValueError, TypeError, AttributeError):
        return None
