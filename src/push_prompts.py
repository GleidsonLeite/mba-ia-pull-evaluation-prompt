"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        print(f"Pushing prompt to LangSmith Hub: {prompt_name}")

        # Extract system and user prompts
        system_prompt = prompt_data.get("system_prompt", "").strip()
        user_prompt = prompt_data.get("user_prompt", "").strip()

        if not system_prompt or not user_prompt:
            print("❌ Error: system_prompt or user_prompt is empty")
            return False

        # Create ChatPromptTemplate from messages
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_prompt)
        ])

        # Prepare metadata
        tags = prompt_data.get("tags", [])
        description = prompt_data.get("description", "")
        techniques = prompt_data.get("techniques_applied", [])

        # Push to LangSmith Hub using Client API
        client = Client()
        url = client.push_prompt(
            prompt_name,
            object=prompt_template,
            tags=tags,
            description=description
        )

        print(f"✓ Prompt pushed successfully")
        print(f"✓ URL: {url}")
        print(f"✓ Prompt name: {prompt_name}")
        print(f"✓ Techniques: {', '.join(techniques)}")

        return True

    except Exception as e:
        print(f"❌ Error pushing prompt: {e}")
        import traceback
        print(traceback.format_exc())
        return False


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    # Check required fields
    required_fields = ['description', 'system_prompt', 'version']
    for field in required_fields:
        if field not in prompt_data:
            errors.append(f"Required field missing: {field}")

    # Check system_prompt is not empty
    system_prompt = prompt_data.get('system_prompt', '').strip()
    if not system_prompt:
        errors.append("system_prompt is empty")

    # Check for unresolved TODOs, but allow TODO references in Negative Instructions
    # (where it's instructing the model NOT to do something)
    prompt_lines = system_prompt.split('\n')
    in_negative_instructions = False
    has_unresolved_todo = False

    for line in prompt_lines:
        if "## Negative Instructions" in line:
            in_negative_instructions = True
        elif line.startswith("##") and "## Negative Instructions" not in line:
            in_negative_instructions = False

        # Skip checks in Negative Instructions section
        if in_negative_instructions and "## Negative Instructions" not in line:
            continue

        # Check for unresolved [TODO] markers outside of Negative Instructions
        if "[TODO]" in line or (line.strip().startswith("TODO") and not any(
            marker in line for marker in ["Do not", "Do NOT", "Never", "Avoid", "Do NOT output"]
        )):
            has_unresolved_todo = True
            break

    if has_unresolved_todo:
        errors.append("system_prompt contains unresolved TODOs")

    # Check for minimum techniques
    techniques = prompt_data.get('techniques_applied', [])
    if len(techniques) < 2:
        errors.append(f"Minimum 2 techniques required, found: {len(techniques)}")

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    print_section_header("PUSH OPTIMIZED PROMPTS TO LANGSMITH")

    # Check required environment variables
    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    # Load v2 prompt
    prompt_v2 = load_yaml("prompts/bug_to_user_story_v2.yml")
    if not prompt_v2 or "bug_to_user_story_v2" not in prompt_v2:
        print("❌ Failed to load v2 prompt from prompts/bug_to_user_story_v2.yml")
        return 1

    prompt_data = prompt_v2["bug_to_user_story_v2"]

    # Validate prompt
    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Validation errors:")
        for error in errors:
            print(f"   - {error}")
        return 1

    print("✓ Prompt validation passed\n")

    # Try to use username if available, otherwise just use the prompt name
    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
    if username:
        prompt_name = f"{username}/bug_to_user_story_v2"
    else:
        prompt_name = "bug_to_user_story_v2"
        print("⚠️  No USERNAME_LANGSMITH_HUB set, pushing with just prompt name")

    if push_prompt_to_langsmith(prompt_name, prompt_data):
        print(f"\n✅ SUCCESS: Prompt '{prompt_name}' pushed to LangSmith Hub")
        return 0
    else:
        print(f"\n❌ FAILED: Could not push prompt '{prompt_name}'")
        return 1


if __name__ == "__main__":
    sys.exit(main())
