"""
Comprehensive tests for validation service
Testing schema validation edge cases
"""
import pytest
from app.services.validation import validate_schema, get_validation_errors, _check_type


class TestCheckType:
    """Test internal type checker"""
    
    def test_check_string_type(self):
        """Test string type checking"""
        assert _check_type("hello", "string") == True
        assert _check_type(123, "string") == False
    
    def test_check_number_type(self):
        """Test number type checking"""
        assert _check_type(123, "number") == True
        assert _check_type("123", "number") == True
        assert _check_type("abc", "number") == False
    
    def test_check_boolean_type(self):
        """Test boolean type checking"""
        assert _check_type(True, "boolean") == True
        assert _check_type(False, "boolean") == True
        assert _check_type("true", "boolean") == False
    
    def test_check_null_value(self):
        """Test null values - should return True"""
        assert _check_type(None, "string") == True
        assert _check_type(None, "number") == True


class TestValidateSchema:
    """Test schema validation"""
    
    def test_validate_empty_data(self):
        """Test validation with empty data - should return True"""
        assert validate_schema({}, {}) == True
        assert validate_schema(None, {}) == True
    
    def test_validate_required_field_present(self):
        """Test validation with required field present"""
        data = {"records": [{"name": "John", "age": 25}]}
        schema = {"name": {"required": True}}
        assert validate_schema(data, schema) == True
    
    def test_validate_required_field_missing(self):
        """Test validation with required field missing"""
        data = {"records": [{"age": 25}]}
        schema = {"name": {"required": True}}
        assert validate_schema(data, schema) == False
    
    def test_validate_type_mismatch(self):
        """Test validation with type mismatch"""
        data = {"records": [{"age": "abc"}]}
        schema = {"age": {"type": "number"}}
        assert validate_schema(data, schema) == False
    
    def test_validate_numeric_min_constraint(self):
        """Test validation with min constraint"""
        data = {"records": [{"age": 5}]}
        schema = {"age": {"type": "number", "min": 10}}
        assert validate_schema(data, schema) == False
    
    def test_validate_numeric_max_constraint(self):
        """Test validation with max constraint"""
        data = {"records": [{"age": 150}]}
        schema = {"age": {"type": "number", "max": 120}}
        assert validate_schema(data, schema) == False
    
    def test_validate_numeric_within_range(self):
        """Test validation with value within range"""
        data = {"records": [{"age": 25}]}
        schema = {"age": {"type": "number", "min": 0, "max": 120}}
        assert validate_schema(data, schema) == True
    
    def test_validate_invalid_data_format(self):
        """Test validation with invalid data format"""
        data = {"records": "not a list"}
        schema = {"name": {"required": True}}
        assert validate_schema(data, schema) == False


class TestGetValidationErrors:
    """Test validation error reporting"""
    
    def test_get_errors_empty_data(self):
        """Test error reporting with empty data"""
        errors = get_validation_errors({}, {})
        assert len(errors) == 0
    
    def test_get_errors_required_field_missing(self):
        """Test error message for missing required field"""
        data = {"records": [{"age": 25}]}
        schema = {"name": {"required": True}}
        errors = get_validation_errors(data, schema)
        assert len(errors) == 1
        assert "Missing required field" in errors[0]
    
    def test_get_errors_type_mismatch(self):
        """Test error message for type mismatch"""
        data = {"records": [{"age": "abc"}]}
        schema = {"age": {"type": "number"}}
        errors = get_validation_errors(data, schema)
        assert len(errors) == 1
        assert "expected number" in errors[0]
    
    def test_get_errors_multiple_records(self):
        """Test error reporting across multiple records"""
        data = {"records": [
            {"name": "John", "age": 25},
            {"age": 30},  # Missing name
            {"name": "Bob", "age": "invalid"}  # Invalid age
        ]}
        schema = {
            "name": {"required": True},
            "age": {"type": "number"}
        }
        errors = get_validation_errors(data, schema)
        assert len(errors) == 2  # One for missing name, one for invalid age
    
    def test_get_errors_invalid_format(self):
        """Test error reporting with invalid data format"""
        data = {"records": "not a list"}
        schema = {"name": {"required": True}}
        errors = get_validation_errors(data, schema)
        assert len(errors) == 1
        assert "Invalid data format" in errors[0]
    
    def test_get_errors_numeric_constraints(self):
        """Test error reporting for numeric constraints"""
        data = {"records": [
            {"age": 5},  # Below min
            {"age": 150}  # Above max
        ]}
        schema = {"age": {"type": "number", "min": 10, "max": 120}}
        errors = get_validation_errors(data, schema)
        assert len(errors) >= 2
