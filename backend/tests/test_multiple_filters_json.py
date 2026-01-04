"""
Test to validate that multiple filters work correctly from JSON sent as query
"""
import pandas as pd
from app.services.filtering import apply_filters


def test_multiple_filters_from_json():
    """
    Test scenario: Frontend sends multiple filters via JSON
    """
    df = pd.DataFrame({
        "name": ["John Smith", "Jane Doe", "Bob Johnson", "Alice Williams", "Tom Baker"],
        "age": ["25", "30", "35", "28", "45"],  # String type (as CSV would be)
        "city": ["NYC", "LA", "NYC", "Chicago", "Boston"],
        "status": ["active", "inactive", "active", "active", "inactive"]
    })
    
    # Simulate JSON from frontend with multiple filters
    # This is what gets sent when user applies multiple filters
    filters_json = {
        "name": {"op": "contains", "value": "John"},  # Should match "John Smith" and "Bob Johnson"
        "age": {"op": ">=", "value": "30"},  # Should match ages >= 30
        "city": {"op": "equals", "value": "NYC"}  # Should match NYC rows
    }
    
    print("Original DataFrame:")
    print(df)
    print(f"\nFilters being applied: {filters_json}\n")
    
    result = apply_filters(df, filters_json)
    
    print("Result after applying ALL filters:")
    print(result)
    print(f"\nRows returned: {len(result)}")
    print("\nExpected: 1 row (Bob Johnson, age 35, NYC)")
    print("If multiple filters aren't working, might see 2 rows (text search only)")
    print(f"Actual rows returned: {len(result)}")
    
    # Assertion
    assert len(result) == 1, f"Expected 1 row with all filters, got {len(result)}"
    assert result.iloc[0]["name"] == "Bob Johnson"
    print("\n✅ Multiple filters working correctly!")


def test_filter_precedence():
    """
    Test to understand filter application order
    """
    df = pd.DataFrame({
        "product": ["Apple", "Banana", "Orange", "Applesauce"],
        "price": ["1.00", "0.50", "0.75", "2.50"],
        "quantity": ["10", "20", "5", "15"]
    })
    
    # Test 1: Text contains "Apple"
    filters1 = {"product": {"op": "contains", "value": "Apple"}}
    result1 = apply_filters(df, filters1)
    print("Filter 1 - Product contains 'Apple':")
    print(f"  Result: {len(result1)} rows\n")
    assert len(result1) == 2  # "Apple" and "Applesauce"
    
    # Test 2: Price > 1.00
    filters2 = {"price": {"op": ">", "value": "1.00"}}
    result2 = apply_filters(df, filters2)
    print("Filter 2 - Price > 1.00:")
    print(f"  Result: {len(result2)} rows\n")
    assert len(result2) == 1  # Only "Applesauce" at 2.50
    
    # Test 3: BOTH filters (should return only rows matching BOTH conditions)
    filters3 = {
        "product": {"op": "contains", "value": "Apple"},
        "price": {"op": ">", "value": "1.00"}
    }
    result3 = apply_filters(df, filters3)
    print("Filter 1+2 - Product contains 'Apple' AND Price > 1.00:")
    print(result3)
    print(f"  Result: {len(result3)} rows\n")
    print("Expected: 1 row (Applesauce, price 2.50)")
    assert len(result3) == 1  # Only "Applesauce"
    assert result3.iloc[0]["product"] == "Applesauce"
    print("✅ Filter combination works!")


if __name__ == "__main__":
    print("="*60)
    print("TEST 1: Multiple Filters from JSON")
    print("="*60)
    test_multiple_filters_from_json()
    
    print("\n" + "="*60)
    print("TEST 2: Filter Precedence")
    print("="*60)
    test_filter_precedence()
    
    print("\n✅ All tests passed!")
