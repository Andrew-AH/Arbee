from freezegun import freeze_time

from libs.vendors.bet365.urls import get_url_for_bet365_today_page, get_url_for_bet365_tomorrow_page


def test_get_url_for_bet365_tomorrow_page_for_monday():
    with freeze_time("2025-03-31 12:00:00"):
        url = get_url_for_bet365_tomorrow_page()
        assert url == "https://www.bet365.com.au/#/AS/B2488/T2/"


def test_get_url_for_bet365_tomorrow_page_for_sunday():
    with freeze_time("2025-03-30 12:00:00"):
        url = get_url_for_bet365_tomorrow_page()
        assert url == "https://www.bet365.com.au/#/AS/B2488/T1/"


def test_get_url_for_bet365_today_page_for_monday():
    with freeze_time("2025-03-31 12:00:00"):
        url = get_url_for_bet365_today_page()
        assert url == "https://www.bet365.com.au/#/AS/B2488/T1/"


def test_get_url_for_bet365_today_page_for_sunday():
    with freeze_time("2025-03-30 12:00:00"):
        url = get_url_for_bet365_today_page()
        assert url == "https://www.bet365.com.au/#/AS/B2488/T7/"
