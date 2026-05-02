# Hardware & GPU Management

SME Bridge is designed to run multimodal LLM inference locally. This document outlines the hardware requirements and the strategies implemented to manage resource usage.

## Minimum Requirements

- **GPU:** NVIDIA GPU with at least 8GB VRAM (recommended for Gemma 2B or similar).
- **CPU:** Multi-core processor (x86_64 or ARM64).
- **RAM:** 16GB System RAM.
- **Storage:** ~10GB for model weights and dependencies.

## GPU Resource Management Strategies

To ensure stability on consumer hardware, the processing pipeline implements several hardening strategies:

1. **Sequential Page Processing:** Multi-page PDFs are processed one page at a time. This keeps the memory footprint of the image and the LLM context within manageable limits.
2. **Image Normalization:**
   - **Downscaling:** Images are resized to a maximum dimension of 1024px while preserving aspect ratio.
   - **Grayscale:** Images are converted to grayscale to reduce payload size.
3. **GPU Cache Clearing:** After every page is processed, the system explicitly calls `torch.cuda.empty_cache()` (if available) to release unused VRAM and prevent fragmentation.
4. **No-Op Fallbacks:** The GPU management logic is designed to fail gracefully. If PyTorch or CUDA is not detected, the system automatically falls back to CPU or no-op management without crashing.

## Monitoring

You can monitor GPU usage during bill processing using:
```bash
nvidia-smi -l 1
```

## Stress Testing

To verify hardware stability, you can upload a "dense" PDF (e.g., 15+ pages of complex utility bills) and monitor the worker logs for any OOM or timeout errors.
