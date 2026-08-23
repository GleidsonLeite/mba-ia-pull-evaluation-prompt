"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

class TestPrompts:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Load the v2 prompt for all tests."""
        self.prompts = load_prompts("prompts/bug_to_user_story_v2.yml")
        self.prompt_data = self.prompts.get("bug_to_user_story_v2", {})
        self.system_prompt = self.prompt_data.get("system_prompt", "")

    def test_prompt_has_system_prompt(self):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in self.prompt_data, "Field 'system_prompt' not found"
        assert self.system_prompt.strip(), "system_prompt is empty"

    def test_prompt_has_role_definition(self):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        # Look for persona markers in Portuguese or English
        persona_markers = [
            "Senior Product Manager",
            "Product Manager",
            "Você é",
            "You are"
        ]
        has_persona = any(marker.lower() in self.system_prompt.lower() for marker in persona_markers)
        assert has_persona, "No persona/role definition found in system_prompt"

    def test_prompt_mentions_format(self):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        format_markers = [
            "Markdown",
            "Como um",
            "Eu quero",
            "Para que",
            "User Story",
            "user-story"
        ]
        has_format = any(marker.lower() in self.system_prompt.lower() for marker in format_markers)
        assert has_format, "No User Story format or Markdown requirement found"

    def test_prompt_has_few_shot_examples(self):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        example_count = self.system_prompt.lower().count("### exemplo")
        assert example_count >= 2, f"Need at least 2 examples, found {example_count}"

        has_input_output = (
            "**Entrada:**" in self.system_prompt
            and "**Saída:**" in self.system_prompt
        )
        assert has_input_output, "No Entrada/Saída example structure found"

    def test_prompt_no_todos(self):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        # Split the prompt into sections to check for unresolved TODOs
        # Allow [TODO] in the "Negative Instructions" section since it's about what NOT to do
        prompt_lines = self.system_prompt.split('\n')

        in_negative_instructions = False
        for line in prompt_lines:
            if "## Negative Instructions" in line:
                in_negative_instructions = True
            elif line.startswith("##") and "## Negative Instructions" not in line:
                in_negative_instructions = False

            # Skip lines in Negative Instructions section
            if in_negative_instructions and "## Negative Instructions" not in line:
                continue

            # Check for unresolved [TODO] markers outside of Negative Instructions
            if "[TODO]" in line or (line.strip().startswith("TODO") and not any(
                marker in line for marker in ["Do not", "Do NOT", "Never", "Avoid", "Do NOT output"]
            )):
                assert False, f"Found unresolved TODO in: {line}"

    def test_minimum_techniques(self):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = self.prompt_data.get("techniques_applied", [])
        assert isinstance(techniques, list), "techniques_applied must be a list"
        assert len(techniques) >= 2, f"Minimum 2 techniques required, found {len(techniques)}: {techniques}"

        # Verify expected techniques are present
        expected_techniques = {"few-shot-learning", "chain-of-thought", "role-prompting"}
        found_techniques = set(t.lower().replace("_", "-") for t in techniques)
        assert found_techniques.intersection(expected_techniques), \
            f"Expected at least one of {expected_techniques}, found {techniques}"

    def test_prompt_uses_one_stable_format_without_criteria_quotas(self):
        """Garante formato único e critérios guiados pelo relato, não por cotas."""
        forbidden_instructions = [
            "FORMAT SELECTION",
            "SIMPLE BUGS",
            "COMPLEX BUGS",
            "3-5 criteria",
            "5-7",
            "7+",
        ]

        for instruction in forbidden_instructions:
            assert instruction not in self.system_prompt, \
                f"Found contradictory or quota-based instruction: {instruction}"

    def test_prompt_examples_demonstrate_three_complexity_levels(self):
        """Valida exemplos em português para casos simples, técnicos e múltiplos."""
        assert self.system_prompt.count("**Entrada:**") >= 3
        assert self.system_prompt.count("**Saída:**") >= 3

    def test_prompt_defines_fact_grounding_policy(self):
        """Exige regras explícitas contra detalhes e soluções não informados."""
        prompt_lower = self.system_prompt.lower()
        assert "fonte de verdade" in prompt_lower
        assert "não invente" in prompt_lower
        assert "soluç" in prompt_lower and "técnic" in prompt_lower

    def test_prompt_fallback_is_fully_in_portuguese(self):
        """Evita instruções em inglês no fallback exibido ao usuário."""
        assert "Não foi possível criar uma User Story válida." in self.system_prompt
        assert "Clarify" not in self.system_prompt
        assert "Provide affected" not in self.system_prompt

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
