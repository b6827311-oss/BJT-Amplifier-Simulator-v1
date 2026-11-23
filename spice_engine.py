"""ngspice adapter for the ENG29 2121 Lab 04 CE amplifier simulator.

This module contains **no Flask imports**.  It only knows how to

1. locate a real ``ngspice`` executable,
2. turn validated SI-unit parameters into a netlist,
3. run ngspice in batch mode inside a private temporary directory,
4. parse the ASCII rawfile that ngspice writes, and
5. reduce the raw data to engineering summaries for the web layer.

Every number shown by the web app must come from :func:`run_analysis`;
nothing in this module fabricates a waveform or a gain.

Units
-----
All arguments and return values are SI: volts, ohms, farads, hertz, seconds.
"""

from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Circuit fixture (Lab 04 reference CE voltage-divider amplifier)
# ---------------------------------------------------------------------------

MODEL_NAME = "QNPN"
MODEL_PARAMS = {
    "IS": "1e-14",
    "BF": "100",
    "VAF": "100",
    "CJE": "8p",
    "CJC": "4p",
    "TF": "0.3n",
}
MODEL_CARD = ".model QNPN NPN (" + " ".join(
    f"{key}={value}" for key, value in MODEL_PARAMS.items()
) + ")"
MODEL_SUMMARY = (
    "QNPN · generic small-signal NPN (ไม่ใช่วงจรรุ่นการค้า) · "
    "IS=1e-14 A · BF=100 · VAF=100 V · CJE=8 pF · CJC=4 pF · TF=0.3 ns"
)

ANALYSES = ("dc", "ac", "tran")
ANALYSIS_LABELS = {
    "dc": "DC operating point (.op)",
    "ac": "AC frequency response (.ac)",
    "tran": "Transient waveform (.tran)",
}

AC_FSTART = 0.1  # Hz -- shows the input/output coupling high-pass corner
AC_FSTOP = 500e6  # Hz -- shows the high-frequency shelf of this circuit
AC_POINTS_PER_DECADE = 20

THERMAL_VOLTAGE = 0.02585  # V at 27 degC, used by the analytical estimate only

_NON_FINITE = "ค่าอินพุตต้องเป็นจำนวนจำกัด (ไม่ใช่ NaN หรือ Infinity)"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class SpiceError(RuntimeError):
    """ngspice could not complete the requested analysis."""

    def __init__(self, user_message, detail=""):
        super().__init__(user_message)
        self.user_message = user_message
        self.detail = detail


class SpiceNotFound(SpiceError):
    """No ngspice executable was found on this machine."""

    def __init__(self, detail=""):
        super().__init__(
            "ไม่พบ ngspice บนเครื่องนี้ — ติดตั้ง ngspice 47 แล้วตั้งค่า "
            "NGSPICE_BIN หรือเพิ่มโฟลเดอร์ bin ลง PATH "
            "(ดูวิธีใน README หัวข้อ “ngspice”)",
            detail,
        )


# ---------------------------------------------------------------------------
# Parameter helpers
# ---------------------------------------------------------------------------


def spice_number(value):
    """Format an SI value with a SPICE suffix while keeping it readable.

    ``2200`` -> ``2.2k``, ``1e-5`` -> ``10u``, ``0.5`` -> ``0.5``.
    """

    value = float(value)
    magnitude = abs(value)
    if magnitude == 0:
        return "0"
    for factor, suffix in (
        (1e9, "g"),
        (1e6, "meg"),
        (1e3, "k"),
        (1.0, ""),
        (1e-3, "m"),
        (1e-6, "u"),
        (1e-9, "n"),
        (1e-12, "p"),
        (1e-15, "f"),
    ):
        scaled = magnitude / factor
        if scaled >= 1 or factor == 1e-15:
            return f"{value / factor:.10g}{suffix}"
    return f"{value:.10g}"


def _require_positive(params, keys):
    for key in keys:
        value = params.get(key)
        try:
            value = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"ค่าอินพุต {key} ต้องเป็นตัวเลข") from None
        if not math.isfinite(value):
            raise ValueError(_NON_FINITE)
        if value <= 0:
            raise ValueError(f"ค่าอินพุต {key} ต้องมากกว่า 0")
        params[key] = value


def normalize_params(params):
    """Copy and validate the SI parameters used to build a netlist."""

    data = {key: params[key] for key in params}
    _require_positive(
        data,
        (
            "vcc",
            "r1",
            "r2",
            "rc",
            "re",
            "rl",
            "cin",
            "cout",
            "amp",
            "freq",
        ),
    )
    if data["re"] <= 0:
        raise ValueError("RE ต้องมากกว่า 0 (Emitter ต่อลงกราวด์โดยตรงไม่ได้ในโหมดนี้)")
    if not (0 < data["freq"] <= 1e6):
        raise ValueError("ความถี่ต้องอยู่ระหว่าง 0 ถึง 1 MHz")
    if data["amp"] > 1.0:
        raise ValueError("Amplitude ต้องไม่เกิน 1 V peak")
    return data


# ---------------------------------------------------------------------------
# Executable discovery
# ---------------------------------------------------------------------------

_CANDIDATE_NAMES = ("ngspice_con.exe", "ngspice.exe") if os.name == "nt" else ("ngspice",)

_engine_cache = {}


def _project_root():
    return Path(__file__).resolve().parent


def _candidate_paths():
    """Yield possible ngspice executables, best first."""

    env_value = os.environ.get("NGSPICE_BIN", "").strip().strip('"')
    if env_value:
        env_path = Path(env_value)
        if env_path.is_dir():
            for name in _CANDIDATE_NAMES:
                yield env_path / name
        else:
            yield env_path

    for name in ("ngspice_con", "ngspice"):
        found = shutil.which(name)
        if found and Path(found).suffix.lower() not in {".cmd", ".bat"}:
            yield Path(found)

    for name in _CANDIDATE_NAMES:
        yield _project_root() / "tools" / "ngspice" / "Spice64" / "bin" / name

    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA", "")
        if local:
            for name in _CANDIDATE_NAMES:
                yield Path(local) / "ngspice" / "Spice64" / "bin" / name
                yield Path(local) / "Programs" / "ngspice" / "Spice64" / "bin" / name
        for name in _CANDIDATE_NAMES:
            yield Path("C:/Spice64/bin") / name
            yield Path("C:/ngspice/Spice64/bin") / name
        for base in ("C:/Program Files", "C:/Program Files (x86)"):
            for name in _CANDIDATE_NAMES:
                yield from sorted(Path(base).glob(f"ngspice*/Spice64/bin/{name}"))
                yield from sorted(Path(base).glob(f"ngspice*/bin/{name}"))
    else:
        for path in (
            "/usr/bin/ngspice",
            "/usr/local/bin/ngspice",
            "/opt/homebrew/bin/ngspice",
            "/opt/local/bin/ngspice",
        ):
            yield Path(path)


def find_ngspice():
    """Return the path to a working ngspice executable, or ``None``."""

    for candidate in _candidate_paths():
        try:
            if candidate.is_file():
                return candidate
        except OSError:
            continue
    return None


def _engine_env(exe):
    env = os.environ.copy()
    bin_dir = Path(exe).resolve().parent
    env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
    share = bin_dir.parent / "share" / "ngspice"
    if share.is_dir():
        env["SPICE_LIB_DIR"] = str(share)
        scripts = share / "scripts"
        if scripts.is_dir():
            env["SPICE_SCRIPTS"] = str(scripts)
    return env


def engine_info(refresh=False):
    """Return ``{path, version, label}`` for the discovered engine.

    Raises :class:`SpiceNotFound` when no executable is available.
    """

    if _engine_cache and not refresh:
        return dict(_engine_cache)

    exe = find_ngspice()
    if exe is None:
        raise SpiceNotFound(
            "ค้นหาใน PATH, tools/ngspice, %LOCALAPPDATA%/ngspice และ C:/Spice64 แล้ว"
        )

    try:
        completed = subprocess.run(
            [str(exe), "-v"],
            capture_output=True,
            text=True,
            timeout=15,
            env=_engine_env(exe),
        )
        text = (completed.stdout or "") + (completed.stderr or "")
    except (OSError, subprocess.SubprocessError) as exc:
        raise SpiceError(
            f"เรียก ngspice ไม่ได้: {exe}",
            f"{type(exc).__name__}: {exc}",
        ) from exc

    match = re.search(r"ngspice-(\d+)", text)
    version = f"ngspice-{match.group(1)}" if match else "ngspice (ไม่ทราบรุ่น)"
    info = {
        "path": str(exe),
        "version": version,
        "label": version,
        "raw_version_text": text.strip(),
    }
    _engine_cache.update(info)
    return dict(info)


def clear_engine_cache():
    _engine_cache.clear()


# ---------------------------------------------------------------------------
# Netlist construction
# ---------------------------------------------------------------------------


def transient_timing(freq):
    """Choose a transient window that always shows ~20 signal periods."""

    period = 1.0 / float(freq)
    tstop = min(max(20.0 * period, 0.005), 1.0)
    tstep = tstop / 4000.0
    return tstep, tstop


def build_netlist(params, analysis):
    """Return ``(netlist_text, meta)`` for one analysis.

    ``params`` must already use SI units; it is validated again here so the
    engine can be used (and tested) without the Flask layer.
    """

    if analysis not in ANALYSES:
        raise ValueError(f"ไม่รู้จัก analysis: {analysis}")

    data = normalize_params(params)
    tstep, tstop = transient_timing(data["freq"])

    lines = [
        f"* ENG29 2121 Lab 04 -- CE voltage-divider amplifier -- {analysis}",
        "* Model is embedded so the netlist is self-contained and reproducible.",
        f"VCC vcc 0 DC {spice_number(data['vcc'])}",
        (
            "VIN in 0 DC 0 AC 1 "
            f"SIN(0 {spice_number(data['amp'])} {spice_number(data['freq'])})"
        ),
        f"R1 vcc vb {spice_number(data['r1'])}",
        f"R2 vb 0 {spice_number(data['r2'])}",
        f"RC vcc vc {spice_number(data['rc'])}",
        f"RE ve 0 {spice_number(data['re'])}",
        f"CIN in vb {spice_number(data['cin'])}",
        f"COUT vc out {spice_number(data['cout'])}",
        f"RL out 0 {spice_number(data['rl'])}",
        f"Q1 vc vb ve {MODEL_NAME}",
        MODEL_CARD,
    ]

    if analysis == "dc":
        lines.append(".op")
        lines.append(".save all @q1[ic] @q1[ib] @q1[ie] @q1[vbe]")
    elif analysis == "ac":
        lines.append(
            f".ac dec {AC_POINTS_PER_DECADE} "
            f"{spice_number(AC_FSTART)} {spice_number(AC_FSTOP)}"
        )
        lines.append(".save all")
    else:
        lines.append(f".tran {spice_number(tstep)} {spice_number(tstop)}")
        lines.append(".save all")

    lines.append(".end")
    meta = {
        "analysis": analysis,
        "tstep": tstep,
        "tstop": tstop,
        "ac_fstart": AC_FSTART,
        "ac_fstop": AC_FSTOP,
        "ac_points_per_decade": AC_POINTS_PER_DECADE,
    }
    return "\n".join(lines) + "\n", meta


# ---------------------------------------------------------------------------
# Rawfile parsing (ngspice ASCII raw format)
# ---------------------------------------------------------------------------


@dataclass
class RawPlot:
    plotname: str = ""
    flags: str = ""
    variables: list = field(default_factory=list)
    points: list = field(default_factory=list)

    @property
    def is_complex(self):
        return "complex" in self.flags.lower()

    @property
    def n_points(self):
        return len(self.points)

    def series(self, name):
        """Return one column as a list (complex or float)."""

        target = name.strip().lower()
        for index, variable in enumerate(self.variables):
            if variable.strip().lower() == target:
                return [point[index] for point in self.points]
        raise KeyError(f"ไม่พบตัวแปร {name} ใน rawfile (มี: {', '.join(self.variables)})")

    def has(self, name):
        target = name.strip().lower()
        return any(v.strip().lower() == target for v in self.variables)


def _parse_value(token, is_complex):
    """Parse one rawfile value; tolerate both ``a,b`` and ``(a,b)`` styles."""

    token = token.strip().strip("(),").strip()
    if not token:
        raise ValueError("ค่าตัวเลขว่างใน rawfile")
    if is_complex:
        parts = [p.strip().strip("(),") for p in token.replace(",", " ").split() if p]
        if len(parts) != 2:
            raise ValueError(f"ค่าซับซ้อนไม่ครบคู่: {token!r}")
        return complex(float(parts[0]), float(parts[1]))
    return float(token)


def parse_raw(text):
    """Parse an ngspice ASCII rawfile into a list of :class:`RawPlot`."""

    lines = [line.rstrip("\r\n") for line in text.splitlines()]
    plots = []
    index = 0
    total = len(lines)

    while index < total:
        if not lines[index].startswith("Title:"):
            index += 1
            continue

        header = {}
        while (
            index < total
            and lines[index].strip()
            and not lines[index].startswith("Variables:")
        ):
            key, _, value = lines[index].partition(":")
            if value:
                header[key.strip()] = value.strip()
            index += 1

        while index < total and not lines[index].strip():
            index += 1
        if index >= total or not lines[index].startswith("Variables:"):
            raise ValueError("rawfile ไม่มีส่วน Variables:")

        index += 1
        variables = []
        while index < total and lines[index].strip() and not lines[index].startswith("Values:"):
            parts = lines[index].split()
            if len(parts) >= 2:
                variables.append(parts[1])
            index += 1
        while index < total and not lines[index].startswith("Values:"):
            index += 1
        if index >= total:
            raise ValueError("rawfile ไม่มีส่วน Values:")
        index += 1

        is_complex = "complex" in header.get("Flags", "").lower()
        expected = len(variables)
        points = []
        current = []

        while index < total:
            line = lines[index]
            if line.startswith("Title:") or line.startswith("Plotname:"):
                break
            if not line.strip():
                index += 1
                continue

            if line[0].isdigit():
                if current:
                    points.append(current)
                    current = []
                pieces = line.split(None, 1)
                line = pieces[1] if len(pieces) > 1 else ""
                if not line.strip():
                    index += 1
                    continue

            # ngspice writes `real,imag`; some variants wrap it in `(...)`.
            # Normalising the brackets lets both forms reach _parse_value.
            normalized = line.strip().replace("(", " ").replace(")", " ")
            tokens = [tok for tok in re.split(r"[\s,]+", normalized) if tok]
            if is_complex:
                if len(tokens) < 2 or len(tokens) % 2:
                    raise ValueError(f"ค่าซับซ้อนไม่ครบคู่: {line!r}")
                for pos in range(0, len(tokens), 2):
                    current.append(
                        _parse_value(f"{tokens[pos]},{tokens[pos + 1]}", True)
                    )
            else:
                if not tokens:
                    raise ValueError(f"ค่าตัวเลขว่างใน rawfile: {line!r}")
                for token in tokens:
                    current.append(_parse_value(token, False))
            index += 1

        if current:
            points.append(current)

        for row in points:
            if len(row) != expected:
                raise ValueError(
                    f"rawfile มี {len(row)} ค่า แต่ประกาศ {expected} ตัวแปร"
                )

        plots.append(
            RawPlot(
                plotname=header.get("Plotname", ""),
                flags=header.get("Flags", ""),
                variables=variables,
                points=points,
            )
        )

    if not plots:
        raise ValueError("rawfile ว่างหรือไม่ใช่รูปแบบ ASCII raw ของ ngspice")
    return plots


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------


@dataclass
class SpiceRun:
    analysis: str
    netlist: str
    log: str
    plot: RawPlot
    engine: dict
    elapsed: float
    raw_bytes: int
    meta: dict


def run_analysis(params, analysis, timeout=20):
    """Run one analysis and return the parsed raw data plus provenance."""

    netlist, meta = build_netlist(params, analysis)
    engine = engine_info()
    exe = engine["path"]

    workdir = Path(tempfile.mkdtemp(prefix="bjt_spice_"))
    circuit = workdir / "circuit.cir"
    logfile = workdir / "run.log"
    rawfile = workdir / "run.raw"

    try:
        circuit.write_text(netlist, encoding="ascii", newline="\n")
        started = time.perf_counter()
        try:
            completed = subprocess.run(
                [
                    str(exe),
                    "-b",
                    "-o",
                    str(logfile),
                    "-r",
                    str(rawfile),
                    str(circuit),
                ],
                cwd=str(workdir),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=_engine_env(exe),
            )
        except subprocess.TimeoutExpired as exc:
            raise SpiceError(
                f"ngspice ใช้เวลาเกิน {timeout} วินาที จึงยกเลิกการจำลอง",
                (exc.stderr or "") if isinstance(exc.stderr, str) else "",
            ) from exc
        except OSError as exc:
            raise SpiceError(
                f"เรียก ngspice ไม่ได้: {exe}",
                f"{type(exc).__name__}: {exc}",
            ) from exc
        elapsed = time.perf_counter() - started

        log = ""
        if logfile.exists():
            log = logfile.read_text(encoding="utf-8", errors="replace")
        console = ((completed.stdout or "") + (completed.stderr or "")).strip()
        if console:
            log = (log + "\n" + console).strip()
        if not log:
            log = "(ngspice ไม่ได้เขียน log)"

        if completed.returncode != 0:
            raise SpiceError(
                f"ngspice ทำงานไม่สำเร็จ (exit code {completed.returncode})",
                log[-4000:],
            )

        if not rawfile.exists() or rawfile.stat().st_size == 0:
            raise SpiceError(
                "ngspice ไม่ได้สร้างไฟล์ผลลัพธ์ (rawfile ว่าง)",
                log[-4000:],
            )

        raw_text = rawfile.read_text(encoding="utf-8", errors="replace")
        raw_bytes = len(raw_text)
        plots = parse_raw(raw_text)
        plot = plots[0]

        if plot.n_points == 0:
            raise SpiceError("ผลลัพธ์จาก ngspice ไม่มีข้อมูล", log[-4000:])

        return SpiceRun(
            analysis=analysis,
            netlist=netlist,
            log=log,
            plot=plot,
            engine=engine,
            elapsed=elapsed,
            raw_bytes=raw_bytes,
            meta=meta,
        )
    except ValueError as exc:
        if isinstance(exc, SpiceError):
            raise
        raise SpiceError(f"อ่านผลลัพธ์จาก ngspice ไม่ได้: {exc}", "") from exc
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Engineering summaries
# ---------------------------------------------------------------------------


def _first(plot, name):
    value = plot.series(name)[0]
    return float(getattr(value, "real", value))


def summarize_dc(plot):
    """Reduce an operating-point plot to the Lab 04 DC quantities."""

    vb = _first(plot, "v(vb)")
    ve = _first(plot, "v(ve)")
    vc = _first(plot, "v(vc)")
    vce = vc - ve

    def device_current(name):
        key = f"i(@q1[{name}])"
        return abs(_first(plot, key)) if plot.has(key) else None

    ic = device_current("ic")
    ib = device_current("ib")
    ie = device_current("ie")

    if ic is None or ib is None:
        raise SpiceError(
            "ngspice ไม่ได้คืนค่ากระแสของ Q1 (@q1[ic]/@q1[ib])",
            "ตรวจสอบ .save @q1[ic] @q1[ib] ใน netlist",
        )

    return {
        "vb": vb,
        "ve": ve,
        "vc": vc,
        "vce": vce,
        "ic": ic,
        "ib": ib,
        "ie": ie,
        "vbe": _first(plot, "v(@q1[vbe])") if plot.has("v(@q1[vbe])") else vb - ve,
        "region": _dc_region(vce, ib),
    }


def _dc_region(vce, ib):
    if ib is not None and ib <= 0:
        return "cutoff"
    if vce <= 0.2:
        return "saturation"
    if vce < 1.0:
        return "near_saturation"
    return "active"


def _interp_log(freqs, values, target):
    """Log-frequency linear interpolation of a dB/degree curve."""

    if not freqs or not values:
        return None
    if target <= freqs[0]:
        return values[0]
    if target >= freqs[-1]:
        return values[-1]
    for i in range(1, len(freqs)):
        if freqs[i] >= target:
            f0, f1 = freqs[i - 1], freqs[i]
            v0, v1 = values[i - 1], values[i]
            if f0 <= 0 or f1 <= 0 or f0 == f1:
                return v1
            ratio = (math.log10(target) - math.log10(f0)) / (
                math.log10(f1) - math.log10(f0)
            )
            return v0 + (v1 - v0) * ratio
    return values[-1]


def _crossing(freqs, values, level, rising, start, end):
    """Find the log-frequency where ``values`` crosses ``level``."""

    step = 1 if end >= start else -1
    previous = values[start]
    for i in range(start + step, end + step, step):
        current = values[i]
        hit = previous <= level <= current if rising else previous >= level >= current
        if hit and previous != current:
            f0, f1 = freqs[i - step], freqs[i]
            ratio = (level - previous) / (current - previous)
            if f0 > 0 and f1 > 0:
                log0, log1 = math.log10(f0), math.log10(f1)
                return 10 ** (log0 + (log1 - log0) * ratio)
            return f1
        previous = current
    return None


def summarize_ac(plot, reference_freq):
    """Return Bode arrays plus midband / -3 dB summary values."""

    freqs = [float(getattr(f, "real", f)) for f in plot.series("frequency")]
    vin = plot.series("v(in)")
    vout = plot.series("v(out)")

    gain_db = []
    phase_rad = []
    for vi, vo in zip(vin, vout):
        ratio = vo / vi if vi != 0 else complex(0, 0)
        gain_db.append(20.0 * math.log10(abs(ratio)) if abs(ratio) > 0 else -180.0)
        phase_rad.append(math.atan2(ratio.imag, ratio.real))

    # Unwrap the phase and anchor the midband (peak gain) near -180 degrees.
    unwrapped = []
    for i, value in enumerate(phase_rad):
        if i == 0:
            unwrapped.append(value)
        else:
            delta = value - phase_rad[i - 1]
            while delta > math.pi:
                delta -= 2 * math.pi
            while delta < -math.pi:
                delta += 2 * math.pi
            unwrapped.append(unwrapped[-1] + delta)

    peak_index = max(range(len(gain_db)), key=lambda i: gain_db[i])
    anchor = unwrapped[peak_index]
    turns = round((anchor + math.pi) / (2 * math.pi))
    phase_deg = [math.degrees(value - turns * 2 * math.pi) for value in unwrapped]

    max_gain_db = gain_db[peak_index]
    threshold = max_gain_db - 3.0
    fl = _crossing(freqs, gain_db, threshold, True, 0, peak_index)
    fh = _crossing(freqs, gain_db, threshold, False, peak_index, len(freqs) - 1)

    return {
        "freqs": freqs,
        "gain_db": gain_db,
        "phase_deg": phase_deg,
        "max_gain_db": max_gain_db,
        "max_gain_freq": freqs[peak_index],
        "max_gain_linear": 10 ** (max_gain_db / 20.0),
        "fl": fl,
        "fh": fh,
        "gain_at_ref_db": _interp_log(freqs, gain_db, reference_freq),
        "phase_at_ref_deg": _interp_log(freqs, phase_deg, reference_freq),
    }


def summarize_tran(plot, freq):
    """Return steady-state amplitudes and phase-inversion evidence."""

    times = [float(getattr(t, "real", t)) for t in plot.series("time")]
    vin = [float(getattr(v, "real", v)) for v in plot.series("v(in)")]
    vout = [float(getattr(v, "real", v)) for v in plot.series("v(out)")]

    skip = int(len(times) * 0.2)
    window = slice(skip, len(times)) if len(times) > 10 else slice(0, len(times))
    t_win = times[window]
    vin_win = vin[window]
    vout_win = vout[window]

    vin_pp = max(vin_win) - min(vin_win)
    vout_pp = max(vout_win) - min(vout_win)
    gain = vout_pp / vin_pp if vin_pp else None

    mean_in = sum(vin_win) / len(vin_win)
    mean_out = sum(vout_win) / len(vout_win)
    covariance = sum(
        (a - mean_in) * (b - mean_out) for a, b in zip(vin_win, vout_win)
    )
    inverted = covariance < 0

    return {
        "times": times,
        "vin": vin,
        "vout": vout,
        "time_window": (t_win[0], t_win[-1]) if t_win else (0.0, 0.0),
        "vin_pp": vin_pp,
        "vout_pp": vout_pp,
        "gain_pp": gain,
        "inverted": inverted,
        "phase_text": "กลับเฟส 180° (inverted)" if inverted else "ไม่กลับเฟส (in phase)",
    }


def analytical_ac_estimate(vcc, r1, r2, rc, re, rl, beta, vbe):
    """Midband small-signal estimate from the Lab 03 analytical DC point.

    This is deliberately a separate, clearly-labelled estimate -- not a
    replacement for the ngspice result.
    """

    from dc_bias import calculate_dc_bias

    dc = calculate_dc_bias(vcc, r1, r2, rc, re, beta, vbe)
    ie = abs(dc["ie"])
    if ie <= 0:
        return None
    re_small = THERMAL_VOLTAGE / ie
    load = (rc * rl) / (rc + rl) if (rc + rl) else 0.0
    gain = load / (re + re_small) if (re + re_small) else 0.0
    return {
        "re_small": re_small,
        "rc_parallel_rl": load,
        "gain_linear": gain,
        "gain_db": 20.0 * math.log10(gain) if gain > 0 else None,
        "ie": ie,
        "dc": dc,
    }
