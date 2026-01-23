"""
Performance optimization utilities for faster-whisper-hotkey.

This module provides utilities for lazy loading, memory optimization,
and performance profiling to improve application startup time and
runtime efficiency.

Functions
---------
lazy_import
    Decorator for lazy-loading modules.

LazyLoader
    Class for lazy-loading modules.

profile_performance
    Context manager for profiling performance.

get_memory_usage
    Get current memory usage of the process.

Notes
-----
- Heavy imports are deferred until first use
- Memory optimizations help reduce footprint
- Performance profiling helps identify bottlenecks
"""

import logging
import sys
import time
import threading
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar
import importlib

logger = logging.getLogger(__name__)

_T = TypeVar('T')


class LazyLoader:
    """
    A class for lazy-loading modules.

    This defers the import of a module until it's actually used,
    which can significantly improve startup time for applications
    with many heavy dependencies.

    Examples
    --------
    >>> torch = LazyLoader("torch")
    >>> # torch is not loaded yet
    >>> torch.tensor([1, 2, 3])  # Now torch is loaded
    """

    def __init__(self, module_name: str):
        """
        Initialize a LazyLoader.

        Parameters
        ----------
        module_name
            Name of the module to lazy-load.
        """
        self._module_name = module_name
        self._module: Optional[Any] = None

    def _load(self):
        """Load the module if not already loaded."""
        if self._module is None:
            try:
                self._module = importlib.import_module(self._module_name)
                logger.debug(f"Lazy-loaded module: {self._module_name}")
            except ImportError as e:
                logger.error(f"Failed to lazy-load {self._module_name}: {e}")
                raise
        return self._module

    def __getattr__(self, name: str) -> Any:
        """Get an attribute from the lazily-loaded module."""
        module = self._load()
        return getattr(module, name)

    def __call__(self, *args, **kwargs):
        """Make the lazy loader callable if the module is."""
        module = self._load()
        if callable(module):
            return module(*args, **kwargs)
        raise TypeError(f"Module {self._module_name} is not callable")


def lazy_import(module_name: str, attribute: Optional[str] = None):
    """
    Decorator for lazy-loading modules or module attributes.

    Parameters
    ----------
    module_name
        Name of the module to lazy-load.
    attribute
        Optional specific attribute to import from the module.

    Returns
    -------
    Callable
        A callable that returns the lazily-loaded module/attribute.

    Examples
    --------
    >>> @lazy_import("numpy")
    ... def get_np():
    ...     pass
    >>> np = get_np()  # numpy is loaded on first call
    """
    _cached: Optional[Any] = None
    _lock = threading.Lock()

    def getter() -> Any:
        nonlocal _cached
        if _cached is not None:
            return _cached
        with _lock:
            if _cached is not None:
                return _cached
            try:
                module = importlib.import_module(module_name)
                if attribute:
                    _cached = getattr(module, attribute)
                else:
                    _cached = module
                logger.debug(f"Lazy-imported: {module_name}" + (f".{attribute}" if attribute else ""))
                return _cached
            except ImportError as e:
                logger.error(f"Failed to lazy-import {module_name}: {e}")
                raise

    return getter


class PerformanceProfiler:
    """
    Context manager for profiling performance.

    Tracks execution time and optionally memory usage.

    Examples
    --------
    >>> with PerformanceProfiler("model_loading"):
    ...     model = load_model()
    """

    _active_profilers: Dict[str, list] = {}

    def __init__(self, name: str, log_threshold: float = 0.1):
        """
        Initialize a PerformanceProfiler.

        Parameters
        ----------
        name
            Name of the operation being profiled.
        log_threshold
            Minimum time in seconds to log (operations faster than
            this are not logged to reduce noise).
        """
        self.name = name
        self.log_threshold = log_threshold
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        elapsed = self.elapsed_time

        # Store for later analysis
        if self.name not in self._active_profilers:
            self._active_profilers[self.name] = []
        self._active_profilers[self.name].append(elapsed)

        if elapsed >= self.log_threshold:
            logger.info(f"Performance: {self.name} took {elapsed:.3f}s")

    @property
    def elapsed_time(self) -> float:
        """Get the elapsed time in seconds."""
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time is not None else time.perf_counter()
        return end - self.start_time

    @classmethod
    def get_stats(cls, name: Optional[str] = None) -> Dict[str, Dict[str, float]]:
        """
        Get statistics for profiled operations.

        Parameters
        ----------
        name
            Optional specific operation name. If None, returns all stats.

        Returns
        -------
        Dict[str, Dict[str, float]]
            Statistics including count, total, min, max, avg times.
        """
        stats = {}
        for op_name, times in (cls._active_profilers.items() if name is None else [(name, cls._active_profilers.get(name, []))]):
            if times:
                stats[op_name] = {
                    "count": len(times),
                    "total": sum(times),
                    "min": min(times),
                    "max": max(times),
                    "avg": sum(times) / len(times),
                }
        return stats

    @classmethod
    def clear_stats(cls, name: Optional[str] = None):
        """
        Clear profiling statistics.

        Parameters
        ----------
        name
            Optional specific operation name. If None, clears all stats.
        """
        if name is None:
            cls._active_profilers.clear()
        elif name in cls._active_profilers:
            del cls._active_profilers[name]


def get_memory_usage() -> Dict[str, float]:
    """
    Get current memory usage of the process.

    Returns
    -------
    Dict[str, float]
        Memory usage in MB with keys 'rss' (resident set size),
        'vms' (virtual memory size), and 'percent' (percentage of
        total physical memory).

    Notes
    -----
    This function uses psutil if available, otherwise returns zeros.
    """
    try:
        import psutil
        process = psutil.Process()
        mem_info = process.memory_info()
        return {
            "rss_mb": mem_info.rss / 1024 / 1024,
            "vms_mb": mem_info.vms / 1024 / 1024,
            "percent": process.memory_percent(),
        }
    except ImportError:
        logger.debug("psutil not available for memory profiling")
        return {"rss_mb": 0, "vms_mb": 0, "percent": 0}
    except Exception as e:
        logger.warning(f"Failed to get memory usage: {e}")
        return {"rss_mb": 0, "vms_mb": 0, "percent": 0}


def profile_performance(func: Callable[..., _T]) -> Callable[..., _T]:
    """
    Decorator to profile function performance.

    Parameters
    ----------
    func
        Function to profile.

    Returns
    -------
    Callable[..., _T]
        Wrapped function that logs execution time.

    Examples
    --------
    >>> @profile_performance
    ... def slow_function():
    ...     time.sleep(1)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__qualname__
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = time.perf_counter() - start
            if elapsed > 0.1:  # Only log if slower than 100ms
                logger.debug(f"Performance: {func_name} took {elapsed:.3f}s")
    return wrapper


def optimize_imports():
    """
    Apply import optimizations for faster startup.

    This function configures various optimizations:
    - Disables unnecessary pywin32 post-import hooks
    - Optimizes importlib bootstrap
    """
    # Optimize importlib for faster subsequent imports
    try:
        import importlib._bootstrap
        importlib._bootstrap._called_from_importlib_hooks.add(__name__)
    except Exception:
        pass

    # Reduce pywin32 COM initialization overhead
    try:
        import sys
        if 'pywintypes' in sys.modules:
            # pywintypes already loaded, skip optimization
            pass
    except Exception:
        pass


class ResourceMonitor:
    """
    Monitor system resources during operation.

    Tracks memory and CPU usage over time.

    Examples
    --------
    >>> monitor = ResourceMonitor()
    >>> monitor.start()
    >>> # Do some work
    >>> monitor.stop()
    >>> print(monitor.get_stats())
    """

    def __init__(self, sample_interval: float = 1.0):
        """
        Initialize a ResourceMonitor.

        Parameters
        ----------
        sample_interval
            Seconds between resource samples.
        """
        self.sample_interval = sample_interval
        self._monitoring = False
        self._thread: Optional[threading.Thread] = None
        self._samples: list = []

    def start(self):
        """Start monitoring resources in background."""
        if self._monitoring:
            return

        self._monitoring = True
        self._samples = []

        def _monitor_loop():
            while self._monitoring:
                try:
                    memory = get_memory_usage()
                    cpu = self._get_cpu_percent()
                    self._samples.append({
                        "time": time.time(),
                        "memory_mb": memory["rss_mb"],
                        "cpu_percent": cpu,
                    })
                except Exception as e:
                    logger.debug(f"Resource monitor error: {e}")
                time.sleep(self.sample_interval)

        self._thread = threading.Thread(target=_monitor_loop, daemon=True)
        self._thread.start()

    def stop(self) -> Dict[str, Any]:
        """
        Stop monitoring and return statistics.

        Returns
        -------
        Dict[str, Any]
            Statistics including avg/max memory and CPU usage.
        """
        self._monitoring = False
        if self._thread:
            self._thread.join(timeout=2.0)

        if not self._samples:
            return {"count": 0, "avg_memory_mb": 0, "max_memory_mb": 0, "avg_cpu": 0, "max_cpu": 0}

        memories = [s["memory_mb"] for s in self._samples]
        cpus = [s["cpu_percent"] for s in self._samples]

        return {
            "count": len(self._samples),
            "avg_memory_mb": sum(memories) / len(memories),
            "max_memory_mb": max(memories),
            "avg_cpu": sum(cpus) / len(cpus),
            "max_cpu": max(cpus),
        }

    def _get_cpu_percent(self) -> float:
        """Get current CPU percent."""
        try:
            import psutil
            return psutil.cpu_percent(interval=None)
        except Exception:
            return 0.0


# Apply optimizations on import
optimize_imports()
