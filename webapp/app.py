import io
import json
import numpy as np
import pandas as pd
import requests
import streamlit as st
from PIL import Image

import astropy.units as u
from astroquery.skyview import SkyView

from storage import Storage, StorageConfig
from archive_discovery import discover_archives, get_mast_preview_products

st.set_page_config(page_title="FORGE Orion", layout="wide")

SDSS_URL = "https://skyserver.sdss.org/dr17/SkyServerWS/ImgCutout/getjpeg"
SURVEYS = {"J": "2MASS-J", "H": "2MASS-H", "K": "2MASS-K"}


def robust_limits(data, low=5, high=99):
    arr = np.asarray(data, dtype=float)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return 0.0, 1.0
    lo, hi = np.percentile(finite, [low, high])
    if hi <= lo:
        lo, hi = np.nanmin(finite), np.nanmax(finite)
    return float(lo), float(hi)


@st.cache_data(show_spinner=False)
def get_sdss_jpeg(ra, dec, fov_arcmin=6.0, size=512):
    scale = (fov_arcmin * 60.0) / size
    params = {
        "ra": float(ra),
        "dec": float(dec),
        "scale": scale,
        "width": size,
        "height": size,
    }
    r = requests.get(SDSS_URL, params=params, timeout=60)
    r.raise_for_status()
    return r.content


@st.cache_data(show_spinner=False)
def get_2mass(ra, dec, band, fov_arcmin=6.0, pixels=500):
    radius = (fov_arcmin / 2.0) * u.arcmin
    images = SkyView.get_images(
        position=f"{float(ra)} {float(dec)}",
        survey=[SURVEYS[band]],
        radius=radius,
        pixels=f"{pixels},{pixels}",
    )
    if not images:
        return None
    for hdu in images[0]:
        if getattr(hdu, "data", None) is not None:
            arr = np.squeeze(hdu.data)
            if arr.ndim == 2:
                return np.asarray(arr, dtype=float)
    return None


def normalize_image(data):
    lo, hi = robust_limits(data)
    scaled = (np.clip(data, lo, hi) - lo) / max(hi - lo, 1e-12)
    return (scaled * 255).astype(np.uint8)


def sector_asymmetry(data, r_in=8, r_out=14, n_sectors=8):
    ny, nx = data.shape
    x0 = (nx - 1) / 2.0
    y0 = (ny - 1) / 2.0
    yy, xx = np.indices(data.shape)
    dx = xx - x0
    dy = yy - y0
    rr = np.sqrt(dx**2 + dy**2)
    theta = (np.degrees(np.arctan2(dy, dx)) + 360.0) % 360.0

    names = ["E", "NE", "N", "NW", "W", "SW", "S", "SE"]
    width = 360.0 / n_sectors
    medians = []

    for i, name in enumerate(names):
        center = i * width
        start = (center - width / 2) % 360
        end = (center + width / 2) % 360
        if start < end:
            amask = (theta >= start) & (theta < end)
        else:
            amask = (theta >= start) | (theta < end)

        mask = (rr >= r_in) & (rr < r_out) & amask & np.isfinite(data)
        vals = data[mask]
        medians.append((name, float(np.median(vals)) if vals.size else np.nan))

    sdf = pd.DataFrame(medians, columns=["sector", "median"])
    vals = sdf["median"].to_numpy(dtype=float)
    finite = vals[np.isfinite(vals)]

    if finite.size == 0:
        return sdf, np.nan, "UNKNOWN"

    frac = (
        (finite.max() - finite.min()) / abs(finite.mean())
        if finite.mean() != 0
        else np.nan
    )
    if np.isfinite(frac):
        flag = "STRONG" if frac >= 0.50 else "MODERATE" if frac >= 0.20 else "LOW"
    else:
        flag = "UNKNOWN"

    return sdf, frac, flag


def build_storage(backend, bucket, prefix):
    if backend == "Local":
        return Storage(StorageConfig(backend="local", prefix=prefix))

    s3 = st.secrets.get("s3", {})
    return Storage(
        StorageConfig(
            backend="s3",
            bucket=bucket,
            prefix=prefix,
            endpoint_url=s3.get("endpoint_url"),
            region_name=s3.get("region_name"),
            aws_access_key_id=s3.get("aws_access_key_id"),
            aws_secret_access_key=s3.get("aws_secret_access_key"),
        )
    )


st.title("FORGE Orion")
st.caption("Multi-wavelength target discovery, morphology, and archive search")

with st.sidebar:
    st.header("Storage")
    storage_backend = st.selectbox("Backend", ["Local", "S3-compatible"])
    storage_prefix = st.text_input("Project prefix", "forge/orion")
    storage_bucket = ""

    if storage_backend == "S3-compatible":
        storage_bucket = st.text_input("Bucket name")
        st.caption("Credentials are read from Streamlit Secrets.")

    if st.button("Test storage"):
        try:
            storage = build_storage(storage_backend, storage_bucket, storage_prefix)
            _, where = storage.test_connection()
            st.success(f"Storage connected: {where}")
        except Exception as exc:
            st.error(f"Storage connection failed: {exc}")

    st.divider()
    st.header("Target")
    mode = st.radio("Analysis mode", ["Point source", "Morphology region"])
    name = st.text_input("Target name", "candidate_01")
    ra = st.number_input("RA (deg)", value=84.040452, format="%.6f")
    dec = st.number_input("Dec (deg)", value=-5.739921, format="%.6f")
    fov = st.slider("Field of view (arcmin)", 2.0, 12.0, 6.0, 0.5)
    discovery_radius = st.slider("Archive search radius (arcsec)", 5, 180, 30, 5)

    st.divider()
    uploaded = st.file_uploader("Candidate CSV", type=["csv"])


if uploaded is not None:
    try:
        cdf = pd.read_csv(uploaded)
        st.subheader("Candidate list")
        st.dataframe(cdf, use_container_width=True)
    except Exception as exc:
        st.warning(f"Could not read CSV: {exc}")


st.subheader("Archive Discovery")
st.caption("Check what exists at this coordinate before downloading large datasets.")

if st.button("Discover archives", type="secondary"):
    with st.spinner("Querying MAST, SDSS spectroscopy, IRSA, and ALMA..."):
        try:
            manifest, archive_details = discover_archives(
                ra, dec, discovery_radius
            )
            st.dataframe(manifest, use_container_width=True)

            for item in archive_details:
                with st.expander(f"{item['archive']} — {item['summary']}"):
                    if item.get("details"):
                        st.json(item["details"])
                    else:
                        st.write("No additional records.")

            try:
                storage = build_storage(
                    storage_backend, storage_bucket, storage_prefix
                )
                storage.save_json(
                    f"targets/{name}/archive_manifest.json",
                    {
                        "target_name": name,
                        "ra_deg": ra,
                        "dec_deg": dec,
                        "radius_arcsec": discovery_radius,
                        "archives": archive_details,
                    },
                )
            except Exception:
                pass

        except Exception as exc:
            st.error(f"Archive discovery failed: {exc}")


st.subheader("MAST Preview Products")
st.caption("Load a few representative public quick-look products from MAST.")

if st.button("Show MAST previews"):
    with st.spinner("Loading representative MAST previews..."):
        try:
            previews = get_mast_preview_products(ra, dec, discovery_radius)

            if not previews:
                st.info("No MAST quick-look JPG/PNG preview products were found for this coordinate.")
            else:
                pcols = st.columns(min(3, len(previews)))

                for i, item in enumerate(previews):
                    col = pcols[i % len(pcols)]
                    uri = item["dataURI"]
                    download_url = (
                        "https://mast.stsci.edu/api/v0.1/Download/file?uri="
                        + requests.utils.quote(uri, safe=":")
                    )

                    try:
                        rr = requests.get(download_url, timeout=60)
                        rr.raise_for_status()
                        img = Image.open(io.BytesIO(rr.content))
                        col.image(
                            img,
                            caption=item.get("filename", "MAST preview"),
                            use_container_width=True,
                        )
                    except Exception as exc:
                        col.warning(
                            f"Preview unavailable: {item.get('filename', 'unknown')}"
                        )

        except Exception as exc:
            st.error(f"MAST preview lookup failed: {exc}")


st.divider()
st.subheader("Multi-band Analysis")

if st.button("Acquire + Analyze", type="primary"):
    try:
        storage = build_storage(storage_backend, storage_bucket, storage_prefix)
    except Exception as exc:
        storage = None
        st.warning(f"Analysis will run, but storage is not configured: {exc}")

    st.subheader(f"{name} — {mode}")
    st.write(f"**RA:** {ra:.6f}°   **Dec:** {dec:.6f}°")

    cols = st.columns(4)

    try:
        sdss_bytes = get_sdss_jpeg(ra, dec, fov)
        sdss = Image.open(io.BytesIO(sdss_bytes)).convert("L")
        cols[0].image(sdss, caption="SDSS optical", use_container_width=True)
        if storage is not None:
            storage.save_bytes(
                f"targets/{name}/sdss.jpg",
                sdss_bytes,
                "image/jpeg",
            )
    except Exception as exc:
        cols[0].error(f"SDSS unavailable: {exc}")

    band_data = {}

    for col, band in zip(cols[1:], ["J", "H", "K"]):
        try:
            data = get_2mass(ra, dec, band, fov)
            band_data[band] = data

            if data is None:
                col.warning(f"2MASS {band} unavailable")
                continue

            display = normalize_image(data)
            col.image(display, caption=f"2MASS {band}", use_container_width=True)

            if storage is not None:
                png = Image.fromarray(display)
                buf = io.BytesIO()
                png.save(buf, format="PNG")
                storage.save_bytes(
                    f"targets/{name}/2mass_{band}.png",
                    buf.getvalue(),
                    "image/png",
                )

        except Exception as exc:
            band_data[band] = None
            col.error(f"2MASS {band} error: {exc}")

    st.divider()

    if mode == "Morphology region":
        st.subheader("Local background asymmetry")
        rows = []

        for band in ["J", "H", "K"]:
            data = band_data.get(band)
            if data is None:
                continue

            sectors, frac, flag = sector_asymmetry(data)
            bright = sectors.loc[sectors["median"].idxmax(), "sector"]
            faint = sectors.loc[sectors["median"].idxmin(), "sector"]

            rows.append(
                {
                    "band": band,
                    "fractional_sector_range": frac,
                    "brightest_sector": bright,
                    "faintest_sector": faint,
                    "asymmetry_flag": flag,
                }
            )

        if rows:
            result_df = pd.DataFrame(rows)
            st.dataframe(result_df, use_container_width=True)

            if storage is not None:
                storage.save_json(
                    f"targets/{name}/analysis.json",
                    {
                        "target_name": name,
                        "mode": mode,
                        "ra_deg": ra,
                        "dec_deg": dec,
                        "field_of_view_arcmin": fov,
                        "morphology": rows,
                    },
                )
        else:
            st.info("No usable 2MASS data for morphology analysis.")

    else:
        st.subheader("Point-source mode")
        st.info(
            "FORGE currently provides centered multi-band context here. "
            "Catalog colors and calibrated point-source photometry are the next integration."
        )

        if storage is not None:
            storage.save_json(
                f"targets/{name}/analysis.json",
                {
                    "target_name": name,
                    "mode": mode,
                    "ra_deg": ra,
                    "dec_deg": dec,
                    "field_of_view_arcmin": fov,
                },
            )


st.divider()
st.caption(
    "FORGE web app v0.3.1 — archive discovery + MAST previews + portable storage + multi-band analysis."
)
