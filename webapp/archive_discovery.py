import pandas as pd
import astropy.units as u
from astropy.coordinates import SkyCoord

from astroquery.mast import Observations
from astroquery.sdss import SDSS
from astroquery.ipac.irsa import Irsa
from astroquery.alma import Alma


def _safe_len(table):
    try:
        return len(table) if table is not None else 0
    except Exception:
        return 0


def discover_mast(coord, radius):
    out = {
        "archive": "MAST",
        "status": "OK",
        "count": 0,
        "summary": "",
        "details": [],
    }
    try:
        table = Observations.query_region(coord, radius=radius)
        out["count"] = _safe_len(table)

        if out["count"] > 0:
            cols = table.colnames
            mission_col = "obs_collection" if "obs_collection" in cols else None
            inst_col = "instrument_name" if "instrument_name" in cols else None
            dtype_col = "dataproduct_type" if "dataproduct_type" in cols else None

            missions = []
            if mission_col:
                vc = pd.Series([str(x) for x in table[mission_col]]).value_counts()
                missions = [{"mission": k, "count": int(v)} for k, v in vc.head(12).items()]

            out["details"] = missions
            out["summary"] = ", ".join(
                f"{x['mission']} ({x['count']})" for x in missions[:6]
            ) or f"{out['count']} observations"
        else:
            out["summary"] = "No matching observations"
    except Exception as exc:
        out.update(status="ERROR", summary=str(exc))
    return out


def discover_sdss_spectra(coord, radius):
    out = {
        "archive": "SDSS spectroscopy",
        "status": "OK",
        "count": 0,
        "summary": "",
        "details": [],
    }
    try:
        table = SDSS.query_region(coord, radius=radius, spectro=True)
        out["count"] = _safe_len(table)

        if out["count"] > 0:
            cols = table.colnames
            rows = []
            for row in table[:10]:
                item = {}
                for key in ["ra", "dec", "plate", "mjd", "fiberID", "specobjid"]:
                    if key in cols:
                        try:
                            item[key] = str(row[key])
                        except Exception:
                            pass
                rows.append(item)
            out["details"] = rows
            out["summary"] = f"{out['count']} spectroscopic match(es)"
        else:
            out["summary"] = "No spectroscopic match"
    except Exception as exc:
        out.update(status="ERROR", summary=str(exc))
    return out


def discover_irsa(coord, radius):
    out = {
        "archive": "IRSA",
        "status": "OK",
        "count": 0,
        "summary": "",
        "details": [],
    }

    catalogs = [
        ("2MASS PSC", "fp_psc"),
        ("AllWISE", "allwise_p3as_psd"),
    ]

    total = 0
    details = []
    try:
        for label, catalog in catalogs:
            try:
                table = Irsa.query_region(
                    coord,
                    catalog=catalog,
                    spatial="Cone",
                    radius=radius,
                )
                n = _safe_len(table)
                total += n
                details.append({"catalog": label, "count": int(n)})
            except Exception as exc:
                details.append({"catalog": label, "count": 0, "error": str(exc)})

        out["count"] = total
        out["details"] = details
        out["summary"] = ", ".join(f"{x['catalog']} ({x['count']})" for x in details)
    except Exception as exc:
        out.update(status="ERROR", summary=str(exc))
    return out


def discover_alma(coord, radius):
    out = {
        "archive": "ALMA",
        "status": "OK",
        "count": 0,
        "summary": "",
        "details": [],
    }
    try:
        table = Alma.query_region(coord, radius=radius, public=True, science=True)
        out["count"] = _safe_len(table)

        if out["count"] > 0:
            cols = table.colnames
            rows = []
            for row in table[:10]:
                item = {}
                for key in [
                    "target_name",
                    "band_list",
                    "frequency_support",
                    "t_min",
                    "t_max",
                    "s_resolution",
                ]:
                    if key in cols:
                        try:
                            item[key] = str(row[key])
                        except Exception:
                            pass
                rows.append(item)
            out["details"] = rows
            out["summary"] = f"{out['count']} public science dataset(s)"
        else:
            out["summary"] = "No public science datasets"
    except Exception as exc:
        out.update(status="ERROR", summary=str(exc))
    return out


def discover_archives(ra_deg, dec_deg, radius_arcsec=30.0):
    coord = SkyCoord(ra=float(ra_deg) * u.deg, dec=float(dec_deg) * u.deg, frame="icrs")

    # Keep SDSS within its server cone-search limit.
    sdss_radius = min(float(radius_arcsec), 180.0) * u.arcsec
    radius = float(radius_arcsec) * u.arcsec

    results = [
        discover_mast(coord, radius),
        discover_sdss_spectra(coord, sdss_radius),
        discover_irsa(coord, radius),
        discover_alma(coord, radius),
    ]

    manifest = pd.DataFrame(
        [
            {
                "archive": x["archive"],
                "status": x["status"],
                "count": x["count"],
                "summary": x["summary"],
            }
            for x in results
        ]
    )

    return manifest, results
