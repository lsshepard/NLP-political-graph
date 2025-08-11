"""Data processing module for parsing and transforming responses"""

import json
from typing import List, Optional


class DataProcessor:
    """Handles data processing and transformation"""
    
    @staticmethod
    def parse_standpoints_response(response: str) -> List[str]:
        """Parse standpoints from assistant response"""
        if response is None or response.startswith("Error:"):
            print(f"Assistant query failed: {response}")
            return []

        try:
            parsed_data = json.loads(response)
            return parsed_data['standpoints']
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Raw response: {response}")
            return []
    
    @staticmethod
    def parse_supporting_arguments_response(response: str) -> Optional[List[str]]:
        """Parse supporting arguments from assistant response"""
        if response is None or response.startswith("Error:"):
            print(f"Assistant query failed: {response}")
            return None

        try:
            parsed_data = json.loads(response)
            return parsed_data['new_supporting_arguments'], parsed_data['existing_supporting_arguments']
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Raw response: {response}")
            return None
