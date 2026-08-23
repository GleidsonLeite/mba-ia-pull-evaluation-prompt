"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()


def pull_prompts_from_langsmith():
    """
    Pulls the bug_to_user_story_v1 prompt from LangSmith Hub.

    Returns:
        Dictionary with the prompt data, or None if failed
    """
    try:
        print("Pulling prompt from LangSmith Hub: leonanluppi/bug_to_user_story_v1")
        prompt_template = hub.pull("leonanluppi/bug_to_user_story_v1")

        # Extract system and human messages from the ChatPromptTemplate
        system_prompt = ""
        user_prompt = ""

        for message in prompt_template.messages:
            if hasattr(message, 'prompt') and hasattr(message.prompt, 'template'):
                template = message.prompt.template
                if message.__class__.__name__ == "SystemMessagePromptTemplate":
                    system_prompt = template
                elif message.__class__.__name__ == "HumanMessagePromptTemplate":
                    user_prompt = template

        prompt_data = {
            "bug_to_user_story_v1": {
                "description": "Prompt para converter relatos de bugs em User Stories",
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "version": "v1",
                "created_at": "2025-01-15",
                "tags": ["bug-analysis", "user-story", "product-management"]
            }
        }

        print("✓ Prompt pulled successfully")
        return prompt_data

    except Exception as e:
        print(f"❌ Error pulling prompt: {e}")
        return None


def main():
    """Função principal"""
    print_section_header("PULL PROMPTS FROM LANGSMITH")

    # Check required environment variables
    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    # Pull prompt from LangSmith
    prompt_data = pull_prompts_from_langsmith()

    if not prompt_data:
        print("❌ Failed to pull prompts from LangSmith")
        return 1

    # Save to local file
    output_file = "prompts/bug_to_user_story_v1.yml"
    if save_yaml(prompt_data, output_file):
        print(f"\n✓ Prompt saved to {output_file}")
        return 0
    else:
        print(f"\n❌ Failed to save prompt to {output_file}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
