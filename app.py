import math

from flask import Flask, render_template, request

import plots as chart
import spice_engine
from dc_bias import (
    calculate_dc_bias,
    calculate_emitter_bias,
    calculate_fixed_bias,
)

app = Flask(__name__)
app.jinja_env.filters["freq"] = chart.format_freq


class FormError(ValueError):
    """Raised when the submitted form cannot be mapped to a bias model."""


# Field metadata shared by the form and the validation messages.
FIELD_META = {
    "vcc": {"label": "VCC", "hint": "Supply Voltage [V]"},
    "r1": {"label": "R1", "hint": "Upper Divider [kΩ]"},
    "r2": {"label": "R2", "hint": "Lower Divider [kΩ]"},
    "rb": {"label": "RB", "hint": "Base Resistor [kΩ]"},
    "rc": {"label": "RC", "hint": "Collector Resistor [kΩ]"},
    "re": {"label": "RE", "hint": "Emitter Resistor [kΩ]"},
    "beta": {"label": "β", "hint": "Current Gain [–]"},
    "vbe": {"label": "VBE", "hint": "Base-Emitter Voltage [V]"},
}

MODE_OPTIONS = [
    ("divider", "Voltage Divider Bias"),
    ("fixed", "Fixed Bias"),
    ("emitter", "Emitter Bias"),
]

MODES = {
    "divider": {
        "label": "Voltage Divider Bias",
        "note": "R1 จาก VCC ไป Base · R2 จาก Base ลงกราวด์ · RE จาก Emitter ลงกราวด์",
        "fields": ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"),
        "resistors": ("r1", "r2", "rc", "re"),
        "defaults": {
            "vcc": "12",
            "r1": "100",
            "r2": "22",
            "rc": "2.2",
            "re": "1",
            "beta": "100",
            "vbe": "0.70",
        },
        "calculator": calculate_dc_bias,
    },
    "fixed": {
        "label": "Fixed Bias",
        "note": "RB จาก VCC ไป Base · Emitter ต่อลงกราวด์โดยตรง (VE = 0 V)",
        "fields": ("vcc", "rb", "rc", "beta", "vbe"),
        "resistors": ("rb", "rc"),
        "defaults": {
            "vcc": "12",
            "rb": "1000",
            "rc": "2.2",
            "beta": "100",
            "vbe": "0.70",
        },
        "calculator": calculate_fixed_bias,
    },
    "emitter": {
        "label": "Emitter Bias",
        "note": "RB จาก VCC ไป Base · RE จาก Emitter ลงกราวด์",
        "fields": ("vcc", "rb", "rc", "re", "beta", "vbe"),
        "resistors": ("rb", "rc", "re"),
        "defaults": {
            "vcc": "12",
            "rb": "1000",
            "rc": "2.2",
            "re": "1",
            "beta": "100",
            "vbe": "0.70",
        },
        "calculator": calculate_emitter_bias,
    },
}

DEFAULT_MODE = "divider"

WARNING_MESSAGES = {
    "cutoff": "Cutoff: IB ≤ 0 — Forward-Active approximation ใช้ไม่ได้",
    "near_saturation": "Near Saturation: VCE ≤ 0.2 V — ผลอาจไม่แม่นยำ",
}

# ---------------------------------------------------------------------------
# Lab 04 -- SPICE amplifier simulator
# ---------------------------------------------------------------------------

# The reference circuit is a single voltage-divider CE amplifier.  The form
# collects engineering units that a student actually reads off a schematic;
# the conversion to SI happens in :func:`_parse_simulation` only.
SIM_FIELDS = (
    {"name": "vcc", "label": "VCC", "hint": "Supply Voltage [V]", "default": "12"},
    {"name": "r1", "label": "R1", "hint": "Upper Divider [kΩ]", "default": "100"},
    {"name": "r2", "label": "R2", "hint": "Lower Divider [kΩ]", "default": "22"},
    {"name": "rc", "label": "RC", "hint": "Collector Resistor [kΩ]", "default": "2.2"},
    {"name": "re", "label": "RE", "hint": "Emitter Resistor [kΩ]", "default": "1"},
    {"name": "rl", "label": "RL", "hint": "Load Resistor [kΩ]", "default": "10"},
    {"name": "cin", "label": "Cin", "hint": "Input Coupling [µF]", "default": "10"},
    {"name": "cout", "label": "Cout", "hint": "Output Coupling [µF]", "default": "10"},
    {"name": "amp", "label": "Source", "hint": "Amplitude [mV peak]", "default": "10"},
    {"name": "freq", "label": "Frequency", "hint": "Source Frequency [Hz]", "default": "1000"},
)

SIM_RESISTORS = ("r1", "r2", "rc", "re", "rl")
SIM_CAPACITORS = ("cin", "cout")
SIM_ANALYSES = (
    ("dc", "DC Operating Point", ".op"),
    ("ac", "AC Frequency Response", ".ac"),
    ("tran", "Transient Waveform", ".tran"),
)
SIM_ANALYSIS_LABELS = {key: f"{label} ({command})" for key, label, command in SIM_ANALYSES}

SIM_REGION_LABELS = {
    "active": ("Forward-Active", "status--active"),
    "near_saturation": ("Near Saturation", "status--near"),
    "saturation": ("Saturation", "status--cutoff"),
    "cutoff": ("Cutoff", "status--cutoff"),
}


def _sim_defaults():
    return {field["name"]: field["default"] for field in SIM_FIELDS}


def _sim_fields(values):
    return [
        {
            "name": field["name"],
            "label": field["label"],
            "hint": field["hint"],
            "value": values.get(field["name"], ""),
        }
        for field in SIM_FIELDS
    ]


def _sim_read_form():
    return {
        field["name"]: request.form.get(field["name"], "").strip()
        for field in SIM_FIELDS
    }


def _parse_simulation(values):
    """Validate the form and convert kΩ / µF / mV to SI units (only here)."""

    parsed = {}
    for field in SIM_FIELDS:
        name = field["name"]
        raw = values.get(name, "").strip()
        if not raw:
            raise FormError("กรุณากรอกค่าตัวเลขให้ครบทุกช่อง")
        try:
            value = float(raw)
        except ValueError:
            raise FormError(f"{field['label']} ต้องเป็นตัวเลข") from None
        if not math.isfinite(value):
            raise FormError(
                f"{field['label']}: ค่าอินพุตต้องเป็นจำนวนจำกัด (ไม่ใช่ NaN หรือ Infinity)"
            )
        if name in SIM_RESISTORS:
            value *= 1000.0
        elif name in SIM_CAPACITORS:
            value *= 1e-6
        elif name == "amp":
            value *= 1e-3
        parsed[name] = value

    if parsed["vcc"] <= 0:
        raise FormError("VCC ต้องมากกว่า 0")
    for name in SIM_RESISTORS:
        if parsed[name] <= 0:
            raise FormError(f"{name.upper()} ต้องมากกว่า 0")
    if parsed["cin"] <= 0 or parsed["cout"] <= 0:
        raise FormError("Cin และ Cout ต้องมากกว่า 0")
    if parsed["freq"] <= 0:
        raise FormError("ความถี่ต้องมากกว่า 0")
    if parsed["freq"] > 1e6:
        raise FormError("ความถี่ต้องไม่เกิน 1 MHz")
    if parsed["amp"] <= 0:
        raise FormError("Amplitude ต้องมากกว่า 0")
    if parsed["amp"] > 1.0:
        raise FormError("Amplitude ต้องไม่เกิน 1 V peak")
    return parsed


def _engine_status():
    try:
        return spice_engine.engine_info(), None
    except spice_engine.SpiceError as exc:
        return None, exc


def _render_simulator(
    values,
    analysis="dc",
    result=None,
    error=None,
    error_detail="",
    status=200,
):
    engine, engine_error = _engine_status()
    return (
        render_template(
            "simulator.html",
            sim_fields=_sim_fields(values),
            values=values,
            analysis=analysis,
            analyses=SIM_ANALYSES,
            engine=engine,
            engine_error=engine_error,
            model_summary=spice_engine.MODEL_SUMMARY,
            result=result,
            error=error,
            error_detail=error_detail,
        ),
        status,
    )


@app.get("/simulator")
def simulator():
    values = _sim_defaults()
    analysis = request.args.get("analysis", "dc")
    if analysis not in spice_engine.ANALYSES:
        analysis = "dc"
    return _render_simulator(values, analysis=analysis)


@app.post("/simulate")
def simulate():
    values = _sim_read_form()
    analysis = request.form.get("analysis", "dc").strip() or "dc"
    if analysis not in spice_engine.ANALYSES:
        return _render_simulator(
            values,
            analysis="dc",
            error=f"ไม่รู้จักการวิเคราะห์ที่เลือก ({analysis})",
        )

    try:
        params = _parse_simulation(values)
    except FormError as exc:
        return _render_simulator(values, analysis=analysis, error=str(exc))

    try:
        run = spice_engine.run_analysis(params, analysis)
    except spice_engine.SpiceError as exc:
        return _render_simulator(
            values,
            analysis=analysis,
            error=exc.user_message,
            error_detail=exc.detail,
        )
    except ValueError as exc:
        return _render_simulator(values, analysis=analysis, error=str(exc))

    analytical = None
    try:
        analytical = spice_engine.analytical_ac_estimate(
            params["vcc"],
            params["r1"],
            params["r2"],
            params["rc"],
            params["re"],
            params["rl"],
            100.0,
            0.70,
        )
    except ValueError:
        analytical = None

    result = {
        "analysis": analysis,
        "analysis_label": SIM_ANALYSIS_LABELS[analysis],
        "engine": run.engine,
        "model_summary": spice_engine.MODEL_SUMMARY,
        "netlist": run.netlist,
        "log": run.log,
        "elapsed_ms": run.elapsed * 1000.0,
        "points": run.plot.n_points,
        "raw_kb": run.raw_bytes / 1024.0,
        "params": params,
        "display": values,
        "meta": run.meta,
        "analytical": analytical,
        "dc": None,
        "ac": None,
        "tran": None,
        "charts": {},
    }

    try:
        if analysis == "dc":
            summary = spice_engine.summarize_dc(run.plot)
            summary["region_label"], summary["region_class"] = SIM_REGION_LABELS[
                summary["region"]
            ]
            result["dc"] = summary
        elif analysis == "ac":
            summary = spice_engine.summarize_ac(run.plot, params["freq"])
            result["ac"] = summary
            result["charts"] = chart.bode_svgs(summary)
        else:
            summary = spice_engine.summarize_tran(run.plot, params["freq"])
            result["tran"] = summary
            result["charts"] = {"transient": chart.transient_svg(summary)}
    except (KeyError, ValueError, spice_engine.SpiceError) as exc:
        message = exc.user_message if isinstance(exc, spice_engine.SpiceError) else str(exc)
        return _render_simulator(
            values,
            analysis=analysis,
            error=f"อ่านผลลัพธ์จาก ngspice ไม่ได้: {message}",
            error_detail=run.log[-4000:],
        )

    return _render_simulator(values, analysis=analysis, result=result)



def _requested_mode(raw_mode):
    """Map the submitted mode to a known model.

    An empty value means the Lab 02 form (no mode field), which is still the
    voltage-divider circuit. Any other unknown value is an error: guessing
    Divider here would hide a broken form.
    """
    mode = (raw_mode or "").strip()
    if not mode:
        return DEFAULT_MODE
    if mode not in MODES:
        raise FormError(
            f"ไม่รู้จักโหมดวงจรที่เลือก ({mode}) — "
            "กรุณาเลือก Voltage Divider, Fixed หรือ Emitter"
        )
    return mode


def _mode_fields(mode, values):
    return [
        {
            "name": name,
            "label": FIELD_META[name]["label"],
            "hint": FIELD_META[name]["hint"],
            "value": values.get(name, ""),
        }
        for name in MODES[mode]["fields"]
    ]


def _float_or_none(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _render(mode, values, result=None, error=None, warning_messages=None):
    return render_template(
        "index.html",
        mode=mode,
        modes=MODE_OPTIONS,
        mode_label=MODES[mode]["label"] if mode else None,
        mode_note=MODES[mode]["note"] if mode else None,
        fields=_mode_fields(mode, values) if mode else [],
        values=values,
        result=result,
        error=error,
        warning_messages=warning_messages or [],
        vbe=_float_or_none(values.get("vbe")),
    )


def _read_known_fields(mode):
    return {
        name: request.form.get(name, "").strip()
        for name in MODES[mode]["fields"]
    }


def _parse_inputs(mode, values):
    """Convert the form strings to SI units (kΩ -> Ω happens only here)."""
    config = MODES[mode]
    parsed = {}
    for name in config["fields"]:
        try:
            value = float(values[name])
        except ValueError:
            raise FormError("กรุณากรอกค่าตัวเลขให้ครบทุกช่อง") from None
        if name in config["resistors"]:
            value *= 1000  # form unit is kΩ, the engineering core uses Ω
        parsed[name] = value
    return parsed


@app.get("/")
def index():
    values = {}
    error = None
    try:
        mode = _requested_mode(request.args.get("mode"))
    except FormError as exc:
        return _render(None, values, error=str(exc))

    # Keep values the user already typed when switching mode.
    for name in MODES[mode]["fields"]:
        values[name] = (
            request.args.get(name, "").strip() or MODES[mode]["defaults"][name]
        )
    return _render(mode, values)


@app.post("/calculate")
def calculate():
    try:
        mode = _requested_mode(request.form.get("mode"))
    except FormError as exc:
        return _render(None, {}, error=str(exc))

    values = _read_known_fields(mode)

    try:
        parsed = _parse_inputs(mode, values)
    except FormError as exc:
        return _render(mode, values, error=str(exc))

    try:
        result = MODES[mode]["calculator"](**parsed)
    except ValueError as exc:
        return _render(mode, values, error=str(exc))

    warning_messages = [WARNING_MESSAGES[code] for code in result["warnings"]]
    return _render(
        mode,
        values,
        result=result,
        warning_messages=warning_messages,
    )


if __name__ == "__main__":
    app.run(debug=True)
