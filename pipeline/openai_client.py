"""OpenAI client module for handling API interactions"""

from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI
import time
from typing import Optional


class OpenAIClient:
    """Handles OpenAI API interactions"""
    
    def __init__(self):
        load_dotenv()
        self.client = OpenAI()
    
    def query_assistant(self, assistant_id: str, prompt: str, timeout_seconds: int = 300) -> Optional[str]:
        """Query an assistant and return the response"""
        start_time = datetime.now()
        
        # Create a thread
        thread = self.client.beta.threads.create()
        
        # Add message to thread
        self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt
        )
        
        # Run the assistant
        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )
        
        # Wait for completion with timeout
        while run.status in ['queued', 'in_progress']:
            if datetime.now() - start_time > timedelta(seconds=timeout_seconds):
                return f"Error: Timeout after {timeout_seconds} seconds"
            
            time.sleep(1)
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
        
        if run.status == 'completed':
            # Get messages
            messages = self.client.beta.threads.messages.list(thread_id=thread.id)
            response_text = messages.data[0].content[0].text.value
            print(response_text)
            
            # Extract JSON from markdown code blocks if present
            if response_text.startswith('```json'):
                # Remove the opening and closing markdown code blocks
                json_content = response_text.replace('```json\n', '').replace('\n```', '')
                return json_content
            elif response_text.startswith('```'):
                # Handle case where it's just ``` without json specifier
                json_content = response_text.replace('```\n', '').replace('\n```', '')
                return json_content
            else:
                return response_text
        elif run.status == 'failed':
            return f"Error: Run failed - {run.last_error}"
        elif run.status == 'cancelled':
            return f"Error: Run was cancelled"
        elif run.status == 'expired':
            return f"Error: Run expired"
        else:
            return f"Error: Run status is {run.status}"
