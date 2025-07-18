from tsl.utils import global_id_to_site_id

class SourceInvalid(ValueError): ...


class DestinationInvalid(ValueError): ...


def siteid_or_coords(
    source: str, dest: str
) -> tuple[str, str] | tuple[str, str, str, str]:
    """
    Validate source and destination as either site ids or pairs of lat, lon.

    Returns a tuple of either (source_siteid, dest_siteid) or (s_lat, s_lon, d_lat, d_lon)
    """
    errors = []

    if "," in source and "," in dest:
        # remove occasional parentheses
        source, dest = source.strip("()"), dest.strip("()")

        s_lat, s_lon = (x.strip() for x in source.split(","))
        if not (s_lat.isdecimal() and s_lon.isdecimal()):
            errors.append(SourceInvalid())

        d_lat, d_lon = (x.strip() for x in dest.split(","))
        if not (d_lat.isdecimal() and d_lon.isdecimal()):
            errors.append(DestinationInvalid())

        if errors:
            raise ExceptionGroup("errors", errors)  # noqa: F821

        return (s_lat, s_lon, d_lat, d_lon)

    else:
        try:
            source = global_id_to_site_id(source)
        except ValueError:
            errors.append(SourceInvalid())

        try:
            dest = global_id_to_site_id(dest)
        except ValueError:
            errors.append(DestinationInvalid())

        if errors:
            raise ExceptionGroup("errors", errors)  # noqa: F821

        return (source, dest)
