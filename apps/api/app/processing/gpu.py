import logging

logger = logging.getLogger(__name__)

def clear_gpu_cache() -> None:
    """
    Safely clears the GPU cache if PyTorch and CUDA are available.
    Designed to prevent OOM errors during sequential page processing.
    """
    try:
        # Import torch only inside the function to avoid heavy dependency
        # at the module level for CPU-only environments.
        import torch
        
        if torch.cuda.is_available():
            logger.debug("Clearing CUDA cache...")
            torch.cuda.empty_cache()
        else:
            logger.debug("CUDA not available, skipping cache clear.")
            
    except ImportError:
        # PyTorch not installed
        logger.debug("PyTorch not installed, skipping GPU cache clear.")
    except Exception as e:
        logger.warning(f"Unexpected error clearing GPU cache: {e}")
