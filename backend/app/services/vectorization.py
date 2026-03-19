# Embeddings and vectorization for LLM integration
import numpy as np
import pandas as pd
import pickle
import h5py
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
import os
from app.config.settings import settings
from app.utils.logger import logger

# Stateless vectorizer (no fitting required)
_vectorizer = HashingVectorizer(
    n_features=512,
    alternate_sign=False,
    norm="l2"
)

def _get_genai():
    """Lazy import for Google Generative AI"""
    import google.generativeai as genai
    if settings.google_api_key:
        genai.configure(api_key=settings.google_api_key)
    return genai

def generate_embeddings(text: str, provider: str = "local") -> np.ndarray:
    """
    Generate embeddings for text data
    Providers: 'local' (Hashing), 'gemini' (Google Generative AI)
    """
    if not text or not isinstance(text, str):
        size = 768 if provider == "gemini" else 512
        return np.zeros(size)

    try:
        if provider == "gemini" and settings.google_api_key:
            genai = _get_genai()
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document"
            )
            return np.array(result['embedding'])
        else:
            # Fallback to local hashing
            vector = _vectorizer.transform([text])
            return vector.toarray()[0]

    except Exception as e:
        logger.error(f"Embedding error with provider {provider}: {str(e)}")
        size = 768 if provider == "gemini" else 512
        return np.zeros(size)


def batch_generate_embeddings(texts: List[str], provider: str = "local") -> List[np.ndarray]:
    """
    Generate embeddings for multiple texts
    """
    if not texts:
        return []

    try:
        texts = [t if isinstance(t, str) else "" for t in texts]
        
        if provider == "gemini" and settings.google_api_key:
            genai = _get_genai()
            # Gemini batch embedding (max 100 per request)
            # For simplicity, we process in chunks if needed
            all_embeddings = []
            chunk_size = 100
            for i in range(0, len(texts), chunk_size):
                chunk = texts[i:i + chunk_size]
                result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=chunk,
                    task_type="retrieval_document"
                )
                all_embeddings.extend(result['embedding'])
            return all_embeddings
        else:
            vectors = _vectorizer.transform(texts)
            embeddings = vectors.toarray()
            # If Gemini was requested but we are falling back, pad/truncate to 768
            if provider == "gemini":
                padded = np.zeros((embeddings.shape[0], 768))
                padded[:, :512] = embeddings
                return padded.tolist()
            return embeddings.tolist()

    except Exception as e:
        logger.error(f"Batch embedding error with provider {provider}: {str(e)}")
        size = 768 if provider == "gemini" else 512
        return [np.zeros(size) for _ in texts]


def dataframe_to_vectors(df: pd.DataFrame, method: str = "hybrid", provider: str = "local") -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Convert DataFrame to vector representation suitable for LLMs
    
    Methods:
    - 'hybrid': Combines text embeddings + numeric normalization + one-hot encoding
    - 'text_only': Text embeddings for all columns (treats everything as text)
    - 'numeric': Numeric normalization only (scales values to 0-1)
    
    Providers:
    - 'local': HashingVectorizer (512d)
    - 'gemini': Google Generative AI (768d)
    
    Returns:
        - vectors: numpy array of shape (n_samples, n_features)
        - metadata: dict with vectorization info (column mapping, feature names, etc.)
    """
    if df is None or df.empty:
        raise ValueError("DataFrame is empty")
    
    embedding_size = 768 if provider == "gemini" else 512
    
    try:
        vectors_list = []
        column_metadata = {}
        feature_names = []
        current_feature_idx = 0
        
        for col_name in df.columns:
            col_data = df[col_name]
            col_type = col_data.dtype
            
            # Handle numeric columns
            if pd.api.types.is_numeric_dtype(col_type):
                # Normalize numeric columns
                numeric_vector = col_data.fillna(col_data.median()).values.reshape(-1, 1)
                scaler = StandardScaler()
                scaled = scaler.fit_transform(numeric_vector).flatten()
                
                vectors_list.append(scaled.reshape(-1, 1))
                column_metadata[col_name] = {
                    "type": "numeric",
                    "feature_indices": [current_feature_idx],
                    "scaler_params": {
                        "mean": float(scaler.mean_[0]),
                        "std": float(scaler.scale_[0])
                    }
                }
                feature_names.append(f"{col_name}_normalized")
                current_feature_idx += 1
            
            # Handle boolean columns
            elif pd.api.types.is_bool_dtype(col_type):
                bool_vector = col_data.astype(int).values.reshape(-1, 1)
                vectors_list.append(bool_vector)
                column_metadata[col_name] = {
                    "type": "boolean",
                    "feature_indices": [current_feature_idx]
                }
                feature_names.append(f"{col_name}_bool")
                current_feature_idx += 1
            
            # Handle categorical/text columns
            else:
                if method == "hybrid" or method == "text_only":
                    # Use text embeddings for text columns
                    texts = col_data.fillna("").astype(str).tolist()
                    embeddings = batch_generate_embeddings(texts, provider=provider)
                    embeddings_array = np.array(embeddings)
                    vectors_list.append(embeddings_array)
                    
                    column_metadata[col_name] = {
                        "type": "text_embedded",
                        "feature_indices": list(range(current_feature_idx, current_feature_idx + embedding_size)),
                        "embedding_size": embedding_size,
                        "provider": provider
                    }
                    feature_names.extend([f"{col_name}_emb_{i}" for i in range(embedding_size)])
                    current_feature_idx += embedding_size
                else:
                    # Numeric-only method: one-hot encode categorical
                    unique_vals = col_data.nunique()
                    if unique_vals <= 10:  # Only one-hot encode if not too many categories
                        one_hot = pd.get_dummies(col_data, prefix=col_name, drop_first=True)
                        vectors_list.append(one_hot.values)
                        column_metadata[col_name] = {
                            "type": "categorical_encoded",
                            "feature_indices": list(range(current_feature_idx, current_feature_idx + len(one_hot.columns))),
                            "categories": one_hot.columns.tolist()
                        }
                        feature_names.extend(one_hot.columns.tolist())
                        current_feature_idx += len(one_hot.columns)
                    else:
                        # Too many categories, use text embedding
                        texts = col_data.fillna("").astype(str).tolist()
                        embeddings = batch_generate_embeddings(texts, provider=provider)
                        embeddings_array = np.array(embeddings)
                        vectors_list.append(embeddings_array)
                        column_metadata[col_name] = {
                            "type": "text_embedded",
                            "feature_indices": list(range(current_feature_idx, current_feature_idx + embedding_size)),
                            "embedding_size": embedding_size,
                            "provider": provider
                        }
                        feature_names.extend([f"{col_name}_emb_{i}" for i in range(embedding_size)])
                        current_feature_idx += embedding_size
        
        # Concatenate all vectors
        final_vectors = np.hstack(vectors_list)
        
        metadata = {
            "shape": final_vectors.shape,
            "method": method,
            "provider": provider,
            "n_samples": final_vectors.shape[0],
            "n_features": final_vectors.shape[1],
            "column_metadata": column_metadata,
            "feature_names": feature_names,
            "original_columns": list(df.columns)
        }
        
        return final_vectors, metadata
        
    except Exception as e:
        raise RuntimeError(f"Failed to vectorize DataFrame: {str(e)}")


def save_vectors_pickle(vectors: np.ndarray, metadata: Dict[str, Any], output_path: str) -> None:
    """
    Save vectors and metadata to pickle file (.pkl)
    """
    try:
        data = {
            "vectors": vectors,
            "metadata": metadata
        }
        with open(output_path, 'wb') as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        raise RuntimeError(f"Failed to save pickle file: {str(e)}")


def save_vectors_hdf5(vectors: np.ndarray, metadata: Dict[str, Any], output_path: str) -> None:
    """
    Save vectors and metadata to HDF5 file (.h5)
    HDF5 is better for large datasets and supports chunking
    """
    try:
        with h5py.File(output_path, 'w') as f:
            # Store main vectors
            f.create_dataset('vectors', data=vectors, compression='gzip', compression_opts=9)
            
            # Store metadata
            meta_group = f.create_group('metadata')
            meta_group.attrs['shape'] = vectors.shape
            meta_group.attrs['method'] = metadata.get('method', 'hybrid')
            meta_group.attrs['n_samples'] = metadata.get('n_samples', vectors.shape[0])
            meta_group.attrs['n_features'] = metadata.get('n_features', vectors.shape[1])
            
            # Store feature names
            feature_names = metadata.get('feature_names', [])
            f.create_dataset('feature_names', data=[n.encode('utf-8') for n in feature_names])
            
            # Store column metadata as JSON-compatible structure
            columns_group = meta_group.create_group('column_info')
            for col_name, col_info in metadata.get('column_metadata', {}).items():
                col_group = columns_group.create_group(col_name)
                col_group.attrs['type'] = col_info.get('type', 'unknown')
                if 'feature_indices' in col_info:
                    col_group.create_dataset('feature_indices', data=col_info['feature_indices'])
                if 'scaler_params' in col_info:
                    params_group = col_group.create_group('scaler_params')
                    for k, v in col_info['scaler_params'].items():
                        params_group.attrs[k] = v
            
            # Store original columns
            original_cols = metadata.get('original_columns', [])
            f.create_dataset('original_columns', data=[c.encode('utf-8') for c in original_cols])
    except Exception as e:
        raise RuntimeError(f"Failed to save HDF5 file: {str(e)}")


def load_vectors_pickle(file_path: str) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Load vectors and metadata from pickle file
    """
    try:
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
        return data['vectors'], data['metadata']
    except Exception as e:
        raise RuntimeError(f"Failed to load pickle file: {str(e)}")


def load_vectors_hdf5(file_path: str) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Load vectors and metadata from HDF5 file
    """
    try:
        with h5py.File(file_path, 'r') as f:
            vectors = f['vectors'][:]
            
            metadata = {
                "shape": tuple(f['metadata'].attrs['shape']),
                "method": f['metadata'].attrs['method'],
                "n_samples": int(f['metadata'].attrs['n_samples']),
                "n_features": int(f['metadata'].attrs['n_features']),
                "feature_names": [name.decode('utf-8') if isinstance(name, bytes) else name 
                                for name in f['feature_names'][:]],
                "original_columns": [col.decode('utf-8') if isinstance(col, bytes) else col 
                                   for col in f['original_columns'][:]],
                "column_metadata": {}
            }
        
        return vectors, metadata
    except Exception as e:
        raise RuntimeError(f"Failed to load HDF5 file: {str(e)}")
