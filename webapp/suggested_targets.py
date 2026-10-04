import numpy as np
import pandas as pd
import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS

from astroquery.ipac.irsa import Irsa
from astroquery.skyview import SkyView


def suggest_compact_stars(ra_deg, dec_deg, radius_arcmin=6.0, limit=8):
    """Return nearby 2MASS point sources ranked by bright Ks magnitude."""
    coord = SkyCoord(
        ra=float(ra_deg) * u.deg,
        dec=float(dec_deg) * u.deg,
        frame="icrs",
    )

    try:
        table = Irsa.query_region(
            coord,
            catalog="fp_psc",
            spatial="Cone",
            radius=float(radius_arcmin) * u.arcmin,
        )
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
            })
        except Exception:
            continue

    df = pd.DataFrame(rows)
    if df.empty:
        return df, None

    # Prefer clean, good-quality sources, then bright Ks.
    def qscore(x):
        s = str(x)
        return sum(1 for c in s if c == "A")

    df["quality_score"] = df["ph_qual"].apply(qscore)
    df["clean_score"] = (df["cc_flg"] == "000").astype(int)

    df = df.sort_values(
        by=["clean_score", "quality_score", "ks_mag", "separation_arcsec"],
        ascending=[False, False, True, True],
        na_position="last",
    ).head(limit)

    return df.drop(columns=["quality_score", "clean_score"]), None


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
