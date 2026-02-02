from datetime import date


def ordinal(n: int) -> str:
    if 11 <= n % 100 <= 13:
        return f"{n}th"
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def resolve_system_variables() -> dict[str, str]:
    today = date.today()

    return {
        # Long / short dates
        "currentdate": today.strftime("%B %d, %Y"),
        "currentdate_short": today.strftime("%m/%d/%Y"),

        # Components
        "currentday": str(today.day),
        "currentday_ordinal": ordinal(today.day),
        "currentmonth": today.strftime("%B"),
        "year": str(today.year),
    }
