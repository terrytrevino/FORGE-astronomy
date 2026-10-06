import astropy.units as u
from astropy.coordinates import SkyCoord
from astroquery.simbad import Simbad


def resolve_object_name(name):
    """Resolve an astronomical object name to an authoritative ICRS position.

    Returns a compact dictionary suitable for the FORGE target panel.
    SIMBAD is tried first so we can preserve the canonical identifier and
    object type. Astropy's Sesame resolver is used as a fallback.
    """
    query = str(name or "").strip()
    if not query:
        return {"status": "ERROR", "message": "Enter an astronomical object name."}

    try:
        table = Simbad.query_object(query)
        if table is not None and len(table):
            row = table[0]
            cols = table.colnames

            main_id = str(row["main_id"]) if "main_id" in cols else query
            otype = str(row["otype"]) if "otype" in cols else ""

            # Current astroquery SIMBAD may expose decimal coordinates directly.
            if "ra" in cols and "dec" in cols:
                try:
                    ra = float(row["ra"])
                    dec = float(row["dec"])
                    return {
                        "status": "OK",
                        "input_name": query,
                        "canonical_name": main_id,
                        "object_type": otype,
                        "ra_deg": ra,
                        "dec_deg": dec,
                        "resolver": "SIMBAD",
                    }
                except Exception:
                    pass

            # Older SIMBAD table format returns sexagesimal strings.
            if "RA" in cols and "DEC" in cols:
                coord = SkyCoord(
                    str(row["RA"]),
                    str(row["DEC"]),
                    unit=(u.hourangle, u.deg),
                    frame="icrs",
                )
                return {
                    "status": "OK",
                    "input_name": query,
                    "canonical_name": main_id,
                    "object_type": otype,
                    "ra_deg": float(coord.ra.deg),
                    "dec_deg": float(coord.dec.deg),
                    "resolver": "SIMBAD",
                }
    except Exception:
        pass

    try:
        coord = SkyCoord.from_name(query)
        return {
            "status": "OK",
            "input_name": query,
            "canonical_name": query,
            "object_type": "",
            "ra_deg": float(coord.ra.deg),
            "dec_deg": float(coord.dec.deg),
            "resolver": "Sesame",
        }
    except Exception as exc:
        return {
            "status": "ERROR",
            "input_name": query,
            "message": f"Could not resolve this name: {exc}",
        }
