"""Configuration module for the pipeline"""


class PipelineConfig:
    """Configuration class for pipeline settings"""
    
    def __init__(self):
        self.assistant_ids = {
            'standpoints': 'asst_xAQSvhhA3bZUPzYWBSUbv8hk',
            'supporting_arguments': 'asst_mcGhHVlmMMnlpjMt6ReFRjTj',
            'node_aggregator': 'asst_H8KYznUzdaBPsujS0qjsdO2S'
        }
        self.topics = ['Formueskatt']
        self.recursion_limit = 3
        self.timeout_seconds = 300
        
        # Parallel processing configuration
        self.max_workers = 4  # Number of concurrent threads
        self.enable_parallel = True  # Enable/disable parallel processing
        self.batch_size = 10  # Process standpoints in batches for memory management
