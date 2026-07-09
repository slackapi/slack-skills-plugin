import random

from deepeval.models import GeminiModel

from tests.config import GEMINI_API_KEY_POOL, GEMINI_MODEL


def make_judge_model() -> GeminiModel:
    """Gemini model used as the DeepEval judge for LLM-graded eval tests."""
    return GeminiModel(model=GEMINI_MODEL, api_key=random.choice(GEMINI_API_KEY_POOL), temperature=0)
