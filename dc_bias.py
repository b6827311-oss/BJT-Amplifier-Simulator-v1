"""Engineering calculations for BJT common-emitter DC bias circuits.

Lab 03 adds two bias models next to the Lab 02 voltage-divider model:

* ``calculate_dc_bias``      -- voltage-divider bias (Lab 02, unchanged results)
* ``calculate_fixed_bias``   -- fixed bias (base resistor only)
* ``calculate_emitter_bias`` -- emitter bias (base and emitter resistors)

All inputs use SI units: volts and ohms. This module has no Flask or HTML
dependency so the engineering model can be tested independently.
"""

import math

VCE_SAT_WARNING = 0.2  # V -- heuristic from the Lab 02/03 preview image

_NON_FINITE_MESSAGE = "ค่าอินพุตต้องเป็นจำนวนจำกัด (ไม่ใช่ NaN หรือ Infinity)"
_OVERFLOW_MESSAGE = "ค่าอินพุตมากเกินกว่าที่แบบจำลองจะคำนวณได้"


def _require_finite(values):
    if not all(math.isfinite(value) for value in values):
        raise ValueError(_NON_FINITE_MESSAGE)


def _require_gains(beta, vbe):
    """Validate the transistor parameters every bias mode shares."""
    if beta <= 0:
        raise ValueError("β ต้องมากกว่า 0")
    if vbe <= 0:
        raise ValueError("VBE ต้องมากกว่า 0")


def _solve(vcc, rc, re, beta, vbe, ib, *, mode, vth=None, rth=None):
    """Return the shared result dict from a base current and the circuit values."""
    ic = beta * ib
    ie = (beta + 1) * ib
    ve = ie * re
    vb = ve + vbe
    vc = vcc - ic * rc
    vce = vc - ve

    results = (ib, ic, ie, ve, vb, vc, vce)
    if not all(math.isfinite(value) for value in results):
        raise ValueError(_OVERFLOW_MESSAGE)

    warnings = []
    if ib <= 0:
        warnings.append("cutoff")
    if vce <= VCE_SAT_WARNING:
        warnings.append("near_saturation")

    if "cutoff" in warnings:
        region = "cutoff"
    elif "near_saturation" in warnings:
        region = "near_saturation"
    else:
        region = "active"

    return {
        "mode": mode,
        "vth": vth,
        "rth": rth,
        "ib": ib,
        "ic": ic,
        "ie": ie,
        "ve": ve,
        "vb": vb,
        "vc": vc,
        "vce": vce,
        "warnings": warnings,
        "region": region,
    }


def calculate_dc_bias(vcc, r1, r2, rc, re, beta, vbe):
    """Return the DC operating point for the voltage-divider bias circuit.

    Parameters are in volts and ohms. Raises ValueError when an input is
    outside the model's valid range.
    """
    _require_finite((vcc, r1, r2, rc, re, beta, vbe))

    if vcc <= 0:
        raise ValueError("VCC ต้องมากกว่า 0")
    if r1 <= 0 or r2 <= 0 or rc <= 0 or re <= 0:
        raise ValueError("R1, R2, RC, RE ต้องมากกว่า 0")
    _require_gains(beta, vbe)

    vth = vcc * r2 / (r1 + r2)
    rth = r1 * r2 / (r1 + r2)
    ib = (vth - vbe) / (rth + (beta + 1) * re)

    return _solve(
        vcc, rc, re, beta, vbe, ib, mode="divider", vth=vth, rth=rth
    )


def calculate_fixed_bias(vcc, rb, rc, beta, vbe):
    """Return the DC operating point for the fixed bias circuit.

    The base is fed from VCC through RB and the emitter is grounded, so
    VE = 0 V. Parameters are in volts and ohms.
    """
    _require_finite((vcc, rb, rc, beta, vbe))

    if vcc <= 0:
        raise ValueError("VCC ต้องมากกว่า 0")
    if rb <= 0 or rc <= 0:
        raise ValueError("RB, RC ต้องมากกว่า 0")
    _require_gains(beta, vbe)

    ib = (vcc - vbe) / rb

    return _solve(vcc, rc, 0.0, beta, vbe, ib, mode="fixed")


def calculate_emitter_bias(vcc, rb, rc, re, beta, vbe):
    """Return the DC operating point for the emitter bias circuit.

    The base is fed from VCC through RB and the emitter is returned to
    ground through RE. Parameters are in volts and ohms.
    """
    _require_finite((vcc, rb, rc, re, beta, vbe))

    if vcc <= 0:
        raise ValueError("VCC ต้องมากกว่า 0")
    if rb <= 0 or rc <= 0 or re <= 0:
        raise ValueError("RB, RC, RE ต้องมากกว่า 0")
    _require_gains(beta, vbe)

    ib = (vcc - vbe) / (rb + (beta + 1) * re)

    return _solve(vcc, rc, re, beta, vbe, ib, mode="emitter")
