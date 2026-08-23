#!/usr/bin/env python
import os
import yaml
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# Load v3 prompt
with open('prompts/bug_to_user_story_v3.yml') as f:
    prompt_v3 = yaml.safe_load(f)

prompt_data = prompt_v3['bug_to_user_story_v3']

# Create ChatPromptTemplate
prompt_template = ChatPromptTemplate.from_messages([
    ("system", prompt_data.get("system_prompt", "").strip()),
    ("human", prompt_data.get("user_prompt", "").strip())
])

# Push to LangSmith
client = Client()
prompt_name = "bug_to_user_story_v3"
url = client.push_prompt(
    prompt_name,
    object=prompt_template,
    tags=prompt_data.get("tags", []),
    description=prompt_data.get("description", "")
)

print(f"✅ v3 pushed successfully")
print(f"URL: {url}")
