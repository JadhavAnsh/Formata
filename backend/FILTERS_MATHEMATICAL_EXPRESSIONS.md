# Filter Operations: Mathematical Expressions & Implementation

This document provides mathematical formulations and descriptions of all filtering operations implemented in the Formata backend. These filters are designed for data preprocessing, quality control, and dataset refinement in tabular data processing pipelines.

---

## 1. Text Search Filter

### Operation: Content Search (Global)
**Type:** Full-table text matching  
**Operator:** `contains`

#### Mathematical Expression

$$\text{Filter}(D, q) = \{r \in D \mid \exists c \in \text{columns}(r) : q \subseteq \text{lower}(c)\}$$

Where:
- $D$ = dataset (set of rows)
- $q$ = query string (case-insensitive)
- $\text{lower}(c)$ = lowercase transformation of cell value $c$
- $\subseteq$ = substring containment relation

#### Functionality
Performs case-insensitive substring matching across all columns in the dataset. Returns rows where the query string appears in at least one column. Useful for free-text search and exploratory filtering.

#### Implementation Details
- Converts all column values to strings
- Performs case-insensitive comparison
- Uses bitwise OR to combine matches across columns
- Returns all rows containing the query term

---

## 2. Numeric Range Filter

### Operation: Bounded Range Query
**Type:** Column-specific numeric filtering  
**Operator:** `between`

#### Mathematical Expression

$$\text{NumericRange}(D, \text{col}, v_{\min}, v_{\max}) = \{r \in D \mid v_{\min} \leq \text{numeric}(r.\text{col}) \leq v_{\max}\}$$

Where:
- $D$ = dataset
- $\text{col}$ = target column name
- $v_{\min}, v_{\max}$ = numeric bounds (inclusive)
- $\text{numeric}(x)$ = conversion to numeric type

#### Functionality
Filters rows where numeric values fall within a specified inclusive range. Automatically detects numeric columns and converts values using best-effort coercion (NaN → excluded).

#### Implementation Details
- Applies to global numeric range filter (`_numericRange`)
- Supports column-level numeric range filtering
- Handles type coercion with error recovery
- Returns rows satisfying $v_{\min} \leq x \leq v_{\max}$

---

## 2.1 Numeric Comparison Filters

### Operations: Point Comparisons
**Types:** Greater than, Greater than or equal, Less than, Less than or equal, Equals

#### Mathematical Expressions

**Greater Than:**
$$\text{GT}(D, \text{col}, v) = \{r \in D \mid \text{numeric}(r.\text{col}) > v\}$$

**Greater Than or Equal:**
$$\text{GTE}(D, \text{col}, v) = \{r \in D \mid \text{numeric}(r.\text{col}) \geq v\}$$

**Less Than:**
$$\text{LT}(D, \text{col}, v) = \{r \in D \mid \text{numeric}(r.\text{col}) < v\}$$

**Less Than or Equal:**
$$\text{LTE}(D, \text{col}, v) = \{r \in D \mid \text{numeric}(r.\text{col}) \leq v\}$$

**Equals:**
$$\text{EQ}(D, \text{col}, v) = \{r \in D \mid \text{numeric}(r.\text{col}) = v\}$$

#### Functionality
Perform single-value comparisons on numeric columns. Support threshold-based selection, boundary conditions, and exact matching. Commonly used for outlier detection and stratified filtering.

#### Use Cases
- Thresholding: `price > 100`
- Ranges: `age >= 18` AND `age <= 65`
- Exact matching: `status == 1`

---

## 3. Date Range Filter

### Operation: Temporal Bounded Range Query
**Type:** Column-specific datetime filtering  
**Operators:** `range`, `between`

#### Mathematical Expression

$$\text{DateRange}(D, \text{col}, t_{\text{start}}, t_{\text{end}}) = \{r \in D \mid t_{\text{start}} \leq \text{datetime}(r.\text{col}) \leq t_{\text{end}}\}$$

Where:
- $D$ = dataset
- $\text{col}$ = target temporal column
- $t_{\text{start}}, t_{\text{end}}$ = temporal boundaries (inclusive)
- $\text{datetime}(x)$ = datetime conversion function

#### Functionality
Filters rows where temporal values fall within a specified inclusive date/timestamp range. Automatically detects datetime columns using heuristic analysis (>60% valid conversion rate).

#### Implementation Details
- Iterates through columns to identify datetime-compatible columns
- Converts candidate columns to datetime format
- Applies inclusive range filtering: $t_{\text{start}} \leq t \leq t_{\text{end}}$
- Handles parsing errors gracefully

#### Use Cases
- Time-based cohort selection: `date >= 2023-01-01 AND date <= 2023-12-31`
- Event window filtering: transactions within a specific month
- Temporal cross-sectional analysis

---

## 3.1 Datetime Equality Filter

### Operation: Exact Temporal Matching
**Type:** Column-specific datetime filtering  
**Operator:** `equals` or `==`

#### Mathematical Expression

$$\text{DateEQ}(D, \text{col}, t_{\text{target}}) = \{r \in D \mid \text{datetime}(r.\text{col}) = t_{\text{target}}\}$$

#### Functionality
Matches rows with exact datetime values. Useful for selecting specific dates or timestamps.

---

## 4. Boolean Filter

### Operation: Binary State Matching
**Type:** Column-specific boolean filtering  
**Operator:** `equals` or `==`

#### Mathematical Expression

$$\text{BoolEQ}(D, \text{col}, b) = \{r \in D \mid \text{bool}(r.\text{col}) = b\}$$

Where:
- $b \in \{\text{True}, \text{False}\}$ = target boolean value
- $\text{bool}(x)$ = conversion to boolean type

#### Functionality
Filters rows based on binary column values. Automatically detects boolean-typed columns.

#### Use Cases
- Flag-based filtering: `is_active = True`
- Categorical binary selection: `has_error = False`

---

## 5. Text Comparison Filters

### Operations: String Pattern Matching
**Types:** Exact match, Contains, Starts with, Ends with, In-list

#### Mathematical Expressions

**Case-Insensitive Equals:**
$$\text{StrEQ}(D, \text{col}, s) = \{r \in D \mid \text{lower}(r.\text{col}) = \text{lower}(s)\}$$

**Substring Contains:**
$$\text{StrContains}(D, \text{col}, s) = \{r \in D \mid s \subseteq \text{lower}(r.\text{col})\}$$

**String Prefix Matching:**
$$\text{StartsWith}(D, \text{col}, s) = \{r \in D \mid \text{lower}(r.\text{col}) \text{ starts with } \text{lower}(s)\}$$

**String Suffix Matching:**
$$\text{EndsWith}(D, \text{col}, s) = \{r \in D \mid \text{lower}(r.\text{col}) \text{ ends with } \text{lower}(s)\}$$

**Set Membership:**
$$\text{In}(D, \text{col}, S) = \{r \in D \mid \text{lower}(r.\text{col}) \in \{\text{lower}(s) \mid s \in S\}\}$$

Where:
- $D$ = dataset
- $\text{col}$ = target string column
- $s \in S$ = string value(s) in set $S$
- $\text{lower}()$ = case-insensitive normalization

#### Functionality

| Operation | Behavior | Example |
|-----------|----------|---------|
| **Equals** | Exact string match (case-insensitive) | `city == "new york"` matches "New York", "NEW YORK" |
| **Contains** | Substring presence | `name contains "john"` matches "john_smith", "johnson" |
| **Starts with** | Prefix matching | `code starts_with "US"` matches "USA101", "US-WEST" |
| **Ends with** | Suffix matching | `email ends_with ".edu"` matches "user@*.edu" |
| **In** | Set membership | `country in ["USA", "CAN", "MEX"]` matches any value in list |

#### Features
- All operations are **case-insensitive** for robustness
- Whitespace handling: values are stripped before comparison
- NA handling: missing values are excluded from results
- Set-based filtering supports CSV-like value lists

---

## 6. Column Resolution Algorithm

### Context: Automatic Column Detection

When a filter references a column by key, the system uses fuzzy column resolution:

$$\text{ResolveColumn}(D, k) = \begin{cases}
c & \text{if } \text{lower}(k) = \text{lower}(c) \\
c & \text{if } \text{lower}(k) \subseteq \text{lower}(c) \\
c & \text{if } \text{lower}(c) \subseteq \text{lower}(k) \\
\text{None} & \text{otherwise}
\end{cases}$$

This enables flexible column references:
- Exact match: `"Age"` finds `"Age"` column
- Substring: `"age"` finds `"user_age"` or `"Age"` columns
- Heuristic: `"user_age"` finds `"age"` column

---

## 7. Composite Filtering Pipeline

### Operation: Chained Filter Application

When multiple filters are applied simultaneously:

$$\text{ApplyFilters}(D, F) = D' = \bigcap_{f \in F} f(D)$$

Where:
- $F$ = set of filter rules
- $f(D)$ = application of single filter to dataset
- $\bigcap$ = set intersection (row-wise AND logic)

### Processing Order

1. **Global Filters** (applied first):
   - `_textSearch`: Full-table content search
   - `_dateRange`: Global temporal bounds
   - `_numericRange`: Global numeric bounds

2. **Column-Specific Filters** (applied sequentially):
   - Iterate through remaining columns
   - Skip column-agnostic filters (keys starting with `_`)
   - Apply column type detection and appropriate filter
   - Accumulate filtered rows

### Filter Combination Semantics

Multiple column filters combine with **AND logic** (intersection):
$$\text{Result} = (col_1 \text{ filter}) \cap (col_2 \text{ filter}) \cap \ldots \cap (col_n \text{ filter})$$

---

## 8. Type Detection Strategy

### Heuristic Column Type Classification

The system detects column types automatically:

$$\text{Type}(\text{col}) = \begin{cases}
\text{boolean} & \text{if dtype} = \text{bool} \\
\text{numeric} & \text{if dtype} \in \{\text{int}, \text{float}\} \\
\text{numeric} & \text{if } \frac{\#\text{(valid numeric conversions)}}{\text{total}} > 0.6 \\
\text{datetime} & \text{if } \frac{\#\text{(valid datetime conversions)}}{\text{total}} > 0.6 \\
\text{text} & \text{otherwise}
\end{cases}$$

**Rationale:** A column is classified as a type if >60% of non-null values can be converted to that type.

---

## 9. Practical Example

### Scenario: Multi-Filter Query

**Input:** Dataset with columns `[user_id, age, registration_date, is_active, country]`

**Filters Applied:**
```json
{
  "_textSearch": {"op": "contains", "value": "john"},
  "age": {"op": ">=", "value": 18},
  "registration_date": {"op": "range", "start": "2023-01-01", "end": "2024-12-31"},
  "is_active": {"op": "==", "value": true},
  "country": {"op": "in", "value": ["USA", "CAN"]}
}
```

**Mathematical Execution:**

$$\text{Result} = \text{TextSearch}(D, \text{"john"}) \cap \text{GT}(D, \text{age}, 18) \cap \text{DateRange}(D, \text{reg\_date}, t_1, t_2) \cap \text{BoolEQ}(D, \text{active}, \text{True}) \cap \text{In}(D, \text{country}, \{USA, CAN\})$$

**Interpretation:** Rows matching all conditions:
- Contains "john" in any column
- Age ≥ 18
- Registered between 2023-01-01 and 2024-12-31
- Active status = True
- Country in {USA, Canada}

---

## 10. Error Handling & Edge Cases

### Type Coercion Failures
When a value cannot be converted to the target type:
- **Numeric coercion:** NaN → excluded from filter result
- **Datetime coercion:** Unparseable dates → excluded
- **String operations:** Always succeed (fallback to string comparison)

### Missing Value Handling
- Null/NA values: Generally excluded from filter results
- Exception: `equals` operations on numeric may include NaN
- Rationale: Preserve data quality during filtering

### Empty/Null Dataset Handling
$$\text{ApplyFilters}(\emptyset, F) = \emptyset$$
Filters return original dataset if input is empty or null.

---

## References for Research Paper Integration

**Suggested citations and methodological notes:**

1. **Data Filtering Techniques:** Standard relational algebra operations (selection, $\sigma$)
2. **Type Detection:** Heuristic approaches similar to pandas `infer_objects()`
3. **String Matching:** Case-insensitive substring matching (KMP or similar)
4. **Temporal Filtering:** ISO 8601 datetime parsing conventions
5. **Composite Filtering:** Set-theoretic intersection semantics

**Recommendation for Academic Writing:**
- Reference relational algebra for mathematical foundation
- Cite pandas documentation for type coercion strategies
- Note heuristic thresholds (0.6 confidence) as design decisions
- Discuss NA handling implications for statistical validity

---

## Implementation Repository

**Source Files:**
- [app/services/filtering.py](../app/services/filtering.py) — Filter logic
- [app/api/process.py](../app/api/process.py) — Filter API endpoints
- Tests: [tests/test_filters_detailed.py](../../tests/test_filters_detailed.py)

**API Endpoint:**
- POST `/process/filter` — Apply filters to dataset

---

**Document Version:** 1.0  
**Last Updated:** March 31, 2026  
**Purpose:** Mathematical documentation for research and academic publications
