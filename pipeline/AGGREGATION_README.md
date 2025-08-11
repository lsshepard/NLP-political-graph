# Node Aggregation Pipeline

This document explains how to use the new node aggregation functionality in the pipeline.

## Overview

The node aggregation step is a new addition to the pipeline that runs after all other steps are complete. It uses an LLM assistant to identify and merge similar or redundant nodes in the graph, creating a more concise and coherent representation.

## How It Works

1. **Analysis**: The LLM assistant analyzes all supporting argument nodes in the graph
2. **Recommendations**: It suggests which nodes should be merged together based on semantic similarity
3. **Execution**: The pipeline merges the recommended nodes, updates all relevant edges, and removes the original nodes
4. **Output**: A new graph file is saved with the aggregated structure

## LLM Response Format

The LLM assistant returns recommendations in this JSON format:

```json
{
  "merged_nodes": [
    {
      "original_ids": ["id1", "id4"],
      "new_argument": "Ny sammenslått formulering",
      "node_type": "argument"
    }
  ]
}
```

The `node_type` field specifies the type of the merged node and can be:

- `"argument"` - for logical arguments and reasoning
- `"fact"` - for factual statements and evidence
- `"value"` - for value-based claims and principles

## Usage

### Option 1: Run as part of the full pipeline

The aggregation step automatically runs after the main pipeline completes:

```bash
cd pipeline
python pipeline.py
```

### Option 2: Run aggregation only on existing output

Use the standalone script to run aggregation on an existing output file:

```bash
cd pipeline

# Interactive mode - choose from available files
python run_aggregation_only.py

# Or specify a file directly
python run_aggregation_only.py output/current_2025-08-10_18-36-13.json
```

## Configuration

The node aggregator assistant ID is configured in `config.py`:

```python
self.assistant_ids = {
    'standpoints': 'asst_xAQSvhhA3bZUPzYWBSUbv8hk',
    'supporting_arguments': 'asst_mcGhHVlmMMnlpjMt6ReFRjTj',
    'node_aggregator': 'asst_H8KYznUzdaBPsujS0qjsdO2S'
}
```

## Output Files

- **Original pipeline output**: Saved before aggregation
- **Aggregated output**: New file with timestamp, created after aggregation
- **File naming**: `current_YYYY-MM-DD_HH-MM-SS.json`

## Error Handling

The aggregation step includes comprehensive error handling:

- LLM API failures
- JSON parsing errors
- File I/O issues
- Invalid node references

If aggregation fails, the original graph remains unchanged.

## Limitations

- Only supporting argument nodes are considered for aggregation
- Topics and standpoints are preserved
- Edge relationships are maintained during merging
- The LLM's recommendations determine what gets merged

## Edge Direction Fix

**Important**: The pipeline has been updated to fix incorrect edge directions and ensure consistency throughout. Previously, edges were created with inconsistent directions, which created invalid graph structures.

**Current correct and consistent structure**:

- **Topics** are at the top level
- **Standpoints** point TO topics (`standpoint → topic`) - they support/explain the topic
- **Arguments/Facts/Values** point TO the nodes they support (`supporting_node → supported_node`)

This ensures the graph follows the logical hierarchy: `topic ← standpoint ← argument/fact/value`

**Edge Types**:

- `standpoint_to_topic`: Standpoint supports the topic
- `supports`: Supporting argument/fact/value supports another node (argument, standpoint, or topic)

## Testing

To test the aggregation functionality:

1. Run the full pipeline to generate a graph
2. Use `run_aggregation_only.py` to test aggregation on the output
3. Compare the before/after node and edge counts
4. Verify that the merged nodes maintain logical connections
