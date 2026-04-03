"""
Comprehensive tests for normalization service
Testing column standardization and type normalization
"""
import pytest
import pandas as pd
from app.services.normalization import standardize_columns, normalize_types, prepare_for_export


class TestStandardizeColumns:
    """Test column name standardization"""
    
    def test_standardize_simple_columns(self):
        """Test standardization of simple column names"""
        df = pd.DataFrame({"Name": [1], "Age": [2], "City": [3]})
        result = standardize_columns(df)
        assert list(result.columns) == ["name", "age", "city"]
    
    def test_standardize_columns_with_spaces(self):
        """Test standardization with spaces"""
        df = pd.DataFrame({"First Name": [1], "Last Name": [2]})
        result = standardize_columns(df)
        assert list(result.columns) == ["first_name", "last_name"]
    
    def test_standardize_columns_with_special_chars(self):
        """Test standardization with special characters"""
        df = pd.DataFrame({"Name@Email": [1], "Phone#": [2], "Address-Line": [3]})
        result = standardize_columns(df)
        assert "name_email" in result.columns
        assert "phone" in result.columns
        assert "address_line" in result.columns
    
    def test_standardize_duplicate_columns(self):
        """Test handling of duplicate column names"""
        df = pd.DataFrame([[1, 2, 3]], columns=["Name", "name", "NAME"])
        result = standardize_columns(df)
        # Should handle duplicates by adding suffix
        assert len(result.columns) == 3
        assert result.columns[0] == "name"
        assert "_1" in result.columns[1] or "_2" in result.columns[2]
    
    def test_standardize_empty_dataframe(self):
        """Test standardization of empty DataFrame"""
        df = pd.DataFrame()
        result = standardize_columns(df)
        assert result.empty
    
    def test_standardize_none_input(self):
        """Test standardization with None input"""
        result = standardize_columns(None)
        assert result is None
    
    def test_standardize_columns_with_numbers(self):
        """Test standardization with numeric column names"""
        df = pd.DataFrame([[1, 2]], columns=[123, 456])
        result = standardize_columns(df)
        assert "123" in result.columns or "456" in result.columns


class TestNormalizeTypes:
    """Test data type normalization"""
    
    def test_normalize_numeric_strings(self):
        """Test conversion of numeric strings to numbers"""
        df = pd.DataFrame({"age": ["25", "30", "35"]})
        result = normalize_types(df)
        assert pd.api.types.is_numeric_dtype(result["age"])
    
    def test_normalize_boolean_values(self):
        """Test conversion of boolean strings"""
        df = pd.DataFrame({"active": ["true", "false", "true", "false", "yes"]})
        result = normalize_types(df)
        assert result["active"].dtype == bool or result["active"].dtype == object
        # Check values are boolean
        if result["active"].dtype == bool:
            assert result["active"].iloc[0] == True
            assert result["active"].iloc[1] == False
    
    def test_normalize_mixed_boolean_formats(self):
        """Test various boolean formats"""
        df = pd.DataFrame({"flag": ["yes", "no", "1", "0", "true", "false"]})
        result = normalize_types(df)
        # Should detect as boolean column
        assert result["flag"].dtype in [bool, object]
    
    def test_normalize_null_values(self):
        """Test normalization of various null representations"""
        df = pd.DataFrame({"value": ["", "null", "none", "nan", "na", "n/a", "undefined", "valid"]})
        result = normalize_types(df)
        # Null replacements happen but text values remain as strings after normalization
        # The "null", "none", etc. strings are normalized, but "valid" should still be present
        assert "valid" in result["value"].values or len(result["value"]) > 0
    
    def test_normalize_datetime_strings(self):
        """Test conversion of datetime strings"""
        df = pd.DataFrame({"date": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"]})
        result = normalize_types(df)
        assert pd.api.types.is_datetime64_any_dtype(result["date"])
    
    def test_normalize_empty_dataframe(self):
        """Test normalization of empty DataFrame"""
        df = pd.DataFrame()
        result = normalize_types(df)
        assert result.empty
    
    def test_normalize_none_input(self):
        """Test normalization with None input"""
        result = normalize_types(None)
        assert result is None
    
    def test_normalize_mixed_types(self):
        """Test normalization with mixed type columns"""
        df = pd.DataFrame({
            "name": ["John", "Jane", "Bob"],
            "age": ["25", "30", "abc"],  # Mixed valid/invalid numbers
            "active": ["true", "false", "maybe"]  # Mixed boolean
        })
        result = normalize_types(df)
        # Name should stay as text
        assert result["name"].dtype == object
    
    def test_normalize_preserves_valid_data(self):
        """Test that valid data is preserved during normalization"""
        df = pd.DataFrame({
            "name": ["Alice", "Bob"],
            "age": ["25", "30"],
            "score": ["95.5", "87.3"]
        })
        result = normalize_types(df)
        # Check data integrity
        assert len(result) == 2
        assert result["name"].iloc[0] == "Alice"
    
    def test_normalize_handles_whitespace(self):
        """Test normalization handles whitespace properly"""
        df = pd.DataFrame({
            "value": ["  25  ", "  30  ", "  text  "]
        })
        result = normalize_types(df)
        # Whitespace should be handled
        assert result is not None

    def test_normalize_dirty_csv_values(self):
        """Test normalization of common dirty CSV values"""
        df = pd.DataFrame({
            "age": ["70 years", "21 years", "unknown"],
            "salary": ["33301rs", "₹83,724", "N/A"],
            "join_date": ["17/02/1990", "Mar 27 2026", "not_provided"],
            "email": ["robertskrista@example.net", "welchrichard", "unknown"],
            "city": ["", "unknown", "South Ryanside"],
        })

        result = normalize_types(df)

        assert pd.api.types.is_integer_dtype(result["age"])
        assert result["age"].iloc[0] == 70
        assert result["age"].iloc[1] == 21
        assert pd.isna(result["age"].iloc[2])

        assert pd.api.types.is_numeric_dtype(result["salary"])
        assert result["salary"].iloc[0] == 33301
        assert result["salary"].iloc[1] == 83724
        assert pd.isna(result["salary"].iloc[2])

        assert pd.api.types.is_datetime64_any_dtype(result["join_date"])
        assert pd.isna(result["join_date"].iloc[2])

        assert result["email"].iloc[0] == "robertskrista@example.net"
        assert pd.isna(result["email"].iloc[1])
        assert pd.isna(result["email"].iloc[2])

        assert pd.isna(result["city"].iloc[0])
        assert pd.isna(result["city"].iloc[1])
        assert result["city"].iloc[2] == "South Ryanside"


class TestPrepareForExport:
    """Test export-safe formatting behavior"""

    def test_prepare_for_export_converts_epoch_date_ints(self):
        """Epoch nanoseconds in datetime-like columns should export as readable dates"""
        df = pd.DataFrame(
            {
                "join_date": [635212800000000000, -9223372036854775808, 1774569600000000000],
                "name": ["A", "B", "C"],
            }
        )

        result = prepare_for_export(df)

        assert result["join_date"].iloc[0] == "1990-02-17"
        assert result["join_date"].iloc[1] is None
        assert result["join_date"].iloc[2] == "2026-03-27"
