from typing import AsyncIterator, Literal, Optional, Tuple, Any
import json

BASE_URL = "https://grok.com/rest/app-chat"

_TOOL_OVERRIDES = {
    "web":  {"imageGen": False, "webSearch": True,  "xSearch": False},
    "x":    {"imageGen": False, "webSearch": False, "xSearch": True},
    "none": {"imageGen": False, "webSearch": False, "xSearch": False},
}


def _payload(text: str, mode: Literal["web", "x", "none"], response_id: Optional[str] = None) -> dict:
    p = {
        "temporary": False,
        "modelName": "grok-3",
        "message": text,
        "fileAttachments": [],
        "imageAttachments": [],
        "disableSearch": mode == "none",
        "enableImageGeneration": False,
        "returnImageBytes": False,
        "returnRawGrokInXaiRequest": False,
        "enableImageStreaming": False,
        "imageGenerationCount": 2,
        "forceConcise": False,
        "toolOverrides": _TOOL_OVERRIDES[mode],
        "enableSideBySide": True,
        "sendFinalMetadata": True,
        "isPreset": False,
        "isReasoning": False,
        "disableTextFollowUps": True,
        "customInstructions": "",
        "deepsearch preset": "",
        "webpageUrls": [],
        "disableArtifact": True,
        "responseMetadata": {"requestModelDetails": {"modelId": "grok-3"}},
    }
    if response_id:
        p["parentResponseId"] = response_id
    return p


async def send_message(
    session,
    conv_id: Optional[str],
    text: str,
    mode: Literal["web", "x", "none"],
    response_id: Optional[str] = None,
) -> AsyncIterator[Tuple[Optional[str], Optional[str], Optional[Any]]]:
    if conv_id:
        url = f"{BASE_URL}/conversations/{conv_id}/responses"
    else:
        url = f"{BASE_URL}/conversations/new"

    payload = _payload(text, mode, response_id)

    async with session.stream("POST", url, json=payload) as resp:
        resp.raise_for_status()
        async for line in resp.aiter_lines():
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            result = data.get("result", {})

            if "conversation" in result:
                yield None, result["conversation"].get("conversationId"), None

            response = result.get("response", {})
            token = response.get("token")
            if token:
                yield token, None, None

            if "modelResponse" in response:
                yield None, None, response["modelResponse"]


def parse_citations(model_response: dict) -> list:
    """Extract citations from a modelResponse dict (result.response.modelResponse)."""
    return [
        {"title": r.get("title", ""), "url": r.get("url", "")}
        for r in model_response.get("webSearchResults", [])
        if r.get("url")
    ]
