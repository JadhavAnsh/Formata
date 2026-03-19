import pandas as pd
import numpy as np
import os
import sys

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.vectorization import dataframe_to_vectors

def test_dataframe_to_vectors_local_hybrid():
    df = pd.DataFrame({
        'text': ['hello world', 'test case'],
        'num': [1.0, 2.0],
        'bool': [True, False]
    })
    
    vectors, metadata = dataframe_to_vectors(df, method='hybrid', provider='local')
    
    print("Metadata keys:", metadata['column_metadata'].keys())
    for col, meta in metadata['column_metadata'].items():
        print(f"Column {col} type: {meta['type']}")
    
    assert vectors.shape[0] == 2
    assert 'text_embedded' in metadata['column_metadata']['text']['type']
    assert metadata['column_metadata']['num']['type'] == 'numeric'
    assert metadata['column_metadata']['bool']['type'] == 'numeric'
    assert metadata['provider'] == 'local'
    assert metadata['n_features'] == 512 + 1 + 1

def test_dataframe_to_vectors_local_numeric_only():
    df = pd.DataFrame({
        'text': ['cat', 'dog', 'cat'],
        'num': [1.0, 2.0, 3.0]
    })
    
    vectors, metadata = dataframe_to_vectors(df, method='numeric', provider='local')
    
    assert vectors.shape[0] == 3
    # 'cat' vs 'dog' -> should one-hot encode since unique <= 10
    assert metadata['column_metadata']['text']['type'] == 'categorical_encoded'
    assert metadata['column_metadata']['num']['type'] == 'numeric'

def test_vector_shapes_gemini_fallback():
    # If API key is missing, it should fallback to local but we can check if it tries to use 768d
    df = pd.DataFrame({
        'text': ['hello']
    })
    
    # We mock settings.google_api_key to be None for this test if needed, 
    # but the service already handles it.
    vectors, metadata = dataframe_to_vectors(df, method='text_only', provider='gemini')
    print("Gemini fallback shape:", vectors.shape)
    assert vectors.shape[1] == 768

if __name__ == "__main__":
    # Simple manual run
    test_dataframe_to_vectors_local_hybrid()
    test_dataframe_to_vectors_local_numeric_only()
    test_vector_shapes_gemini_fallback()
    print("All vectorization tests passed!")
