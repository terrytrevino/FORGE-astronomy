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
from suggested_targets import suggest_compact_stars, suggest_compact_star_catalogs, suggest_morphology_regions
from spectroscopy import fetch_sdss_spectrum, spectrum_dataframe, spectrum_figure

st.set_page_config(page_title="FORGE Orion", layout="wide")


st.markdown(
        """
        <style>
        html, body, [data-testid="stAppViewContainer"], .stApp {
            background:
                radial-gradient(circle at 18% 22%, rgba(90,110,255,0.24) 0%, rgba(90,110,255,0.00) 20%),
                radial-gradient(circle at 78% 30%, rgba(120,70,220,0.22) 0%, rgba(120,70,220,0.00) 22%),
                radial-gradient(circle at 62% 70%, rgba(70,140,255,0.18) 0%, rgba(70,140,255,0.00) 24%),
                radial-gradient(circle at 35% 78%, rgba(180,90,120,0.16) 0%, rgba(180,90,120,0.00) 20%),
                linear-gradient(180deg, #06101b 0%, #081423 35%, #091827 100%) !important;
            background-attachment: fixed !important;
            color: #e8eef7 !important;
        }

        [data-testid="stAppViewContainer"] > .main {
            background: transparent !important;
        }

        .block-container {
            background: rgba(8, 15, 28, 0.72);
            border: 1px solid rgba(180, 210, 255, 0.10);
            border-radius: 18px;
            padding: 1.5rem 1.5rem 2rem 1.5rem;
            backdrop-filter: blur(6px);
        }

        section[data-testid="stSidebar"] {
            background: rgba(6, 12, 22, 0.92);
            border-right: 1px solid rgba(180, 210, 255, 0.08);
        }

        h1, h2, h3 {
            color: #f2f6fb;
        }

        div[data-testid="stExpander"],
        div[data-testid="stDataFrame"],
        div[data-testid="stTable"] {
            background: rgba(12, 20, 34, 0.55);
            border-radius: 12px;
        }

        .stButton > button {
            border-radius: 10px;
            border: 1px solid rgba(190, 220, 255, 0.18);
            background: rgba(20, 32, 54, 0.88);
            color: #edf4ff;
        }

        .stButton > button:hover {
            border-color: rgba(130, 180, 255, 0.40);
            background: rgba(28, 42, 68, 0.96);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )



# FORGE_HIGH_CONTRAST_UI
st.markdown(
    """
    <style>
    /* Inactive and active tabs */
    button[data-baseweb="tab"] {
        color: #DDE7F5 !important;
        font-weight: 600 !important;
    }
    button[data-baseweb="tab"][aria-selected="false"] {
        color: #C7D4E8 !important;
        opacity: 1 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #FFFFFF !important;
    }

    /* Stronger section dividers */
    hr {
        border: none !important;
        border-top: 1px solid rgba(180, 205, 240, 0.42) !important;
        margin-top: 1rem !important;
        margin-bottom: 1rem !important;
    }

    /* Input/select visual boundaries */
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextInput"] input {
        border: 1px solid rgba(185, 210, 245, 0.48) !important;
        background-color: #0F1D30 !important;
    }

    /* File uploader */
    section[data-testid="stFileUploaderDropzone"] {
        border: 1.5px solid rgba(185, 210, 245, 0.55) !important;
        background-color: rgba(15, 29, 48, 0.88) !important;
    }
    section[data-testid="stFileUploaderDropzone"] small,
    section[data-testid="stFileUploaderDropzone"] span {
        color: #D4DEEC !important;
        opacity: 1 !important;
    }

    /* All standard buttons get a visible boundary */
    .stButton > button,
    .stDownloadButton > button {
        border: 1.5px solid rgba(190, 215, 250, 0.62) !important;
        background-color: #142742 !important;
        color: #F4F8FD !important;
        font-weight: 600 !important;
    }
    .stButton > button:hover,
    .stDownloadButton > button:hover {
        border-color: #9FC2FF !important;
        background-color: #1B355A !important;
    }

    /* Expanders and dataframe boundaries */
    details[data-testid="stExpander"],
    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(175, 200, 235, 0.34) !important;
        border-radius: 10px !important;
    }

    /* Secondary/help text */
    [data-testid="stCaptionContainer"],
    [data-testid="stMarkdownContainer"] small {
        color: #C7D3E5 !important;
        opacity: 1 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# FORGE_SIDEBAR_SELECT_CONTRAST
st.markdown(
    """
    <style>
    /* Sidebar dropdown/select boxes */
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background-color: #13263F !important;
        border: 1.8px solid #8FB3E8 !important;
        border-radius: 8px !important;
        color: #F6F9FD !important;
        min-height: 2.45rem !important;
        box-shadow: 0 0 0 1px rgba(143,179,232,0.10) !important;
    }

    section[data-testid="stSidebar"] div[data-baseweb="select"] span {
        color: #F6F9FD !important;
        opacity: 1 !important;
    }

    section[data-testid="stSidebar"] div[data-baseweb="select"] svg {
        fill: #DDE9F8 !important;
        color: #DDE9F8 !important;
    }

    /* Dropdown popup menu */
    div[data-baseweb="popover"] ul {
        background-color: #102039 !important;
        border: 1.5px solid #789DCE !important;
    }

    div[data-baseweb="popover"] li {
        color: #F1F6FC !important;
        background-color: #102039 !important;
    }

    div[data-baseweb="popover"] li:hover,
    div[data-baseweb="popover"] li[aria-selected="true"] {
        background-color: #1B3A61 !important;
        color: #FFFFFF !important;
    }

    /* Sidebar labels above controls */
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
        color: #E7EEF8 !important;
        opacity: 1 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

SDSS_URL = "https://skyserver.sdss.org/dr17/SkyServerWS/ImgCutout/getjpeg"
SURVEYS = {"J": "2MASS-J", "H": "2MASS-H", "K": "2MASS-K"}

KNOWN_TARGETS = {
    "target_01": {"ra": 83.806016, "dec": -5.394502, "label": "APOGEE / Orion reference"},
    "target_02": {"ra": 83.833500, "dec": -5.427083, "label": "APOGEE / Orion reference"},
    "target_03": {"ra": 83.809458, "dec": -5.406833, "label": "APOGEE / Orion reference"},
}


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



st.markdown(
    """
    <div style="
        padding: 2.2rem 2.4rem 2rem 2.4rem;
        border-radius: 22px;
        margin-bottom: 1.2rem;
        border: 1px solid rgba(140,170,255,0.18);
        background:
            radial-gradient(circle at 18% 35%, rgba(100,120,255,0.24), transparent 24%),
            radial-gradient(circle at 78% 28%, rgba(130,80,220,0.20), transparent 26%),
            radial-gradient(circle at 58% 82%, rgba(70,150,255,0.14), transparent 30%),
            linear-gradient(135deg, #09111d 0%, #0c1b30 55%, #111827 100%);
    ">
      <div style="font-size:2.3rem;font-weight:700;color:#f3f7fb;margin-bottom:0.35rem;">
        FORGE Astronomy
      </div>
      <div style="font-size:1.02rem;color:#c8d3e3;margin-bottom:0.75rem;">
        Field Observation, Retrieval, Generation, and Evaluation
      </div>
      <div style="font-size:0.95rem;color:#9fb2cc;max-width:900px;">
        Multi-wavelength archive discovery, target selection, spectroscopy, morphology,
        and reproducible astronomical analysis.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

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

    # Build a persistent target menu from references + saved project targets.
    saved_targets = []
    try:
        _storage_for_menu = build_storage(storage_backend, storage_bucket, storage_prefix)
        saved_targets = _storage_for_menu.list_targets()
    except Exception:
        pass

    target_choices = ["New target"] + list(KNOWN_TARGETS.keys())
    for t in saved_targets:
        if t not in target_choices:
            target_choices.append(t)

    selected_target = st.selectbox("Saved / reference target", target_choices)

    default_name = "candidate_01"
    default_ra = 84.040452
    default_dec = -5.739921

    if selected_target in KNOWN_TARGETS:
        default_name = selected_target
        default_ra = KNOWN_TARGETS[selected_target]["ra"]
        default_dec = KNOWN_TARGETS[selected_target]["dec"]
    elif selected_target != "New target":
        default_name = selected_target
        try:
            _saved = _storage_for_menu.load_json(f"targets/{selected_target}/analysis.json")
            default_ra = float(_saved.get("ra_deg", default_ra))
            default_dec = float(_saved.get("dec_deg", default_dec))
        except Exception:
            try:
                _saved = _storage_for_menu.load_json(f"targets/{selected_target}/archive_manifest.json")
                default_ra = float(_saved.get("ra_deg", default_ra))
                default_dec = float(_saved.get("dec_deg", default_dec))
            except Exception:
                pass

    mode = st.radio("Analysis mode", ["Point source", "Morphology region"])
    name = st.text_input("Target name", value=default_name)
    ra = st.number_input("RA (deg)", value=float(default_ra), format="%.6f")
    dec = st.number_input("Dec (deg)", value=float(default_dec), format="%.6f")
    fov = st.slider("Field of view (arcmin)", 2.0, 12.0, 6.0, 0.5)
    discovery_radius = st.slider("Archive search radius (arcsec)", 5, 180, 30, 5)

    st.divider()
    uploaded = st.file_uploader("Candidate CSV", type=["csv"])


if uploaded is not None:
    try:
        cdf = pd.read_csv(uploaded)
        st.subheader("Candidate list")
        st.dataframe(cdf, use_container_width=True)

        if {"target_id", "ra_deg", "dec_deg"}.issubset(cdf.columns):
            st.caption("Candidate coordinates are ready to promote into the saved target library after analysis.")
    except Exception as exc:
        st.warning(f"Could not read CSV: {exc}")



st.subheader("Suggested targets near current field")
st.caption(f"Center: RA {ra:.6f}, Dec {dec:.6f} · Search field: {fov:.1f} arcmin · Suggestions are generated from the currently selected target.")

suggest_tab1, suggest_tab2 = st.tabs(["Nearby compact stars", "Morphology regions"])

with suggest_tab1:
    if st.button("Suggest compact stars"):
        with st.spinner("Searching 2MASS and Gaia DR3 near the current field..."):
            two_df, gaia_df, two_note, gaia_note = suggest_compact_star_catalogs(
                ra, dec, radius_arcmin=max(3.0, fov), limit=8
            )

            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("**2MASS PSC candidates**")
                if two_note:
                    st.warning(two_note)
                if two_df.empty:
                    st.info("No 2MASS compact-star candidates found.")
                else:
                    st.dataframe(two_df, use_container_width=True)
                    st.download_button(
                        "Download 2MASS candidates",
                        two_df.to_csv(index=False).encode("utf-8"),
                        file_name="forge_2mass_compact_star_candidates.csv",
                        mime="text/csv",
                    )

            with col_b:
                st.markdown("**Gaia DR3 candidates**")
                if gaia_note:
                    st.warning(gaia_note)
                if gaia_df.empty:
                    st.info("No Gaia compact-star candidates found.")
                else:
                    st.dataframe(gaia_df, use_container_width=True)
                    st.download_button(
                        "Download Gaia candidates",
                        gaia_df.to_csv(index=False).encode("utf-8"),
                        file_name="forge_gaia_compact_star_candidates.csv",
                        mime="text/csv",
                    )

with suggest_tab2:
    if st.button("Suggest morphology regions"):
        with st.spinner("Finding high-gradient regions in 2MASS K..."):
            morph_df, morph_err = suggest_morphology_regions(
                ra, dec, fov_arcmin=max(6.0, fov), limit=8
            )
            if morph_err:
                st.error(f"Morphology search failed: {morph_err}")
            elif morph_df.empty:
                st.info("No morphology candidates found.")
            else:
                st.dataframe(morph_df, use_container_width=True)
                st.download_button(
                    "Download morphology candidates",
                    morph_df.to_csv(index=False).encode("utf-8"),
                    file_name="forge_morphology_candidates.csv",
                    mime="text/csv",
                )

st.divider()
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

st.subheader("Spectroscopy")
st.caption(
    "Check for a spectrum at the current coordinate, or use a known SDSS example "
    "to verify the plotting and line-marker workflow."
)

show_lines = st.checkbox("Show common line markers", value=True)

spec_tab1, spec_tab2 = st.tabs([
    "Current target spectrum",
    "Known SDSS demo spectrum",
])

with spec_tab1:
    st.write(
        "Search SDSS spectroscopy within 5 arcsec of the current RA/Dec. "
        "If no spectrum exists, FORGE will report that clearly."
    )

    if st.button("Plot current target spectrum", key="plot_current_spectrum"):
        with st.spinner("Checking SDSS spectroscopy..."):
            wave, flux, meta = fetch_sdss_spectrum(
                ra, dec, radius_arcsec=5.0
            )

            if wave is None:
                st.info(str(meta))
            else:
                fig = spectrum_figure(
                    wave,
                    flux,
                    show_lines=show_lines,
                )
                st.pyplot(fig, use_container_width=True)

                with st.expander("Spectrum metadata"):
                    st.json(meta)

                sdf = spectrum_dataframe(wave, flux)
                st.download_button(
                    "Download spectrum CSV",
                    sdf.to_csv(index=False).encode("utf-8"),
                    file_name=f"{name}_sdss_spectrum.csv",
                    mime="text/csv",
                    key="download_current_spectrum",
                )

with spec_tab2:
    st.write(
        "Use this known SDSS example to confirm that FORGE can retrieve, plot, "
        "label, and export a real spectrum even when the current target has no SDSS spectrum."
    )

    if st.button("Load known SDSS demo spectrum", key="load_demo_spectrum"):
        demo_ra = 2.02344596573482
        demo_dec = 14.8398237551311

        with st.spinner("Loading known SDSS demo spectrum..."):
            wave, flux, meta = fetch_sdss_spectrum(
                demo_ra,
                demo_dec,
                radius_arcsec=5.0,
            )

            if wave is None:
                st.error(str(meta))
            else:
                fig = spectrum_figure(
                    wave,
                    flux,
                    show_lines=show_lines,
                )
                st.pyplot(fig, use_container_width=True)

                with st.expander("Demo spectrum metadata"):
                    st.json(meta)

                sdf = spectrum_dataframe(wave, flux)
                st.download_button(
                    "Download demo spectrum CSV",
                    sdf.to_csv(index=False).encode("utf-8"),
                    file_name="forge_sdss_demo_spectrum.csv",
                    mime="text/csv",
                    key="download_demo_spectrum",
                )

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
    "FORGE web app v0.7 — parallel 2MASS/Gaia discovery + high-contrast dark UI + spectroscopy."
)
