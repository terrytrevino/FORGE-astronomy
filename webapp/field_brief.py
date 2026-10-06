import base64
import json
import zlib

import pandas as pd


def archive_inventory_dataframe(results):
    rows = []
    for item in results or []:
        rows.append({
            "archive": item.get("archive", ""),
            "status": item.get("status", ""),
            "count": item.get("count", 0),
            "summary": item.get("summary", ""),
        })
    return pd.DataFrame(rows)


def _archive_names_with_data(results):
    names = []
    for item in results or []:
        try:
            count = int(item.get("count", 0) or 0)
        except Exception:
            count = 0
        if str(item.get("status", "")).upper() == "OK" and count > 0:
            names.append(str(item.get("archive", "")))
    return names


def discovery_lens_text(results, analysis=None, spectrum=None):
    names = _archive_names_with_data(results)

    parts = []
    if names:
        parts.append(
            "This field has returned observational coverage from "
            + ", ".join(names[:6])
            + (" and additional services." if len(names) > 6 else ".")
        )
    else:
        parts.append(
            "The current search returned limited archive coverage in the selected search windows."
        )

    if analysis:
        mode = analysis.get("mode", "")
        if mode == "Morphology region" and analysis.get("morphology"):
            strong = [
                row for row in analysis["morphology"]
                if str(row.get("asymmetry_flag", "")).upper() in {"STRONG", "MODERATE"}
            ]
            if strong:
                parts.append(
                    "The local infrared morphology is measurably asymmetric in at least one band, "
                    "so environmental structure should be considered when interpreting point-source measurements."
                )
        elif mode == "Point source":
            parts.append(
                "The current analysis is centered on point-source context rather than extended morphology."
            )

    if spectrum:
        label = spectrum.get("label") or spectrum.get("archive")
        if label:
            parts.append(
                f"A real spectrum has been retrieved from {label}; spectral features should be interpreted "
                "together with pipeline quality flags and reference transitions."
            )

    return " ".join(parts)


def unknowns_list(results, analysis=None, spectrum=None):
    unknowns = []

    archive_map = {
        str(x.get("archive", "")): x for x in (results or [])
    }

    if not spectrum:
        unknowns.append("No spectrum has yet been attached to this Field Brief session.")

    if not analysis:
        unknowns.append("No FORGE analysis result has yet been attached to this Field Brief session.")

    nrao = archive_map.get("NRAO radio")
    if nrao and str(nrao.get("status", "")).upper() in {"TIMEOUT", "ERROR"}:
        unknowns.append(
            "NRAO coverage remains unresolved because the external archive query did not complete."
        )

    if not _archive_names_with_data(results):
        unknowns.append(
            "Archive absence in this brief may reflect search radius, service availability, or archive coverage rather than true non-observation."
        )

    if not unknowns:
        unknowns.append(
            "Further interpretation still depends on instrument-specific calibration, source cross-matching, and scientific context beyond archive presence alone."
        )

    return unknowns


def brief_markdown(target_name, ra_deg, dec_deg, results=None, analysis=None, spectrum=None):
    lines = [
        f"# FORGE Field Brief — {target_name}",
        "",
        f"**RA:** {float(ra_deg):.6f}°  ",
        f"**Dec:** {float(dec_deg):.6f}°",
        "",
        "## Archive inventory",
    ]

    inv = archive_inventory_dataframe(results)
    if inv.empty:
        lines.append("No archive inventory has been generated in this session.")
    else:
        for _, row in inv.iterrows():
            lines.append(
                f"- **{row['archive']}** — {row['status']} — {row['count']} — {row['summary']}"
            )

    lines.extend(["", "## Discovery Lens", discovery_lens_text(results, analysis, spectrum)])

    lines.extend(["", "## Analysis"])
    if analysis:
        lines.append(f"Mode: **{analysis.get('mode', 'Unknown')}**")
        morph = analysis.get("morphology") or []
        for row in morph:
            lines.append(
                f"- {row.get('band', '?')}: {row.get('asymmetry_flag', '')} asymmetry; "
                f"brightest {row.get('brightest_sector', '')}, faintest {row.get('faintest_sector', '')}"
            )
    else:
        lines.append("No FORGE analysis result attached yet.")

    lines.extend(["", "## Spectroscopy"])
    if spectrum:
        lines.append(
            f"Retrieved: **{spectrum.get('label') or spectrum.get('archive') or 'Spectrum'}**"
        )
        if spectrum.get("note"):
            lines.append(spectrum["note"])
    else:
        lines.append("No spectrum attached to this brief yet.")

    lines.extend(["", "## What remains unknown?"])
    for item in unknowns_list(results, analysis, spectrum):
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Provenance",
        "Generated from the active FORGE session. Archive imagery, spectra, and metadata remain attributed to their originating observatories and archives.",
        "",
        "FORGE Astronomy — Field Observation, Retrieval, Generation, and Evaluation",
    ])

    return "\n".join(lines)



def build_share_payload(target_name, ra_deg, dec_deg, results=None, analysis=None, spectrum=None):
    """Create a compact, share-safe Field Brief payload.

    Only synthesis/provenance data are included; raw spectra/images remain in
    their originating archives and are not embedded in the URL.
    """
    inventory = []
    for item in results or []:
        inventory.append({
            "archive": item.get("archive", ""),
            "status": item.get("status", ""),
            "count": item.get("count", 0),
            "summary": item.get("summary", ""),
        })

    analysis_compact = None
    if analysis:
        analysis_compact = {
            "mode": analysis.get("mode", ""),
            "morphology": analysis.get("morphology", []),
        }

    spectrum_compact = None
    if spectrum:
        spectrum_compact = {
            "label": spectrum.get("label", ""),
            "archive": spectrum.get("archive", ""),
            "note": spectrum.get("note", ""),
        }

    return {
        "v": "0.12",
        "target_name": str(target_name),
        "ra_deg": float(ra_deg),
        "dec_deg": float(dec_deg),
        "archives": inventory,
        "analysis": analysis_compact,
        "spectrum": spectrum_compact,
    }


def encode_brief_payload(payload):
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    compressed = zlib.compress(raw, level=9)
    return base64.urlsafe_b64encode(compressed).decode("ascii").rstrip("=")


def decode_brief_payload(token):
    try:
        token = str(token).strip()
        padding = "=" * (-len(token) % 4)
        compressed = base64.urlsafe_b64decode((token + padding).encode("ascii"))
        raw = zlib.decompress(compressed)
        payload = json.loads(raw.decode("utf-8"))

        if not isinstance(payload, dict):
            raise ValueError("Field Brief payload is not an object")

        required = ["target_name", "ra_deg", "dec_deg"]
        missing = [key for key in required if key not in payload]
        if missing:
            raise ValueError(f"Missing Field Brief field(s): {', '.join(missing)}")

        return payload, None
    except Exception as exc:
        return None, f"Could not decode this FORGE Field Brief link: {exc}"
