"""Utility module for advanced parallel processing features"""

import time
import concurrent.futures
from typing import List, Callable, Any, Dict, Iterator
from functools import wraps


def rate_limit(calls_per_second: int):
    """Decorator to rate limit function calls"""
    def decorator(func):
        min_interval = 1.0 / calls_per_second
        last_call_time = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            # Use function name as key for rate limiting
            func_key = func.__name__
            
            if func_key in last_call_time:
                time_since_last = current_time - last_call_time[func_key]
                if time_since_last < min_interval:
                    time.sleep(min_interval - time_since_last)
            
            last_call_time[func_key] = time.time()
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


class BatchProcessor:
    """Process items in batches to manage memory and API rate limits"""
    
    def __init__(self, batch_size: int = 10, max_workers: int = 4):
        self.batch_size = batch_size
        self.max_workers = max_workers
    
    def process_batches(self, items: List[Any], process_func: Callable, 
                       batch_size: int = None) -> List[Any]:
        """Process items in batches using parallel execution"""
        batch_size = batch_size or self.batch_size
        results = []
        
        # Split items into batches
        batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit batch processing tasks
            future_to_batch = {
                executor.submit(self._process_batch, batch, process_func): i 
                for i, batch in enumerate(batches)
            }
            
            # Collect results in order
            batch_results = [None] * len(batches)
            for future in concurrent.futures.as_completed(future_to_batch):
                batch_idx = future_to_batch[future]
                try:
                    batch_results[batch_idx] = future.result()
                except Exception as exc:
                    print(f"Batch {batch_idx} failed: {exc}")
                    batch_results[batch_idx] = []
            
            # Flatten results
            for batch_result in batch_results:
                if batch_result:
                    results.extend(batch_result)
        
        return results
    
    def _process_batch(self, batch: List[Any], process_func: Callable) -> List[Any]:
        """Process a single batch of items"""
        results = []
        for item in batch:
            try:
                result = process_func(item)
                if result:
                    results.append(result)
            except Exception as exc:
                print(f"Item processing failed: {exc}")
        return results


class ProgressTracker:
    """Track progress of parallel operations"""
    
    def __init__(self, total_items: int, description: str = "Processing"):
        self.total_items = total_items
        self.description = description
        self.completed = 0
        self.start_time = time.time()
        self._lock = concurrent.futures.threading.Lock()
    
    def update(self, count: int = 1):
        """Update progress count"""
        with self._lock:
            self.completed += count
            self._print_progress()
    
    def _print_progress(self):
        """Print current progress"""
        elapsed = time.time() - self.start_time
        if self.completed > 0:
            rate = self.completed / elapsed
            eta = (self.total_items - self.completed) / rate if rate > 0 else 0
            print(f"{self.description}: {self.completed}/{self.total_items} "
                  f"({self.completed/self.total_items*100:.1f}%) "
                  f"[{elapsed:.1f}s, {rate:.2f} items/s, ETA: {eta:.1f}s]")
        else:
            print(f"{self.description}: {self.completed}/{self.total_items} "
                  f"({self.completed/self.total_items*100:.1f}%) [{elapsed:.1f}s]")


def parallel_map(func: Callable, items: List[Any], max_workers: int = 4, 
                show_progress: bool = True) -> List[Any]:
    """Parallel map function with progress tracking"""
    if show_progress:
        tracker = ProgressTracker(len(items), f"Executing {func.__name__}")
    
    results = [None] * len(items)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {
            executor.submit(func, item): i 
            for i, item in enumerate(items)
        }
        
        for future in concurrent.futures.as_completed(future_to_index):
            index = future_to_index[future]
            try:
                results[index] = future.result()
                if show_progress:
                    tracker.update(1)
            except Exception as exc:
                print(f"Item {index} failed: {exc}")
                results[index] = None
    
    return results
