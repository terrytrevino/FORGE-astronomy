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

            finite = np.isfinite(wavelength) & np.isfinite(flux)
            wavelength = wavelength[finite]
            flux = flux[finite]

    except Exception as exc:
        return None, None, {
            "error": f"APOGEE FITS parsing failed: {exc}",
            "url": url,
            **meta,
        }

    meta = {
        **meta,
        "archive": "SDSS APOGEE DR17",
        "spectrum_type": "apStar combined H-band spectrum",
        "url": url,
    }
    return wavelength, flux, meta


def apogee_spectrum_figure(wavelength, flux):
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(wavelength, flux, linewidth=0.75)
    ax.set_xlabel("Wavelength (Å)")
    ax.set_ylabel("Flux")
    ax.set_title("APOGEE DR17 H-band spectrum")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    return fig
