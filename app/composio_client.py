import logging
from composio import ComposioToolSet
from .config import settings

logger = logging.getLogger(__name__)
_toolset = None


def get_toolset():
    global _toolset
    if _toolset is None:
        _toolset = ComposioToolSet(api_key=settings.COMPOSIO_API_KEY)
    return _toolset


def execute(action: str, params: dict, entity_id: str = "default") -> dict:
    toolset = get_toolset()
    result = toolset.execute_action(
        action=action,
        params=params,
        entity_id=entity_id,
    )
    if not result.get("successful", False):
        error = result.get("error") or result.get("data", {})
        raise RuntimeError(f"Composio action '{action}' failed: {error}")
    return result.get("data", {})
