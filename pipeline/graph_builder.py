"""Graph builder module for constructing and managing graph structures"""

import uuid
import threading
from typing import List, Dict, Any


class GraphBuilder:
    """Builds the graph structure with nodes and edges in a thread-safe manner"""
    
    def __init__(self):
        self.nodes: List[Dict[str, Any]] = []
        self.edges: List[Dict[str, Any]] = []
        self._lock = threading.Lock()  # Thread safety lock
    
    def add_topic(self, topic: str) -> str:
        """Add a topic node and return its ID"""
        topic_id = self._generate_id()
        with self._lock:
            self.nodes.append({'id': topic_id, 'name': topic, 'type': 'topic'})
        return topic_id
    
    def add_standpoint(self, standpoint: str, topic_id: str) -> str:
        """Add a standpoint node and connect it to topic"""
        standpoint_id = self._generate_id()
        with self._lock:
            self.nodes.append({'id': standpoint_id, 'name': standpoint, 'type': 'standpoint'})
            # Fix: Standpoint should point TO topic (standpoint supports/explains the topic)
            self.edges.append({'source': standpoint_id, 'target': topic_id, 'type': 'standpoint_to_topic'})
        return standpoint_id
    
    def add_supporting_argument(self, argument: str, type: str,parent_id: str) -> str:
        """Add a supporting argument node and connect it to parent"""
        argument_id = self._generate_id()
        with self._lock:
            self.nodes.append({'id': argument_id, 'name': argument, 'type': type})
            # Fix: Supporting argument should point TO the node it supports
            self.edges.append({'source': argument_id, 'target': parent_id, 'type': 'supports'})
        return argument_id
    
    def add_existing_supporting_argument(self, argument_id: str, parent_id: str) -> str:
        """Add a supporting argument node and connect it to parent"""
        with self._lock:
            # Fix: Supporting argument should point TO the node it supports
            self.edges.append({'source': argument_id, 'target': parent_id, 'type': 'supports'})
        return argument_id
    
    def _generate_id(self) -> str:
        """Generate a unique UUID"""
        return str(uuid.uuid4())
    
    def get_graph_data(self) -> Dict[str, Any]:
        """Get the complete graph data"""
        with self._lock:
            return {'nodes': self.nodes.copy(), 'edges': self.edges.copy()}
        
    def get_existing_arguments(self, parent_argument_id: str):
        
        # Find all ancestors of the parent_argument_id node
        # With corrected edge direction: supporting arguments point TO the nodes they support
        ancestors = set()
        to_process = [parent_argument_id]
        
        while to_process:
            current_id = to_process.pop(0)
            if current_id not in ancestors:
                ancestors.add(current_id)
                # Find all nodes that have edges pointing TO current_id (supporting arguments)
                for edge in self.edges:
                    if edge['source'] == current_id:
                        to_process.append(edge['target'])
        
        # Return all nodes except the ancestors
        return [node for node in self.nodes if node['id'] not in ancestors]
    
    def aggregate_nodes(self, merged_nodes_data: List[Dict[str, Any]]) -> None:
        """Aggregate nodes based on LLM recommendations"""
        with self._lock:
            for merge_info in merged_nodes_data:
                original_ids = merge_info.get('original_ids', [])
                new_argument = merge_info.get('new_argument', '')
                node_type = merge_info.get('node_type', 'supporting_argument')  # Default fallback
                
                if len(original_ids) < 2 or not new_argument:
                    continue
                
                # Create new merged node with specified type
                merged_node_id = self._generate_id()
                merged_node = {
                    'id': merged_node_id,
                    'name': new_argument,
                    'type': node_type
                }
                self.nodes.append(merged_node)
                
                # Find all edges that reference the original nodes
                edges_to_update = []
                edges_to_remove = []
                
                for edge in self.edges:
                    if edge['source'] in original_ids:
                        # Update source to point to merged node (supporting argument relationship)
                        new_edge = edge.copy()
                        new_edge['source'] = merged_node_id
                        edges_to_update.append(new_edge)
                        edges_to_remove.append(edge)
                    elif edge['target'] in original_ids:
                        # Update target to point to merged node (supported node relationship)
                        new_edge = edge.copy()
                        new_edge['target'] = merged_node_id
                        edges_to_update.append(new_edge)
                        edges_to_remove.append(edge)
                
                # Remove old edges and add new ones
                for edge in edges_to_remove:
                    self.edges.remove(edge)
                self.edges.extend(edges_to_update)
                
                # Remove original nodes
                self.nodes = [node for node in self.nodes if node['id'] not in original_ids]
    
    def get_all_nodes_for_aggregation(self) -> List[Dict[str, Any]]:
        """Get all nodes formatted for the aggregation assistant"""
        with self._lock:
            # Return only supporting argument nodes (excluding topics and standpoints)
            # Include argument, fact, and value types
            return [node for node in self.nodes if node['type'] in ['argument', 'fact', 'value']]
    
    def get_stats(self) -> Dict[str, int]:
        """Get current graph statistics"""
        with self._lock:
            return {
                'total_nodes': len(self.nodes),
                'total_edges': len(self.edges),
                'topics': len([n for n in self.nodes if n['type'] == 'topic']),
                'standpoints': len([n for n in self.nodes if n['type'] == 'standpoint']),
                'arguments': len([n for n in self.nodes if n['type'] == 'supporting_argument'])
            }
