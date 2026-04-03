import re
from typing import Any, Dict, List, Tuple

import pandas as pd
from sklearn.ensemble import RandomForestClassifier


SEMANTIC_LABELS = [
    "Email",
    "Address",
    "DateTime",
    "Name",
    "Phone",
    "URL",
    "PostalCode",
    "Identifier",
    "Boolean",
    "Numeric",
    "Currency",
    "Percentage",
    "Category",
    "FreeText",
    "Unknown",
]


def _to_text(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def _regex_density(text: pd.Series, pattern: str, case: bool = False) -> float:
    if text.empty:
        return 0.0
    return float(text.str.contains(pattern, regex=True, case=case, na=False).mean())


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _name_keyword_density(column_name: str, keywords: List[str]) -> float:
    low = column_name.lower()
    return 1.0 if any(k in low for k in keywords) else 0.0


def _column_features(column_name: str, values: pd.Series) -> list[float]:
    text = _to_text(values)
    non_empty = text[text != ""]

    row_count = max(1, len(text))
    non_empty_ratio = len(non_empty) / row_count
    unique_ratio = float(non_empty.nunique(dropna=True) / max(1, len(non_empty))) if len(non_empty) else 0.0

    lengths = non_empty.str.len() if len(non_empty) else pd.Series([0])
    avg_len = _safe_float(lengths.mean())
    std_len = _safe_float(lengths.std())

    total_chars = max(1.0, float(non_empty.str.len().sum()))
    digit_density = float(non_empty.str.count(r"\d").sum()) / total_chars if len(non_empty) else 0.0
    alpha_density = float(non_empty.str.count(r"[A-Za-z]").sum()) / total_chars if len(non_empty) else 0.0
    space_density = float(non_empty.str.count(r"\s").sum()) / total_chars if len(non_empty) else 0.0
    punct_density = float(non_empty.str.count(r"[^\w\s]").sum()) / total_chars if len(non_empty) else 0.0

    numeric_ratio = float(pd.to_numeric(non_empty, errors="coerce").notna().mean()) if len(non_empty) else 0.0
    datetime_ratio = float(pd.to_datetime(non_empty, errors="coerce").notna().mean()) if len(non_empty) else 0.0
    bool_ratio = (
        float(non_empty.str.lower().isin(["true", "false", "1", "0", "yes", "no", "y", "n"]).mean())
        if len(non_empty)
        else 0.0
    )

    email_density = _regex_density(non_empty, r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
    url_density = _regex_density(non_empty, r"^(https?://|www\.)")
    phone_density = _regex_density(non_empty, r"^(\+?\d[\d\-()\s]{7,}\d)$")
    postal_density = _regex_density(non_empty, r"^\d{5}(-\d{4})?$|^[A-Za-z]\d[A-Za-z][ -]?\d[A-Za-z]\d$")
    currency_density = _regex_density(non_empty, r"^[\$€£¥]\s?\d|\d\s?(usd|eur|inr|gbp)$")
    percent_density = _regex_density(non_empty, r"^-?\d+(\.\d+)?%$")
    address_density = _regex_density(non_empty, r"\b(st|street|rd|road|ave|avenue|blvd|lane|ln|apt|suite|floor)\b")
    name_density = _regex_density(non_empty, r"^[A-Za-z][A-Za-z .'-]{1,}$")
    id_pattern_density = _regex_density(non_empty, r"^[A-Za-z]{0,4}[-_]?[A-Za-z0-9]{4,}$")

    # Column-name lexical priors
    kw_email = _name_keyword_density(column_name, ["email", "mail"])
    kw_address = _name_keyword_density(column_name, ["address", "addr", "street", "city", "state", "country"])
    kw_date = _name_keyword_density(column_name, ["date", "time", "timestamp", "created", "updated", "dob"])
    kw_name = _name_keyword_density(column_name, ["name", "first", "last", "fullname"])
    kw_phone = _name_keyword_density(column_name, ["phone", "mobile", "tel", "contact"])
    kw_url = _name_keyword_density(column_name, ["url", "website", "link", "uri", "domain"])
    kw_postal = _name_keyword_density(column_name, ["zip", "postal", "pincode"])
    kw_id = _name_keyword_density(column_name, ["id", "uuid", "guid", "key", "code"])
    kw_numeric = _name_keyword_density(column_name, ["qty", "quantity", "count", "number", "score", "age"])
    kw_currency = _name_keyword_density(column_name, ["amount", "price", "cost", "revenue", "salary", "income"])
    kw_percent = _name_keyword_density(column_name, ["percent", "rate", "ratio", "pct"])
    kw_bool = _name_keyword_density(column_name, ["is_", "has_", "flag", "enabled", "active", "valid"])

    return [
        non_empty_ratio,
        unique_ratio,
        avg_len,
        std_len,
        digit_density,
        alpha_density,
        space_density,
        punct_density,
        numeric_ratio,
        datetime_ratio,
        bool_ratio,
        email_density,
        url_density,
        phone_density,
        postal_density,
        currency_density,
        percent_density,
        address_density,
        name_density,
        id_pattern_density,
        kw_email,
        kw_address,
        kw_date,
        kw_name,
        kw_phone,
        kw_url,
        kw_postal,
        kw_id,
        kw_numeric,
        kw_currency,
        kw_percent,
        kw_bool,
    ]


def _prototype_series(values: List[str]) -> pd.Series:
    return pd.Series(values * 3)


def _synthetic_training_set() -> Tuple[list[list[float]], list[str]]:
    samples: Dict[str, List[Tuple[str, pd.Series]]] = {
        "Email": [
            ("email", _prototype_series(["alice@example.com", "bob@corp.io", "team@demo.org"])),
            ("user_email", _prototype_series(["name.surname@domain.net", "user1@test.ai"])),
        ],
        "Address": [
            ("address", _prototype_series(["123 Main St", "42 Market Road", "221B Baker Street"])),
            ("city_address", _prototype_series(["5 Avenue Lane", "10 Downing St"])),
        ],
        "DateTime": [
            ("created_at", _prototype_series(["2024-01-01", "2025/04/10", "12/31/2023"])),
            ("timestamp", _prototype_series(["2025-01-12 09:30:00", "2023-11-14 17:20:00"])),
        ],
        "Name": [
            ("full_name", _prototype_series(["John Doe", "Jane Smith", "Maria Garcia"])),
            ("first_name", _prototype_series(["Ravi", "Ananya", "Sam"])),
        ],
        "Phone": [
            ("phone", _prototype_series(["+1 555 202 3030", "(555) 111-2222", "9876543210"])),
        ],
        "URL": [
            ("website", _prototype_series(["https://example.com", "http://corp.io", "www.demo.org"])),
        ],
        "PostalCode": [
            ("zip_code", _prototype_series(["94105", "10001", "560001", "12345-6789"])),
        ],
        "Identifier": [
            ("user_id", _prototype_series(["USR_001", "A12B34", "550e8400-e29b-41d4-a716-446655440000"])),
            ("sku_code", _prototype_series(["SKU-1023", "PRD_7781", "INV-9812"])),
        ],
        "Boolean": [
            ("is_active", _prototype_series(["true", "false", "yes", "no", "1", "0"])),
        ],
        "Numeric": [
            ("count", _prototype_series(["10", "20", "35", "44", "58"])),
            ("score", _prototype_series(["91.5", "88.2", "76.0"])),
        ],
        "Currency": [
            ("amount", _prototype_series(["$12.30", "$99.99", "1200 usd", "€250.50"])),
        ],
        "Percentage": [
            ("success_rate", _prototype_series(["98%", "76.5%", "12%"])),
        ],
        "Category": [
            ("status", _prototype_series(["pending", "approved", "rejected", "hold"])),
            ("segment", _prototype_series(["A", "B", "C", "D"])),
        ],
        "FreeText": [
            ("comment", _prototype_series(["Customer requested a callback", "Long paragraph of notes goes here"])),
        ],
        "Unknown": [
            ("misc", _prototype_series(["@@@", "", "-", "n/a", "???"])),
        ],
    }

    x_train: list[list[float]] = []
    y_train: list[str] = []
    for label, groups in samples.items():
        for column_name, series in groups:
            x_train.append(_column_features(column_name, series))
            y_train.append(label)

    return x_train, y_train


def _heuristic_override(column_name: str, series: pd.Series) -> Tuple[str, float] | None:
    text = _to_text(series)
    non_empty = text[text != ""]
    if non_empty.empty:
        return ("Unknown", 0.7)

    email_density = _regex_density(non_empty, r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
    url_density = _regex_density(non_empty, r"^(https?://|www\.)")
    phone_density = _regex_density(non_empty, r"^(\+?\d[\d\-()\s]{7,}\d)$")
    percent_density = _regex_density(non_empty, r"^-?\d+(\.\d+)?%$")

    if email_density >= 0.7:
        return ("Email", min(0.99, 0.75 + email_density * 0.2))
    if url_density >= 0.7:
        return ("URL", min(0.99, 0.75 + url_density * 0.2))
    if phone_density >= 0.7:
        return ("Phone", min(0.99, 0.75 + phone_density * 0.2))
    if percent_density >= 0.75:
        return ("Percentage", min(0.99, 0.75 + percent_density * 0.2))

    numeric_ratio = float(pd.to_numeric(non_empty, errors="coerce").notna().mean())
    datetime_ratio = float(pd.to_datetime(non_empty, errors="coerce").notna().mean())
    bool_ratio = float(non_empty.str.lower().isin(["true", "false", "1", "0", "yes", "no", "y", "n"]).mean())
    unique_ratio = float(non_empty.nunique(dropna=True) / max(1, len(non_empty)))
    avg_len = float(non_empty.str.len().mean())

    if bool_ratio > 0.9:
        return ("Boolean", 0.9)
    if datetime_ratio > 0.9:
        return ("DateTime", 0.9)
    if numeric_ratio > 0.95:
        return ("Numeric", 0.85)
    if unique_ratio > 0.97 and avg_len > 6 and _name_keyword_density(column_name, ["id", "key", "code", "uuid", "guid"]):
        return ("Identifier", 0.85)

    return None


def infer_semantic_schema_labels(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Robust semantic inference for arbitrary CSV schemas.

    Uses a RandomForest classifier with rich pattern/statistical features and
    keyword-aware priors, then applies conservative heuristic overrides when
    evidence is very strong.
    """
    if df is None or df.empty:
        return {"columns": {}, "model": "random_forest", "status": "skipped", "reason": "empty_dataframe"}

    x_train, y_train = _synthetic_training_set()
    clf = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        class_weight="balanced_subsample",
        max_depth=14,
        min_samples_leaf=1,
    )
    clf.fit(x_train, y_train)

    labels: Dict[str, Dict[str, Any]] = {}
    for col in df.columns:
        col_name = str(col)
        feats = _column_features(col_name, df[col])

        probs = clf.predict_proba([feats])[0]
        classes = clf.classes_.tolist()
        ranked = sorted(zip(classes, probs), key=lambda item: item[1], reverse=True)

        predicted = ranked[0][0]
        confidence = float(ranked[0][1])

        heuristic = _heuristic_override(col_name, df[col])
        if heuristic is not None and heuristic[1] >= confidence:
            predicted, confidence = heuristic

        if confidence < 0.4:
            predicted = "Unknown"

        labels[col_name] = {
            "label": predicted,
            "confidence": round(confidence, 4),
            "top_candidates": [
                {"label": lbl, "probability": round(float(prob), 4)}
                for lbl, prob in ranked[:3]
            ],
            "feature_signature": {
                "non_empty_ratio": round(feats[0], 4),
                "unique_ratio": round(feats[1], 4),
                "avg_length": round(feats[2], 4),
                "digit_density": round(feats[4], 4),
                "numeric_ratio": round(feats[8], 4),
                "datetime_ratio": round(feats[9], 4),
                "bool_ratio": round(feats[10], 4),
                "email_density": round(feats[11], 4),
                "url_density": round(feats[12], 4),
                "phone_density": round(feats[13], 4),
                "postal_density": round(feats[14], 4),
                "currency_density": round(feats[15], 4),
                "percentage_density": round(feats[16], 4),
            },
        }

    return {
        "model": "random_forest",
        "labels": SEMANTIC_LABELS,
        "columns": labels,
        "status": "completed",
        "notes": "Designed for schema-agnostic CSV inference with mixed/noisy data.",
    }
