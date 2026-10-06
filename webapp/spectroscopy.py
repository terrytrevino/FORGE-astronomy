import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import astropy.units as u
from astropy.coordinates import SkyCoord
from astroquery.sdss import SDSS


COMMON_LINES = [
    ("Ca K", 3933.66),
    ("Ca H", 3968.47),
    ("Hδ", 4101.74),
    ("Hγ", 4340.47),
    ("Hβ", 4861.33),
    ("[O III]", 5006.84),
    ("Na D", 5892.0),
    ("Hα", 6562.80),
    ("[N II]", 6583.45),
    ("[S II]", 6716.44),
    ("[S II]", 6730.82),
]

# A deliberately small set of representative, published APOGEE H-band
# abundance-sensitive atomic lines. The full APOGEE/ASPCAP analysis uses
# many more atomic and molecular features plus stellar-atmosphere models.
APOGEE_REFERENCE_LINES = [
    ("K I", 15163.067),
    ("K I", 15168.376),
    ("Mg I", 15740.716),
    ("Mg I", 15748.886),
    ("Mg I", 15765.842),
    ("Si I", 15888.409),
    ("Si I", 15960.060),
    ("Ca I", 16150.763),
    ("Ca I", 16155.236),
    ("Al I", 16718.957),
    ("Al I", 16763.359),
]

APOGEE_PIXMASK_BITS = {
    0: "BADPIX",
    1: "CRPIX",
    2: "SATPIX",
    3: "UNFIXABLE",
    4: "BADDARK",
    5: "BADFLAT",
    6: "BADERR",
    7: "NOSKY",
    8: "LITTROW_GHOST",
    9: "PERSIST_HIGH",
    10: "PERSIST_MED",
    11: "PERSIST_LOW",
    12: "SIG_SKYLINE",
    13: "SIG_TELLURIC",
    14: "NOT_ENOUGH_PSF",
}

APOGEE_HARD_BAD_BITS = {0, 1, 2, 3, 4, 5, 6}
APOGEE_CAUTION_BITS = {7, 8, 9, 10, 11, 12, 13, 14}

APOGEE_FEATURE_GUIDE = [
    {
        "species": "Mg I",
        "meaning": "Neutral magnesium; an alpha element used in stellar chemical-abundance work.",
        "abundance_note": "Interpret with APOGEE/ASPCAP [Mg/Fe] or [Mg/H], not line depth alone.",
    },
    {
        "species": "Si I",
        "meaning": "Neutral silicon; another alpha element and tracer of stellar chemical history.",
        "abundance_note": "Use model-derived [Si/Fe] or [Si/H] where available.",
    },
    {
        "species": "Ca I",
        "meaning": "Neutral calcium; alpha-element features occur in the APOGEE H band.",
        "abundance_note": "Use model-derived [Ca/Fe] or [Ca/H] where available.",
    },
    {
        "species": "Al I",
        "meaning": "Neutral aluminum; useful for nucleosynthetic and stellar-population studies.",
        "abundance_note": "Use model-derived [Al/Fe] or [Al/H] where available.",
    },
    {
        "species": "K I",
        "meaning": "Neutral potassium; APOGEE includes measurable potassium features in suitable stars.",
        "abundance_note": "Use model-derived [K/Fe] or [K/H] where available.",
    },
    {
        "species": "CO / CN / OH",
        "meaning": "Molecular features distributed across the H band carry information about C, N, and O.",
        "abundance_note": "APOGEE derives these abundances from many blended molecular features and atmosphere models.",
    },
]


def fetch_sdss_spectrum(ra_deg, dec_deg, radius_arcsec=5.0):
    coord = SkyCoord(
        ra=float(ra_deg) * u.deg,
        dec=float(dec_deg) * u.deg,
        frame="icrs",
    )

    matches = SDSS.query_region(
        coord,
        radius=min(float(radius_arcsec), 180.0) * u.arcsec,
        spectro=True,
    )

    if matches is None or len(matches) == 0:
        return None, None, "No SDSS spectroscopic match"

    spectra = SDSS.get_spectra(matches=matches[:1])
    if not spectra:
        return None, None, "Spectrum metadata found, but no spectrum file returned"

    hdul = spectra[0]

    try:
        data = hdul[1].data
        names = [x.lower() for x in data.names]

        if "loglam" in names:
            wavelength = 10 ** np.asarray(data["loglam"], dtype=float)
        elif "wavelength" in names:
            wavelength = np.asarray(data["wavelength"], dtype=float)
        else:
            return None, None, "Spectrum file did not contain a recognized wavelength column"

        if "flux" not in names:
            return None, None, "Spectrum file did not contain a flux column"

        flux = np.asarray(data["flux"], dtype=float)

        finite = np.isfinite(wavelength) & np.isfinite(flux)
        wavelength = wavelength[finite]
        flux = flux[finite]

        meta = {}
        for key in ["plate", "mjd", "fiberID", "specobjid", "ra", "dec"]:
            if key in matches.colnames:
                meta[key] = str(matches[0][key])

        return wavelength, flux, meta

    finally:
        try:
            hdul.close()
        except Exception:
            pass


def spectrum_dataframe(wavelength, flux):
    return pd.DataFrame({
        "wavelength_angstrom": wavelength,
        "flux": flux,
    })


def spectrum_figure(wavelength, flux, show_lines=True):
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(wavelength, flux, linewidth=0.8)
    ax.set_xlabel("Wavelength (Å)")
    ax.set_ylabel("Flux")
    ax.set_title("SDSS spectrum")
    ax.grid(alpha=0.2)

    if show_lines and len(wavelength):
        ymin, ymax = ax.get_ylim()
        for label, wave in COMMON_LINES:
            if wavelength.min() <= wave <= wavelength.max():
                ax.axvline(wave, linewidth=0.6, linestyle="--", alpha=0.55)
                ax.text(
                    wave,
                    ymax,
                    label,
                    rotation=90,
                    va="top",
                    ha="right",
                    fontsize=7,
                    alpha=0.8,
                )

    fig.tight_layout()
    return fig


def _query_apogee_metadata(apogee_id=None, ra_deg=None, dec_deg=None):
    """Query DR17 SkyServer for APOGEE star metadata needed to build apStar URL."""
    if apogee_id:
        where = f"star.apogee_id = '{str(apogee_id).replace("'", "''")}'"
    else:
        if ra_deg is None or dec_deg is None:
            return None
        # nearest APOGEE star within ~3 arcsec
        where = (
            "star.apstar_id = near.apstar_id "
        )

    if apogee_id:
        query = f"""
        SELECT TOP 1
            star.apogee_id,
            star.apstar_id,
            star.ra,
            star.dec,
            star.telescope,
            star.field
        FROM apogeeStar AS star
        WHERE {where}
        """
    else:
        query = f"""
        SELECT TOP 1
            star.apogee_id,
            star.apstar_id,
            star.ra,
            star.dec,
            star.telescope,
            star.field
        FROM apogeeStar AS star
        JOIN dbo.fGetNearbyApogeeStarEq({float(ra_deg)}, {float(dec_deg)}, 0.05) near
            ON star.apstar_id = near.apstar_id
        ORDER BY near.distance
        """

    try:
        table = SDSS.query_sql(query)
    except Exception:
        table = None

    if table is None or len(table) == 0:
        return None

    row = table[0]
    meta = {k: str(row[k]) for k in table.colnames}
    return meta


def fetch_apogee_spectrum(apogee_id=None, ra_deg=None, dec_deg=None):
    """
    Retrieve a real APOGEE DR17 combined apStar spectrum.

    Returns wavelength Angstrom, flux, metadata/status.
    """
    import io
    import requests
    from astropy.io import fits

    meta = _query_apogee_metadata(
        apogee_id=apogee_id,
        ra_deg=ra_deg,
        dec_deg=dec_deg,
    )
    if not meta:
        return None, None, "No APOGEE DR17 target match"

    target_id = meta.get("apogee_id", apogee_id or "")
    telescope = meta.get("telescope", "").strip()
    field = meta.get("field", "").strip()

    # Some SkyServer versions may not expose telescope/field in the view.
    # Recover them from apstar_id when possible:
    # apogee.apo25m.stars.FIELD.APOGEE_ID
    apstar_id = meta.get("apstar_id", "")
    parts = apstar_id.split(".")
    if not telescope and len(parts) >= 5:
        telescope = parts[1]
    if not field and len(parts) >= 5:
        field = parts[-2]

    if not telescope or not field or not target_id:
        return None, None, {
            "error": "APOGEE match found but telescope/field metadata were incomplete",
            **meta,
        }

    url = (
        "https://data.sdss.org/sas/dr17/apogee/spectro/redux/dr17/stars/"
        f"{telescope}/{field}/apStar-dr17-{target_id}.fits"
    )

    try:
        r = requests.get(url, timeout=(8, 30))
        r.raise_for_status()
    except Exception as exc:
        return None, None, {
            "error": f"APOGEE spectrum download failed: {exc}",
            "url": url,
            **meta,
        }

    try:
        with fits.open(io.BytesIO(r.content), memmap=False) as hdul:
            flux = np.asarray(hdul[1].data, dtype=float)

            # apStar extension 1 may be 1-D or stacked. Use first combined spectrum row.
            if flux.ndim > 1:
                flux = np.asarray(flux[0], dtype=float)

            hdr = hdul[1].header
            crval = hdr.get("CRVAL1")
            cdelt = hdr.get("CDELT1")
            if crval is None or cdelt is None:
                # fall back to primary header
                hdr = hdul[0].header
                crval = hdr.get("CRVAL1")
                cdelt = hdr.get("CDELT1")

            if crval is None or cdelt is None:
                return None, None, {
                    "error": "APOGEE apStar file lacked wavelength WCS keywords",
                    "url": url,
                    **meta,
                }

            pix = np.arange(len(flux), dtype=float)
            # APOGEE apStar wavelength is logarithmic log10(lambda/Angstrom).
            wavelength = 10 ** (float(crval) + float(cdelt) * pix)

            # Recover per-pixel uncertainty / mask information when present.
            # APOGEE apStar products commonly provide these in subsequent HDUs,
            # but we inspect EXTNAME/dtype rather than assuming one rigid layout.
            error = None
            pixmask = None

            for hdu in hdul[2:]:
                arr = getattr(hdu, "data", None)
                if arr is None:
                    continue

                try:
                    arr = np.asarray(arr)
                    if arr.ndim > 1:
                        arr = np.asarray(arr[0])
                    arr = np.squeeze(arr)
                except Exception:
                    continue

                if arr.ndim != 1 or len(arr) != len(flux):
                    continue

                extname = str(hdu.header.get("EXTNAME", "")).upper()

                if pixmask is None and ("MASK" in extname or np.issubdtype(arr.dtype, np.integer)):
                    try:
                        pixmask = np.asarray(arr, dtype=np.int64)
                        continue
                    except Exception:
                        pass

                if error is None and any(k in extname for k in ["ERR", "ERROR", "SIGMA"]):
                    try:
                        error = np.asarray(arr, dtype=float)
                        continue
                    except Exception:
                        pass

                if error is None and "IVAR" in extname:
                    try:
                        ivar = np.asarray(arr, dtype=float)
                        error = np.full_like(ivar, np.nan, dtype=float)
                        good_ivar = np.isfinite(ivar) & (ivar > 0)
                        error[good_ivar] = 1.0 / np.sqrt(ivar[good_ivar])
                        continue
                    except Exception:
                        pass

            # Conservative positional fallbacks for legacy apStar layouts.
            if error is None and len(hdul) > 2:
                try:
                    arr = np.asarray(hdul[2].data)
                    if arr.ndim > 1:
                        arr = np.asarray(arr[0])
                    arr = np.squeeze(arr).astype(float)
                    if arr.ndim == 1 and len(arr) == len(flux):
                        error = arr
                except Exception:
                    pass

            if pixmask is None and len(hdul) > 3:
                try:
                    arr = np.asarray(hdul[3].data)
                    if arr.ndim > 1:
                        arr = np.asarray(arr[0])
                    arr = np.squeeze(arr)
                    if arr.ndim == 1 and len(arr) == len(flux):
                        pixmask = arr.astype(np.int64)
                except Exception:
                    pass

            finite = np.isfinite(wavelength) & np.isfinite(flux)
            wavelength = wavelength[finite]
            flux = flux[finite]
            if error is not None:
                error = np.asarray(error)[finite]
            if pixmask is not None:
                pixmask = np.asarray(pixmask)[finite]

    except Exception as exc:
        return None, None, {
            "error": f"APOGEE FITS parsing failed: {exc}",
            "url": url,
            **meta,
        }

    quality = {
        "available": pixmask is not None or error is not None,
        "pixmask": pixmask,
        "error": error,
    }

    if pixmask is not None:
        hard_bad = np.zeros(len(pixmask), dtype=bool)
        caution = np.zeros(len(pixmask), dtype=bool)
        for bit in APOGEE_HARD_BAD_BITS:
            hard_bad |= (pixmask & (1 << bit)) != 0
        for bit in APOGEE_CAUTION_BITS:
            caution |= (pixmask & (1 << bit)) != 0

        quality["hard_bad"] = hard_bad
        quality["caution"] = caution
        quality["flagged_count"] = int(np.sum(hard_bad | caution))
        quality["hard_bad_count"] = int(np.sum(hard_bad))
        quality["caution_count"] = int(np.sum(caution))

    meta = {
        **meta,
        "archive": "SDSS APOGEE DR17",
        "spectrum_type": "apStar combined H-band spectrum",
        "url": url,
        "_quality": quality,
    }
    return wavelength, flux, meta


def apogee_spectrum_figure(wavelength, flux, show_lines=True, quality=None, show_quality=True):
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.plot(wavelength, flux, linewidth=0.75, label="Spectrum")
    ax.set_xlabel("Wavelength (Å)")
    ax.set_ylabel("Flux")
    ax.set_title("APOGEE DR17 H-band spectrum")
    ax.grid(alpha=0.2)

    if show_lines and len(wavelength):
        ymin, ymax = ax.get_ylim()
        yrange = ymax - ymin if ymax > ymin else 1.0
        visible_index = 0
        for label, wave in APOGEE_REFERENCE_LINES:
            if wavelength.min() <= wave <= wavelength.max():
                ax.axvline(wave, linewidth=0.6, linestyle="--", alpha=0.5)

                # Keep labels inside the plotting area and stagger them slightly
                # so neighboring APOGEE lines remain readable.
                frac = 0.88 if visible_index % 2 == 0 else 0.76
                y_text = ymin + frac * yrange
                ax.text(
                    wave,
                    y_text,
                    label,
                    rotation=90,
                    va="top",
                    ha="right",
                    fontsize=7,
                    alpha=0.88,
                    clip_on=True,
                )
                visible_index += 1

    if show_quality and quality and quality.get("available"):
        hard_bad = quality.get("hard_bad")
        caution = quality.get("caution")

        if hard_bad is not None and np.any(hard_bad):
            idx = np.where(hard_bad)[0]
            if len(idx) > 250:
                idx = idx[::max(1, len(idx) // 250)]
            ax.scatter(
                wavelength[idx],
                flux[idx],
                marker="x",
                s=18,
                alpha=0.75,
                label="Pipeline bad/cosmic/saturated pixel",
            )

        if caution is not None and np.any(caution):
            idx = np.where(caution)[0]
            if len(idx) > 250:
                idx = idx[::max(1, len(idx) // 250)]
            ax.scatter(
                wavelength[idx],
                flux[idx],
                marker="o",
                facecolors="none",
                s=18,
                alpha=0.65,
                label="Pipeline caution: sky/telluric/persistence",
            )

        # Flag unusually high, otherwise unmasked points as candidates for review.
        good = np.ones(len(flux), dtype=bool)
        if hard_bad is not None:
            good &= ~hard_bad
        if caution is not None:
            good &= ~caution

        if np.sum(good) > 30:
            s = pd.Series(flux)
            baseline = s.rolling(window=15, center=True, min_periods=5).median().to_numpy()
            resid = flux - baseline
            valid_resid = resid[good & np.isfinite(resid)]
            if len(valid_resid) > 20:
                med = np.nanmedian(valid_resid)
                mad = np.nanmedian(np.abs(valid_resid - med))
                sigma = 1.4826 * mad if mad > 0 else np.nanstd(valid_resid)
                if np.isfinite(sigma) and sigma > 0:
                    candidate = good & np.isfinite(resid) & (resid > med + 6.0 * sigma)
                    idx = np.where(candidate)[0]
                    if len(idx) > 40:
                        idx = idx[np.argsort(resid[idx])[-40:]]
                    if len(idx):
                        ax.scatter(
                            wavelength[idx],
                            flux[idx],
                            marker="^",
                            s=28,
                            alpha=0.8,
                            label="Unflagged upward outlier — inspect",
                        )

        handles, labels = ax.get_legend_handles_labels()
        if labels:
            ax.legend(loc="best", fontsize=7, framealpha=0.7)

    fig.tight_layout()
    return fig


def apogee_quality_summary(quality):
    if not quality or not quality.get("available"):
        return pd.DataFrame([{
            "quality layer": "Unavailable",
            "count": 0,
            "meaning": "This spectrum did not expose a usable APOGEE per-pixel error/mask array.",
        }])

    rows = []
    if "hard_bad_count" in quality:
        rows.append({
            "quality layer": "Pipeline bad pixels",
            "count": quality.get("hard_bad_count", 0),
            "meaning": "Bad pixel, cosmic ray, saturation, unfixable, bad dark/flat, or bad-error flags.",
        })
        rows.append({
            "quality layer": "Pipeline caution pixels",
            "count": quality.get("caution_count", 0),
            "meaning": "Sky/telluric contamination, persistence, ghost, missing sky, or PSF warning.",
        })

    if quality.get("error") is not None:
        rows.append({
            "quality layer": "Uncertainty array",
            "count": int(np.sum(np.isfinite(quality["error"]))),
            "meaning": "Per-pixel uncertainty values available for further quantitative screening.",
        })

    return pd.DataFrame(rows)


def apogee_feature_guide():
    """Educational guide for representative APOGEE H-band fingerprints."""
    return pd.DataFrame(APOGEE_FEATURE_GUIDE)


def _extract_wave_flux_from_hdul(hdul):
    """Best-effort extraction of 1-D wavelength/flux arrays from common MAST FITS spectra."""
    wave_names = ["wavelength", "wave", "lambda", "lam", "loglam"]
    flux_names = ["flux", "flam", "flux_ergs", "net", "science", "spec"]

    for hdu in hdul:
        data = getattr(hdu, "data", None)
        if data is None:
            continue

        # Binary-table spectra.
        names = getattr(data, "names", None)
        if names:
            lower_map = {str(n).lower(): n for n in names}
            wcol = next((lower_map[n] for n in wave_names if n in lower_map), None)
            fcol = next((lower_map[n] for n in flux_names if n in lower_map), None)

            if wcol is not None and fcol is not None:
                wave = np.asarray(data[wcol], dtype=float)
                flux = np.asarray(data[fcol], dtype=float)

                # One-row vector columns are common in extracted MAST spectra.
                wave = np.squeeze(wave)
                flux = np.squeeze(flux)

                if wave.ndim > 1:
                    wave = np.asarray(wave[0], dtype=float)
                if flux.ndim > 1:
                    flux = np.asarray(flux[0], dtype=float)

                if str(wcol).lower() == "loglam":
                    wave = 10 ** wave

                if wave.ndim == 1 and flux.ndim == 1:
                    n = min(len(wave), len(flux))
                    wave = wave[:n]
                    flux = flux[:n]
                    finite = np.isfinite(wave) & np.isfinite(flux)
                    if finite.sum() > 10:
                        return wave[finite], flux[finite]

        # Image-array spectra with linear/log WCS.
        try:
            arr = np.asarray(data, dtype=float)
            arr = np.squeeze(arr)
            if arr.ndim == 1 and arr.size > 10:
                hdr = hdu.header
                crval = hdr.get("CRVAL1")
                cdelt = hdr.get("CDELT1")
                crpix = hdr.get("CRPIX1", 1.0)
                ctype = str(hdr.get("CTYPE1", "")).upper()

                if crval is not None and cdelt is not None:
                    pix = np.arange(arr.size, dtype=float) + 1.0
                    axis = float(crval) + (pix - float(crpix)) * float(cdelt)
                    if "LOG" in ctype:
                        axis = 10 ** axis

                    finite = np.isfinite(axis) & np.isfinite(arr)
                    if finite.sum() > 10:
                        return axis[finite], arr[finite]
        except Exception:
            pass

    return None, None


def fetch_mast_spectrum_product(data_uri):
    """Download one MAST FITS product and return wavelength, flux, status/meta."""
    import gzip
    import io
    import requests
    from astropy.io import fits

    url = (
        "https://mast.stsci.edu/api/v0.1/Download/file?uri="
        + requests.utils.quote(str(data_uri), safe=":")
    )

    try:
        r = requests.get(url, timeout=(8, 35))
        r.raise_for_status()
        raw = r.content

        if raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)

        with fits.open(io.BytesIO(raw), memmap=False) as hdul:
            wave, flux = _extract_wave_flux_from_hdul(hdul)

        if wave is None:
            return None, None, {
                "error": "No recognized 1-D wavelength/flux pair found in this FITS product",
                "url": url,
            }

        return wave, flux, {
            "archive": "MAST",
            "url": url,
            "data_uri": str(data_uri),
        }

    except Exception as exc:
        return None, None, {
            "error": f"MAST spectrum retrieval/parsing failed: {exc}",
            "url": url,
            "data_uri": str(data_uri),
        }


def generic_spectrum_figure(wavelength, flux, title="MAST spectrum", show_lines=False):
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(wavelength, flux, linewidth=0.8)
    ax.set_xlabel("Wavelength")
    ax.set_ylabel("Flux")
    ax.set_title(title)
    ax.grid(alpha=0.2)

    if show_lines and len(wavelength):
        ymin, ymax = ax.get_ylim()
        for label, wave in COMMON_LINES:
            if wavelength.min() <= wave <= wavelength.max():
                ax.axvline(wave, linewidth=0.6, linestyle="--", alpha=0.55)
                ax.text(
                    wave,
                    ymax,
                    label,
                    rotation=90,
                    va="top",
                    ha="right",
                    fontsize=7,
                    alpha=0.8,
                )

    fig.tight_layout()
    return fig
