"""
Functions for processing METAR observations retrieved via the NOAA
`Aviation Weather Center Text Data Server (TDS) <https://www.aviationweather.gov/dataserver>`_.
"""

__all__ = ['metar_csv_reader', 'parse_metar_values', 'sorted_by_observation_time']

from collections.abc import Iterable
import csv
import functools
import typing


def metar_csv_reader(inp: Iterable[str]) -> csv.DictReader:
    """
    Creates a reader for the CSV-formatted METAR input. Skips over the TDS metadata
    prolog and attempts to read the field names, advancing the input stream so that the
    next yielded item will be the first METAR record.

    For example,

    :param inp: a text input stream that implements the iterator protocol (such as a
        file-like object)
    :return: the reader
    """
    for rec in inp:
        if rec.startswith('raw_text,station_id,'):
            return csv.DictReader(inp, fieldnames=rec.strip().split(','))


def parse_metar_values(d: dict[str, str]) -> dict[str, typing.Any]:
    """
    Parses the values of a METAR record, converting non-string values to a ``float``,
    ``int``, or ``bool`` based on the type specified in `TDS METAR Field Descriptions
    <https://www.aviationweather.gov/dataserver/fields?datatype=metar>`_. Empty fields
    are converted to ``None``.

    :param d: the raw METAR fields
    :return: a copy of the METAR record with non-string values converted to appropriate
        built-in types
    """
    def convert_if_not_blank(f, v: str):
        vv = v.strip()
        if vv:
            return f(vv)
        else:
            return None

    float_or_none = functools.partial(convert_if_not_blank, float)
    int_or_none = functools.partial(convert_if_not_blank, int)
    bool_or_none = functools.partial(convert_if_not_blank, bool)

    converter = {
        'latitude': float_or_none,
        'longitude': float_or_none,
        'temp_c': float_or_none,
        'dewpoint_c': float_or_none,
        'wind_dir_degrees': int_or_none,
        'wind_speed_kt': int_or_none,
        'wind_gust_kt': int_or_none,
        'visibility_statute_mi': float_or_none,
        'altim_in_hg': float_or_none,
        'sea_level_pressure_mb': float_or_none,
        'cloud_base_ft_agl': int_or_none,
        'three_hr_pressure_tendency_mb': float_or_none,
        'maxT_c': float_or_none,
        'minT_c': float_or_none,
        'maxT24hr_c': float_or_none,
        'minT24hr_c': float_or_none,
        'precip_in': float_or_none,
        'pcp3hr_in': float_or_none,
        'pcp6hr_in': float_or_none,
        'pcp24hr_in': float_or_none,
        'snow_in': float_or_none,
        'vert_vis_ft': int_or_none,
        'elevation_m': float_or_none,
        'auto': bool_or_none,
        'auto_station': bool_or_none,
        'maintenance_indicator_on': bool_or_none,
        'corrected': bool_or_none,
        'lightning_sensor_off': bool_or_none,
        'freezing_rain_sensor_off': bool_or_none,
        'present_weather_sensor_off': bool_or_none,
        'no_signal': bool_or_none
    }

    def convert(k: str, v: str) -> tuple:
        return k, converter.get(k, str)(v)

    return dict([convert(k, v) for k, v in d.items()])


def sorted_by_observation_time(metars: Iterable[dict]) -> list[dict]:
    """
    Returns METAR records sorted by the ``observation_time``. TDS returns
    ``observation_time`` as an ISO 8601 date/time formatted string, which is a convenient
    value for sorting in time order.

    :param metars: the METAR records
    :return: a new sorted list
    """
    return sorted(metars, key=lambda m: m['observation_time'])
