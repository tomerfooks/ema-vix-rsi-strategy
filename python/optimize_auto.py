"""
Auto-detecting optimizer that chooses the best backend:
- M1/M2/M3 Mac: PyTorch MPS (Metal GPU acceleration)
- NVIDIA GPU: CUDA acceleration
- Intel/AMD CPU: Numba JIT (CPU optimized)

Usage:
    python optimize_auto.py GOOG 1h
"""

import sys
import platform
import subprocess

def detect_hardware():
    """Detect available hardware and return best backend"""
    
    # Check for Apple Silicon
    machine = platform.machine()
    is_apple_silicon = machine == 'arm64'
    
    # Check for NVIDIA GPU (CUDA)
    has_cuda = False
    try:
        from numba import cuda
        has_cuda = cuda.is_available()
    except:
        pass
    
    # Check for PyTorch MPS (Apple Metal)
    has_mps = False
    if is_apple_silicon:
        try:
            import torch
            has_mps = torch.backends.mps.is_available()
        except:
            pass
    
    return {
        'is_apple_silicon': is_apple_silicon,
        'has_cuda': has_cuda,
        'has_mps': has_mps,
        'cpu_brand': subprocess.getoutput('sysctl -n machdep.cpu.brand_string') if sys.platform == 'darwin' else 'Unknown'
    }


def choose_backend(hw_info):
    """Choose the best optimization backend"""
    
    if hw_info['has_cuda']:
        return 'cuda', '🎮 NVIDIA GPU (CUDA)', 'Expected: 200K+ tests/sec'
    elif hw_info['has_mps']:
        return 'mps', '🍎 Apple Silicon GPU (Metal)', 'Expected: 100K-200K tests/sec'
    else:
        return 'cpu', '💻 CPU (Numba JIT)', 'Expected: 25K tests/sec'


def main():
    if len(sys.argv) < 3:
        print("Usage: python optimize_auto.py TICKER INTERVAL")
        print("Example: python optimize_auto.py GOOG 1h")
        sys.exit(1)
    
    ticker = sys.argv[1].upper()
    interval = sys.argv[2]
    
    print("🔍 Auto-detecting hardware...\n")
    
    hw_info = detect_hardware()
    
    print(f"   CPU: {hw_info['cpu_brand']}")
    print(f"   Architecture: {platform.machine()}")
    print(f"   Apple Silicon: {'✅' if hw_info['is_apple_silicon'] else '❌'}")
    print(f"   CUDA Available: {'✅' if hw_info['has_cuda'] else '❌'}")
    print(f"   Metal (MPS) Available: {'✅' if hw_info['has_mps'] else '❌'}")
    
    backend, backend_name, expected_perf = choose_backend(hw_info)
    
    print(f"\n🚀 Selected Backend: {backend_name}")
    print(f"   {expected_perf}\n")
    print("=" * 60)
    
    # Import and run the appropriate optimizer
    if backend == 'cuda':
        print("\n⚠️  CUDA detected - but optimize_gpu.py not fully implemented yet")
        print("   Falling back to CPU optimizer...\n")
        backend = 'cpu'
    
    if backend == 'mps':
        print("\n⚠️  MPS detected - but Metal optimizer not implemented yet")
        print("   Falling back to CPU optimizer...\n")
        backend = 'cpu'
    
    if backend == 'cpu':
        # Use existing Numba optimizer
        import optimize_numba
        print(f"🎯 Running Numba-optimized CPU backend for {ticker} {interval}\n")
        # The script will run with sys.argv already set
        optimize_numba.main()


if __name__ == '__main__':
    main()
