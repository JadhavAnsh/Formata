"""
Comprehensive test for multiple filters to understand the actual behavior
"""
import pandas as pd
from app.services.filtering import apply_filters


def test_filters_detailed():
    """Test multiple filters in detail"""
    df = pd.DataFrame({
        "name": ["John Smith", "Jane Doe", "Bob Johnson", "Alice Williams", "Tom Baker"],
        "age": [25, 30, 35, 28, 45],
        "city": ["NYC", "LA", "NYC", "Chicago", "Boston"],
        "active": [True, True, False, True, False]
    })
    
    print("="*60)
    print("Original DataFrame:")
    print(df)
    print(f"Total rows: {len(df)}\n")
    
    # Test 1: Text search for "John"
    print("="*60)
    print("Test 1: Text search containing 'John'")
    filters1 = {"_textSearch": {"op": "contains", "value": "John"}}
    result1 = apply_filters(df, filters1)
    print(result1)
    print(f"Result: {len(result1)} rows\n")
    
    # Test 2: Age >= 30
    print("="*60)
    print("Test 2: Age >= 30")
    filters2 = {"age": {"op": ">=", "value": 30}}
    result2 = apply_filters(df, filters2)
    print(result2)
    print(f"Result: {len(result2)} rows\n")
    
    # Test 3: City = "NYC"
    print("="*60)
    print("Test 3: City equals 'NYC'")
    filters3 = {"city": {"op": "equals", "value": "NYC"}}
    result3 = apply_filters(df, filters3)
    print(result3)
    print(f"Result: {len(result3)} rows\n")
    
    # Test 4: Multiple column filters (should work)
    print("="*60)
    print("Test 4: Age >= 30 AND City = 'NYC'")
    filters4 = {
        "age": {"op": ">=", "value": 30},
        "city": {"op": "equals", "value": "NYC"}
    }
    result4 = apply_filters(df, filters4)
    print(result4)
    print(f"Result: {len(result4)} rows")
    print("Expected: 1 row (Bob Johnson, 35, NYC)\n")
    
    # Test 5: Text search + column filter
    print("="*60)
    print("Test 5: Text search 'John' AND Age >= 30")
    filters5 = {
        "_textSearch": {"op": "contains", "value": "John"},
        "age": {"op": ">=", "value": 30}
    }
    result5 = apply_filters(df, filters5)
    print(result5)
    print(f"Result: {len(result5)} rows")
    print("Expected: 1 row (Bob Johnson, 35)")
    print("BUG: If only text search was applied, result would be 2 rows\n")
    
    # Test 6: Multiple column filters + text search
    print("="*60)
    print("Test 6: Text 'John' AND Age >= 30 AND City = 'NYC'")
    filters6 = {
        "_textSearch": {"op": "contains", "value": "John"},
        "age": {"op": ">=", "value": 30},
        "city": {"op": "equals", "value": "NYC"}
    }
    result6 = apply_filters(df, filters6)
    print(result6)
    print(f"Result: {len(result6)} rows")
    print("Expected: 1 row (Bob Johnson, 35, NYC)\n")


if __name__ == "__main__":
    test_filters_detailed()
