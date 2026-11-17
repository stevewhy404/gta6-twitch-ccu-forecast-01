"""gta6-twitch-ccu-forecast-01 forecaster in Python 3.13 (standard library only).

Learns the empirical release-day shape (hourly log-ratios relative to hour 1) from comparables
provided in the case data, and applies robust spread estimation for quantile forecasts.
"""

import json
import math
import os
from pathlib import Path

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.645, -0.674, 0, 0.674, 1.645]

def round2(x: float) -> float | int:
    scaled = x * 100
    whole = math.floor(scaled)
    if scaled - whole >= 0.5:
        whole += 1
    value = whole / 100
    return int(value) if value.is_integer() else value

def extract_pseudo_comparables(comparables):
    cases = []
    for comp in comparables:
        name = comp.get('name', '')
        if 'Grand Theft Auto' in name:
            continue
        day_start = comp.get('day_start')
        hourly = comp.get('hourly', [])
        if not day_start or not hourly:
            continue
        hourly_map = {row['from']: row['viewers'] for row in hourly}
        p1_val = hourly_map.get(day_start)
        if p1_val is None:
            date_prefix = day_start[:10]
            matching = [r for r in hourly if r['from'].startswith(date_prefix)]
            if not matching:
                continue
            matching.sort(key=lambda x: x['from'])
            p1_row = matching[0]
            day_start_actual = p1_row['from']
            p1_val = p1_row['viewers']
            actuals = {}
            from datetime import datetime, timedelta
            try:
                dt = datetime.fromisoformat(day_start_actual.replace('Z', '+00:00'))
                for h in range(2, 25):
                    dt_h = dt + timedelta(hours=h-1)
                    t_str = dt_h.isoformat().replace('+00:00', 'Z')
                    if t_str in hourly_map:
                        actuals[h] = hourly_map[t_str]
            except Exception:
                continue
        else:
            actuals = {}
            from datetime import datetime, timedelta
            try:
                dt = datetime.fromisoformat(day_start.replace('Z', '+00:00'))
                for h in range(2, 25):
                    dt_h = dt + timedelta(hours=h-1)
                    t_str = dt_h.isoformat().replace('+00:00', 'Z')
                    if t_str in hourly_map:
                        actuals[h] = hourly_map[t_str]
            except Exception:
                continue

        if len(actuals) >= 20:
            cases.append({'p1': p1_val, 'actuals': actuals})
    return cases

def forecast_case(case: dict, name: str) -> dict:
    if case["levels"] != LEVELS:
        raise ValueError(f"{name} asks for levels {case['levels']}, not {LEVELS}")
    first = next((k for k in case["known"] if k["hour"] == 1), None)
    if first is None:
        raise ValueError(f"{name} has no hour-1 print")
    p1 = max(1.0, float(first["viewers"]))

    comparables = case.get("comparables", [])
    pseudo_cases = extract_pseudo_comparables(comparables)

    log_ratios_by_hour = {h: [] for h in range(2, 25)}
    for c in pseudo_cases:
        cp1 = max(1.0, float(c['p1']))
        for h, y in c['actuals'].items():
            if 2 <= h <= 24:
                try:
                    lr = math.log(max(1.0, float(y))) - math.log(cp1)
                    log_ratios_by_hour[h].append(lr)
                except Exception:
                    pass

    median_lr = {}
    spread_sigma = {}
    for h in range(2, 25):
        lrs = log_ratios_by_hour[h]
        if lrs:
            s_lrs = sorted(lrs)
            n = len(s_lrs)
            med = s_lrs[n//2] if n%2 != 0 else (s_lrs[n//2-1] + s_lrs[n//2]) / 2.0
            median_lr[h] = med
            abs_devs = sorted([abs(x - med) for x in s_lrs])
            mean_abs = sum(abs_devs) / len(abs_devs)
            spread_sigma[h] = max(0.12, mean_abs * 1.15)
        else:
            median_lr[h] = 0.0
            spread_sigma[h] = 0.15 * math.sqrt(h - 1)

    hours_out = []
    for row in case["forecast"]:
        h = row["hour"]
        r = median_lr.get(h, 0.0)
        sig = spread_sigma.get(h, 0.15 * math.sqrt(h - 1))
        median_val = p1 * math.exp(r)
        qs = [round2(max(1.0, min(1e9, median_val * math.exp(z * sig)))) for z in Z]
        # Ensure non-decreasing
        for i in range(1, len(qs)):
            if qs[i] < qs[i-1]:
                qs[i] = qs[i-1]
        hours_out.append({"hour": h, "q": qs})

    return {"hours": hours_out}

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        forecast = forecast_case(case, path.name)
        (OUTPUT_DIR / f"{path.stem}.out").write_text(json.dumps(forecast, separators=(",", ":")) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
