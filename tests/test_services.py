import pytest
from app.ai.analyzers.call_analyzer import CallAnalyzer

def test_call_analyzer_post_processing_success():
    analyzer = CallAnalyzer()

    mock_raw_data = {
        "manager_name": "Сергій",
        "script_started_correctly": 1,
        "asked_vin": 1,
        "asked_mileage": 1,
        "offered_diagnostics": 1,
        "service_booking": 1,
        "rude": 0,
        "conflict": 0,
        "answered_topic": 1,
        "toxic": 0,
        "violations": 0,
        "needs_attention": False,
        "manager_comment": "Все чудово."
    }

    result = analyzer._post_process(mock_raw_data)

    assert result.manager_name == "Сергій"
    assert result.score == 6
    assert result.needs_attention is False
    assert "ALERT:" not in result.manager_comment

def test_call_analyzer_post_processing_violations():
    analyzer = CallAnalyzer()

    mock_raw_data = {
        "manager_name": "Андрій",
        "script_started_correctly": 0,
        "asked_vin": 0,
        "asked_mileage": 1,
        "offered_diagnostics": 0,
        "service_booking": 0,
        "rude": 1,
        "conflict": 1,
        "answered_topic": 0,
        "toxic": 1,
        "violations": 1,
        "needs_attention": True,
        "manager_comment": "Менеджер розмовляв дуже грубо."
    }

    result = analyzer._post_process(mock_raw_data)

    assert result.manager_name == "Андрій"
    assert result.score == -9
    assert result.needs_attention is True
    assert result.manager_comment.startswith("ALERT:")
