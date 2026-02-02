from datetime import datetime


def get_url_for_vendor_alpha_tomorrow_page() -> str:
    # Monday = 1, Sunday = 7
    dayOfWeek = (datetime.now().weekday() + 2) % 7
    # Adjusting the value to make sure Sunday is 7, not 0
    if dayOfWeek == 0:
        dayOfWeek = 7
    return f"https://www.example-vendor-alpha.com/#/AS/B2488/T{dayOfWeek}/"


def get_url_for_vendor_alpha_today_page() -> str:
    # Monday = 1, Sunday = 7
    dayOfWeek = (datetime.now().weekday() + 1) % 7
    # Adjusting the value to make sure Sunday is 7, not 0
    if dayOfWeek == 0:
        dayOfWeek = 7
    return f"https://www.example-vendor-alpha.com/#/AS/B2488/T{dayOfWeek}/"
