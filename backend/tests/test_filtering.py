"""
Comprehensive tests for filtering service
Testing column filtering and data filtering
"""
import pytest
import pandas as pd
from app.services.filtering import apply_filters, _resolve_column, _detect_column_type


class TestResolveColumn:
    """Test column name resolution"""
    
    def test_resolve_exact_match(self):
        """Test exact column name match"""
        df = pd.DataFrame({"name": [1], "age": [2]})
        result = _resolve_column(df, "name")
        assert result == "name"
    
    def test_resolve_case_insensitive(self):
        """Test case-insensitive matching"""
        df = pd.DataFrame({"Name": [1], "Age": [2]})
        result = _resolve_column(df, "name")
        assert result == "Name"
    
    def test_resolve_partial_match(self):
        """Test partial column name matching"""
        df = pd.DataFrame({"user_name": [1], "user_age": [2]})
        result = _resolve_column(df, "name")
        assert result == "user_name"
    
    def test_resolve_no_match(self):
        """Test when no column matches"""
        df = pd.DataFrame({"name": [1], "age": [2]})
        result = _resolve_column(df, "email")
        assert result is None


class TestDetectColumnType:
    """Test column type detection"""
    
    def test_detect_boolean_type(self):
        """Test boolean type detection"""
        series = pd.Series([True, False, True, False])
        result = _detect_column_type(series)
        assert result == "boolean"
    
    def test_detect_numeric_type(self):
        """Test numeric type detection"""
        series = pd.Series([1, 2, 3, 4, 5])
        result = _detect_column_type(series)
        assert result == "numeric"
    
    def test_detect_datetime_type(self):
        """Test datetime type detection"""
        series = pd.Series(["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"])
        result = _detect_column_type(series)
        assert result == "datetime"
    
    def test_detect_text_type(self):
        """Test text type detection"""
        series = pd.Series(["hello", "world", "test"])
        result = _detect_column_type(series)
        assert result == "text"


class TestApplyFilters:
    """Test filter application"""
    
    def test_apply_no_filters(self):
        """Test with no filters - should return original"""
        df = pd.DataFrame({"name": ["John", "Jane"], "age": [25, 30]})
        result = apply_filters(df, {})
        assert len(result) == len(df)
    
    def test_apply_text_search_filter(self):
        """Test text search filter"""
        df = pd.DataFrame({
            "name": ["John", "Jane", "Bob"],
            "city": ["NYC", "LA", "Chicago"]
        })
        filters = {"_textSearch": {"op": "contains", "value": "Jo"}}
        result = apply_filters(df, filters)
        assert len(result) == 1
        assert result.iloc[0]["name"] == "John"
    
    def test_apply_empty_dataframe(self):
        """Test with empty DataFrame"""
        df = pd.DataFrame()
        result = apply_filters(df, {"_textSearch": {"op": "contains", "value": "test"}})
        assert result.empty
    
    def test_apply_none_input(self):
        """Test with None input"""
        result = apply_filters(None, {})
        assert result is None
    
    def test_apply_text_search_case_insensitive(self):
        """Test case-insensitive text search"""
        df = pd.DataFrame({"name": ["JOHN", "jane", "Bob"]})
        filters = {"_textSearch": {"op": "contains", "value": "john"}}
        result = apply_filters(df, filters)
        assert len(result) == 1
    
    def test_apply_text_search_no_matches(self):
        """Test text search with no matches"""
        df = pd.DataFrame({"name": ["John", "Jane"]})
        filters = {"_textSearch": {"op": "contains", "value": "xyz"}}
        result = apply_filters(df, filters)
        assert len(result) == 0
    
    def test_apply_filters_preserves_data(self):
        """Test that filtering preserves data integrity"""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["John", "Jane", "Bob"],
            "age": [25, 30, 35]
        })
        filters = {"_textSearch": {"op": "contains", "value": "Jane"}}
        result = apply_filters(df, filters)
        assert len(result) == 1
        assert result.iloc[0]["id"] == 2
        assert result.iloc[0]["age"] == 30
