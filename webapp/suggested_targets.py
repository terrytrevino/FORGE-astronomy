import numpy as np
import pandas as pd
import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS

from astroquery.ipac.irsa import Irsa
from astroquery.skyview import SkyView
from astroquery.gaia import Gaia
import time


def _query_2mass_with_retry(coord, radius, attempts=2):
    last_error = None
    for attempt in range(attempts):
        try:
            return Irsa.query_region(
                coord,
                catalog="fp_psc",
                spatial="Cone",
                radius=radius,
            ), None
        except Exception as exc:
            last_error = exc
            if attempt < attempts - 1:
                time.sleep(1.2)
    return None, last_error


def _suggest_from_gaia(coord, radius_arcmin=6.0, limit=8):
    """Fallback compact-star suggestions using Gaia DR3."""
    radius = float(radius_arcmin) * u.arcmin
    try:
        job = Gaia.cone_search_async(coord, radius)
        table = job.get_results()
    except Exception as exc:
        return pd.DataFrame(), str(exc)

    if table is None or len(table) == 0:
        return pd.DataFrame(), None

    rows = []
    cols = table.colnames

    for row in table:
        try:
            ra = float(row["ra"])
            dec = float(row["dec"])
            src = SkyCoord(ra=ra * u.deg, dec=dec * u.deg)
            sep = coord.separation(src).arcsec

            rows.append({
                "target_id": f"Gaia_DR3_{row['source_id']}" if "source_id" in cols else "Gaia_DR3",
                "ra_deg": ra,
                "dec_deg": dec,
                "separation_arcsec": sep,
                "g_mag": float(row["phot_g_mean_mag"]) if "phot_g_mean_mag" in cols else np.nan,
                "bp_mag": float(row["phot_bp_mean_mag"]) if "phot_bp_mean_mag" in cols else np.nan,
                "rp_mag": float(row["phot_rp_mean_mag"]) if "phot_rp_mean_mag" in cols else np.nan,
                "source_catalog": "Gaia DR3 fallback",
            })
        except Exception:
            continue

    df = pd.DataFrame(rows)
    if df.empty:
        return df, None

    df = df.sort_values(
        by=["g_mag", "separation_arcsec"],
        ascending=[True, True],
        na_position="last",
    ).head(limit)

    return df, None


def suggest_compact_stars(ra_deg, dec_deg, radius_arcmin=6.0, limit=8):
    """
    Return nearby compact-star candidates.

    Primary source: 2MASS PSC via IRSA.
    Fallback source: Gaia DR3 if IRSA is unavailable or returns no usable rows.
    """
    coord = SkyCoord(
        ra=float(ra_deg) * u.deg,
        dec=float(dec_deg) * u.deg,
        frame="icrs",
    )

    table, irsa_error = _query_2mass_with_retry(
        coord,
        float(radius_arcmin) * u.arcmin,
        attempts=2,
    )

    if table is not None and len(table) > 0:
        rows = []
        cols = table.colnames

        for row in table:
            try:
                ra = float(row["ra"])
                dec = float(row["dec"])
                src = SkyCoord(ra=ra * u.deg, dec=dec * u.deg)
                sep = coord.separation(src).arcsec

                j = float(row["j_m"]) if "j_m" in cols else np.nan
                h = float(row["h_m"]) if "h_m" in cols else np.nan
                k = float(row["k_m"]) if "k_m" in cols else np.nan

                rows.append({
                    "target_id": str(row["designation"]) if "designation" in cols else "2MASS",
                    "ra_deg": ra,
                    "dec_deg": dec,
                    "separation_arcsec": sep,
                    "j_mag": j,
                    "h_mag": h,
                    "ks_mag": k,
                    "ph_qual": str(row["ph_qual"]) if "ph_qual" in cols else "",
                    "cc_flg": str(row["cc_flg"]) if "cc_flg" in cols else "",
                    "source_catalog": "2MASS PSC",
                })
            except Exception:
                continue

        df = pd.DataFrame(rows)

        if not df.empty:
            def qscore(x):
                s = str(x)
                return sum(1 for ch in s if ch == "A")

            df["quality_score"] = df["ph_qual"].apply(qscore)
            df["clean_score"] = (df["cc_flg"] == "000").astype(int)

            df = df.sort_values(
                by=["clean_score", "quality_score", "ks_mag", "separation_arcsec"],
                ascending=[False, False, True, True],
                na_position="last",
            ).head(limit)

            return df.drop(columns=["quality_score", "clean_score"]), None

    # Resilient fallback: Gaia DR3.
    gaia_df, gaia_error = _suggest_from_gaia(
        coord,
        radius_arcmin=radius_arcmin,
        limit=limit,
    )

    if not gaia_df.empty:
        note = None
        if irsa_error is not None:
            note = f"IRSA unavailable; using Gaia DR3 fallback. IRSA error: {irsa_error}"
        else:
            note = "No usable 2MASS rows; using Gaia DR3 fallback."
        return gaia_df, note

    combined = []
    if irsa_error is not None:
        combined.append(f"IRSA: {irsa_error}")
    if gaia_error:
        combined.append(f"Gaia: {gaia_error}")

    return pd.DataFrame(), " | ".join(combined) if combined else None


def suggest_morphology_regions(
    ra_deg,
    dec_deg,
    fov_arcmin=10.0,
    limit=8,
    pixels=600,
):
    """Find high-gradient regions in a 2MASS-K image and convert pixels to sky coordinates."""
    try:
        images = SkyView.get_images(
            position=f"{float(ra_deg)} {float(dec_deg)}",
            survey=["2MASS-K"],
            radius=(float(fov_arcmin) / 2.0) * u.arcmin,
            pixels=f"{pixels},{pixels}",
        )
    except Exception as exc:
        return pd.DataFrame(), str(exc)

    if not images:
        return pd.DataFrame(), None

    hdu = None
    for candidate in images[0]:
        if getattr(candidate, "data", None) is not None:
            arr = np.squeeze(candidate.data)
            if arr.ndim == 2:
                hdu = candidate
                data = np.asarray(arr, dtype=float)
                break

    if hdu is None:
        return pd.DataFrame(), None

    # Robustly suppress extreme point sources before computing local gradients.
    finite = data[np.isfinite(data)]
    if finite.size == 0:
        return pd.DataFrame(), None

    lo, hi = np.percentile(finite, [5, 99])
    clipped = np.clip(data, lo, hi)

    gy, gx = np.gradient(clipped)
    grad = np.hypot(gx, gy)

    # Avoid image edges and avoid placing suggestions too near each other.
    margin = max(20, pixels // 30)
    grad[:margin, :] = np.nan
    grad[-margin:, :] = np.nan
    grad[:, :margin] = np.nan
    grad[:, -margin:] = np.nan

    flat_order = np.argsort(np.nan_to_num(grad, nan=-np.inf).ravel())[::-1]

    selected = []
    min_sep_pix = max(30, pixels // 12)

    for idx in flat_order:
        if len(selected) >= limit:
            break
        y, x = np.unravel_index(idx, grad.shape)
        if not np.isfinite(grad[y, x]):
            continue

        if any(np.hypot(x - sx, y - sy) < min_sep_pix for sx, sy, _ in selected):
            continue

        selected.append((x, y, float(grad[y, x])))

    if not selected:
        return pd.DataFrame(), None

    try:
        wcs = WCS(hdu.header)
        px = np.array([[x, y] for x, y, _ in selected], dtype=float)
        world = wcs.pixel_to_world(px[:, 0], px[:, 1])
        ras = np.asarray(world.ra.deg)
        decs = np.asarray(world.dec.deg)
    except Exception as exc:
        return pd.DataFrame(), f"WCS conversion failed: {exc}"

    rows = []
    for i, ((x, y, score), ra, dec) in enumerate(zip(selected, ras, decs), start=1):
        rows.append({
            "target_id": f"morphology_{i:02d}",
            "ra_deg": float(ra),
            "dec_deg": float(dec),
            "x_pixel": float(x),
            "y_pixel": float(y),
            "gradient_score": float(score),
        })

    return pd.DataFrame(rows), None
