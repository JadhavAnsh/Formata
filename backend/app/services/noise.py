# Deduplication and outlier removal

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from app.utils.logger import logger

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency guard
    SentenceTransformer = None


_semantic_model = None


def _get_semantic_model():
    global _semantic_model
    if _semantic_model is not None:
        return _semantic_model
    if SentenceTransformer is None:
        return None
    try:
        # Local-only model loading. Users can pre-cache this model for offline runs.
        _semantic_model = SentenceTransformer("all-MiniLM-L6-v2")
        return _semantic_model
    except Exception as exc:
        logger.warning(f"Semantic dedupe model unavailable, fallback to normalized dedupe: {exc}")
        return None


def _normalized_fingerprint(df: pd.DataFrame) -> pd.Series:
    normalized = df.map(lambda x: str(x).strip().lower() if pd.notna(x) else "")
    return normalized.apply(lambda row: "|".join(row.values.astype(str)), axis=1)


def _semantic_row_text(df: pd.DataFrame) -> list[str]:
    rendered_rows = []
    for _, row in df.iterrows():
        parts = []
        for col in df.columns:
            value = row[col]
            if pd.notna(value):
                parts.append(f"{col}:{str(value).strip()}")
        rendered_rows.append(" | ".join(parts))
    return rendered_rows


def remove_duplicates(df: pd.DataFrame, semantic_threshold: float = 0.92) -> pd.DataFrame:
    """
    Remove duplicate rows (schema-agnostic)
    """
    if df is None or df.empty:
        return df

    try:
        df_copy = df.copy()
        initial_count = len(df_copy)

        # 1) Remove exact duplicates first.
        df_deduped = df_copy.drop_duplicates()
        exact_dupes_removed = initial_count - len(df_deduped)
        logger.info(f"[DEDUPE] Initial rows: {initial_count}")
        logger.info(
            f"[DEDUPE] After exact match removal: {len(df_deduped)} (removed {exact_dupes_removed})"
        )

        # 2) Remove normalized-text duplicates.
        fingerprint = _normalized_fingerprint(df_deduped)
        df_deduped = df_deduped.loc[~fingerprint.duplicated()]
        normalized_removed = initial_count - exact_dupes_removed - len(df_deduped)
        if normalized_removed > 0:
            logger.info(
                f"[DEDUPE] After normalized removal: {len(df_deduped)} (removed {normalized_removed})"
            )

        # 3) Semantic near-duplicate pass for non-exact textual variants.
        model = _get_semantic_model()
        if model is not None and len(df_deduped) > 1 and len(df_deduped) <= 5000:
            row_text = _semantic_row_text(df_deduped)
            embeddings = model.encode(row_text, normalize_embeddings=True, show_progress_bar=False)
            vectors = np.array(embeddings)

            keep_mask = np.ones(len(df_deduped), dtype=bool)
            for idx in range(len(df_deduped)):
                if not keep_mask[idx]:
                    continue
                sims = np.dot(vectors[idx + 1 :], vectors[idx])
                near_dup_idx = np.where(sims >= semantic_threshold)[0]
                if near_dup_idx.size > 0:
                    keep_mask[idx + 1 + near_dup_idx] = False

            semantic_removed = int((~keep_mask).sum())
            if semantic_removed > 0:
                df_deduped = df_deduped.iloc[keep_mask]
                logger.info(
                    f"[DEDUPE] Semantic near-duplicates removed: {semantic_removed} "
                    f"(threshold={semantic_threshold})"
                )
        elif len(df_deduped) > 5000:
            logger.info("[DEDUPE] Semantic pass skipped for very large dataset (>5000 rows)")

        return df_deduped.reset_index(drop=True)

    except Exception as e:
        # Fail soft but log the error
        logger.warning(f"[DEDUPE ERROR] {str(e)}")
        return df


def remove_outliers(
    df: pd.DataFrame,
    columns: list | None = None,
    contamination: float = 0.05,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Remove outliers using IsolationForest for multi-dimensional anomaly detection.
    """
    if df is None or df.empty:
        return df

    cleaned_df = df.copy()

    try:
        # Auto-detect numeric-like columns if not provided
        if not columns:
            columns = []
            for col in cleaned_df.columns:
                numeric_series = pd.to_numeric(cleaned_df[col], errors="coerce")
                if numeric_series.notna().sum() > len(numeric_series) * 0.6:
                    columns.append(col)

        valid_cols = [c for c in columns if c in cleaned_df.columns]
        if not valid_cols:
            return cleaned_df.reset_index(drop=True)

        numeric_frame = cleaned_df[valid_cols].apply(pd.to_numeric, errors="coerce")
        if numeric_frame.dropna(how="all").shape[0] < 5:
            return cleaned_df.reset_index(drop=True)

        numeric_frame = numeric_frame.fillna(numeric_frame.median(numeric_only=True))

        if len(valid_cols) >= 2:
            iso = IsolationForest(
                contamination=max(0.001, min(float(contamination), 0.3)),
                random_state=random_state,
                n_estimators=200,
            )
            preds = iso.fit_predict(numeric_frame)
            inlier_mask = preds == 1
            cleaned_df = cleaned_df.loc[inlier_mask]
        else:
            cleaned_df = df.copy()

        # For small/simple datasets, IsolationForest can be conservative.
        # Compute IQR filtering too and keep the stricter result.
        fallback_mask = pd.Series(True, index=df.index)
        for col in valid_cols:
            series = pd.to_numeric(df[col], errors="coerce")
            if series.notna().sum() < 5:
                continue
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            if pd.isna(iqr) or iqr == 0:
                continue
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            col_mask = ((series >= lower) & (series <= upper)) | series.isna()
            fallback_mask = fallback_mask & col_mask

        iqr_filtered_df = df.loc[fallback_mask]
        if len(iqr_filtered_df) < len(cleaned_df):
            cleaned_df = iqr_filtered_df

    except Exception:
        return df

    return cleaned_df.reset_index(drop=True)
