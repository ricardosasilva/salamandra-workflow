import datetime
import re

from django.conf import settings
import pytz
from workalendar.america import Brazil

cal = Brazil()

def camel_to_snake_case(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()



def fullname(o):
    # o.__module__ + "." + o.__class__.__qualname__ is an example in
    # this context of H.L. Mencken's "neat, plausible, and wrong."
    # Python makes no guarantees as to whether the __module__ special
    # attribute is defined, so we take a more circumspect approach.
    # Alas, the module name is explicitly excluded from __qualname__
    # in Python 3.

    module = o.__class__.__module__
    if module is None or module == str.__class__.__module__:
      return o.__class__.__name__  # Avoid reporting __builtin__
    else:
      return module + '.' + o.__class__.__name__


def add_workday(initial_datetime, minutes, start_workday_hour=9, end_workday_hour=18):
    minutes += (initial_datetime.hour * 60) + initial_datetime.minute

    days = int(minutes / 1440)
    total_minutes_remains = minutes % 1440
    hours_remains = int(total_minutes_remains / 60)
    minutes_remains = total_minutes_remains % 60

    result = cal.add_working_days(initial_datetime, days)

    timezone = pytz.timezone(settings.TIME_ZONE)

    if hours_remains > end_workday_hour:
      hours_remains = start_workday_hour
      minutes_remains = 0
      result = cal.add_working_days(result, 1)

    if hours_remains < start_workday_hour:
      hours_remains = start_workday_hour
      minutes_remains = 0

    result = timezone.localize(
        datetime.datetime(
          year=result.year,
          month=result.month,
          day=result.day,
          hour=hours_remains,
          minute=minutes_remains
        )
      )
    return result


def sub_workday(initial_datetime, minutes, start_workday_hour=9, end_workday_hour=18):
    minutes += (initial_datetime.hour * 60) + initial_datetime.minute

    days = int(minutes / 1440)
    total_minutes_remains = minutes % 1440
    hours_remains = int(total_minutes_remains / 60)
    minutes_remains = total_minutes_remains % 60

    result = cal.sub_working_days(initial_datetime, days)

    timezone = pytz.timezone(settings.TIME_ZONE)

    if hours_remains > end_workday_hour:
      hours_remains = start_workday_hour
      minutes_remains = 0
      result = cal.add_working_days(result, 1)

    if hours_remains < start_workday_hour:
      hours_remains = start_workday_hour
      minutes_remains = 0

    result = timezone.localize(
        datetime.datetime(
          year=result.year,
          month=result.month,
          day=result.day,
          hour=hours_remains,
          minute=minutes_remains
        )
      )
    return result