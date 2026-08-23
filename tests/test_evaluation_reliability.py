"""Testes de confiabilidade para falhas transitórias durante a avaliação."""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import evaluate
import metrics


def test_retry_succeeds_after_transient_error():
    attempts = 0

    def operation():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return {"status": "error", "score": None, "error": "rate limit"}
        return {"status": "ok", "score": 0.9}

    result = evaluate.invoke_with_retry(
        operation,
        operation_name="precision",
        max_attempts=3,
        base_delay=0,
    )

    assert result == {"status": "ok", "score": 0.9}
    assert attempts == 2


def test_retry_exhaustion_invalidates_evaluation():
    attempts = 0

    def operation():
        nonlocal attempts
        attempts += 1
        return {"status": "error", "score": None, "error": "rate limit"}

    with pytest.raises(evaluate.EvaluationIncompleteError, match="precision"):
        evaluate.invoke_with_retry(
            operation,
            operation_name="precision",
            max_attempts=3,
            base_delay=0,
        )

    assert attempts == 3


def test_generation_failure_returns_status_instead_of_empty_answer():
    class BrokenChain:
        def invoke(self, _inputs):
            raise RuntimeError("provider unavailable")

    class BrokenPrompt:
        def __or__(self, _llm):
            return BrokenChain()

    example = SimpleNamespace(
        inputs={"bug_report": "Um bug"},
        outputs={"reference": "Uma referência"},
    )

    result = evaluate.evaluate_prompt_on_example(BrokenPrompt(), example, object())

    assert result["status"] == "error"
    assert result["answer"] is None
    assert "provider unavailable" in result["error"]


def test_metric_json_parse_failure_is_not_scored_as_zero(monkeypatch):
    class InvalidJsonLlm:
        def invoke(self, _messages):
            return SimpleNamespace(content="resposta inválida")

    monkeypatch.setattr(metrics, "get_evaluator_llm", lambda: InvalidJsonLlm())

    result = metrics.evaluate_clarity("bug", "story", "reference")

    assert result["status"] == "error"
    assert result["score"] is None
    assert "JSON" in result["error"]


def test_incomplete_run_summary_contains_no_scores():
    result = evaluate.incomplete_evaluation_result(
        "bug_to_user_story_v2",
        evaluate.EvaluationIncompleteError("precision rate limit"),
    )

    assert result == {
        "prompt": "bug_to_user_story_v2",
        "scores": None,
        "passed": False,
        "status": "incomplete",
        "error": "precision rate limit",
    }


@pytest.mark.parametrize(
    "metric_function",
    [
        metrics.evaluate_tone_score,
        metrics.evaluate_acceptance_criteria_score,
        metrics.evaluate_user_story_format_score,
        metrics.evaluate_completeness_score,
    ],
)
def test_all_additional_metrics_use_status_aware_errors(monkeypatch, metric_function):
    class InvalidJsonLlm:
        def invoke(self, _messages):
            return SimpleNamespace(content="sem json")

    monkeypatch.setattr(metrics, "get_evaluator_llm", lambda: InvalidJsonLlm())

    result = metric_function("bug", "story", "reference")

    assert result["status"] == "error"
    assert result["score"] is None
