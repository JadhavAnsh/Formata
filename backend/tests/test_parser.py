"""
Comprehensive tests for parser service
Testing edge cases, error handling, and functionality
"""
import pytest
import pandas as pd
import os
import json
import tempfile
from app.services.parser import parse_csv, parse_json, parse_excel, parse_markdown


class TestParseCSV:
    """Test CSV parsing with edge cases"""
    
    def test_parse_valid_csv(self, tmp_path):
        """Test parsing a valid CSV file"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age,city\nJohn,25,NYC\nJane,30,LA")
        
        df = parse_csv(str(csv_file))
        assert len(df) == 2
        assert list(df.columns) == ["name", "age", "city"]
        assert df.iloc[0]["name"] == "John"
    
    def test_parse_csv_with_empty_rows(self, tmp_path):
        """Test CSV with empty rows - should be dropped"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age\nJohn,25\n\n\nJane,30\n\n")
        
        df = parse_csv(str(csv_file))
        assert len(df) == 2  # Empty rows should be removed
    
    def test_parse_csv_with_whitespace(self, tmp_path):
        """Test CSV with whitespace - should be trimmed"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age\n  John  ,  25  \n  Jane  ,  30  ")
        
        df = parse_csv(str(csv_file))
        assert df.iloc[0]["name"] == "John"
        assert df.iloc[0]["age"] == "25"
    
    def test_parse_csv_nonexistent_file(self):
        """Test parsing non-existent file - should raise FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            parse_csv("nonexistent.csv")
    
    def test_parse_csv_empty_file(self, tmp_path):
        """Test parsing empty CSV file"""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")
        
        with pytest.raises(RuntimeError):
            parse_csv(str(csv_file))
    
    def test_parse_csv_only_headers(self, tmp_path):
        """Test CSV with only headers, no data"""
        csv_file = tmp_path / "headers_only.csv"
        csv_file.write_text("name,age,city")
        
        df = parse_csv(str(csv_file))
        assert len(df) == 0  # No data rows
        assert len(df.columns) == 3
    
    def test_parse_csv_special_characters(self, tmp_path):
        """Test CSV with special characters"""
        csv_file = tmp_path / "special.csv"
        csv_file.write_text('name,description\n"John","Hello, World"\n"Jane","Test & Test"')
        
        df = parse_csv(str(csv_file))
        assert len(df) == 2
        assert df.iloc[0]["description"] == "Hello, World"


class TestParseJSON:
    """Test JSON parsing with edge cases"""
    
    def test_parse_json_list_of_records(self, tmp_path):
        """Test JSON with list of records"""
        json_file = tmp_path / "test.json"
        data = [{"name": "John", "age": 25}, {"name": "Jane", "age": 30}]
        json_file.write_text(json.dumps(data))
        
        result = parse_json(str(json_file))
        assert "records" in result
        assert len(result["records"]) == 2
    
    def test_parse_json_wrapped_records(self, tmp_path):
        """Test JSON with wrapped records"""
        json_file = tmp_path / "test.json"
        data = {"records": [{"name": "John"}, {"name": "Jane"}]}
        json_file.write_text(json.dumps(data))
        
        result = parse_json(str(json_file))
        assert len(result["records"]) == 2
    
    def test_parse_json_single_object(self, tmp_path):
        """Test JSON with single object - should wrap as record"""
        json_file = tmp_path / "test.json"
        data = {"name": "John", "age": 25}
        json_file.write_text(json.dumps(data))
        
        result = parse_json(str(json_file))
        assert "records" in result
        assert len(result["records"]) == 1
        assert result["records"][0]["name"] == "John"
    
    def test_parse_json_empty_file(self, tmp_path):
        """Test empty JSON file - should return empty records"""
        json_file = tmp_path / "empty.json"
        json_file.write_text("")
        
        result = parse_json(str(json_file))
        assert result == {"records": []}
    
    def test_parse_json_invalid_json(self, tmp_path):
        """Test invalid JSON - should raise RuntimeError"""
        json_file = tmp_path / "invalid.json"
        json_file.write_text("{invalid json")
        
        with pytest.raises(RuntimeError):
            parse_json(str(json_file))
    
    def test_parse_json_nonexistent_file(self):
        """Test non-existent JSON file"""
        with pytest.raises(FileNotFoundError):
            parse_json("nonexistent.json")
    
    def test_parse_json_nested_structure(self, tmp_path):
        """Test JSON with nested structure"""
        json_file = tmp_path / "nested.json"
        data = {"data": [{"name": "John", "details": {"age": 25}}]}
        json_file.write_text(json.dumps(data))
        
        result = parse_json(str(json_file))
        assert "records" in result
        assert len(result["records"]) == 1


class TestParseMarkdown:
    """Test Markdown parsing with edge cases"""
    
    def test_parse_valid_markdown(self, tmp_path):
        """Test parsing valid Markdown file"""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Header\n\nSome content here.")
        
        content = parse_markdown(str(md_file))
        assert "# Header" in content
        assert "Some content here." in content
    
    def test_parse_markdown_empty_file(self, tmp_path):
        """Test empty Markdown file"""
        md_file = tmp_path / "empty.md"
        md_file.write_text("")
        
        content = parse_markdown(str(md_file))
        assert content == ""
    
    def test_parse_markdown_with_whitespace(self, tmp_path):
        """Test Markdown with excessive whitespace"""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Header\n\n\n\n\nContent\n\n\n")
        
        content = parse_markdown(str(md_file))
        # Should normalize multiple newlines
        assert "\n\n\n\n" not in content
    
    def test_parse_markdown_nonexistent_file(self):
        """Test non-existent Markdown file"""
        with pytest.raises(FileNotFoundError):
            parse_markdown("nonexistent.md")


class TestParseExcel:
    """Test Excel parsing - requires openpyxl"""
    
    def test_parse_excel_nonexistent_file(self):
        """Test non-existent Excel file"""
        with pytest.raises(FileNotFoundError):
            parse_excel("nonexistent.xlsx")
    
    # Note: Full Excel tests require creating Excel files which needs openpyxl
    # Skipping detailed Excel tests for now unless openpyxl is available

