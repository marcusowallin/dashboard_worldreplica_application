"""Smoke test: every module in the skeleton imports cleanly."""
import importlib

import pytest

MODULES = [
    "src.model.fuel",
    "src.model.periods",
    "src.model.income",
    "src.model.guidance",
    "src.model.decomposition",
    "src.twins",
    "src.data_sources",
    "src.news_tagger",
    "src.live_state",
    "src.story.sources",
    "src.story.method_content",
    "src.ui.method_parts",
    "src.consensus_reader",
]


@pytest.mark.parametrize("name", MODULES)
def test_module_imports(name):
    """Each module can be imported (catches typos and missing files early)."""
    assert importlib.import_module(name) is not None
