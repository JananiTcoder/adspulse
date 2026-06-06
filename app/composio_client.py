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


def execute(action: str, params: dict, connected_account_id: str = None) -> dict:
    toolset = get_toolset()
    kwargs = {
        "action": action,
        "params": params,
        "entity_id": "default",
    }
    if connected_account_id:
        kwargs["connected_account_id"] = connected_account_id
    result = toolset.execute_action(**kwargs)
    ok = result.get("successful") or result.get("successfull") or False
    if not ok:
        error = result.get("error") or result.get("data", {})
        raise RuntimeError(f"Composio action '{action}' failed: {error}")
    return result.get("data", {})
