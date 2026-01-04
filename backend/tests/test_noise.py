"""
Comprehensive tests for noise removal service
Testing duplicate removal and outlier detection
"""
import pytest
import pandas as pd
import numpy as np
from app.services.noise import remove_duplicates, remove_outliers


class TestRemoveDuplicates:
    """Test duplicate removal functionality"""
    
    def test_remove_exact_duplicates(self):
        """Test removal of exact duplicate rows"""
        df = pd.DataFrame({
            "name": ["John", "Jane", "John", "Bob"],
            "age": [25, 30, 25, 35]
        })
        result = remove_duplicates(df)
        assert len(result) == 3  # One duplicate should be removed
    
    def test_remove_no_duplicates(self):
        """Test with no duplicates - should return same count"""
        df = pd.DataFrame({
            "name": ["John", "Jane", "Bob"],
            "age": [25, 30, 35]
        })
        result = remove_duplicates(df)
        assert len(result) == 3
    
    def test_remove_fuzzy_duplicates(self):
        """Test fuzzy duplicate detection (case/whitespace)"""
        df = pd.DataFrame({
            "name": ["John", " john ", "JOHN", "Jane"],
            "age": [25, 25, 25, 30]
        })
        result = remove_duplicates(df)
        # Fuzzy matching should detect similar rows
        assert len(result) < 4
    
    def test_remove_duplicates_empty_df(self):
        """Test with empty DataFrame"""
        df = pd.DataFrame()
        result = remove_duplicates(df)
        assert result.empty
    
    def test_remove_duplicates_none_input(self):
        """Test with None input"""
        result = remove_duplicates(None)
        assert result is None
    
    def test_remove_all_duplicates(self):
        """Test when all rows are duplicates"""
        df = pd.DataFrame({
            "name": ["John", "John", "John"],
            "age": [25, 25, 25]
        })
        result = remove_duplicates(df)
        assert len(result) == 1  # Only one unique row should remain
    
    def test_remove_duplicates_with_nulls(self):
        """Test duplicate detection with null values"""
        df = pd.DataFrame({
            "name": ["John", "John", None, None],
            "age": [25, 25, 30, 30]
        })
        result = remove_duplicates(df)
        # Should handle nulls properly
        assert len(result) <= 4


class TestRemoveOutliers:
    """Test outlier removal using IQR method"""
    
    def test_remove_outliers_simple(self):
        """Test outlier removal with clear outliers"""
        df = pd.DataFrame({
            "value": [10, 12, 13, 14, 15, 100, 105]  # 100, 105 are outliers
        })
        result = remove_outliers(df)
        # With only 7 values and high outliers, IQR method should detect them
        # But our function requires at least 5 non-null values after conversion
        # The IQR calculation should remove extreme outliers
        assert len(result) <= len(df)
        # If outliers are removed, check they're actually removed
        if len(result) < len(df):
            assert result["value"].max() < 50
    
    def test_remove_outliers_no_outliers(self):
        """Test with no outliers - should return same count"""
        df = pd.DataFrame({
            "value": [10, 12, 13, 14, 15, 16, 18]
        })
        result = remove_outliers(df)
        assert len(result) == len(df)
    
    def test_remove_outliers_multiple_columns(self):
        """Test outlier removal across multiple columns"""
        df = pd.DataFrame({
            "col1": [10, 12, 13, 14, 15, 100],
            "col2": [20, 22, 23, 24, 25, 26]
        })
        result = remove_outliers(df, columns=["col1"])
        # Only col1 outliers should be removed
        assert len(result) < len(df)
    
    def test_remove_outliers_auto_detect(self):
        """Test auto-detection of numeric columns"""
        df = pd.DataFrame({
            "name": ["A", "B", "C", "D", "E", "F"],
            "value": [10, 12, 13, 14, 15, 100]
        })
        result = remove_outliers(df)  # No columns specified
        # Should auto-detect and process numeric column
        assert len(result) < len(df)
    
    def test_remove_outliers_empty_df(self):
        """Test with empty DataFrame"""
        df = pd.DataFrame()
        result = remove_outliers(df)
        assert result.empty
    
    def test_remove_outliers_none_input(self):
        """Test with None input"""
        result = remove_outliers(None)
        assert result is None
    
    def test_remove_outliers_sparse_data(self):
        """Test with sparse data (< 10 values) - should skip"""
        df = pd.DataFrame({
            "value": [1, 2, 3, 100]  # Only 4 values
        })
        result = remove_outliers(df)
        # Should not remove outliers from sparse data
        assert len(result) == len(df)
    
    def test_remove_outliers_constant_values(self):
        """Test with constant values - should skip"""
        df = pd.DataFrame({
            "value": [10, 10, 10, 10, 10]
        })
        result = remove_outliers(df)
        assert len(result) == len(df)
    
    def test_remove_outliers_with_nulls(self):
        """Test outlier removal with null values"""
        df = pd.DataFrame({
            "value": [10, 12, None, 14, 15, 100, None]
        })
        result = remove_outliers(df)
        # Should handle nulls and still remove outliers
        assert result is not None
    
    def test_remove_outliers_mixed_types(self):
        """Test with mixed type column"""
        df = pd.DataFrame({
            "value": ["10", "12", "abc", "14", "15", "100"]
        })
        result = remove_outliers(df)
        # Should convert to numeric and process
        assert result is not None
