"""
Comprehensive tests for conversion service
Testing CSV to JSON and JSON to CSV conversion
"""
import pytest
import pandas as pd
import json
import os
from app.services.conversion import csv_to_json, json_to_csv


class TestCSVToJSON:
    """Test CSV to JSON conversion"""
    
    def test_csv_to_json_simple(self, tmp_path):
        """Test simple CSV to JSON conversion"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age,city\nJohn,25,NYC\nJane,30,LA")
        
        result = csv_to_json(str(csv_file))
        assert "records" in result
        assert len(result["records"]) == 2
        assert result["records"][0]["name"] == "John"
    
    def test_csv_to_json_with_metadata(self, tmp_path):
        """Test that metadata is included"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age\nJohn,25")
        
        result = csv_to_json(str(csv_file))
        assert "meta" in result
        assert result["meta"]["source"] == "csv"
        assert result["meta"]["rows"] == 1
        assert "columns" in result["meta"]
    
    def test_csv_to_json_empty_rows(self, tmp_path):
        """Test CSV with empty rows"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age\nJohn,25\n\n\nJane,30")
        
        result = csv_to_json(str(csv_file))
        assert len(result["records"]) == 2
    
    def test_csv_to_json_special_values(self, tmp_path):
        """Test CSV with special null-like values"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,value\nJohn,null\nJane,")
        
        result = csv_to_json(str(csv_file))
        # null and empty should be converted to None
        assert result["records"][0]["value"] is None
        assert result["records"][1]["value"] is None
    
    def test_csv_to_json_nonexistent_file(self):
        """Test with nonexistent file"""
        with pytest.raises(FileNotFoundError):
            csv_to_json("nonexistent.csv")
    
    def test_csv_to_json_numeric_conversion(self, tmp_path):
        """Test automatic numeric type conversion"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age,score\nJohn,25,95.5\nJane,30,87.3")
        
        result = csv_to_json(str(csv_file))
        # Numbers should be converted
        assert isinstance(result["records"][0]["age"], (int, float))
        assert isinstance(result["records"][0]["score"], (int, float))

    def test_csv_to_json_dirty_values_are_cleaned(self, tmp_path):
        """Test that dirty CSV values are normalized during conversion"""
        csv_file = tmp_path / "dirty.csv"
        csv_file.write_text(
            "name,age,salary,join_date,email,city,score\n"
            "Sydney Haynes,70 years,33301rs,17/02/1990,robertskrista@example.net,unknown,999999\n"
            "David Wheeler,N/A,\"₹83,724\",Mar 27 2026,welchrichard,South Ryanside,80.71",
            encoding="utf-8",
        )

        result = csv_to_json(str(csv_file))

        first = result["records"][0]
        second = result["records"][1]

        assert first["age"] == 70
        assert first["salary"] == 33301
        assert first["email"] == "robertskrista@example.net"
        assert first["city"] is None

        assert second["age"] is None
        assert second["email"] is None


class TestJSONToCSV:
    """Test JSON to CSV conversion"""
    
    def test_json_to_csv_simple(self, tmp_path):
        """Test simple JSON to CSV conversion"""
        json_data = {"records": [
            {"name": "John", "age": 25},
            {"name": "Jane", "age": 30}
        ]}
        output_file = tmp_path / "output.csv"
        
        json_to_csv(json_data, str(output_file))
        
        # Verify CSV was created
        assert output_file.exists()
        df = pd.read_csv(str(output_file))
        assert len(df) == 2
        assert "name" in df.columns
    
    def test_json_to_csv_list_input(self, tmp_path):
        """Test JSON list (not wrapped) as input"""
        json_data = [
            {"name": "John", "age": 25},
            {"name": "Jane", "age": 30}
        ]
        output_file = tmp_path / "output.csv"
        
        json_to_csv(json_data, str(output_file))
        
        assert output_file.exists()
        df = pd.read_csv(str(output_file))
        assert len(df) == 2
    
    def test_json_to_csv_empty_data(self, tmp_path):
        """Test with empty JSON data"""
        json_data = {}
        output_file = tmp_path / "output.csv"
        
        with pytest.raises(ValueError):
            json_to_csv(json_data, str(output_file))
    
    def test_json_to_csv_no_records(self, tmp_path):
        """Test with no records"""
        json_data = {"records": []}
        output_file = tmp_path / "output.csv"
        
        with pytest.raises(ValueError):
            json_to_csv(json_data, str(output_file))
    
    def test_json_to_csv_nested_structure(self, tmp_path):
        """Test JSON with nested structure - should flatten"""
        json_data = {"records": [
            {"name": "John", "details": {"age": 25, "city": "NYC"}}
        ]}
        output_file = tmp_path / "output.csv"
        
        json_to_csv(json_data, str(output_file))
        
        # Should flatten nested structure
        df = pd.read_csv(str(output_file))
        assert "details_age" in df.columns or "details.age" in df.columns
    
    def test_json_to_csv_invalid_structure(self, tmp_path):
        """Test with invalid JSON structure"""
        json_data = "invalid"
        output_file = tmp_path / "output.csv"
        
        with pytest.raises(ValueError):
            json_to_csv(json_data, str(output_file))

    def test_json_to_csv_preserves_human_readable_dates(self, tmp_path):
        """Test that datetime values are exported as readable strings"""
        json_data = {
            "records": [
                {"name": "John", "join_date": "2023-01-01"},
                {"name": "Jane", "join_date": "2024-02-03"},
            ]
        }
        output_file = tmp_path / "dated-output.csv"

        json_to_csv(json_data, str(output_file))

        output_text = output_file.read_text(encoding="utf-8")
        assert "2023-01-01" in output_text
        assert "2024-02-03" in output_text
        assert "-9223372036854775808" not in output_text
