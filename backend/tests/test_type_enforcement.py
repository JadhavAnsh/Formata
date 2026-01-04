import pytest
import pandas as pd
import numpy as np
from app.services.type_enforcement import (
    detect_column_types,
    enforce_types,
    validate_ranges
)


class TestTypeEnforcement:
    """Test type enforcement functionality"""
    
    def test_detect_column_types_numeric(self):
        """Test detection of numeric types"""
        df = pd.DataFrame({
            'int_col': ['1', '2', '3', '4', '5'],
            'float_col': ['1.5', '2.3', '3.7', '4.2', '5.9'],
            'mixed_col': ['1', '2', 'three', '4', '5']
        })
        
        types = detect_column_types(df)
        
        assert types['int_col'] == 'int'
        assert types['float_col'] == 'float'
        assert types['mixed_col'] == 'string'  # Mixed content defaults to string
    
    def test_detect_column_types_boolean(self):
        """Test detection of boolean types"""
        df = pd.DataFrame({
            'bool_col1': ['true', 'false', 'true', 'false'],
            'bool_col2': ['yes', 'no', 'yes', 'no'],
            'bool_col3': ['1', '0', '1', '0']
        })
        
        types = detect_column_types(df)
        
        assert types['bool_col1'] == 'bool'
        assert types['bool_col2'] == 'bool'
        assert types['bool_col3'] == 'bool'
    
    def test_detect_column_types_datetime(self):
        """Test detection of datetime types"""
        df = pd.DataFrame({
            'date_col': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'datetime_col': ['2024-01-01 10:30:00', '2024-01-02 11:45:00', '2024-01-03 14:20:00']
        })
        
        types = detect_column_types(df)
        
        assert types['date_col'] == 'datetime'
        assert types['datetime_col'] == 'datetime'
    
    def test_enforce_types_integers(self):
        """Test enforcing integer types"""
        df = pd.DataFrame({
            'age': ['25', '30', '35', '40'],
            'count': ['100', '200', '300', '400']
        })
        
        type_map = {'age': 'int', 'count': 'int'}
        result_df, report = enforce_types(df, type_map=type_map, auto_detect=False)
        
        assert pd.api.types.is_integer_dtype(result_df['age'])
        assert pd.api.types.is_integer_dtype(result_df['count'])
        assert report['columns_enforced'] == 2
        assert len(report['errors']) == 0
    
    def test_enforce_types_booleans(self):
        """Test enforcing boolean types"""
        df = pd.DataFrame({
            'active': ['true', 'false', 'true', 'yes', 'no'],
            'verified': ['1', '0', '1', '1', '0']
        })
        
        type_map = {'active': 'bool', 'verified': 'bool'}
        result_df, report = enforce_types(df, type_map=type_map, auto_detect=False)
        
        assert result_df['active'].dtype == 'object' or result_df['active'].dtype == 'bool'
        assert report['columns_enforced'] == 2
    
    def test_enforce_types_with_nulls(self):
        """Test type enforcement handles null values"""
        df = pd.DataFrame({
            'value': ['10', '20', None, '40', '50']
        })
        
        type_map = {'value': 'int'}
        result_df, report = enforce_types(df, type_map=type_map, auto_detect=False)
        
        assert pd.api.types.is_integer_dtype(result_df['value'])
        assert result_df['value'].isna().sum() == 1
    
    def test_enforce_types_auto_detect(self):
        """Test auto-detection of types"""
        df = pd.DataFrame({
            'id': ['1', '2', '3'],
            'name': ['Alice', 'Bob', 'Charlie'],
            'active': ['true', 'false', 'true'],
            'score': ['95.5', '87.2', '91.8']
        })
        
        result_df, report = enforce_types(df, auto_detect=True)
        
        assert report['columns_enforced'] == 4
        assert pd.api.types.is_integer_dtype(result_df['id'])
        assert result_df['name'].dtype == 'object'  # String
        assert pd.api.types.is_numeric_dtype(result_df['score'])
    
    def test_validate_ranges_flag(self):
        """Test range validation with flagging"""
        df = pd.DataFrame({
            'age': [25, 150, 35, -5, 45],
            'score': [85, 95, 105, 75, 90]
        })
        
        range_rules = {
            'age': {'min': 0, 'max': 120, 'action': 'flag'},
            'score': {'min': 0, 'max': 100, 'action': 'flag'}
        }
        
        result_df, violations = validate_ranges(df, range_rules)
        
        assert len(violations) == 3  # age > 120, age < 0, score > 100
        assert len(result_df) == 5  # No rows dropped with 'flag' action
    
    def test_validate_ranges_drop(self):
        """Test range validation with dropping"""
        df = pd.DataFrame({
            'age': [25, 150, 35, -5, 45]
        })
        
        range_rules = {
            'age': {'min': 0, 'max': 120, 'action': 'drop'}
        }
        
        result_df, violations = validate_ranges(df, range_rules)
        
        assert len(result_df) == 3  # Only valid ages remain
        assert len(violations) == 2  # Two violations found
    
    def test_validate_ranges_clip(self):
        """Test range validation with clipping"""
        df = pd.DataFrame({
            'age': [25, 150, 35, -5, 45]
        })
        
        range_rules = {
            'age': {'min': 0, 'max': 120, 'action': 'clip'}
        }
        
        result_df, violations = validate_ranges(df, range_rules)
        
        assert len(result_df) == 5  # All rows retained
        assert result_df['age'].max() == 120  # Clipped to max
        assert result_df['age'].min() == 0  # Clipped to min
    
    def test_empty_dataframe(self):
        """Test handling of empty DataFrame"""
        df = pd.DataFrame()
        
        result_df, report = enforce_types(df, auto_detect=True)
        
        assert len(result_df) == 0
        assert report['columns_enforced'] == 0
    
    def test_error_handling_invalid_column(self):
        """Test error handling for invalid column names"""
        df = pd.DataFrame({
            'age': ['25', '30', '35']
        })
        
        type_map = {'nonexistent_col': 'int'}
        result_df, report = enforce_types(df, type_map=type_map, auto_detect=False)
        
        assert len(report['errors']) == 1
        assert 'nonexistent_col' in report['errors'][0]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
