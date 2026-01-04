"""
Test to reproduce the multiple filters bug
"""
import pandas as pd
from app.services.filtering import apply_filters


def test_multiple_filters_bug():
    """
    Reproduce the issue: when multiple filters are applied,
    only one filter is being used
    """
    df = pd.DataFrame({
        "name": ["John Smith", "Jane Doe", "Bob Johnson", "Alice Williams"],
        "age": [25, 30, 35, 28],
        "city": ["NYC", "LA", "NYC", "Chicago"]
    })
    
    # Test 1: Apply only text search
    filters1 = {
        "_textSearch": {"op": "contains", "value": "John"}
    }
    result1 = apply_filters(df, filters1)
    print(f"Text search only: {len(result1)} rows")
    print(result1)
    assert len(result1) == 2  # Should match "John Smith" and "Johnson"
    
    # Test 2: Apply only numeric filter
    filters2 = {
        "age": {"op": ">=", "value": 30}
    }
    result2 = apply_filters(df, filters2)
    print(f"\nNumeric filter only: {len(result2)} rows")
    print(result2)
    assert len(result2) == 2  # Jane (30), Bob (35)
    
    # Test 3: Apply BOTH filters (text search AND age >= 30)
    # Expected: Only rows where name contains "John" AND age >= 30
    # Should be: "Bob Johnson" (age 35)
    filters3 = {
        "_textSearch": {"op": "contains", "value": "John"},
        "age": {"op": ">=", "value": 30}
    }
    result3 = apply_filters(df, filters3)
    print(f"\nBoth filters: {len(result3)} rows")
    print(result3)
    
    # BUG: This assertion will fail because only one filter is applied
    print(f"\nExpected: 1 row (Bob Johnson with age 35)")
    print(f"Actual: {len(result3)} rows")
    assert len(result3) == 1, f"Expected 1 row, got {len(result3)}"


if __name__ == "__main__":
    test_multiple_filters_bug()
    print("\n✅ All tests passed!")
