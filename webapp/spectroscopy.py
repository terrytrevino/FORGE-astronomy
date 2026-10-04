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
