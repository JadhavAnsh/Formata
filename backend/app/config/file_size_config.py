"""
Production-grade configuration and utilities for file-size aware processing.

Automatically adjusts pipeline behavior based on file size:
- < 1MB: Full pipeline with all features
- 1-50MB: Balance between quality and speed. Sample for expensive ops.
- > 50MB: Fast mode. Skip heavy operations.
"""

from typing import Dict, Any, Optional


class FileSizeConfig:
    """Configuration auto-tuned based on file size"""
    
    # Size thresholds in MB
    SMALL_FILE_THRESHOLD = 1
    LARGE_FILE_THRESHOLD = 50
    HUGE_FILE_THRESHOLD = 500
    
    @staticmethod
    def get_config_for_size(file_size_mb: float, user_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get optimized configuration based on file size.
        
        Args:
            file_size_mb: File size in megabytes
            user_config: User-provided overrides
        
        Returns:
            Configuration dict for processing pipeline
        """
        # Base config (small file, full quality)
        config = {
            # Normalization & type detection
            "enable_auto_schema": True,
            "schema_sample_size": None,  # Use full dataset
            "use_hybrid_detection": True,
            
            # Data cleaning
            "remove_duplicates": True,
            "remove_outliers": False,
            "enable_drift_detection": True,
            "drift_baseline_sample": None,
            
            # Data profiling
            "enable_profiles": False,  # Can be expensive
            "profile_sample_size": None,
            
            # Vectorization
            "enable_vectorization": False,  # Very expensive
            
            # Missing data
            "handle_missing_data": True,
            "use_knn_imputation": False,  # Expensive
            "missing_strategy": "preserve",
            
            # Preview limits
            "result_preview_rows": 5000,
            
            # Processing timeouts
            "processing_timeout_seconds": 900,  # 15 min
            "normalization_timeout_seconds": 60,  # Per-column timeout
        }
        
        # Adjust for large files (1-50 MB)
        if FileSizeConfig.SMALL_FILE_THRESHOLD < file_size_mb <= FileSizeConfig.LARGE_FILE_THRESHOLD:
            config.update({
                "enable_profiles": False,  # Too slow
                "schema_sample_size": 10000,  # Sample for RF expensive ops
                "profile_sample_size": 5000,
                "result_preview_rows": 2000,
                "use_knn_imputation": False,
                "remove_outliers": False,
                "processing_timeout_seconds": 1200,  # 20 min
            })
        
        # Adjust for huge files (> 50 MB)
        elif file_size_mb > FileSizeConfig.LARGE_FILE_THRESHOLD:
            config.update({
                "enable_auto_schema": True,  # Keep it, but use sample
                "enable_profiles": False,  # Skip, very slow
                "schema_sample_size": 5000,  # Aggressive sampling
                "profile_sample_size": None,  # Skip profiling entirely
                "result_preview_rows": 1000,  # Minimal preview
                "use_knn_imputation": False,  # Skip
                "remove_outliers": False,  # Skip
                "enable_drift_detection": False,  # Skip
                "enable_vectorization": False,  # Skip
                "processing_timeout_seconds": 1800,  # 30 min
            })
        
        # Apply user overrides
        if user_config:
            config.update(user_config)
        
        return config
    
    @staticmethod
    def estimate_file_size_mb(df) -> float:
        """Estimate DataFrame memory usage in MB"""
        if df is None or df.empty:
            return 0.0
        total_bytes = sum(df[col].memory_usage(deep=True) for col in df.columns)
        return total_bytes / (1024 ** 2)


# ============================================================================
# DEFAULT CONFIGURATIONS FOR COMMON SCENARIOS
# ============================================================================

FAST_MODE_CONFIG = {
    """
    Ultra-fast mode for production constraints.
    Skips profiling, drift detection, vectorization, outlier removal.
    """
    "enable_auto_schema": True,
    "remove_duplicates": True,
    "remove_outliers": False,
    "enable_drift_detection": False,
    "enable_profiles": False,
    "enable_vectorization": False,
    "handle_missing_data": True,
    "missing_strategy": "preserve",
    "use_knn_imputation": False,
    "result_preview_rows": 1000,
    "processing_timeout_seconds": 600,
}

BALANCED_MODE_CONFIG = {
    """
    Default balanced mode. Good quality, reasonable speed.
    """
    "enable_auto_schema": True,
    "remove_duplicates": True,
    "remove_outliers": False,
    "enable_drift_detection": True,
    "enable_profiles": False,
    "enable_vectorization": False,
    "handle_missing_data": True,
    "missing_strategy": "preserve",
    "use_knn_imputation": False,
    "result_preview_rows": 2000,
    "processing_timeout_seconds": 900,
}

QUALITY_MODE_CONFIG = {
    """
    Quality-first mode. Takes longer but comprehensive analysis.
    """
    "enable_auto_schema": True,
    "remove_duplicates": True,
    "remove_outliers": True,
    "enable_drift_detection": True,
    "enable_profiles": True,
    "enable_vectorization": False,
    "handle_missing_data": True,
    "missing_strategy": "preserve",
    "use_knn_imputation": False,
    "result_preview_rows": 5000,
    "processing_timeout_seconds": 1200,
}


def get_optimized_config(
    file_size_mb: float,
    mode: str = "auto",
    user_overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get processing configuration.
    
    Args:
        file_size_mb: File size in MB
        mode: "auto" (size-aware), "fast", "balanced", "quality"
        user_overrides: User config overrides
    
    Returns:
        Processing configuration dict
    """
    if mode == "fast":
        config = FAST_MODE_CONFIG.copy()
    elif mode == "quality":
        config = QUALITY_MODE_CONFIG.copy()
    elif mode == "balanced":
        config = BALANCED_MODE_CONFIG.copy()
    else:  # "auto"
        config = FileSizeConfig.get_config_for_size(file_size_mb)
    
    if user_overrides:
        config.update(user_overrides)
    
    return config
