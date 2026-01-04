# Test for data quality score calculation
import unittest
import pandas as pd
import numpy as np
from app.services.validation import calculate_data_quality_score


class TestQualityScore(unittest.TestCase):
    
    def test_perfect_quality_score(self):
        """Test quality score calculation with perfect data"""
        df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
            'age': [25, 30, 35, 28, 32],
            'score': [85.5, 90.0, 78.5, 92.0, 88.0]
        })
        
        result = calculate_data_quality_score(df)
        
        self.assertIn('overall_score', result)
        self.assertIn('completeness_score', result)
        self.assertIn('validity_score', result)
        self.assertIn('consistency_score', result)
        self.assertIn('accuracy_score', result)
        self.assertIn('grade', result)
        
        # Perfect data should have high scores
        self.assertGreater(result['overall_score'], 80)
        self.assertEqual(result['completeness_score'], 100.0)
        print(f"\n✓ Perfect quality data: {result['overall_score']}/100 (Grade: {result['grade']})")
    
    def test_missing_data_quality_score(self):
        """Test quality score calculation with missing data"""
        df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', None, 'Charlie', None, 'Eve'],
            'age': [25, 30, None, 28, None],
            'score': [85.5, None, 78.5, None, 88.0]
        })
        
        result = calculate_data_quality_score(df)
        
        # Missing data should reduce completeness score
        self.assertLess(result['completeness_score'], 100.0)
        self.assertLess(result['overall_score'], 100.0)
        print(f"\n✓ Data with missing values: {result['overall_score']}/100 (Grade: {result['grade']})")
        print(f"  - Completeness: {result['completeness_score']}/100")
    
    def test_duplicate_data_quality_score(self):
        """Test quality score calculation with duplicates"""
        df = pd.DataFrame({
            'id': [1, 2, 3, 3, 3],  # Duplicates
            'name': ['Alice', 'Bob', 'Charlie', 'Charlie', 'Charlie'],
            'age': [25, 30, 35, 35, 35]
        })
        
        result = calculate_data_quality_score(df)
        
        # Duplicates should reduce accuracy score
        self.assertLess(result['accuracy_score'], 100.0)
        print(f"\n✓ Data with duplicates: {result['overall_score']}/100 (Grade: {result['grade']})")
        print(f"  - Accuracy: {result['accuracy_score']}/100")
    
    def test_outliers_quality_score(self):
        """Test quality score calculation with outliers"""
        df = pd.DataFrame({
            'id': range(1, 11),
            'value': [10, 12, 11, 13, 12, 14, 11, 13, 1000, 12]  # 1000 is outlier
        })
        
        result = calculate_data_quality_score(df)
        
        # Outliers should reduce accuracy score
        self.assertLess(result['accuracy_score'], 100.0)
        print(f"\n✓ Data with outliers: {result['overall_score']}/100 (Grade: {result['grade']})")
        print(f"  - Accuracy: {result['accuracy_score']}/100")
    
    def test_quality_score_factors(self):
        """Test that all quality factors are properly included"""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['A', 'B', 'C']
        })
        
        result = calculate_data_quality_score(df)
        
        self.assertIn('factors', result)
        self.assertIn('completeness', result['factors'])
        self.assertIn('validity', result['factors'])
        self.assertIn('consistency', result['factors'])
        self.assertIn('accuracy', result['factors'])
        
        # Check factor structure
        for factor_name, factor_data in result['factors'].items():
            self.assertIn('score', factor_data)
            self.assertIn('weight', factor_data)
            self.assertIn('description', factor_data)
        
        print(f"\n✓ Quality score factors:")
        for name, data in result['factors'].items():
            print(f"  - {name.capitalize()}: {data['score']}/100 (weight: {data['weight']}%)")
    
    def test_quality_grade_assignment(self):
        """Test grade assignment based on score"""
        test_cases = [
            (pd.DataFrame({'a': [1, 2, 3]}), 'A'),  # Perfect data
            (pd.DataFrame({'a': [1, None, 3]}), None),  # Some missing data
        ]
        
        for df, expected_grade_min in test_cases:
            result = calculate_data_quality_score(df)
            self.assertIn('grade', result)
            self.assertIn(result['grade'], ['A', 'B', 'C', 'D', 'F'])
            print(f"\n✓ Quality grade: {result['grade']} (Score: {result['overall_score']}/100)")


if __name__ == '__main__':
    unittest.main()
