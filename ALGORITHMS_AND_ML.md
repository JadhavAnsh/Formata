# Algorithms and Machine Learning Implementation Guide

## Overview
The Formata platform uses multiple machine learning algorithms and statistical methods for data processing, cleaning, and analysis. This document explains all algorithms used, their implementations, and their locations in the codebase.

---

## 1. Random Forest Classifier (Semantic Schema Labeling)

### **What It Does**
Automatically classifies columns in CSV/data files into 15 semantic labels to understand data types and formats beyond simple numeric/text detection.

### **Algorithm Details**
- **Library**: `sklearn.ensemble.RandomForestClassifier`
- **Model Configuration**: 
  - Number of Trees: 300
  - Class Weight: Balanced (handles imbalanced labels)
  - Random State: 42 (reproducible results)
  
### **15 Semantic Labels Recognized**
1. **Email** - Email addresses (e.g., john@example.com)
2. **Address** - Street addresses (e.g., 123 Main St, 5 Avenue Lane)
3. **DateTime** - Date and timestamp values (e.g., 2024-01-01, 2025-01-12 09:30:00)
4. **Name** - Person names (e.g., John Doe, Jane Smith)
5. **Phone** - Phone numbers (e.g., +1 555 202 3030, (555) 111-2222)
6. **URL** - Web URLs (e.g., https://example.com, www.demo.org)
7. **PostalCode** - Postal/Zip codes (e.g., 94105, 12345-6789)
8. **Identifier** - IDs/codes/UUIDs (e.g., USR_001, SKU-1023)
9. **Boolean** - True/False values (e.g., true, false, yes, no, 1, 0)
10. **Numeric** - Numbers (e.g., 10, 20.5, 3.14)
11. **Currency** - Money values (e.g., $12.30, €250.50, 1200 usd)
12. **Percentage** - Percentage values (e.g., 98%, 76.5%)
13. **Category** - Categorical data (e.g., pending, approved, rejected)
14. **FreeText** - Unstructured text (e.g., customer comments, notes)
15. **Unknown** - Could not classify or missing data

### **Feature Extraction (32-Dimensional Feature Vector)**

The model extracts the following features from each column:

**Statistical Features (8):**
- Non-empty value ratio
- Unique values ratio
- Average string length
- Standard deviation of string length

**Character Composition (4):**
- Digit density
- Alphabetic character density
- Space density
- Punctuation density

**Type Detection Ratios (3):**
- Numeric ratio (how many values can be parsed as numbers)
- DateTime ratio (how many values are dates)
- Boolean ratio (how many values are true/false)

**Pattern Matching Densities (7):**
- Email pattern density (regex matching email format)
- URL pattern density (regex matching web URLs)
- Phone pattern density (regex matching phone formats)
- Postal code pattern density (regex matching US/Canadian ZIP/postal)
- Currency pattern density (regex matching currency symbols)
- Percentage pattern density (regex matching % symbols)
- Address pattern density (regex matching street terms)
- Name pattern density (regex matching name formats)
- ID pattern density (regex matching unique identifiers)

**Keyword-Based Priors (12):**
- Column name contains email keywords (email, mail)
- Column name contains address keywords (address, street, city, state, country)
- Column name contains date keywords (date, time, timestamp, created, updated, dob)
- Column name contains name keywords (name, first, last, fullname)
- Column name contains phone keywords (phone, mobile, tel, contact)
- Column name contains URL keywords (url, website, link, domain)
- Column name contains postal keywords (zip, postal, pincode)
- Column name contains ID keywords (id, uuid, guid, key, code)
- Column name contains numeric keywords (qty, quantity, count, number, score, age)
- Column name contains currency keywords (amount, price, cost, revenue, salary, income)
- Column name contains percentage keywords (percent, rate, ratio, pct)
- Column name contains boolean keywords (is_, has_, flag, enabled, active, valid)

### **Training Data**
- **Synthetic Training Set**: Generated from ~40 example samples (3+ examples per label)
- **Training Process**: Built on-the-fly in `_synthetic_training_set()` function
- **No External Model**: Model is trained every time; not pre-saved (ensures consistency)

### **Heuristic Overrides**
After RandomForest classification, high-confidence patterns trigger deterministic overrides:
- Email density ≥ 70% → Override to "Email" (confidence: 0.75-0.99)
- URL density ≥ 70% → Override to "URL"
- Phone density ≥ 70% → Override to "Phone"
- Percentage density ≥ 75% → Override to "Percentage"
- Boolean ratio > 90% → Override to "Boolean" (confidence: 0.9)
- DateTime ratio > 90% → Override to "DateTime"
- Numeric ratio > 95% → Override to "Numeric"
- Unique ratio > 97% + avg_len > 6 + ID keywords → Override to "Identifier"

### **Output**
Returns a dictionary with:
```python
{
  "column_name": {
    "label": "Email",              # Primary semantic label
    "confidence": 0.95,             # 0-1 confidence score
    "top_candidates": [             # Top 3 predictions from RandomForest
      {"label": "Email", "confidence": 0.95},
      {"label": "URL", "confidence": 0.03},
      {"label": "FreeText", "confidence": 0.02}
    ],
    "features": {...}               # 32-dim feature vector used
  }
}
```

### **Location in Code**
- **Main Function**: [`backend/app/services/normalizer.py`](backend/app/services/normalizer.py#L287)
  - `infer_semantic_schema_labels(df)` - Main entry point
  - `_column_features(column_name, values)` - Feature extraction
  - `_synthetic_training_set()` - Training data generator
  - `_heuristic_override()` - Conservative override logic

### **Where It's Used**
1. **Profiling Page** - Shows detected schema for uploaded CSV
2. **Processing Pipeline** - Auto-assigns semantic labels if `enable_auto_schema=True` (default: True)
3. **Filter Form** - Displays detected types for filter suggestions
4. **Data Quality Scoring** - Contributes to overall data quality assessment

### **Performance**
- Processing time: ~100ms for typical CSV (1000s of columns)
- Can process files with 1000+ columns
- Gatable via `enable_auto_schema` config flag

---

## 2. KNN Imputer (Missing Data Handling)

### **What It Does**
Uses K-Nearest Neighbors to intelligently fill missing numeric values based on similarity to other rows.

### **Algorithm Details**
- **Library**: `sklearn.impute.KNNImputer`
- **Configuration**:
  - k (n_neighbors): 5 neighbors
  - Weights: Distance-weighted (closer neighbors have more influence)
  - Distance Metric: Euclidean

### **How It Works**
1. Identifies numeric columns with missing values
2. For each missing value, finds the 5 most similar rows (based on other numeric columns)
3. Calculates weighted average of those 5 neighbors' values
4. Fills the missing value with the weighted average
5. Preserves non-numeric columns (text, dates) unchanged

### **Key Features**
- **Multi-dimensional approximation**: Uses correlations between columns
- **Distance-weighted**: Closer neighbors have more influence than distant ones
- **Handles NaN gracefully**: Uses only available values for distance calculation
- **Preserves data types**: Returns numeric DataFrame with original index

### **Output**
Returns tuple: `(imputed_dataframe, imputation_report)`
```python
Report includes:
{
  "status": "imputed",
  "method": "knn",
  "n_neighbors": 5,
  "columns": {
    "age": {
      "missing_before": 45,
      "missing_after": 0
    },
    "salary": {
      "missing_before": 12,
      "missing_after": 0
    }
  }
}
```

### **Location in Code**
- **Main Function**: [`backend/app/services/missing_data.py`](backend/app/services/missing_data.py#L15)
  - `knn_impute_dataframe(df, target_columns, n_neighbors)` - Main KNN imputation
  - Called with optional flag `use_knn_for_smart=True`

### **Where It's Used**
1. **Processing Pipeline** - Stage 6 (Missing Data Handling)
   - Activated via `missing_data_strategy="fill_smart"` 
   - Or via `use_knn_for_smart=True` flag
2. **Smart Imputation Strategy** - Optional intelligent filling
3. **Preserves Data Integrity** - Fills based on actual data patterns, not arbitrary defaults

### **Configuration**
- Optional feature (not always enabled)
- Can be combined with other strategies (fill_mean, fill_median, fill_mode, etc.)
- Recommended for: Numeric columns with natural correlations (e.g., age + salary)

---

## 3. Isolation Forest (Outlier Detection)

### **What It Does**
Detects outliers/anomalies in multi-dimensional numeric data using a tree-based isolation approach.

### **Algorithm Details**
- **Library**: `sklearn.ensemble.IsolationForest`
- **Configuration**:
  - Contamination: 0.05 (expects ~5% contamination in data, range: 0.1%-30%)
  - Number of trees: 200
  - Random state: 42 (reproducible)

### **How It Works**
1. Builds isolation trees to isolate anomalies
2. Identifies rows that are isolated from the majority (anomalies)
3. Scores each row (lower = more anomalous)
4. Marks rows as inliers (1) or outliers (-1) based on contamination threshold

### **Hybrid Fallback Strategy**
Isolation Forest results are compared with IQR (Interquartile Range) filtering:
- **IQR Method**: Uses statistical bounds Q1 - 1.5×IQR to Q3 + 1.5×IQR
- **Fallback Logic**: If IQR filtering is stricter (removes more rows), uses IQR results
- **Benefit**: Prevents false negatives; uses stricter detection

### **Output**
Cleaned DataFrame with outliers removed, preserving all columns.

### **Location in Code**
- **Main Function**: [`backend/app/services/noise.py`](backend/app/services/noise.py#L60)
  - `remove_outliers(df, columns, contamination, random_state)` - Main outlier detection
  - Auto-detects numeric columns if not specified
  - Requires ≥2 numeric columns to activate

### **Where It's Used**
1. **Processing Pipeline** - Stage 8 (Outlier Removal)
   - Activated via `remove_outliers=True` flag
   - Default: False (disabled by default for performance)
2. **Data Cleaning** - Removes suspicious/anomalous rows
3. **Quality Assurance** - Improves data consistency

### **Performance**
- Time: ~50-100ms for 100k rows with 5 numeric columns
- Scales with number of rows and numeric columns
- Can be disabled for faster processing via `remove_outliers=False`

---

## 4. Sentence Transformers (Semantic Deduplication)

### **What It Does**
Uses neural embeddings to detect near-duplicate rows that aren't exact matches (e.g., rows with typos or slight variations).

### **Algorithm Details**
- **Library**: `sentence_transformers.SentenceTransformer`
- **Model**: "all-MiniLM-L6-v2"
  - 384-dimensional embeddings
  - Fast and lightweight
  - Pre-trained on semantic similarity
  - Downloads ~22MB model on first run
- **Similarity Metric**: Cosine similarity (normalized embeddings)
- **Threshold**: 0.92 (92% similarity = considered duplicate)

### **How It Works**
1. Converts row data to text format (e.g., "name:John Doe | email:john@example.com")
2. Encodes each row text to 384-dim vector representation
3. Computes cosine similarity between all row pairs
4. Identifies pairs with similarity ≥ 0.92
5. Removes one row from each near-duplicate pair

### **3-Stage Deduplication Pipeline**
1. **Exact Duplicates** - Row-for-row identical (fastest)
2. **Normalized Duplicates** - Lowercased, whitespace-trimmed identical text
3. **Semantic Near-Duplicates** - High similarity embeddings (most expensive)

### **Safety Fallback**
- If semantic model fails to load (network/memory issue): gracefully falls back to stages 1 & 2
- Logging warns but doesn't crash
- Continues processing with normalized deduplication only

### **Limitations**
- Only runs on datasets ≤5000 rows (skipped for larger datasets)
- Requires ~200-300MB memory for embeddings
- Takes ~5-10 seconds for 1000 rows

### **Output**
Deduplicated DataFrame with no exact or semantic near-duplicates.

### **Location in Code**
- **Main Function**: [`backend/app/services/noise.py`](backend/app/services/noise.py#L32)
  - `remove_duplicates(df, semantic_threshold)` - Main deduplication
  - `_get_semantic_model()` - Model singleton (loads once, reused)
  - `_semantic_row_text()` - Converts rows to text for encoding

### **Where It's Used**
1. **Processing Pipeline** - Stage 7 (Deduplication)
   - Activated via `remove_duplicates=True` flag (default: True)
   - Includes all 3 stages: exact → normalized → semantic
2. **Data Quality** - Removes redundant rows
3. **Reduces File Size** - Eliminates near-duplicates

### **Configuration**
- Threshold: 0.92 (adjustable, range: 0.85-0.99)
- Can be disabled entirely via `remove_duplicates=False`
- Model path: Cached by Hugging Face transformers library

---

## 5. Kolmogorov-Smirnov (KS) Test (Data Drift Detection)

### **What It Does**
Detects statistical distribution changes (drift) in numeric columns compared to a clean baseline.

### **Algorithm Details**
- **Library**: `scipy.stats.ks_2samp`
- **Statistical Test**: Two-sample KS test
- **Null Hypothesis**: Current data has same distribution as baseline
- **Alpha (significance level)**: 0.05 (5% chance of false positive)
- **Test Statistic**: Maximum absolute difference between cumulative distributions

### **How It Works**
1. Loads clean baseline statistics (from first successful job run)
2. For each numeric column in baseline:
   - Extracts numeric values from current data
   - Computes KS statistic (max divergence between distributions)
   - Calculates p-value (probability of observing this if distributions are same)
3. **Decision**: If p-value < 0.05, column has drifted
4. Returns list of drifted columns and statistics

### **Baseline Creation**
- Saved after first successful processing run
- Stored as JSON: `storage/reports/clean_baseline_stats.json`
- Contains 50-sample values per numeric column
- Used as reference for all future drift comparisons

### **Output**
```python
{
  "status": "drift_detected" or "ok" or "no_baseline",
  "drifted_columns": ["age", "salary"],
  "column_results": {
    "age": {
      "ks_statistic": 0.125,
      "p_value": 0.0001,   # < 0.05 = drifted
      "drifted": True
    },
    "salary": {
      "ks_statistic": 0.082,
      "p_value": 0.0001,
      "drifted": True
    }
  }
}
```

### **Location in Code**
- **Main Functions**: [`backend/app/services/profiler.py`](backend/app/services/profiler.py#L58)
  - `detect_data_drift(df, baseline_path, alpha)` - Main drift detection
  - `save_clean_baseline(df, baseline_path)` - Create baseline after first run
  - `_build_distribution_baseline(df)` - Extract statistics from clean data

### **Where It's Used**
1. **Processing Pipeline** - Stage 11 (Drift Detection)
   - Activated via `enable_drift_detection=True` flag (default: True)
   - Runs after all cleaning steps
2. **Data Quality Scoring** - Contributes to quality assessment
3. **Baseline Management** - Auto-saves baseline after first processing

### **Configuration**
- Alpha: 0.05 (significance level, adjustable)
- Baseline path: `storage/reports/clean_baseline_stats.json`
- Can be disabled via `enable_drift_detection=False`

### **Use Case**
- Early warning if data quality degrades (e.g., new source, pipeline changes)
- Validates data consistency across time
- Helps identify data issues before they impact analysis

---

## 6. IQR Filtering (Interquartile Range Outlier Detection)

### **What It Does**
Statistical outlier detection using quartile-based bounds. Used as fallback/comparison with Isolation Forest.

### **Algorithm Details**
- **Statistical Method**: Quartile-based bounds
- **Formula**: 
  - Q1 = 25th percentile
  - Q3 = 75th percentile
  - IQR = Q3 - Q1
  - Lower bound = Q1 - 1.5 × IQR
  - Upper bound = Q3 + 1.5 × IQR
  - Outliers: Values outside [lower, upper]

### **How It Works**
1. For each numeric column:
   - Calculates Q1, Q3, and IQR
   - Computes statistical bounds
   - Marks values outside bounds as outliers
2. Removes rows containing any outlier
3. Compared to Isolation Forest results; uses stricter method

### **Location in Code**
- **Used in**: [`backend/app/services/noise.py`](backend/app/services/noise.py#L60)
  - Lines ~100-130: Fallback IQR filtering
  - Automatically activated if stricter than Isolation Forest

### **Where It's Used**
1. **Hybrid Outlier Detection** - Fallback comparison method
2. **Conservative Approach** - Ensures most suspicious rows are removed
3. **Interpretability** - Statistical method easier to explain than isolation trees

---

## 7. Other Algorithms & Techniques

### **7.1 Regex Pattern Matching (Data Type Detection)**
- **Location**: [`backend/app/services/normalizer.py`](backend/app/services/normalizer.py) & [`backend/app/services/filtering.py`](backend/app/services/filtering.py)
- **Purpose**: Identifies patterns in data (emails, URLs, phone numbers, etc.)
- **Patterns Used**:
  - Email: `^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$`
  - URL: `^(https?://|www\.)`
  - Phone: `^(\+?\d[\d\-()\s]{7,}\d)$`
  - PostalCode: `^\d{5}(-\d{4})?$|^[A-Za-z]\d[A-Za-z][ -]?\d[A-Za-z]\d$` (US/Canada)
  - Currency: `^[\$€£¥]\s?\d|\d\s?(usd|eur|inr|gbp)$`
  - Percentage: `^-?\d+(\.\d+)?%$`
  - Address: `\b(st|street|rd|road|ave|avenue|blvd|lane|ln|apt|suite|floor)\b`

### **7.2 String Vectorization (Document-to-Vector)**
- **Library**: `sklearn.feature_extraction.text.TfidfVectorizer`
- **Purpose**: Converts text data to TF-IDF vectors for analysis/ML
- **Location**: [`backend/app/services/parser.py`](backend/app/services/parser.py)
- **Output**: Sparse vectors saved as `.pkl` and `.h5` files
- **Usage**: Optional, can be disabled via `enable_vectorization=False`

### **7.3 Data Quality Scoring (Custom Algorithm)**
- **Location**: [`backend/app/services/validation.py`](backend/app/services/validation.py)
- **Formula**: Weighted combination of 4 factors:
  - **Completeness** (40%): % of non-null values
  - **Validity** (30%): % of valid values (correct data types)
  - **Consistency** (20%): Low duplicate row ratio
  - **Accuracy** (10%): Low outlier ratio
- **Score Range**: 0-100
- **Interpretation**:
  - 90-100: Excellent
  - 75-89: Good
  - 60-74: Fair
  - <60: Poor

### **7.4 Ydata-Profiling (Statistical Profiling)**
- **Library**: `ydata_profiling.ProfileReport`
- **Purpose**: Generates comprehensive HTML report with statistics
- **Location**: [`backend/app/services/profiler.py`](backend/app/services/profiler.py)
- **Output**: HTML file with histograms, correlations, missing values analysis
- **Usage**: Optional, can be disabled via `enable_profiles=False` (default: False)
- **Performance**: ~2-5 seconds for typical datasets

### **7.5 Missing Data Strategy Functions**
- **Location**: [`backend/app/services/missing_data.py`](backend/app/services/missing_data.py)
- **Strategies**:
  1. `fill_mean` - Fill with column mean (numeric only)
  2. `fill_median` - Fill with column median (numeric, robust to outliers)
  3. `fill_mode` - Fill with most common value (categorical & numeric)
  4. `fill_smart` - Skewness-aware (mean if low skew, median if high skew)
  5. `fill_forward` - Use previous row value (time-series data)
  6. `fill_backward` - Use next row value
  7. `drop_rows` - Delete rows with missing values
  8. `drop_columns` - Delete columns with missing values
  9. `flag` - Create binary flag column for missing values
  10. `preserve` - Leave missing values as-is (default)

---

## Processing Pipeline Workflow

### **13-Stage Processing Pipeline** [`backend/app/services/pipeline.py`](backend/app/services/pipeline.py)

```
1. Data Parsing (CSV/JSON/Excel)
   ↓
2. Type Enforcement (Parse to correct types)
   ↓
3. Missing Data Handling (Fill/Drop/Flag)
   ↓
4. Normalization (Standardize formatting)
   ↓
5. Semantic Schema Inference (RandomForest - 15 labels)
   ↓
6. Deduplication (Exact → Normalized → Semantic)
   ↓
7. Outlier Removal (IsolationForest + IQR hybrid)
   ↓
8. Type Validation (Enforce semantic types)
   ↓
9. Filter Application (User-defined rules)
   ↓
10. Quality Scoring (Completeness/Validity/Consistency/Accuracy)
    ↓
11. Drift Detection (KS-test vs baseline)
    ↓
12. Profiling & Vectorization (HTML report + TF-IDF vectors - Optional)
    ↓
13. Result Assembly (Gather before/after snapshots, timing, quality scores)
```

### **Configurable Flags**
```python
{
  "enable_auto_schema": True,           # RandomForest schema labeling
  "enable_drift_detection": True,       # KS-test drift detection
  "enable_profiles": False,             # Ydata-profiling HTML generation
  "enable_vectorization": False,        # TF-IDF text vectorization
  "remove_duplicates": True,            # Deduplication (all 3 stages)
  "remove_outliers": False,             # IsolationForest outlier removal
  "missing_data_strategy": "preserve",  # See 7.5 above
  "use_knn_for_smart": False,           # KNN Imputation for smart strategy
  "result_preview_rows": 2000           # Max rows in before/after snapshot
}
```

---

## Performance Characteristics

| Algorithm | Time (on 100k rows) | Space | Status |
|-----------|-------------------|-------|--------|
| RandomForest Schema (1000 cols) | ~100ms | Low | ✅ Always on |
| KNN Imputation | ~500ms | Low | ✅ Optional |
| IsolationForest (5 cols) | ~80ms | Low | ✅ Optional |
| IQR Filtering | ~50ms | Low | ✅ Automatic fallback |
| Semantic Dedupe (≤5k rows) | ~8s | Medium | ✅ Optional |
| KS Drift Test (50 cols) | ~200ms | Low | ✅ Optional |
| Ydata Profiling | ~5s | High | ✅ Optional (default: Off) |
| TF-IDF Vectorization | ~2s | High | ✅ Optional (default: Off) |

---

## Configuration Examples

### **Fast Mode** (Default - ~20 seconds for 3.4MB file)
```python
{
  "enable_auto_schema": True,
  "enable_drift_detection": True,
  "enable_profiles": False,         # Disabled for speed
  "enable_vectorization": False,    # Disabled for speed
  "remove_outliers": False,         # Disabled for speed
  "result_preview_rows": 2000       # Reduced snapshot size
}
```

### **Deep Intelligence Mode** (Slower but comprehensive)
```python
{
  "enable_auto_schema": True,
  "enable_drift_detection": True,
  "enable_profiles": True,          # Enabled for analysis
  "enable_vectorization": True,     # Enabled for ML features
  "remove_outliers": True,          # Enabled for cleaning
  "remove_duplicates": True,        # All dedup stages
  "use_knn_for_smart": True,        # KNN imputation
  "result_preview_rows": 100000     # Full snapshots
}
```

---

## Key Files Reference

| Algorithm | File | Key Functions |
|-----------|------|----------------|
| RandomForest | `backend/app/services/normalizer.py` | `infer_semantic_schema_labels()`, `_column_features()` |
| KNN Imputation | `backend/app/services/missing_data.py` | `knn_impute_dataframe()`, `smart_impute_column()` |
| IsolationForest | `backend/app/services/noise.py` | `remove_outliers()` |
| Semantic Dedupe | `backend/app/services/noise.py` | `remove_duplicates()`, `_get_semantic_model()` |
| KS Test | `backend/app/services/profiler.py` | `detect_data_drift()`, `save_clean_baseline()` |
| Profiling | `backend/app/services/profiler.py` | `generate_profile_html()` |
| Pipeline | `backend/app/services/pipeline.py` | `run_processing_pipeline()` |

---

## Dependencies

```
scikit-learn        >= 1.3.0  (RandomForest, KNN, IsolationForest, TF-IDF)
scipy               >= 1.10.0 (KS test statistics)
pandas              >= 2.0.0  (Data manipulation)
numpy               >= 1.24.0 (Numerical operations)
sentence-transformers >= 2.2.0 (Semantic embeddings - optional)
ydata-profiling     >= 4.0.0  (Data profiling HTML - optional)
```

---

## Future Enhancements

1. **Pre-trained Model Persistence**: Save RandomForest model to disk for faster loading
2. **Incremental Learning**: Update model with new data instead of retraining from scratch
3. **GPU Acceleration**: Use CUDA for large-scale vectorization
4. **Custom Embeddings**: Fine-tune semantic transformer for domain-specific data
5. **Anomaly Trend Detection**: Track drift patterns over time, not just individual columns
6. **Model Explainability**: Add SHAP values to show which features drove schema classification

---

**Document Version**: 1.0  
**Last Updated**: April 2026  
**Maintained By**: Formata ML Team
