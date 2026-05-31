from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_caption_text() -> str:
    return (FIXTURES / "sample_caption.txt").read_text(encoding="utf-8")
