from datetime import datetime, timedelta
from json import JSONDecoder, JSONEncoder

import pytz

MELBOURNE_TZ = pytz.timezone("Australia/Melbourne")
UK_TZ = pytz.timezone("Europe/London")


class DateTimeDecoder(JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.dict_to_object, *args, **kwargs)

    def dict_to_object(self, d):
        if "__type__" not in d:
            return d

        type = d.pop("__type__")
        if type == "datetime":
            try:
                dateobj = datetime(**d)
                return dateobj
            except TypeError as e:
                print(f"Failed to decode datetime: {e}")
                d["__type__"] = type  # Restore the type if decoding fails
        return d  # Return as is if not a datetime type


class DateTimeEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return {
                "__type__": "datetime",
                "year": obj.year,
                "month": obj.month,
                "day": obj.day,
                "hour": obj.hour,
                "minute": obj.minute,
                "second": obj.second,
                "microsecond": obj.microsecond,
            }
        else:
            return super().default(
                obj
            )  # Use super() for calling the parent class method


def determine_execution_date() -> str:
    now = datetime.now()
    # Adjust to previous date if it is before 3AM, easier to restart bot past midnight
    if now.hour < 3:
        now -= timedelta(days=1)

    return now.strftime("%d%m%Y")


def get_latest_datetime(
    enriched_venues: dict[str, list[tuple[str, int, int, datetime]]],
) -> datetime:
    latest_date = datetime.now()

    for _, events in enriched_venues.items():
        for event in events:
            event_datetime = event[3]
            if event_datetime > latest_date:
                latest_date = event_datetime

    return latest_date


def melb_to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = MELBOURNE_TZ.localize(dt)
    else:
        dt = dt.astimezone(MELBOURNE_TZ)
    return dt.astimezone(pytz.utc)


def uk_to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = UK_TZ.localize(dt)
    else:
        dt = dt.astimezone(UK_TZ)
    return dt.astimezone(pytz.utc)
