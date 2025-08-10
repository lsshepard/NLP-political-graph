from datetime import datetime, timedelta

from dotenv import load_dotenv
from openai import OpenAI
import prompts
import time
import json

import uuid





load_dotenv()
client = OpenAI()


assistant_ids = {
    'standpoints': 'asst_xAQSvhhA3bZUPzYWBSUbv8hk',
    'supporting_arguments': 'asst_mcGhHVlmMMnlpjMt6ReFRjTj'
}

topics = ['Formueskatt']

RECURSION_LIMIT = 1



def run_pipeline():
    nodes = []
    edges = []
    for topic in topics:
        topicId = get_id()
        nodes.append({'id': topicId, 'name': topic, 'type': 'topic'})
        standpoints = get_standpoints(topic)
        
        for standpoint in standpoints:
            standpointId = get_id()
            nodes.append({'id': standpointId, 'name': standpoint, 'type': 'standpoint'})
            edges.append({'source': standpointId, 'target': topicId, 'type': 'topic_to_standpoint'})

            i = 0
            get_arguments(standpoint, standpointId, nodes, edges, i)

    print(nodes)
    print(edges)

    with open(f'output/current_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.json', 'w') as f:
        json.dump({'nodes': nodes, 'edges': edges}, f)

def get_standpoints(topic):
    """
    Get standpoints for a specific topic using the assistant
    """
    prompt = prompts.GET_STANDPOINTS_PROMPT(topic)
    assistant_id = assistant_ids['standpoints']
    
    response = query_assistant(assistant_id, prompt)
    
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
    

def get_arguments(parentArgument, parentId, nodes, edges, i):
    """
    Get standpoints for a specific topic using the assistant
    """
    if i >= RECURSION_LIMIT:
        return
    
    prompt = prompts.GET_STANDPOINTS_PROMPT(parentArgument)
    assistant_id = assistant_ids['supporting_arguments']
    
    response = query_assistant(assistant_id, prompt)
    
    if response is None or response.startswith("Error:"):
        print(f"Assistant query failed: {response}")
        return None

    try:
        parsed_data = json.loads(response)
        supporting_arguments = parsed_data['supporting_arguments']

        for argument in supporting_arguments:
            argumentId = get_id()
            nodes.append({'id': argumentId, 'name': argument, 'type': 'supporting_argument'})
            edges.append({'source': argumentId, 'target': parentId, 'type': 'supporting_argument'})

            get_arguments(argument, argumentId, nodes, edges, i + 1)

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Raw response: {response}")
        return None



def query_assistant(assistant_id, prompt, timeout_seconds=300):
    """
    Query an assistant and return the response
    """
    start_time = datetime.now()
    
    # Create a thread
    thread = client.beta.threads.create()
    
    # Add message to thread
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=prompt
    )
    
    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )
    
    # Wait for completion with timeout
    while run.status in ['queued', 'in_progress']:
        if datetime.now() - start_time > timedelta(seconds=timeout_seconds):
            return f"Error: Timeout after {timeout_seconds} seconds"
        
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
    
    if run.status == 'completed':
        # Get messages
        messages = client.beta.threads.messages.list(thread_id=thread.id)
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


def get_id():
    """
    Generate a unique UUID for the topic
    """
    return str(uuid.uuid4())

run_pipeline()