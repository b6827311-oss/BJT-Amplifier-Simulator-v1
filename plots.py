"""Server-side SVG charts for the Lab 04 amplifier simulator.

The charts are plain SVG strings generated from the arrays returned by
``spice_engine``.  There is no chart library, no CDN and no JavaScript, so a
reviewer can inspect every coordinate and confirm that the plotted data is the
real ngspice output.
"""

from __future__ import annotations

import math
from html import escape

TEAL = "#0c8078"
ORANGE = "#b5682a"
NAVY = "#103658"
MUTED = "#5b7388"
GRID = "#e3edf4"
AXIS = "#9cb2c2"

FONT = "Leelawadee UI, Tahoma, Segoe UI, sans-serif"


def _fmt(value, digits=1):
    if value is None or not math.isfinite(value):
        return "—"
    if abs(value) >= 1000:
        return f"{value:,.0f}"
    text = f"{value:.{digits}f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


def _si(value, unit=""):
    if value is None or not math.isfinite(value):
        return "—"
    magnitude = abs(value)
    for factor, prefix in (
        (1e9, "G"),
        (1e6, "M"),
        (1e3, "k"),
        (1, ""),
        (1e-3, "m"),
        (1e-6, "µ"),
        (1e-9, "n"),
    ):
        if magnitude >= factor or factor == 1e-9:
            scaled = value / factor
            digits = 0 if abs(scaled) >= 100 else (1 if abs(scaled) >= 10 else 2)
            text = f"{scaled:.{digits}f}"
            if "." in text:
                text = text.rstrip("0").rstrip(".")
            return f"{text}{prefix}{unit}"
    return f"{value:.2g}{unit}"


def format_freq(value):
    """Public helper used by the Jinja layer (``{{ x|freq }}``)."""

    if value is not None and 0 < value < 1:
        return f"{value:g} Hz"
    return _si(value, "Hz")


def _nice_ticks(low, high, target=5):
    if not (math.isfinite(low) and math.isfinite(high)):
        return [0.0]
    if high <= low:
        high = low + 1.0
    raw = (high - low) / max(1, target)
    exponent = math.floor(math.log10(raw)) if raw > 0 else 0
    base = 10 ** exponent
    for multiplier in (1, 2, 2.5, 5, 10):
        step = multiplier * base
        if step >= raw:
            break
    start = math.floor(low / step) * step
    ticks = []
    value = start
    while value <= high + step * 0.5:
        ticks.append(round(value, 10))
        value += step
    return ticks


def _log_decades(low, high):
    if low <= 0 or high <= 0:
        return []
    start = math.floor(math.log10(low))
    end = math.ceil(math.log10(high))
    decades = []
    for exponent in range(start, end + 1):
        value = 10 ** exponent
        if low * 0.999 <= value <= high * 1.001:
            decades.append(value)
    return decades


class _Frame:
    """Tiny helper that owns the plot rectangle and coordinate mapping."""

    def __init__(self, width, height, left=66, right=18, top=30, bottom=52):
        self.width = width
        self.height = height
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom
        self.plot_w = width - left - right
        self.plot_h = height - top - bottom

    def x_linear(self, value, low, high):
        if high == low:
            return self.left
        return self.left + (value - low) / (high - low) * self.plot_w

    def x_log(self, value, low, high):
        if value <= 0 or low <= 0 or high <= 0:
            return self.left
        lo, hi = math.log10(low), math.log10(high)
        if hi == lo:
            return self.left
        pos = (math.log10(value) - lo) / (hi - lo)
        return self.left + max(0.0, min(1.0, pos)) * self.plot_w

    def y(self, value, low, high):
        if high == low:
            return self.top + self.plot_h
        pos = (value - low) / (high - low)
        return self.top + (1 - max(0.0, min(1.0, pos))) * self.plot_h


def _grid_and_axes(
    frame,
    x_ticks,
    x_labels,
    y_ticks,
    y_labels,
    x_title,
    y_title,
    x_low=None,
    x_high=None,
    log_x=True,
):
    parts = []
    x_low = x_ticks[0] if x_low is None else x_low
    x_high = x_ticks[-1] if x_high is None else x_high
    for value, label in zip(x_ticks, x_labels):
        x = (
            frame.x_log(value, x_low, x_high)
            if log_x
            else frame.x_linear(value, x_low, x_high)
        )
        parts.append(
            f'<line class="grid" x1="{x:.1f}" y1="{frame.top}" '
            f'x2="{x:.1f}" y2="{frame.top + frame.plot_h}"/>'
        )
        parts.append(
            f'<text class="tick" x="{x:.1f}" y="{frame.top + frame.plot_h + 17}" '
            f'text-anchor="middle">{escape(label)}</text>'
        )
    for value, label in zip(y_ticks, y_labels):
        y = frame.y(value, y_ticks[0], y_ticks[-1])
        parts.append(
            f'<line class="grid" x1="{frame.left}" y1="{y:.1f}" '
            f'x2="{frame.left + frame.plot_w}" y2="{y:.1f}"/>'
        )
        parts.append(
            f'<text class="tick" x="{frame.left - 9}" y="{y + 3.5:.1f}" '
            f'text-anchor="end">{escape(label)}</text>'
        )
    parts.append(
        f'<line class="axis" x1="{frame.left}" y1="{frame.top}" '
        f'x2="{frame.left}" y2="{frame.top + frame.plot_h}"/>'
    )
    parts.append(
        f'<line class="axis" x1="{frame.left}" y1="{frame.top + frame.plot_h}" '
        f'x2="{frame.left + frame.plot_w}" y2="{frame.top + frame.plot_h}"/>'
    )
    parts.append(
        f'<text class="axis-title" x="{frame.left + frame.plot_w / 2:.1f}" '
        f'y="{frame.height - 10}" text-anchor="middle">{escape(x_title)}</text>'
    )
    parts.append(
        f'<text class="axis-title" transform="translate(14 {frame.top + frame.plot_h / 2:.1f}) rotate(-90)" '
        f'text-anchor="middle">{escape(y_title)}</text>'
    )
    return parts


def _series_path(frame, values, low, high, x_values, x_low, x_high, log_x=True):
    coords = []
    for xv, yv in zip(x_values, values):
        if yv is None or not math.isfinite(yv):
            continue
        x = frame.x_log(xv, x_low, x_high) if log_x else frame.x_linear(xv, x_low, x_high)
        coords.append(f"{x:.1f},{frame.y(yv, low, high):.1f}")
    if not coords:
        return ""
    return f'<polyline class="trace" points="{" ".join(coords)}"/>'


def _downsample(series_list, max_points=900):
    length = len(series_list[0]) if series_list else 0
    if length <= max_points:
        return series_list
    stride = max(1, math.ceil(length / max_points))
    sampled = []
    for series in series_list:
        taken = [series[i] for i in range(0, length, stride)]
        if length and taken and taken[-1] != series[-1]:
            taken.append(series[-1])
        sampled.append(taken)
    return sampled


def _empty_chart(message):
    return (
        '<svg class="chart" viewBox="0 0 760 240" role="img" '
        'aria-label="ไม่มีข้อมูลกราฟ">'
        '<rect x="1" y="1" width="758" height="238" rx="10" fill="#fbfdff" '
        'stroke="#d3e0ec"/>'
        f'<text x="380" y="124" text-anchor="middle" class="empty">{escape(message)}</text>'
        "</svg>"
    )


def _limit_low(values, floor=0.0):
    finite = [value for value in values if value is not None and math.isfinite(value)]
    return min(finite) if finite else floor


def bode_svgs(summary):
    """Return magnitude and phase SVG strings for an AC summary."""

    freqs = summary.get("freqs") or []
    gains = summary.get("gain_db") or []
    phases = summary.get("phase_deg") or []
    if len(freqs) < 2:
        return {
            "magnitude": _empty_chart("ไม่มีข้อมูล AC"),
            "phase": _empty_chart("ไม่มีข้อมูล AC"),
        }

    f_low, f_high = freqs[0], freqs[-1]
    x_ticks = _log_decades(f_low, f_high)
    x_labels = [_si(value, "Hz") for value in x_ticks]

    # ----- magnitude -------------------------------------------------------
    gain_high = max(gains)
    gain_low = _limit_low(gains)
    # Keep the -3 dB reference visible even when the peak is a narrow one.
    pad = max(3.0, (gain_high - gain_low) * 0.08)
    y_high = gain_high + pad
    y_low = min(gain_low - pad, gain_high - 3.0 - pad)
    y_ticks = _nice_ticks(y_low, y_high, 5)
    frame = _Frame(760, 300)
    parts = [
        '<svg class="chart" viewBox="0 0 760 300" role="img" aria-labelledby="bode-mag-title">',
        '<title id="bode-mag-title">Bode magnitude: voltage gain in dB versus frequency</title>',
        f'<rect x="1" y="1" width="758" height="298" rx="10" fill="#ffffff" stroke="#d3e0ec"/>',
        f'<text class="chart-title" x="{frame.left}" y="20">Magnitude — |Vout / Vin| (dB)</text>',
    ]
    parts.append(
        f'<line class="ref" x1="{frame.left}" y1="{frame.y(gain_high - 3, y_low, y_high):.1f}" '
        f'x2="{frame.left + frame.plot_w}" y2="{frame.y(gain_high - 3, y_low, y_high):.1f}"/>'
    )
    parts.append(
        f'<text class="ref-label" x="{frame.left + frame.plot_w - 6}" '
        f'y="{frame.y(gain_high - 3, y_low, y_high) - 5:.1f}" text-anchor="end">−3 dB</text>'
    )
    for key, color in (("fl", TEAL), ("fh", ORANGE)):
        value = summary.get(key)
        if value:
            x = frame.x_log(value, f_low, f_high)
            parts.append(
                f'<line class="marker" x1="{x:.1f}" y1="{frame.top}" x2="{x:.1f}" '
                f'y2="{frame.top + frame.plot_h}" stroke="{color}"/>'
            )
            parts.append(
                f'<text class="marker-label" x="{x + 4:.1f}" y="{frame.top + 12}" '
                f'fill="{color}">{key.upper()} {_si(value, "Hz")}</text>'
            )
    parts.extend(
        _grid_and_axes(
            frame,
            x_ticks,
            x_labels,
            y_ticks,
            [_fmt(value, 0) for value in y_ticks],
            "Frequency (Hz, log scale)",
            "Gain (dB)",
            f_low,
            f_high,
            True,
        )
    )
    parts.append(
        _series_path(frame, gains, y_low, y_high, freqs, f_low, f_high, log_x=True)
    )
    parts.append("</svg>")
    magnitude = "".join(parts)

    # ----- phase -----------------------------------------------------------
    phase_high = max(phases)
    phase_low = min(phases)
    pad = max(15.0, (phase_high - phase_low) * 0.08)
    y_high = phase_high + pad
    y_low = phase_low - pad
    y_ticks = _nice_ticks(y_low, y_high, 4)
    frame = _Frame(760, 280)
    parts = [
        '<svg class="chart" viewBox="0 0 760 280" role="img" aria-labelledby="bode-phase-title">',
        '<title id="bode-phase-title">Bode phase: phase of Vout relative to Vin in degrees versus frequency</title>',
        f'<rect x="1" y="1" width="758" height="278" rx="10" fill="#ffffff" stroke="#d3e0ec"/>',
        f'<text class="chart-title" x="{frame.left}" y="20">Phase — ∠(Vout / Vin) (°)</text>',
    ]
    parts.extend(
        _grid_and_axes(
            frame,
            x_ticks,
            x_labels,
            y_ticks,
            [_fmt(value, 0) for value in y_ticks],
            "Frequency (Hz, log scale)",
            "Phase (°)",
            f_low,
            f_high,
            True,
        )
    )
    parts.append(
        _series_path(
            frame, phases, y_low, y_high, freqs, f_low, f_high, log_x=True
        )
    )
    parts.append("</svg>")
    phase = "".join(parts)

    return {"magnitude": magnitude, "phase": phase}


def transient_svg(summary):
    """Return one SVG with Vin and Vout on a shared millisecond axis."""

    times = summary.get("times") or []
    vin = summary.get("vin") or []
    vout = summary.get("vout") or []
    if len(times) < 2:
        return _empty_chart("ไม่มีข้อมูล Transient")

    times, vin, vout = _downsample([times, vin, vout], 900)
    t_low, t_high = times[0], times[-1]
    # Keep the whole chart in millivolts so the plotted values, the y axis and
    # the printed tick labels use the same unit.
    vin_mv = [value * 1000.0 for value in vin]
    vout_mv = [value * 1000.0 for value in vout]
    values = vin_mv + vout_mv
    v_high = max(values)
    v_low = min(values)
    span = v_high - v_low
    if span <= 0:
        span = 1.0
    y_high = v_high + span * 0.12
    y_low = v_low - span * 0.12
    y_ticks = _nice_ticks(y_low, y_high, 5)

    frame = _Frame(760, 320)
    parts = [
        '<svg class="chart" viewBox="0 0 760 320" role="img" aria-labelledby="tran-title">',
        '<title id="tran-title">Transient response: input and output voltages versus time</title>',
        f'<rect x="1" y="1" width="758" height="318" rx="10" fill="#ffffff" stroke="#d3e0ec"/>',
        f'<text class="chart-title" x="{frame.left}" y="20">Transient — Vin / Vout (mV) vs time (ms)</text>',
    ]

    x_ticks = _nice_ticks(t_low * 1000.0, t_high * 1000.0, 6)
    x_positions = [frame.x_linear(value / 1000.0, t_low, t_high) for value in x_ticks]
    for value, x in zip(x_ticks, x_positions):
        parts.append(
            f'<line class="grid" x1="{x:.1f}" y1="{frame.top}" x2="{x:.1f}" '
            f'y2="{frame.top + frame.plot_h}"/>'
        )
        parts.append(
            f'<text class="tick" x="{x:.1f}" y="{frame.top + frame.plot_h + 17}" '
            f'text-anchor="middle">{_fmt(value, 1)}</text>'
        )
    for value in y_ticks:
        y = frame.y(value, y_ticks[0], y_ticks[-1])
        parts.append(
            f'<line class="grid" x1="{frame.left}" y1="{y:.1f}" '
            f'x2="{frame.left + frame.plot_w}" y2="{y:.1f}"/>'
        )
        parts.append(
            f'<text class="tick" x="{frame.left - 9}" y="{y + 3.5:.1f}" '
            f'text-anchor="end">{_fmt(value, 1)}</text>'
        )
    zero_y = frame.y(0.0, y_ticks[0], y_ticks[-1])
    parts.append(
        f'<line class="zero" x1="{frame.left}" y1="{zero_y:.1f}" '
        f'x2="{frame.left + frame.plot_w}" y2="{zero_y:.1f}"/>'
    )
    parts.append(
        f'<line class="axis" x1="{frame.left}" y1="{frame.top}" x2="{frame.left}" '
        f'y2="{frame.top + frame.plot_h}"/>'
    )
    parts.append(
        f'<line class="axis" x1="{frame.left}" y1="{frame.top + frame.plot_h}" '
        f'x2="{frame.left + frame.plot_w}" y2="{frame.top + frame.plot_h}"/>'
    )
    parts.append(
        f'<text class="axis-title" x="{frame.left + frame.plot_w / 2:.1f}" '
        f'y="{frame.height - 10}" text-anchor="middle">Time (ms)</text>'
    )
    parts.append(
        f'<text class="axis-title" transform="translate(14 {frame.top + frame.plot_h / 2:.1f}) rotate(-90)" '
        f'text-anchor="middle">Voltage (mV)</text>'
    )

    parts.append(
        _series_path(frame, vin_mv, y_low, y_high, times, t_low, t_high, log_x=False)
        .replace('class="trace"', f'class="trace" stroke="{TEAL}"', 1)
    )
    parts.append(
        _series_path(frame, vout_mv, y_low, y_high, times, t_low, t_high, log_x=False)
        .replace('class="trace"', f'class="trace" stroke="{ORANGE}"', 1)
    )

    # Legend
    legend_x = frame.left + 10
    legend_y = frame.top + 6
    parts.append(
        f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x + 22}" y2="{legend_y}" '
        f'stroke="{TEAL}" stroke-width="3" stroke-linecap="round"/>'
    )
    parts.append(
        f'<text class="legend" x="{legend_x + 28}" y="{legend_y + 4}">Vin</text>'
    )
    parts.append(
        f'<line x1="{legend_x + 72}" y1="{legend_y}" x2="{legend_x + 94}" y2="{legend_y}" '
        f'stroke="{ORANGE}" stroke-width="3" stroke-linecap="round"/>'
    )
    parts.append(
        f'<text class="legend" x="{legend_x + 100}" y="{legend_y + 4}">Vout</text>'
    )
    parts.append("</svg>")
    return "".join(parts)
