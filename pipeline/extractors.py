"""Extractors module for extracting standpoints and arguments"""

import prompts
from typing import List
from config import PipelineConfig
from openai_client import OpenAIClient
from data_processor import DataProcessor
from graph_builder import GraphBuilder


class StandpointExtractor:
    """Extracts standpoints for topics"""
    
    def __init__(self, openai_client: OpenAIClient, config: PipelineConfig):
        self.openai_client = openai_client
        self.config = config
        self.data_processor = DataProcessor()
    
    def extract_standpoints(self, topic: str) -> List[str]:
        """Extract standpoints for a given topic"""
        prompt = prompts.GET_STANDPOINTS_PROMPT(topic)
        assistant_id = self.config.assistant_ids['standpoints']
        
        response = self.openai_client.query_assistant(assistant_id, prompt)
        return self.data_processor.parse_standpoints_response(response)


class ArgumentExtractor:
    """Extracts supporting arguments for standpoints"""
    
    def __init__(self, openai_client: OpenAIClient, config: PipelineConfig):
        self.openai_client = openai_client
        self.config = config
        self.data_processor = DataProcessor()
    
    def extract_arguments(self, parent_argument: str, parent_argument_id: str, graph_builder: GraphBuilder, recursion_level: int = 0):
        """Extract supporting arguments recursively"""
        if recursion_level >= self.config.recursion_limit:
            return
        
        prompt = prompts.GET_SUPPORTING_ARGUMENTS_PROMPT(parent_argument, graph_builder.get_existing_arguments(parent_argument_id))
        assistant_id = self.config.assistant_ids['supporting_arguments']
        
        response = self.openai_client.query_assistant(assistant_id, prompt)
        new_supporting_arguments, existing_supporting_arguments = self.data_processor.parse_supporting_arguments_response(response)
        
        if new_supporting_arguments is not None:
            for argument in new_supporting_arguments:
                argument_id = graph_builder.add_supporting_argument(argument['argument'], argument['type'], parent_argument_id)
                if (argument['type'] == 'argument'):
                    self.extract_arguments(argument['argument'], argument_id, graph_builder, recursion_level + 1)
        if existing_supporting_arguments is not None:
            for argument in existing_supporting_arguments:
                argument_id = graph_builder.add_existing_supporting_argument(argument, parent_argument_id)
