"""Output management module for handling file operations"""

import json
from datetime import datetime
from typing import Dict, Any


class OutputManager:
    """Handles output operations"""
    
    @staticmethod
    def save_graph_data(graph_data: Dict[str, Any], output_dir: str = 'output'):
        """Save graph data to JSON file"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f'{output_dir}/current_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump(graph_data, f)
