"""
Custom Jinja2 filters for mapbuilder
Provides DMS coordinate conversion to match GNG format
"""

def decimal_to_dms(decimal, is_latitude=True):
    """
    Convert decimal degrees to DMS format matching GNG output
    
    Args:
        decimal: Decimal degrees (positive or negative)
        is_latitude: True for lat (N/S), False for lon (E/W)
    
    Returns:
        String in format: N044.52.33.000 or W063.31.36.968
    """
    # Determine hemisphere
    if is_latitude:
        hemisphere = 'N' if decimal >= 0 else 'S'
    else:
        hemisphere = 'E' if decimal >= 0 else 'W'
    
    # Work with absolute value
    decimal = abs(decimal)
    
    # Extract degrees, minutes, seconds
    degrees = int(decimal)
    minutes_decimal = (decimal - degrees) * 60
    minutes = int(minutes_decimal)
    seconds = (minutes_decimal - minutes) * 60
    
    # Format to match GNG output: N044.52.33.000
    if is_latitude:
        return f"{hemisphere}{degrees:03d}.{minutes:02d}.{seconds:06.3f}"
    else:
        return f"{hemisphere}{degrees:03d}.{minutes:02d}.{seconds:06.3f}"


def get_jinja_filters():
    """Return dictionary of custom filters for Jinja2"""
    return {
        'to_dms_lat': lambda x: decimal_to_dms(x, is_latitude=True),
        'to_dms_lon': lambda x: decimal_to_dms(x, is_latitude=False),
    }
