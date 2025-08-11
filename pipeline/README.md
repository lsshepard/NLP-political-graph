# Pipeline Package

This package implements a modular pipeline for extracting political standpoints and arguments using OpenAI assistants with **parallel processing capabilities**.

## Structure

```
pipeline/
├── __init__.py          # Package initialization and exports
├── config.py            # Configuration management
├── openai_client.py     # OpenAI API client
├── data_processor.py    # Data parsing and transformation
├── graph_builder.py     # Graph structure management (thread-safe)
├── extractors.py        # Standpoint and argument extraction
├── output_manager.py    # File output operations
├── pipeline.py          # Main pipeline orchestrator with parallel processing
├── parallel_utils.py    # Advanced parallel processing utilities
├── run.py              # Entry point for execution
└── README.md           # This file
```

## Modules

### `config.py`

- `PipelineConfig`: Centralizes all configuration settings including assistant IDs, topics, limits, and **parallel processing options**

### `openai_client.py`

- `OpenAIClient`: Handles all OpenAI API interactions with proper error handling and timeouts

### `data_processor.py`

- `DataProcessor`: Static methods for parsing JSON responses from assistants

### `graph_builder.py`

- `GraphBuilder`: Manages the construction of nodes and edges in the graph structure with **thread-safe operations**

### `extractors.py`

- `StandpointExtractor`: Extracts standpoints for given topics
- `ArgumentExtractor`: Recursively extracts supporting arguments

### `output_manager.py`

- `OutputManager`: Handles saving graph data to JSON files with timestamps

### `pipeline.py`

- `Pipeline`: Main orchestrator that coordinates all components with **parallel execution**

### `parallel_utils.py` ⭐ **NEW**

- `BatchProcessor`: Process items in batches to manage memory and API rate limits
- `ProgressTracker`: Track progress of parallel operations with ETA and rate information
- `parallel_map`: Parallel map function with progress tracking
- `rate_limit`: Decorator to rate limit function calls

## Parallel Processing Features

### 🚀 **Performance Benefits**

- **Concurrent topic processing**: Multiple topics processed simultaneously
- **Parallel standpoint extraction**: Standpoints for each topic extracted concurrently
- **Thread-safe graph building**: Safe concurrent access to shared data structures
- **Configurable worker count**: Adjust parallelism based on your system capabilities

### ⚙️ **Configuration Options**

```python
from pipeline import PipelineConfig

config = PipelineConfig()
config.max_workers = 8              # Number of concurrent threads
config.enable_parallel = True       # Enable/disable parallel processing
config.batch_size = 20              # Process standpoints in batches
```

### 📊 **Progress Tracking**

- Real-time progress updates with timing information
- ETA calculations and processing rates
- Detailed statistics on completion
- Memory-efficient batch processing

## Usage

### Running the Pipeline

```bash
# From the pipeline directory
python run.py

# Or from the parent directory
python -m pipeline.run
```

### Using Parallel Processing

```python
from pipeline import Pipeline, BatchProcessor, parallel_map

# Create pipeline with custom parallelism
pipeline = Pipeline(max_workers=8)
pipeline.run()

# Use batch processing for large datasets
batch_processor = BatchProcessor(batch_size=50, max_workers=4)
results = batch_processor.process_batches(items, process_function)

# Use parallel map with progress tracking
results = parallel_map(process_function, items, max_workers=6)
```

### Using Individual Components

```python
from pipeline import Pipeline, PipelineConfig, GraphBuilder

# Create a custom configuration
config = PipelineConfig()
config.topics = ['Custom Topic']
config.max_workers = 12  # High parallelism for fast processing

# Use individual components
graph_builder = GraphBuilder()
# ... use as needed
```

## Performance Tuning

### 🎯 **Optimal Settings**

- **Small datasets** (< 100 items): 2-4 workers
- **Medium datasets** (100-1000 items): 4-8 workers
- **Large datasets** (> 1000 items): 8-16 workers
- **API rate limited**: Use `rate_limit` decorator and lower worker counts

### 🔧 **Memory Management**

- Use `batch_size` to control memory usage
- Monitor progress with `ProgressTracker`
- Adjust `max_workers` based on system resources

## Benefits of This Structure

1. **Modularity**: Each component has a single responsibility
2. **Testability**: Individual components can be tested in isolation
3. **Maintainability**: Easy to modify or extend specific functionality
4. **Reusability**: Components can be used independently
5. **Readability**: Clear separation of concerns makes code easier to understand
6. **Extensibility**: Simple to add new extractors, processors, or output formats
7. **Performance**: **Parallel processing for significant speed improvements**
8. **Scalability**: **Handles large datasets efficiently with batch processing**

## Dependencies

- `openai`: OpenAI Python client
- `python-dotenv`: Environment variable management
- `uuid`: UUID generation (built-in)
- `json`: JSON processing (built-in)
- `datetime`: Date/time operations (built-in)
- `concurrent.futures`: Parallel processing (built-in)
- `threading`: Thread safety (built-in)
