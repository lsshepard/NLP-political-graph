"""Main pipeline module that orchestrates the complete workflow"""

import concurrent.futures
import json
import time
from typing import List, Tuple, Dict, Any
from config import PipelineConfig
from openai_client import OpenAIClient
from graph_builder import GraphBuilder
from extractors import StandpointExtractor, ArgumentExtractor
from output_manager import OutputManager


class Pipeline:
    """Main pipeline orchestrator with parallel processing"""
    
    def __init__(self, max_workers: int = None):
        self.config = PipelineConfig()
        self.max_workers = max_workers or min(32, self.config.max_workers)
        self.openai_client = OpenAIClient()
        self.graph_builder = GraphBuilder()
        self.standpoint_extractor = StandpointExtractor(self.openai_client, self.config)
        self.argument_extractor = ArgumentExtractor(self.openai_client, self.config)
        self.output_manager = OutputManager()
        self.start_time = None
    
    def run(self):
        """Execute the complete pipeline with parallel processing"""
        if not self.config.enable_parallel:
            return self._run_sequential()
        
        self.start_time = time.time()
        print(f"Starting parallel pipeline with {self.max_workers} workers...")
        
        # Process topics in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all topic processing tasks
            future_to_topic = {
                executor.submit(self._process_topic, topic): topic 
                for topic in self.config.topics
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_topic):
                topic = future_to_topic[future]
                try:
                    result = future.result()
                    self._print_progress(f"Completed topic: {topic}")
                except Exception as exc:
                    print(f"Topic {topic} generated an exception: {exc}")
        
        self._print_final_results()
        
        # Save output
        graph_data = self.graph_builder.get_graph_data()
        self.output_manager.save_graph_data(graph_data)
        
        # Run node aggregation step
        self._run_node_aggregation()
    
    def _run_sequential(self):
        """Run the pipeline sequentially (fallback)"""
        print("Running pipeline sequentially...")
        self.start_time = time.time()
        
        for topic in self.config.topics:
            self._process_topic(topic)
            self._print_progress(f"Completed topic: {topic}")
        
        self._print_final_results()
        
        # Save output
        graph_data = self.graph_builder.get_graph_data()
        self.output_manager.save_graph_data(graph_data)
        
        # Run node aggregation step
        self._run_node_aggregation()
    
    def _process_topic(self, topic: str):
        """Process a single topic with its standpoints and arguments"""
        topic_id = self.graph_builder.add_topic(topic)
        standpoints = self.standpoint_extractor.extract_standpoints(topic)
        
        if not self.config.enable_parallel:
            # Sequential processing
            for standpoint in standpoints:
                self._process_standpoint(standpoint, topic_id)
            return
        
        # Process standpoints in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all standpoint processing tasks
            future_to_standpoint = {
                executor.submit(self._process_standpoint, standpoint, topic_id): standpoint 
                for standpoint in standpoints
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_standpoint):
                standpoint = future_to_standpoint[future]
                try:
                    result = future.result()
                    self._print_progress(f"Completed standpoint: {standpoint[:50]}...")
                except Exception as exc:
                    print(f"Standpoint {standpoint[:50]}... generated an exception: {exc}")
    
    def _process_standpoint(self, standpoint: str, topic_id: str):
        """Process a single standpoint with its arguments"""
        standpoint_id = self.graph_builder.add_standpoint(standpoint, topic_id)
        self.argument_extractor.extract_arguments(standpoint, standpoint_id, self.graph_builder)
        return standpoint_id
    
    def _print_progress(self, message: str):
        """Print progress with timing information"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            stats = self.graph_builder.get_stats()
            print(f"[{elapsed:.1f}s] {message} | Nodes: {stats['total_nodes']}, Edges: {stats['total_edges']}")
        else:
            print(message)
    
    def _run_node_aggregation(self):
        """Run the node aggregation step using the LLM assistant"""
        print("\n=== Starting Node Aggregation ===")
        
        # Get all nodes for aggregation
        nodes_for_aggregation = self.graph_builder.get_all_nodes_for_aggregation()
        
        # if len(nodes_for_aggregation) < 2:
        #     print("Not enough nodes to aggregate. Skipping aggregation step.")
        #     return
        
        print(f"Found {len(nodes_for_aggregation)} nodes for potential aggregation...")
        
        # Prepare prompt for the assistant
        prompt = self._create_aggregation_prompt(nodes_for_aggregation)
        
        # Query the assistant
        try:
            response = self.openai_client.query_assistant(
                assistant_id=self.config.assistant_ids['node_aggregator'],
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
                        self.graph_builder.aggregate_nodes(merged_nodes)
                        
                        # Get updated stats
                        stats = self.graph_builder.get_stats()
                        print(f"After aggregation: {stats['total_nodes']} nodes, {stats['total_edges']} edges")
                        
                        # Save the updated graph
                        updated_graph_data = self.graph_builder.get_graph_data()
                        self.output_manager.save_graph_data(updated_graph_data)
                        print("Updated graph saved after aggregation.")
                    else:
                        print("No node merging suggestions from LLM.")
                        
                except json.JSONDecodeError as e:
                    print(f"Failed to parse LLM response as JSON: {e}")
                    print(f"Raw response: {response}")
            else:
                print(f"LLM assistant error: {response}")
                
        except Exception as e:
            print(f"Error during node aggregation: {e}")
    
    def _create_aggregation_prompt(self, nodes: List[Dict[str, Any]]) -> str:
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
    
    def _print_final_results(self):
        """Print final pipeline results"""
        if self.start_time:
            total_time = time.time() - self.start_time
            stats = self.graph_builder.get_stats()
            print(f"\n=== Pipeline Complete ===")
            print(f"Total execution time: {total_time:.2f} seconds")
            print(f"Topics processed: {stats['topics']}")
            print(f"Standpoints extracted: {stats['standpoints']}")
            print(f"Arguments extracted: {stats['arguments']}")
            print(f"Total nodes: {stats['total_nodes']}")
            print(f"Total edges: {stats['total_edges']}")
            print(f"Average time per node: {total_time / max(stats['total_nodes'], 1):.3f} seconds")
        else:
            stats = self.graph_builder.get_stats()
            print(f"Total nodes: {stats['total_nodes']}")
            print(f"Total edges: {stats['total_edges']}")


def main():
    """Main entry point"""
    pipeline = Pipeline()
    pipeline.run()


if __name__ == "__main__":
    main()