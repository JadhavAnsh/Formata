import pytest
import pandas as pd
import numpy as np
from app.services.missing_data import (
    analyze_missing_data,
    handle_missing_data,
    get_missing_data_summary
)


class TestMissingData:
    """Test missing data handling functionality"""
    
    def test_analyze_missing_data(self):
        """Test missing data analysis"""
        df = pd.DataFrame({
            'col1': [1, 2, None, 4, 5],
            'col2': [None, None, None, None, None],
            'col3': ['a', 'b', 'c', 'd', 'e']
        })
        
        analysis = analyze_missing_data(df)
        
        assert analysis['total_rows'] == 5
        assert analysis['total_missing'] == 6  # 1 in col1, 5 in col2
        assert 'col1' in analysis['columns']
        assert 'col2' in analysis['columns']
        assert 'col3' not in analysis['columns']
        assert analysis['columns']['col2']['missing_percentage'] == 100.0
    
    def test_analyze_missing_data_recommendations(self):
        """Test that recommendations are generated"""
        df = pd.DataFrame({
            'numeric_col': [1.5, 2.3, None, 4.1, 5.0],
            'bool_col': [True, False, None, True, False],
            'string_col': ['a', None, 'c', 'd', 'e']
        })
        
        analysis = analyze_missing_data(df)
        
        assert 'numeric_col' in analysis['recommendations']
        assert 'bool_col' in analysis['recommendations']
        assert 'string_col' in analysis['recommendations']
        # Numeric columns should recommend median
        assert analysis['recommendations']['numeric_col'] == 'fill_median'
    
    def test_handle_missing_data_fill_mean(self):
        """Test filling missing data with mean"""
        df = pd.DataFrame({
            'value': [10.0, 20.0, None, 40.0, 50.0]
        })
        
        strategy = {'value': 'fill_mean'}
        result_df, report = handle_missing_data(df, strategy=strategy)
        
        assert result_df['value'].isna().sum() == 0
        assert result_df['value'].iloc[2] == 30.0  # Mean of 10, 20, 40, 50
        assert report['columns_processed'] == 1
    
    def test_handle_missing_data_fill_median(self):
        """Test filling missing data with median"""
        df = pd.DataFrame({
            'value': [10.0, 20.0, None, 40.0, 50.0]
        })
        
        strategy = {'value': 'fill_median'}
        result_df, report = handle_missing_data(df, strategy=strategy)
        
        assert result_df['value'].isna().sum() == 0
        assert result_df['value'].iloc[2] == 30.0  # Median of 10, 20, 40, 50
    
    def test_handle_missing_data_fill_mode(self):
        """Test filling missing data with mode"""
        df = pd.DataFrame({
            'category': ['A', 'B', 'A', None, 'A', 'B']
        })
        
        strategy = {'category': 'fill_mode'}
        result_df, report = handle_missing_data(df, strategy=strategy)
        
        assert result_df['category'].isna().sum() == 0
        assert result_df['category'].iloc[3] == 'A'  # Mode is 'A'
    
    def test_handle_missing_data_forward_fill(self):
        """Test forward filling"""
        df = pd.DataFrame({
            'value': [10, None, None, 40, None]
        })
        
        strategy = {'value': 'fill_forward'}
        result_df, report = handle_missing_data(df, strategy=strategy)
        
        assert result_df['value'].isna().sum() == 0
        assert result_df['value'].iloc[1] == 10  # Forward filled from 10
        assert result_df['value'].iloc[2] == 10  # Forward filled from 10
        assert result_df['value'].iloc[4] == 40  # Forward filled from 40
    
    def test_handle_missing_data_backward_fill(self):
        """Test backward filling"""
        df = pd.DataFrame({
            'value': [None, None, 30, None, 50]
        })
        
        strategy = {'value': 'fill_backward'}
        result_df, report = handle_missing_data(df, strategy=strategy)
        
        assert result_df['value'].isna().sum() == 0
        assert result_df['value'].iloc[0] == 30  # Backward filled from 30
        assert result_df['value'].iloc[3] == 50  # Backward filled from 50
    
    def test_handle_missing_data_drop_rows(self):
        """Test dropping rows with missing data"""
        df = pd.DataFrame({
            'value': [10, None, 30, None, 50]
        })
        
        strategy = {'value': 'drop_rows'}
        result_df, report = handle_missing_data(df, strategy=strategy)
        
        assert len(result_df) == 3  # Only rows with data remain
        assert result_df['value'].isna().sum() == 0
        assert report['rows_dropped'] == 2
    
    def test_handle_missing_data_drop_columns(self):
        """Test dropping columns with too much missing data"""
        df = pd.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'col2': [None, None, None, None, None],
            'col3': [10, None, 30, 40, 50]
        })
        
        strategy = {
            'col2': 'drop_columns',
            'col3': 'fill_mean'
        }
        result_df, report = handle_missing_data(df, strategy=strategy)
        
        assert 'col2' not in result_df.columns
        assert 'col1' in result_df.columns
        assert 'col3' in result_df.columns
        assert report['columns_dropped'] == 1
    
    def test_handle_missing_data_flag(self):
        """Test flagging missing data"""
        df = pd.DataFrame({
            'value': [10, None, 30, None, 50]
        })
        
        strategy = {'value': 'flag'}
        result_df, report = handle_missing_data(df, strategy=strategy)
        
        assert 'value_missing' in result_df.columns
        assert result_df['value_missing'].iloc[1] == True
        assert result_df['value_missing'].iloc[0] == False
        assert result_df['value_missing'].sum() == 2
    
    def test_handle_missing_data_fill_value(self):
        """Test filling with custom value"""
        df = pd.DataFrame({
            'value': [10, None, 30, None, 50]
        })
        
        strategy = {'value': 'fill_value'}
        result_df, report = handle_missing_data(df, strategy=strategy, fill_value=0)
        
        assert result_df['value'].isna().sum() == 0
        assert result_df['value'].iloc[1] == 0
        assert result_df['value'].iloc[3] == 0
    
    def test_handle_missing_data_auto_recommendations(self):
        """Test using automatic recommendations"""
        df = pd.DataFrame({
            'numeric_col': [1.5, None, 3.5, 4.0, 5.0],
            'string_col': ['a', 'b', None, 'd', 'e']
        })
        
        # Don't provide strategy, let it use auto-recommendations
        result_df, report = handle_missing_data(df, strategy=None)
        
        assert result_df['numeric_col'].isna().sum() == 0
        assert result_df['string_col'].isna().sum() == 0
        assert report['columns_processed'] == 2
    
    def test_handle_missing_data_mixed_strategies(self):
        """Test using different strategies for different columns"""
        df = pd.DataFrame({
            'col1': [1, None, 3, 4, 5],
            'col2': [10, 20, None, 40, 50],
            'col3': ['a', None, 'c', 'd', 'e']
        })
        
        strategy = {
            'col1': 'fill_mean',
            'col2': 'fill_median',
            'col3': 'fill_mode'
        }
        result_df, report = handle_missing_data(df, strategy=strategy)
        
        assert result_df.isna().sum().sum() == 0
        assert report['columns_processed'] == 3
    
    def test_get_missing_data_summary(self):
        """Test getting human-readable summary"""
        df = pd.DataFrame({
            'col1': [1, None, 3, None, 5],
            'col2': [10, 20, 30, 40, 50]
        })
        
        summary = get_missing_data_summary(df)
        
        assert 'col1' in summary
        assert 'Missing Data Summary' in summary
        assert '40.0%' in summary  # col1 has 40% missing
    
    def test_empty_dataframe(self):
        """Test handling of empty DataFrame"""
        df = pd.DataFrame()
        
        result_df, report = handle_missing_data(df)
        
        assert len(result_df) == 0
        assert report['columns_processed'] == 0
    
    def test_no_missing_data(self):
        """Test DataFrame with no missing data"""
        df = pd.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'col2': ['a', 'b', 'c', 'd', 'e']
        })
        
        analysis = analyze_missing_data(df)
        summary = get_missing_data_summary(df)
        
        assert analysis['total_missing'] == 0
        assert '✓ No missing values detected' in summary
    
    def test_default_strategy(self):
        """Test using default strategy for all columns"""
        df = pd.DataFrame({
            'col1': [1, None, 3],
            'col2': [10, None, 30]
        })
        
        result_df, report = handle_missing_data(df, default_strategy='fill_median')
        
        assert result_df.isna().sum().sum() == 0
        assert report['columns_processed'] == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
