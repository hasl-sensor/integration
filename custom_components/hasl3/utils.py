class SourceInvalid(ValueError): ...


class DestinationInvalid(ValueError): ...


def siteid_or_coords(
    source: str, dest: str
) -> tuple[str, str] | tuple[str, str, str, str]:
    """
    Validate source and destination as either site ids or (lat, lon).

    Returns a tuple of either (source_siteid, dest_siteid) or (s_lat, s_lon, d_lat, d_lon)
    """

    def _is_float(value: str) -> bool:
        try:
            float(value)
            return True
        except ValueError:
            return False

    errors = []

    if "," in source and "," in dest:
        source, dest = source.strip("()"), dest.strip("()")

        s_lat, s_lon = (x.strip() for x in source.split(","))
        if not (_is_float(s_lat) and _is_float(s_lon)):
            errors.append(SourceInvalid())

        d_lat, d_lon = (x.strip() for x in dest.split(","))
        if not (_is_float(d_lat) and _is_float(d_lon)):
            errors.append(DestinationInvalid())

        if errors:
            raise ExceptionGroup("errors", errors)  # noqa: F821

        return (s_lat, s_lon, d_lat, d_lon)

    else:
        return (source, dest)
