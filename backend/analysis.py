import pandas as pd

def parse_bp(bp_str):
    try:
        systolic, diastolic = bp_str.split("/")
        return float(systolic), float(diastolic)
    except:
        return None, None

def is_float(value):
    try:
        float(value)
        return True
    except:
        return False

def safe_float(val):
    return round(val, 2) if pd.notnull(val) else None

def analyze_observations(obs_list):
    data = {}
    for o in obs_list:
        if o.type == "blood_pressure":
            systolic, diastolic = parse_bp(o.value)
            if systolic and diastolic:
                data.setdefault("systolic_bp", []).append({"date": o.date, "value": systolic})
                data.setdefault("diastolic_bp", []).append({"date": o.date, "value": diastolic})
        elif is_float(o.value):
            data.setdefault(o.type, []).append({"date": o.date, "value": float(o.value)})

    results = {}
    for key, values in data.items():
        df = pd.DataFrame(values).sort_values(by="date")
        n = len(df)
        window = min(7, max(1, n))  # tự động điều chỉnh window

        df["rolling_mean"] = df["value"].rolling(window=window).mean()
        df["rolling_std"] = df["value"].rolling(window=window).std()

        trend = "increasing" if pd.notnull(df["rolling_mean"].iloc[-1]) and df["rolling_mean"].iloc[-1] > df["rolling_mean"].iloc[0] else "decreasing"

        results[key] = {
            "trend": trend,
            "mean": safe_float(df["value"].mean()),
            "std_dev": safe_float(df["value"].std()),
            "latest_rolling_mean": safe_float(df["rolling_mean"].iloc[-1]),
            "data_points": n
        }

    return results

def classify_risk(obs_list):
    latest = {}
    for o in obs_list:
        if o.type == "blood_pressure":
            systolic, _ = parse_bp(o.value)
            if systolic:
                latest["systolic_bp"] = systolic
        elif is_float(o.value):
            latest[o.type] = float(o.value)

    score = 0
    if latest.get("heart_rate", 0) > 100:
        score += 1
    if latest.get("temperature", 0) > 38:
        score += 1
    if latest.get("spo2", 100) < 94:
        score += 1
    if latest.get("systolic_bp", 120) > 140:
        score += 1

    if score >= 3:
        return "High"
    elif score == 2:
        return "Medium"
    else:
        return "Low"
