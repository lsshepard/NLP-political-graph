#!/usr/bin/env python3
"""Standalone script to run only the node aggregation step on existing output files"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import PipelineConfig
from openai_client import OpenAIClient
from graph_builder import GraphBuilder
from output_manager import OutputManager


def load_existing_graph(file_path: str) -> Dict[str, Any]:
    """Load graph data from an existing output file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: File {file_path} is not valid JSON")
        sys.exit(1)


def populate_graph_builder(graph_builder: GraphBuilder, graph_data: Dict[str, Any]) -> None:
    """Populate the graph builder with existing graph data"""
    # Clear any existing data
    with graph_builder._lock:
        graph_builder.nodes.clear()
        graph_builder.edges.clear()
        
        # Add nodes
        for node in graph_data.get('nodes', []):
            graph_builder.nodes.append(node)
        
        # Add edges
        for edge in graph_data.get('edges', []):
            graph_builder.edges.append(edge)


def run_aggregation_on_file(input_file: str, output_dir: str = 'output') -> None:
    """Run aggregation on a specific input file and save to new output"""
    print(f"=== Running Node Aggregation on {input_file} ===")
    
    # Load the existing graph data
    graph_data = load_existing_graph(input_file)
    print(f"Loaded graph with {len(graph_data.get('nodes', []))} nodes and {len(graph_data.get('edges', []))} edges")
    
    # Initialize components
    config = PipelineConfig()
    openai_client = OpenAIClient()
    graph_builder = GraphBuilder()
    output_manager = OutputManager()
    
    # Populate graph builder with existing data
    populate_graph_builder(graph_builder, graph_data)
    
    # Get all nodes for aggregation
    nodes_for_aggregation = graph_builder.get_all_nodes_for_aggregation()
    print(f"Found {len(nodes_for_aggregation)} nodes for potential aggregation...")
    
    if len(nodes_for_aggregation) == 0:
        print("No supporting argument nodes found. Nothing to aggregate.")
        return
    
    # Prepare prompt for the assistant
    prompt = create_aggregation_prompt(nodes_for_aggregation)
    
    # Query the assistant
    try:
        print("Querying LLM assistant for node aggregation suggestions...")
        response = openai_client.query_assistant(
            assistant_id=config.assistant_ids['node_aggregator'],
            prompt=prompt
        )
        
        if response and not response.startswith('Error:'):
            # Parse the response
            try:
                aggregation_data = json.loads(response)
                merged_nodes = aggregation_data.get('merged_nodes', [])
                
                if merged_nodes:
                    print(f"LLM suggested merging {len(merged_nodes)} groups of nodes...")
                    
                    # Apply the aggregation
                    graph_builder.aggregate_nodes(merged_nodes)
                    
                    # Get updated stats
                    stats = graph_builder.get_stats()
                    print(f"After aggregation: {stats['total_nodes']} nodes, {stats['total_edges']} edges")
                    
                    # Save the updated graph
                    updated_graph_data = graph_builder.get_graph_data()
                    output_manager.save_graph_data(updated_graph_data, output_dir)
                    print(f"Updated graph saved to {output_dir}/")
                else:
                    print("No node merging suggestions from LLM.")
                    
            except json.JSONDecodeError as e:
                print(f"Failed to parse LLM response as JSON: {e}")
                print(f"Raw response: {response}")
        else:
            print(f"LLM assistant error: {response}")
            
    except Exception as e:
        print(f"Error during node aggregation: {e}")


def create_aggregation_prompt(nodes: List[Dict[str, Any]]) -> str:
    """Create a prompt for the node aggregation assistant"""
    prompt = """You are a node aggregation assistant. Your task is to analyze the following nodes and identify which ones should be merged together based on semantic similarity and logical coherence.

The nodes represent supporting arguments in a political discourse graph. Your goal is to consolidate similar or redundant arguments while maintaining the logical structure.

Please analyze the following nodes and return a JSON response in this exact format:
{
  "merged_nodes": [
    {
      "original_ids": ["id1", "id4"],
      "new_argument": "Ny sammenslått formulering",
      "node_type": "argument"
    }
  ]
}

Guidelines:
- Only merge nodes that are semantically similar or redundant
- Each merged group should have at least 2 nodes
- Provide a clear, concise new argument text that captures the essence of the merged nodes
- Use the exact node IDs provided
- Specify the node_type as "argument", "fact", or "value" based on the nature of the merged content
- If no nodes should be merged, return an empty merged_nodes array

Nodes to analyze:
"""
    
    for node in nodes:
        prompt += f"- ID: {node['id']}, Content: {node['name']}\n"
    
    prompt += "\nPlease provide your response in the specified JSON format."
    return prompt


def list_available_files(output_dir: str = 'output') -> List[str]:
    """List all available output files for selection"""
    output_path = Path(output_dir)
    if not output_path.exists():
        print(f"Output directory {output_dir} does not exist")
        return []
    
    json_files = list(output_path.glob('current_*.json'))
    if not json_files:
        print(f"No output files found in {output_dir}")
        return []
    
    print("Available output files:")
    for i, file_path in enumerate(sorted(json_files, reverse=True)):  # Most recent first
        print(f"  {i+1}. {file_path.name}")
    
    return [str(f) for f in json_files]


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # Use command line argument as input file
        input_file = sys.argv[1]
        if not os.path.exists(input_file):
            print(f"Error: File {input_file} not found")
            sys.exit(1)
    else:
        # Interactive mode - list available files and let user choose
        available_files = list_available_files()
        if not available_files:
            sys.exit(1)
        
        try:
            choice = input(f"\nSelect file number (1-{len(available_files)}) or enter full path: ").strip()
            
            if choice.isdigit():
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(available_files):
                    input_file = available_files[choice_idx]
                else:
                    print("Invalid selection")
                    sys.exit(1)
            else:
                input_file = choice
                if not os.path.exists(input_file):
                    print(f"Error: File {input_file} not found")
                    sys.exit(1)
        except KeyboardInterrupt:
            print("\nOperation cancelled")
            sys.exit(0)
    
    # Run aggregation
    run_aggregation_on_file(input_file)
    print("=== Aggregation Complete ===")


if __name__ == "__main__":
    main()
