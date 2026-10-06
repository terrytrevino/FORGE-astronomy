import io
from concurrent.futures import ThreadPoolExecutor, wait
import json
import numpy as np
import pandas as pd
import requests
import streamlit as st
from PIL import Image

import astropy.units as u
from astroquery.skyview import SkyView

from storage import Storage, StorageConfig
from archive_discovery import discover_archives, discover_mast, discover_sdss_spectra, discover_irsa, discover_alma, get_mast_preview_products, get_mast_spectrum_products
from suggested_targets import suggest_compact_stars, suggest_compact_star_catalogs, suggest_morphology_regions
from spectroscopy import fetch_sdss_spectrum, spectrum_dataframe, spectrum_figure, fetch_apogee_spectrum, apogee_spectrum_figure, apogee_feature_guide, apogee_quality_summary, fetch_mast_spectrum_product, generic_spectrum_figure
from radio_historical import discover_dss, discover_dasch, discover_nrao, discover_casda, get_dss_preview, classify_radio_spectral_candidates
from name_resolver import resolve_object_name

st.set_page_config(page_title="FORGE Orion", layout="wide")


st.markdown(
        """
        <style>
        html, body, [data-testid="stAppViewContainer"], .stApp {
            background-color: #050b14 !important;
            color: #dfe8f3 !important;
            font-family: "Avenir Next", "Segoe UI", "Helvetica Neue", Arial, sans-serif !important;
        }

        [data-testid="stAppViewContainer"] {
            position: relative !important;
            background:
                radial-gradient(circle at 12% 18%, rgba(255,255,255,0.95) 0 1px, transparent 1.8px),
                radial-gradient(circle at 33% 12%, rgba(210,225,255,0.90) 0 1px, transparent 1.7px),
                radial-gradient(circle at 58% 21%, rgba(255,255,255,0.86) 0 1.2px, transparent 1.9px),
                radial-gradient(circle at 84% 16%, rgba(220,235,255,0.88) 0 1px, transparent 1.7px),
                radial-gradient(circle at 17% 55%, rgba(255,255,255,0.82) 0 1px, transparent 1.7px),
                radial-gradient(circle at 73% 62%, rgba(210,230,255,0.84) 0 1.1px, transparent 1.8px),
                radial-gradient(circle at 91% 76%, rgba(255,255,255,0.80) 0 1px, transparent 1.7px),
                radial-gradient(circle at 41% 86%, rgba(230,240,255,0.82) 0 1px, transparent 1.7px),
                radial-gradient(ellipse at 20% 32%, rgba(66,105,210,0.35) 0%, rgba(66,105,210,0.10) 22%, transparent 45%),
                radial-gradient(ellipse at 78% 28%, rgba(130,72,190,0.30) 0%, rgba(130,72,190,0.08) 24%, transparent 46%),
                radial-gradient(ellipse at 58% 76%, rgba(40,130,180,0.25) 0%, rgba(40,130,180,0.06) 25%, transparent 48%),
                linear-gradient(180deg, #040912 0%, #071426 45%, #08111d 100%) !important;
            background-attachment: fixed !important;
            background-size:
                180px 180px,
                230px 230px,
                290px 290px,
                340px 340px,
                260px 260px,
                310px 310px,
                370px 370px,
                410px 410px,
                cover, cover, cover, cover !important;
        }

        [data-testid="stAppViewContainer"] > .main {
            background: transparent !important;
        }

        .block-container {
            background: rgba(6, 12, 22, 0.28) !important;
            border: 1px solid rgba(180, 210, 255, 0.28) !important;
            border-radius: 18px;
            padding: 1.5rem 1.5rem 2rem 1.5rem;
            backdrop-filter: blur(1.5px);
            box-shadow: 0 10px 35px rgba(0,0,0,0.14);
        }

        section[data-testid="stSidebar"] {
            background: rgba(6, 12, 22, 0.58) !important;
            border-right: 1px solid rgba(180, 210, 255, 0.18);
            backdrop-filter: blur(4px);
        }

        h1, h2, h3 {
            color: #eaf1f8;
            letter-spacing: 0.01em;
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
        color: #E8F0F8 !important;
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
        color: #BFCDE0 !important;
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



# FORGE_MOBILE_LAYOUT
st.markdown(
    """
    <style>
    /* Improve readability and stacking on phones / narrow browser windows. */
    @media (max-width: 780px) {
        .block-container {
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
            border-radius: 12px !important;
        }

        .stButton > button,
        .stDownloadButton > button {
            width: 100% !important;
            min-height: 2.7rem !important;
        }

        [data-testid="stDataFrame"] {
            overflow-x: auto !important;
        }

        h1 { font-size: 1.75rem !important; }
        h2 { font-size: 1.35rem !important; }
        h3 { font-size: 1.12rem !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# FORGE_TRANSPARENT_SURFACES
st.markdown(
    """
    <style>
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"],
    [data-testid="stVerticalBlock"],
    [data-testid="stElementContainer"] {
        background: transparent !important;
    }

    section[data-testid="stSidebar"] > div {
        background: transparent !important;
    }

    /* Keep individual controls readable while allowing the page background through */
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div,
    section[data-testid="stFileUploaderDropzone"],
    details[data-testid="stExpander"],
    div[data-testid="stDataFrame"] {
        background-color: rgba(15, 29, 48, 0.88) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

SDSS_URL = "https://skyserver.sdss.org/dr17/SkyServerWS/ImgCutout/getjpeg"
SURVEYS = {"J": "2MASS-J", "H": "2MASS-H", "K": "2MASS-K"}

KNOWN_TARGETS = {
    "target_01": {"ra": 83.806016, "dec": -5.394502, "label": "APOGEE / Orion reference", "apogee_id": "2M05351344-0523402"},
    "target_02": {"ra": 83.833500, "dec": -5.427083, "label": "APOGEE / Orion reference", "apogee_id": "2M05352004-0525375"},
    "target_03": {"ra": 83.809458, "dec": -5.406833, "label": "APOGEE / Orion reference", "apogee_id": "2M05351427-0524246"},
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
    <style>
    .forge-hero {
        position: relative;
        min-height: 330px;
        border-radius: 22px;
        overflow: hidden;
        margin-bottom: 0.55rem;
        border: 1px solid rgba(180,210,255,0.30);
        background-image:
            linear-gradient(90deg, rgba(2,7,15,0.86) 0%, rgba(2,7,15,0.58) 43%, rgba(2,7,15,0.18) 100%),
            linear-gradient(0deg, rgba(2,7,15,0.56) 0%, rgba(2,7,15,0.05) 58%),
            url("https://science.nasa.gov/wp-content/uploads/2023/04/orion-nebula-xlarge_web-jpg.webp");
        background-size: cover;
        background-position: center 48%;
        box-shadow: 0 14px 42px rgba(0,0,0,0.34);
    }

    .forge-hero-content {
        position: absolute;
        left: 2.3rem;
        bottom: 2.0rem;
        max-width: 760px;
        padding-right: 1.5rem;
        text-shadow: 0 2px 12px rgba(0,0,0,0.82);
    }

    .forge-hero-title {
        font-family: "Avenir Next", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
        font-size: 2.55rem;
        line-height: 1.02;
        font-weight: 650;
        color: #edf4fb;
        margin-bottom: 0.45rem;
        letter-spacing: 0.085em;
        text-transform: uppercase;
    }

    .forge-hero-subtitle {
        font-size: 1.03rem;
        color: #d6e2ef;
        margin-bottom: 0.72rem;
        font-weight: 520;
        letter-spacing: 0.025em;
    }

    .forge-hero-tagline {
        font-size: 0.98rem;
        line-height: 1.5;
        color: #c6d5e6;
        max-width: 700px;
    }

    .forge-hero-credit {
        margin: 0.15rem 0 1.15rem 0;
        font-size: 0.72rem;
        color: #aebed3;
        opacity: 0.92;
        text-align: right;
    }

    @media (max-width: 780px) {
        .forge-hero {
            min-height: 300px;
            background-position: 48% center;
        }
        .forge-hero-content {
            left: 1.25rem;
            bottom: 1.35rem;
            padding-right: 1rem;
        }
        .forge-hero-title {
            font-size: 2rem;
        }
    }
    </style>

    <div class="forge-hero" role="img" aria-label="Hubble mosaic of the Orion Nebula, M42">
      <div class="forge-hero-content">
        <div class="forge-hero-title">FORGE Astronomy</div>
        <div class="forge-hero-subtitle">
          Field Observation, Retrieval, Generation, and Evaluation
        </div>
        <div class="forge-hero-tagline">
          One coordinate → many archives → imaging, spectra, morphology, history, and reproducible evidence.
        </div>
      </div>
    </div>
    <div class="forge-hero-credit">
      M42 — Hubble Space Telescope Orion Treasury mosaic ·
      NASA / ESA / M. Robberto (STScI/ESA) / HST Orion Treasury Project Team
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

    # Keep editable target state synchronized when the saved/reference target changes.
    if st.session_state.get("forge_selected_target_prev") != selected_target:
        st.session_state["forge_target_name"] = default_name
        st.session_state["forge_ra"] = float(default_ra)
        st.session_state["forge_dec"] = float(default_dec)
        st.session_state["forge_selected_target_prev"] = selected_target

    st.markdown("**Resolve astronomical name**")
    resolver_query = st.text_input(
        "Object name or catalog ID",
        placeholder="e.g., Betelgeuse, M42, θ1 Ori C, NGC 2024",
        key="forge_resolver_query",
    )

    if st.button("Resolve name", key="forge_resolve_name"):
        with st.spinner("Resolving object name..."):
            st.session_state["forge_resolved_object"] = resolve_object_name(resolver_query)

    resolved = st.session_state.get("forge_resolved_object")
    if resolved:
        if resolved.get("status") == "OK":
            canonical = resolved.get("canonical_name") or resolved.get("input_name")
            otype = resolved.get("object_type") or "object"
            st.caption(
                f"Resolved: {canonical} · {otype} · "
                f"RA {resolved['ra_deg']:.6f}°, Dec {resolved['dec_deg']:.6f}° "
                f"({resolved.get('resolver', 'resolver')})"
            )
            if st.button("Use resolved object", key="forge_use_resolved"):
                st.session_state["forge_target_name"] = str(canonical)
                st.session_state["forge_ra"] = float(resolved["ra_deg"])
                st.session_state["forge_dec"] = float(resolved["dec_deg"])
                st.success("Resolved coordinates loaded into the FORGE target.")
        else:
            st.warning(resolved.get("message", "Object name could not be resolved."))

    mode = st.radio("Analysis mode", ["Point source", "Morphology region"])
    name = st.text_input("Target name", key="forge_target_name")
    ra = st.number_input("RA (deg)", format="%.6f", key="forge_ra")
    dec = st.number_input("Dec (deg)", format="%.6f", key="forge_dec")
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



st.subheader("Explore Nearby Targets & Structure")
st.caption(
    f"Optional follow-up after choosing a target · Center: RA {ra:.6f}, Dec {dec:.6f} · "
    f"Search field: {fov:.1f} arcmin. Discover nearby stars or interesting cloud structure."
)

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

if st.button("Search All Archives", type="primary"):
    st.info(
        "FORGE is querying the integrated archives in parallel. "
        "Slow services will not block the entire search; partial results are kept."
    )

    from astropy.coordinates import SkyCoord

    coord = SkyCoord(
        ra=float(ra) * u.deg,
        dec=float(dec) * u.deg,
        frame="icrs",
    )
    radius = float(discovery_radius) * u.arcsec
    sdss_radius = min(float(discovery_radius), 180.0) * u.arcsec

    jobs = {
        "MAST": lambda: discover_mast(coord, radius),
        "SDSS spectroscopy": lambda: discover_sdss_spectra(coord, sdss_radius),
        "IRSA": lambda: discover_irsa(coord, radius),
        "ALMA": lambda: discover_alma(coord, radius),
        "DSS / photographic plates": lambda: discover_dss(
            ra, dec, radius_arcmin=max(6.0, fov)
        ),
        "Harvard DASCH": lambda: discover_dasch(ra, dec),
    }

    progress = st.progress(0, text="Starting archive queries...")
    status_box = st.empty()

    executor = ThreadPoolExecutor(max_workers=len(jobs))
    future_map = {
        executor.submit(func): label
        for label, func in jobs.items()
    }

    done, not_done = wait(list(future_map.keys()), timeout=65)

    all_results = []
    completed = 0

    for future in done:
        label = future_map[future]
        try:
            result = future.result()
        except Exception as exc:
            result = {
                "archive": label,
                "status": "ERROR",
                "count": 0,
                "summary": str(exc),
                "details": [],
            }

        all_results.append(result)
        completed += 1
        progress.progress(
            min(completed / len(jobs), 1.0),
            text=f"Completed {completed} of {len(jobs)} archive queries",
        )

    for future in not_done:
        label = future_map[future]
        future.cancel()
        all_results.append({
            "archive": label,
            "status": "TIMEOUT",
            "count": 0,
            "summary": (
                "Archive did not complete within the unified FORGE search window. "
                "Other archive results are shown normally."
            ),
            "details": [],
        })

    executor.shutdown(wait=False, cancel_futures=True)

    preferred_order = {
        "MAST": 0,
        "SDSS spectroscopy": 1,
        "IRSA": 2,
        "ALMA": 3,
        "DSS / photographic plates": 4,
        "Harvard DASCH": 5,
    }
    all_results.sort(
        key=lambda x: preferred_order.get(x.get("archive", ""), 99)
    )

    progress.progress(1.0, text="Unified archive search complete")
    status_box.success(
        f"Returned results from {len(done)} of {len(jobs)} archive services "
        f"within the search window."
    )

    all_manifest = pd.DataFrame([
        {
            "archive": item.get("archive", ""),
            "status": item.get("status", ""),
            "count": item.get("count", 0),
            "summary": item.get("summary", ""),
        }
        for item in all_results
    ])

    st.dataframe(all_manifest, use_container_width=True)

    successful_records = int(
        sum(
            int(item.get("count", 0) or 0)
            for item in all_results
            if str(item.get("status", "")).upper() == "OK"
        )
    )
    st.caption(
        f"{successful_records} returned records/layers across completed archive queries. "
        "Counts are archive-specific and are not unique astrophysical-object counts."
    )

    detail_columns = {
        "MAST": ["mission", "count"],
        "SDSS spectroscopy": ["ra", "dec", "plate", "mjd", "fiberID"],
        "IRSA": ["catalog", "count"],
        "ALMA": ["target_name", "band_list", "s_resolution"],
        "DSS / photographic plates": ["survey", "available"],
        "Harvard DASCH": ["series", "platenum", "date", "datetime", "exptime", "scanned"],
        "NRAO radio": [
            "target_name",
            "instrument_name",
            "dataproduct_type",
            "freq_min",
            "freq_max",
            "nums_channels",
            "spectral_resolutions",
        ],
    }

    for item in all_results:
        with st.expander(
            f"{item.get('archive', 'Archive')} — {item.get('summary', '')}"
        ):
            details = item.get("details") or []
            if not details:
                st.write("No additional records.")
                continue

            try:
                ddf = pd.DataFrame(details)
                wanted = [
                    col for col in detail_columns.get(item.get("archive", ""), [])
                    if col in ddf.columns
                ]
                compact = ddf[wanted].head(12) if wanted else ddf.head(12)
                st.dataframe(compact, use_container_width=True)

                if len(ddf) > len(compact):
                    st.caption(
                        f"Showing {len(compact)} representative row(s) from "
                        f"{len(ddf)} returned detail row(s)."
                    )

                with st.expander("Advanced raw metadata"):
                    st.json(details)
            except Exception:
                st.json(details)

    try:
        storage = build_storage(
            storage_backend, storage_bucket, storage_prefix
        )
        storage.save_json(
            f"targets/{name}/all_archive_manifest.json",
            {
                "target_name": name,
                "ra_deg": ra,
                "dec_deg": dec,
                "radius_arcsec": discovery_radius,
                "archives": all_results,
            },
        )
    except Exception:
        pass

st.caption(
    "Search All Archives runs the fast, reliable observation-archive adapters integrated in FORGE. "
    "NRAO radio is intentionally handled as a separate Deep Radio Search because its external TAP service "
    "can be slow or unavailable. Gaia and 2MASS source-catalog matching are handled separately under "
    "Suggested targets / source identity."
)

with st.expander("Advanced archive controls"):
    st.caption(
        "Use this only when you want to rerun the original core subset "
        "(MAST, SDSS spectroscopy, IRSA, and ALMA) separately."
    )
    if st.button("Discover core archives", type="secondary"):
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


st.subheader("Historical + Radio Discovery")
st.caption(
    "Explore how this field appears across time and radio wavelength regimes."
)

hist_tab, radio_tab = st.tabs(["Historical sky", "Radio archives"])

with hist_tab:
    st.write(
        "Check photographic-survey coverage and compare historical optical imagery "
        "with a modern optical view when available."
    )

    if st.button("Discover historical sky", use_container_width=True, key="discover_historical_sky"):
        with st.spinner("Checking DSS / DSS2 and Harvard DASCH..."):
            dss_result = discover_dss(ra, dec, radius_arcmin=max(6.0, fov))
            dasch_result = discover_dasch(ra, dec)

            hist_df = pd.DataFrame([
                {
                    "archive": dss_result["archive"],
                    "status": dss_result["status"],
                    "count": dss_result["count"],
                    "summary": dss_result["summary"],
                },
                {
                    "archive": dasch_result["archive"],
                    "status": dasch_result["status"],
                    "count": dasch_result["count"],
                    "summary": dasch_result["summary"],
                },
            ])
            st.dataframe(hist_df, use_container_width=True)

            h1, h2 = st.columns(2, gap="medium")
            with h1:
                with st.expander("DSS / DSS2 coverage"):
                    st.json(dss_result.get("details", []))
            with h2:
                with st.expander("DASCH plate exposures"):
                    st.json(dasch_result.get("details", []))

            st.markdown("**Then vs. Now**")
            dss_img, dss_err = get_dss_preview(
                ra,
                dec,
                survey="DSS2 Red",
                radius_arcmin=max(6.0, fov),
                pixels=512,
            )

            if dss_img is not None:
                dss_display = normalize_image(dss_img)
                then_col, now_col = st.columns(2, gap="medium")
                then_col.image(
                    dss_display,
                    caption="Then — DSS2 Red photographic survey",
                    use_container_width=True,
                )

                try:
                    sdss_bytes_hist = get_sdss_jpeg(ra, dec, fov)
                    sdss_hist = Image.open(io.BytesIO(sdss_bytes_hist)).convert("L")
                    now_col.image(
                        sdss_hist,
                        caption="Now — SDSS optical",
                        use_container_width=True,
                    )
                except Exception:
                    now_col.info(
                        "No SDSS comparison image was returned for this field."
                    )

                st.caption(
                    "Historical and modern panels are independently calibrated survey products. "
                    "Compare structure and context rather than raw brightness."
                )
            else:
                st.info(
                    f"DSS2 image preview unavailable for this field: {dss_err}"
                )

with radio_tab:
    st.write(
        "Search radio and millimeter archives for continuum, spectral-line, and "
        "interferometric observations associated with the current field."
    )

    rp1, rp2, rp3 = st.columns(3, gap="medium")
    with rp1:
        st.markdown("**ALMA**")
        st.caption("Integrated in the main archive search for millimeter/submillimeter observations.")
    with rp2:
        st.markdown("**ASKAP / CASDA**")
        st.caption("Live public-radio search available directly in FORGE.")
    with rp3:
        st.markdown("**LOFAR / MeerKAT / NRAO**")
        st.caption("Partner archive pathways plus an extended NRAO specialist search.")

    st.markdown(
        """
        <div style="display:flex;gap:0.6rem;flex-wrap:wrap;margin:0.35rem 0 0.9rem 0;">
          <a href="https://vo.astron.nl/browse/__system__/tap" target="_blank"
             style="text-decoration:none;padding:0.45rem 0.75rem;border:1px solid rgba(180,210,255,0.35);
                    border-radius:9px;color:#eef5ff;background:rgba(20,32,54,0.78);">
             ASTRON / LOFAR VO
          </a>
          <a href="https://research.csiro.au/casda/" target="_blank"
             style="text-decoration:none;padding:0.45rem 0.75rem;border:1px solid rgba(180,210,255,0.35);
                    border-radius:9px;color:#eef5ff;background:rgba(20,32,54,0.78);">
             CASDA / ASKAP
          </a>
          <a href="https://archive.sarao.ac.za/" target="_blank"
             style="text-decoration:none;padding:0.45rem 0.75rem;border:1px solid rgba(180,210,255,0.35);
                    border-radius:9px;color:#eef5ff;background:rgba(20,32,54,0.78);">
             MeerKAT Archive
          </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    radio_a, radio_b = st.columns(2, gap="large")

    with radio_a:
        st.markdown("**ASKAP / CASDA**")
        st.caption("Fast public ASKAP product discovery.")
        if st.button("Search ASKAP / CASDA", use_container_width=True, key="search_casda_radio"):
            with st.spinner("Querying CSIRO ASKAP Science Data Archive..."):
                casda_result = discover_casda(
                    ra,
                    dec,
                    radius_arcmin=max(5.0, discovery_radius / 60.0),
                    max_rows=20,
                )
                st.dataframe(
                    pd.DataFrame([{
                        "archive": casda_result["archive"],
                        "status": casda_result["status"],
                        "count": casda_result["count"],
                        "summary": casda_result["summary"],
                    }]),
                    use_container_width=True,
                )
                cdetails = casda_result.get("details", [])
                if cdetails:
                    cdf = pd.DataFrame(cdetails)
                    cols = [
                        col for col in [
                            "target_name",
                            "dataproduct_type",
                            "dataproduct_subtype",
                            "obs_collection",
                            "filename",
                        ] if col in cdf.columns
                    ]
                    st.dataframe(
                        cdf[cols].head(15) if cols else cdf.head(15),
                        use_container_width=True,
                    )
                    with st.expander("Advanced ASKAP metadata"):
                        st.json(cdetails)

    with radio_b:
        st.markdown("**Extended NRAO**")
        st.caption(
            "Best-effort VLA / VLBA / GBT metadata search. This external service can time out."
        )
        if st.button("Run extended NRAO search", use_container_width=True, key="search_extended_nrao"):
            with st.spinner("Querying NRAO VLA / VLBA / GBT metadata..."):
                nrao_result = discover_nrao(
                    ra,
                    dec,
                    radius_arcmin=max(1.0, discovery_radius / 60.0),
                    max_rows=20,
                    attempts=2,
                    read_timeout=45,
                )

                st.dataframe(
                    pd.DataFrame([{
                        "archive": nrao_result["archive"],
                        "status": nrao_result["status"],
                        "count": nrao_result["count"],
                        "summary": nrao_result["summary"],
                    }]),
                    use_container_width=True,
                )

                details = nrao_result.get("details", [])
                if details:
                    with st.expander("Radio observation details"):
                        st.json(details)

                    triage_df = classify_radio_spectral_candidates(details)
                    if not triage_df.empty:
                        st.markdown("**Spectral-line capability triage**")
                        st.caption(
                            "Metadata-based ranking only. A likely-spectral label means the dataset "
                            "looks suitable for line analysis; it does not confirm a detected line."
                        )
                        st.dataframe(triage_df, use_container_width=True)


st.divider()
with st.expander("Discovery Lens — why this field may be worth exploring", expanded=False):
    st.write(
        "FORGE is built to keep the visual and physical context connected. "
        "A rich field may be interesting because multiple archives overlap, because morphology changes "
        "with wavelength, because a real spectrum is available, or because historical and radio coverage "
        "exist at the same coordinates."
    )
    st.caption(
        "Use archive previews and source links as evidence-bearing context rather than decoration. "
        "When a MAST/JWST/HST preview is available, the image remains tied to its archive product and provenance."
    )

st.divider()
st.subheader("Spectroscopy")
st.caption(
    "Check for a spectrum at the current coordinate, or use a known SDSS example "
    "to verify the plotting and line-marker workflow."
)

show_lines = st.checkbox("Show common line markers", value=True)

spec_tab1, spec_tab2, spec_tab3, spec_tab4 = st.tabs([
    "Current SDSS spectrum",
    "Current APOGEE spectrum",
    "MAST spectra",
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
        "Retrieve a real APOGEE DR17 combined H-band spectrum for the current target "
        "when an APOGEE match exists."
    )

    if st.button("Plot current APOGEE spectrum", key="plot_current_apogee_spectrum"):
        with st.spinner("Checking APOGEE DR17 and loading the combined H-band spectrum..."):
            known_apogee_id = None
            if selected_target in KNOWN_TARGETS:
                known_apogee_id = KNOWN_TARGETS[selected_target].get("apogee_id")

            wave, flux, meta = fetch_apogee_spectrum(
                apogee_id=known_apogee_id,
                ra_deg=ra,
                dec_deg=dec,
            )

            if wave is None:
                st.info(str(meta))
            else:
                quality = meta.get("_quality", {}) if isinstance(meta, dict) else {}
                fig = apogee_spectrum_figure(
                    wave,
                    flux,
                    show_lines=show_lines,
                    quality=quality,
                    show_quality=True,
                )
                st.pyplot(fig, use_container_width=True)

                st.caption(
                    "Dashed vertical markers identify representative APOGEE H-band atomic fingerprints. "
                    "X markers flag pipeline-bad pixels; open circles flag caution pixels affected by "
                    "sky/telluric/persistence-style warnings; triangles mark strong upward outliers that "
                    "are not pipeline-flagged and therefore deserve inspection rather than automatic interpretation."
                )

                with st.expander("What do these APOGEE fingerprints mean?", expanded=False):
                    st.write(
                        "APOGEE stellar spectra are usually dominated by absorption features. "
                        "Different atoms and molecules absorb at characteristic wavelengths, creating "
                        "a chemical fingerprint. Abundances such as [Fe/H] or [Mg/Fe] are derived by "
                        "fitting many features with stellar-atmosphere models; a deeper line by itself "
                        "does not mean a proportionally higher abundance."
                    )
                    st.dataframe(apogee_feature_guide(), use_container_width=True)

                with st.expander("Spectral quality: feature or artifact?", expanded=False):
                    st.write(
                        "A visible spike is not automatically an emission line. APOGEE supplies per-pixel "
                        "quality information that can identify cosmic rays, bad/saturated pixels, persistence, "
                        "sky-line contamination, and telluric contamination. FORGE overlays those warnings on "
                        "the plot. An unflagged upward outlier is only a candidate for follow-up: a credible "
                        "emission feature should align with a known transition, persist across neighboring pixels "
                        "or repeat observations, and survive uncertainty/quality checks."
                    )
                    st.dataframe(apogee_quality_summary(quality), use_container_width=True)

                with st.expander("APOGEE spectrum metadata"):
                    display_meta = (
                        {k: v for k, v in meta.items() if k != "_quality"}
                        if isinstance(meta, dict)
                        else meta
                    )
                    st.json(display_meta)

                sdf = spectrum_dataframe(wave, flux)
                st.download_button(
                    "Download APOGEE spectrum CSV",
                    sdf.to_csv(index=False).encode("utf-8"),
                    file_name=f"{name}_apogee_spectrum.csv",
                    mime="text/csv",
                    key="download_apogee_spectrum",
                )

with spec_tab3:
    st.write(
        "Search MAST near the current coordinate for public FITS spectral products "
        "and plot the first product FORGE can parse as a 1-D wavelength/flux spectrum."
    )

    if st.button("Find and plot MAST spectrum", key="plot_mast_spectrum"):
        with st.spinner("Searching MAST spectral products..."):
            products = get_mast_spectrum_products(
                ra, dec, radius_arcsec=discovery_radius, max_products=10
            )

            if not products:
                st.info("No candidate MAST FITS spectral products were found near this coordinate.")
            else:
                st.caption(f"{len(products)} candidate MAST spectral product(s) found.")
                plotted = False
                failures = []

                for product in products:
                    wave, flux, meta = fetch_mast_spectrum_product(product["dataURI"])
                    if wave is None:
                        failures.append({
                            "filename": product.get("filename", ""),
                            "error": meta.get("error", "Could not parse"),
                        })
                        continue

                    title = product.get("filename", "MAST spectrum")
                    fig = generic_spectrum_figure(
                        wave,
                        flux,
                        title=title,
                        show_lines=show_lines,
                    )
                    st.pyplot(fig, use_container_width=True)

                    with st.expander("MAST spectrum product metadata"):
                        st.json({**product, **meta})

                    sdf = spectrum_dataframe(wave, flux)
                    st.download_button(
                        "Download MAST spectrum CSV",
                        sdf.to_csv(index=False).encode("utf-8"),
                        file_name=f"{name}_mast_spectrum.csv",
                        mime="text/csv",
                        key="download_mast_spectrum",
                    )
                    plotted = True
                    break

                if not plotted:
                    st.warning(
                        "MAST spectral products were found, but none of the first candidates "
                        "could be parsed into a 1-D wavelength/flux spectrum."
                    )
                    with st.expander("MAST parsing attempts"):
                        st.json(failures)

with spec_tab4:
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
st.markdown(
    """
    <div style="padding:1rem 0 0.25rem 0;color:#b8c7da;font-size:0.83rem;line-height:1.55;">
      <strong style="color:#eef5ff;">FORGE Astronomy — Web v0.11 public alpha</strong><br>
      Field Observation, Retrieval, Generation, and Evaluation<br>
      Release checkpoint: October 2026<br>
      Co-developed by D. Terry Trevino and Vivian Hom ·
      <a href="https://github.com/terrytrevino/FORGE-astronomy" target="_blank" style="color:#cfe0ff;">source repository</a><br>
      Hero image: M42, Hubble Space Telescope Orion Treasury mosaic ·
      NASA / ESA / M. Robberto (STScI/ESA) / HST Orion Treasury Project Team<br>
      Archive imagery, spectra, and metadata remain attributed to their originating observatories and archives.
    </div>
    """,
    unsafe_allow_html=True,
)
