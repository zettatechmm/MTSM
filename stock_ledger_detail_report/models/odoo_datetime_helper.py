from dateutil import parser
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime

def set_local_time(dt, tz, hour, minute, second):
    """
    convert datetime string in utc to local time with hour, minute, second and return respective utc time
    dt - datetime string
    tz - timezone string (e.g. 'Asia/Yangon')
    """
    obj = parser.parse(dt)
    # set naive datetime to utc. this isn't needed in python3.6. but server is python3.5
    obj = pytz.utc.localize(obj)
    obj = obj.astimezone(pytz.timezone(tz))
    obj = obj.replace(hour=hour, minute=minute, second=second)
    obj = obj.astimezone(pytz.utc)
    obj = datetime.strftime(obj, DEFAULT_SERVER_DATETIME_FORMAT)
    return obj

def local_time(dt, tz):
    """
    convert utc time to tz time str
    dt - datetime object
    tz - timezone string (e.g. 'Asia/Yangon')
    """
    # set naive datetime to utc. this isn't needed in python3.6. but server is python3.5
    datetime_obj = pytz.utc.localize(dt)
    local_tz = pytz.timezone(tz)
    local_datetime = datetime_obj.astimezone(local_tz)
    return datetime.strftime(local_datetime, DEFAULT_SERVER_DATETIME_FORMAT)
