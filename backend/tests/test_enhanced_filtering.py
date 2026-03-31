"""
Comprehensive test suite for enhanced filtering module
Tests multi-filter support, statistical filters, and improved type detection
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.services.filtering import apply_filters, _detect_column_type, _analyze_text_content


def test_single_filters():
    """Test backward compatibility with single filter rules"""
    df = pd.DataFrame({
        'age': [25, 30, 35, 40, 45],
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'active': [True, False, True, True, False]
    })
    
    # Test numeric filter
    filters = {'age': {'op': '>', 'value': '30'}}
    result = apply_filters(df, filters)
    assert len(result) == 3, f"Expected 3 rows, got {len(result)}"
    assert all(result['age'] > 30), "Numeric filter failed"
    
    # Test text filter
    filters = {'name': {'op': 'contains', 'value': 'a'}}
    result = apply_filters(df, filters)
    assert len(result) == 3, f"Expected 3 rows for 'a' filter, got {len(result)}"
    
    print("✓ Single filter tests passed")


def test_multi_filters():
    """Test new multi-filter array support (OR logic within column, AND between columns)"""
    df = pd.DataFrame({
        'age': [25, 30, 35, 40, 45],
        'department': ['Sales', 'Tech', 'Sales', 'HR', 'Tech'],
        'salary': [50000, 80000, 60000, 55000, 90000]
    })
    
    # Test multiple filters on same column (array) - OR logic
    filters = {
        'department': [
            {'op': 'equals', 'value': 'Sales'},
            {'op': 'equals', 'value': 'Tech'}
        ]
    }
    result = apply_filters(df, filters)
    assert len(result) == 4, f"Expected 4 rows (Sales OR Tech), got {len(result)}"
    
    # Test multi-column filters combined with AND logic
    filters = {
        'department': {'op': 'equals', 'value': 'Sales'},
        'salary': {'op': '>', 'value': '55000'}
    }
    result = apply_filters(df, filters)
    assert len(result) == 1, f"Expected 1 row (Sales AND salary>55000), got {len(result)}"
    assert result['salary'].iloc[0] == 60000, "Multi-column filter logic failed"
    
    print("✓ Multi-filter tests passed")


def test_date_filtering():
    """Test date filtering without numeric conversion"""
    dates = pd.date_range('2023-01-01', periods=5, freq='D')
    df = pd.DataFrame({
        'date_col': dates,
        'value': [10, 20, 30, 40, 50]
    })
    
    # Test date range filter
    filters = {
        'date_col': {
            'op': 'range',
            'start': '2023-01-02',
            'end': '2023-01-04'
        }
    }
    result = apply_filters(df, filters)
    assert len(result) == 3, f"Expected 3 rows in date range, got {len(result)}"
    assert result['value'].tolist() == [20, 30, 40], "Date range filter failed"
    
    print("✓ Date filtering tests passed")


def test_statistical_filters():
    """Test statistical filters (mean, median, std dev, IQR)"""
    df = pd.DataFrame({
        'values': [10, 15, 20, 25, 30, 100]  # 100 is an outlier
    })
    
    # Test greater than mean
    filters = {'values': {'op': 'gt_mean'}}
    result = apply_filters(df, filters)
    assert len(result) == 1, f"Expected 1 value > mean, got {len(result)}"
    
    # Test within standard deviation
    filters = {'values': {'op': 'within_std', 'std_multiplier': 1.0}}
    result = apply_filters(df, filters)
    assert len(result) == 5, f"Expected 5 values within 1 std dev, got {len(result)}"
    assert 100 not in result['values'].tolist(), "Outlier should be excluded"
    
    # Test IQR outlier detection
    filters = {'values': {'op': 'iqr'}}
    result = apply_filters(df, filters)
    assert len(result) == 5, f"Expected 5 values in IQR range, got {len(result)}"
    
    print("✓ Statistical filter tests passed")


def test_text_analysis():
    """Test improved text analysis for column type detection"""
    # Text column (prose-like)
    text_series = pd.Series([
        'The quick brown fox',
        'Jumps over the lazy dog',
        'Natural language processing is awesome',
        'Machine learning rocks',
        'Data science forever'
    ])
    text_type = _detect_column_type(text_series)
    assert text_type == 'text', f"Expected 'text', got '{text_type}'"
    
    # Numeric column (should not be detected as text)
    numeric_series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    numeric_type = _detect_column_type(numeric_series)
    assert numeric_type == 'numeric', f"Expected 'numeric', got '{numeric_type}'"
    
    # ID column (mostly numeric but could be mistaken)
    id_series = pd.Series(['ID001', 'ID002', 'ID003', 'ID004', 'ID005'])
    id_type = _detect_column_type(id_series)
    assert id_type == 'text', f"Expected 'text' for ID column, got '{id_type}'"
    
    # Mixed content - should favor the dominant type
    mixed_series = pd.Series(['100', '200', '300', 'N/A', '400'])
    mixed_type = _detect_column_type(mixed_series)
    # Should be detected as numeric because 80% can convert
    assert mixed_type == 'numeric', f"Expected 'numeric' for 80% convertible, got '{mixed_type}'"
    
    print("✓ Text analysis tests passed")


def test_backward_compatibility():
    """Ensure all existing filter operations still work"""
    df = pd.DataFrame({
        'price': [100, 150, 200, 250, 300],
        'category': ['A', 'B', 'A', 'C', 'B'],
        'in_stock': [True, False, True, True, False]
    })
    
    # Test all numeric operators
    operators = [
        ({'price': {'op': '>', 'value': '150'}}, 3),
        ({'price': {'op': '>=', 'value': '150'}}, 4),
        ({'price': {'op': '<', 'value': '250'}}, 3),
        ({'price': {'op': '<=', 'value': '250'}}, 4),
        ({'price': {'op': '==', 'value': '200'}}, 1),
        ({'price': {'op': 'between', 'min': '150', 'max': '250'}}, 3),
    ]
    
    for filters, expected_count in operators:
        result = apply_filters(df, filters)
        assert len(result) == expected_count, f"Filter {filters} expected {expected_count} rows, got {len(result)}"
    
    # Test text operators
    text_ops = [
        ({'category': {'op': 'equals', 'value': 'A'}}, 2),
        ({'category': {'op': 'in', 'value': ['A', 'B']}}, 4),
    ]
    
    for filters, expected_count in text_ops:
        result = apply_filters(df, filters)
        assert len(result) == expected_count, f"Text filter {filters} expected {expected_count} rows, got {len(result)}"
    
    print("✓ Backward compatibility tests passed")


def test_empty_and_null_handling():
    """Test edge cases with empty/null data"""
    # Empty dataframe
    empty_df = pd.DataFrame()
    result = apply_filters(empty_df, {'col': {'op': 'equals', 'value': 'test'}})
    assert len(result) == 0, "Empty dataframe should remain empty"
    
    # DataFrame with nulls
    df_with_nulls = pd.DataFrame({
        'col1': [1, 2, None, 4, 5],
        'col2': ['a', None, 'c', 'd', 'e']
    })
    
    # Filter should exclude nulls
    result = apply_filters(df_with_nulls, {'col1': {'op': '>', 'value': '2'}})
    assert len(result) == 2, "Filter should exclude nulls"
    
    print("✓ Null handling tests passed")


def run_all_tests():
    """Run all test suites"""
    print("\n" + "="*60)
    print("RUNNING ENHANCED FILTERING TEST SUITE")
    print("="*60 + "\n")
    
    try:
        test_single_filters()
        test_multi_filters()
        test_date_filtering()
        test_statistical_filters()
        test_text_analysis()
        test_backward_compatibility()
        test_empty_and_null_handling()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED - No models broken!")
        print("="*60 + "\n")
        return True
        
    except AssertionError as e:
        print("\n" + "="*60)
        print(f"❌ TEST FAILED: {e}")
        print("="*60 + "\n")
        return False
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ UNEXPECTED ERROR: {e}")
        print("="*60 + "\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
