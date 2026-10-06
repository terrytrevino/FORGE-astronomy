import csv
import io
import requests
import pandas as pd
import astropy.units as u
from astropy.coordinates import SkyCoord
from astroquery.skyview import SkyView
import pyvo


DASCH_API = "https://api.starglass.cfa.harvard.edu/public"
NRAO_TAP = "https://data-query.nrao.edu/tap"


def discover_dss(ra_deg, dec_deg, radius_arcmin=6.0):
    """Check DSS/DSS2 image availability through SkyView."""
    surveys = ["DSS", "DSS2 Red", "DSS2 Blue", "DSS2 IR"]
    details = []
    count = 0

    for survey in surveys:
        try:
            imgs = SkyView.get_images(
                position=f"{float(ra_deg)} {float(dec_deg)}",
                survey=[survey],
                radius=(float(radius_arcmin) / 2.0) * u.arcmin,
                pixels="256,256",
            )
            available = bool(imgs)
            if available:
                count += 1
            details.append({
                "survey": survey,
                "available": available,
            })
        except Exception as exc:
            details.append({
                "survey": survey,
                "available": False,
                "error": str(exc),
            })

    return {
        "archive": "DSS / photographic plates",
        "status": "OK",
        "count": count,
        "summary": f"{count} DSS survey layer(s) available",
        "details": details,
    }


def _parse_dasch_lines(payload):
    """DASCH endpoints return a JSON list of CSV-formatted strings."""
    if not payload:
        return pd.DataFrame()

    text = "\n".join(payload)
    try:
        return pd.read_csv(io.StringIO(text))
    except Exception:
        try:
            rows = list(csv.reader(io.StringIO(text)))
            if not rows:
                return pd.DataFrame()
            return pd.DataFrame(rows[1:], columns=rows[0])
        except Exception:
            return pd.DataFrame()


def discover_dasch(ra_deg, dec_deg, max_rows=12):
    """Query Harvard DASCH DR7 exposures intersecting the coordinate."""
    url = f"{DASCH_API}/dasch/dr7/queryexps"
    body = {
        "ra_deg": float(ra_deg) % 360.0,
        "dec_deg": float(dec_deg),
    }

    out = {
        "archive": "Harvard DASCH",
        "status": "OK",
        "count": 0,
        "summary": "",
        "details": [],
    }

    try:
        r = requests.post(url, json=body, timeout=45)
        r.raise_for_status()
        payload = r.json()
        df = _parse_dasch_lines(payload)
        out["count"] = int(len(df))

        if df.empty:
            out["summary"] = "No DASCH plate exposures found"
            return out

        show_cols = [
            c for c in [
                "series",
                "platenum",
                "expnum",
                "solnum",
                "date",
                "datetime",
                "exptime",
                "scanned",
            ] if c in df.columns
        ]

        details = df.head(max_rows)
        if show_cols:
            details = details[show_cols]

        out["details"] = details.fillna("").astype(str).to_dict(orient="records")
        out["summary"] = f"{len(df)} historical plate exposure(s)"
        return out

    except Exception as exc:
        out.update(status="ERROR", summary=str(exc))
        return out


def discover_nrao(ra_deg, dec_deg, radius_arcmin=60.0, max_rows=20):
    """Query the NRAO VO/TAP archive around a coordinate."""
    out = {
        "archive": "NRAO radio",
        "status": "OK",
        "count": 0,
        "summary": "",
        "details": [],
    }

    try:
        service = pyvo.dal.TAPService(NRAO_TAP)

        radius_deg = float(radius_arcmin) / 60.0
        query = f"""
        SELECT TOP {int(max_rows)}
            s_ra,
            s_dec,
            target_name,
            instrument_name,
            dataproduct_type,
            obs_publisher_did,
            freq_min,
            freq_max,
            center_frequencies,
            bandwidths,
            nums_channels,
            spectral_resolutions,
            aggregate_bandwidth,
            t_min,
            t_max,
            access_url
        FROM ivoa.obscore
        WHERE 1=CONTAINS(
            POINT('ICRS', s_ra, s_dec),
            CIRCLE('ICRS', {float(ra_deg)}, {float(dec_deg)}, {radius_deg})
        )
        """

        table = service.search(query).to_table()
        out["count"] = int(len(table))

        if len(table) == 0:
            out["summary"] = "No NRAO archive matches"
            return out

        instruments = []
        if "instrument_name" in table.colnames:
            instruments = sorted(set(str(x) for x in table["instrument_name"] if str(x).strip()))

        details = []
        for row in table:
            item = {}
            for key in [
                "target_name",
                "instrument_name",
                "dataproduct_type",
                "obs_publisher_did",
                "freq_min",
                "freq_max",
                "center_frequencies",
                "bandwidths",
                "nums_channels",
                "spectral_resolutions",
                "aggregate_bandwidth",
                "t_min",
                "t_max",
                "access_url",
            ]:
                if key in table.colnames:
                    try:
                        item[key] = str(row[key])
                    except Exception:
                        pass
            details.append(item)

        out["details"] = details
        out["summary"] = (
            f"{len(table)} radio match(es)"
            + (f" — {', '.join(instruments[:6])}" if instruments else "")
        )
        return out

    except Exception as exc:
        out.update(status="ERROR", summary=str(exc))
        return out
