# Grok API — Endpoint Reference

Phase 0 discovery output. Sources: `mem0ai/grok3-api`, `EveripediaNetwork/grokit`, `boykopovar/Grok3API` source analysis.
Status: **COMPLETE** — sourced from static analysis of `mem0ai/grok3-api`, `boykopovar/Grok3API`, `EveripediaNetwork/grokit`. Citation format deferred to Phase 2 integration test.

---

## Base URL

```
https://grok.com
```

`x.com/i/grok` — pending browser capture to confirm redirect behavior.
`api.x.com/2/grok` — older Grok 2 embedded-in-X API (not targeted by this project).

---

## Authentication

**No bearer token.** The grok.com API authenticates via browser cookies + a dynamic `x-statsig-id` header.

### Required Cookies

| Cookie | Notes |
|---|---|
| `sso` | Primary session token. Has expiry field used for auth check. |
| `sso-rw` | Write-scoped session token. |
| `x-anonuserid` | Anonymous user ID. |
| `x-challenge` | Anti-bot challenge token. |
| `x-signature` | Signature for challenge verification. |

**Expiry check:** `sso` cookie has an `expires` field (Unix timestamp). `is_expired()` compares against `time.time()`.

### `x-statsig-id` Header

Dynamic value, extracted from the browser JS runtime at `grok.com`.

**Extraction method (two approaches):**

1. **localStorage** (preferred for Playwright):
```javascript
for (let key in localStorage) {
    if (key.startsWith('statsig.stable_id')) {
        return localStorage.getItem(key);
    }
}
```

2. **Request interception** — patch `window.fetch`, intercept calls to `https://grok.com/rest/app-chat/conversations/new`, read `x-statsig-id` from the headers object.

Must be obtained after navigating to `grok.com` and waiting for page load (textarea CSS selector: `div.relative.z-10 textarea`).

---

## Endpoints

### 1. New Conversation + First Message

```
POST https://grok.com/rest/app-chat/conversations/new
```

Creates a new conversation and sends the first message in one request.

**Headers:**
```
Content-Type: application/json
Accept: */*
Origin: https://grok.com
Referer: https://grok.com/
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-origin
x-statsig-id: <dynamic>
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...
```

**Request body:**
```json
{
  "temporary": false,
  "modelName": "grok-3",
  "message": "<user text>",
  "fileAttachments": [],
  "imageAttachments": [],
  "disableSearch": false,
  "enableImageGeneration": false,
  "returnImageBytes": false,
  "returnRawGrokInXaiRequest": false,
  "enableImageStreaming": false,
  "imageGenerationCount": 2,
  "forceConcise": false,
  "toolOverrides": {
    "imageGen": false,
    "webSearch": true,
    "xSearch": false
  },
  "enableSideBySide": true,
  "sendFinalMetadata": true,
  "isPreset": false,
  "isReasoning": false,
  "disableTextFollowUps": true,
  "customInstructions": "",
  "deepsearch preset": "",
  "webpageUrls": [],
  "disableArtifact": true,
  "responseMetadata": {
    "requestModelDetails": {
      "modelId": "grok-3"
    }
  }
}
```

Note: `"deepsearch preset"` has a space in the key (confirmed in boykopovar source, line 552).

---

### 2. Continue Conversation

```
POST https://grok.com/rest/app-chat/conversations/{conversationId}/responses
```

Sends a follow-up message in an existing conversation.

**Additional field vs endpoint 1:**
```json
{
  "parentResponseId": "<responseId from previous turn>"
}
```

All other headers and body fields are identical to endpoint 1.

---

### 3. Upload File

```
POST https://grok.com/rest/app-chat/upload-file
```

**Request body:**
```json
{
  "fileName": "<name.ext>",
  "fileMimeType": "<mime/type>",
  "content": "<base64-encoded file content>"
}
```

**Response:**
```json
{
  "fileMetadataId": "<id>"
}
```

Use `fileMetadataId` in the `fileAttachments` array of the message request.

---

## Search Modes

Controlled via `toolOverrides` in the message payload.

| Mode | `toolOverrides` value |
|---|---|
| Web search | `{"imageGen": false, "webSearch": true, "xSearch": false}` |
| X search | `{"imageGen": false, "webSearch": false, "xSearch": true}` |
| Both | `{"imageGen": false, "webSearch": true, "xSearch": true}` |
| No search | `{}` + `"disableSearch": true` |

Additional tool override keys observed in the wild: `xMediaSearch`, `trendsSearch`, `xPostAnalyze`.
Source: boykopovar `askDoc.md`.

**Confirmed by:** source code analysis of boykopovar/Grok3API. **Pending:** empirical browser capture at `x.com/i/grok`.

---

## Streaming Protocol

**NDJSON** — newline-delimited JSON. Each line is a complete JSON object.

**Streaming token line:**
```json
{"result": {"response": {"token": "<partial text>"}}}
```

**Final response line:**
```json
{"result": {"response": {"modelResponse": {"message": "<full text>", "responseId": "<id>"}}}}
```

**Conversation metadata line:**
```json
{"result": {"conversation": {"conversationId": "<id>", "title": "<title>", "createTime": "...", "modifyTime": "..."}}}
```

**Title line:**
```json
{"result": {"title": {"newTitle": "<auto-generated title>"}}}
```

Collect tokens progressively. When `modelResponse` is present, use `modelResponse.message` as the canonical full response (skip accumulated tokens).

---

## Citations / Web Search Results

Confirmed in Phase 2 empirical testing (live web search query).

Citations are in `result.response.modelResponse.webSearchResults` — an array of objects:

```json
{
  "webSearchResults": [
    {
      "title": "Example Site",
      "url": "https://example.com",
      "preview": "Short snippet text..."
    }
  ]
}
```

`parse_citations()` reads `webSearchResults`, filters entries without a `url`, and returns `[{"title": ..., "url": ...}]`.

Note: `modelResponse.message` contains the canonical full response text. Prefer it over accumulated streaming tokens when present.

---

## Open Items

1. **`x.com/i/grok` redirect target** — does it hit `grok.com/rest/...` or `api.x.com`? (not targeted; unverified)
2. **Additional headers** — `baggage`, `sentry-trace` observed in browser traffic but not required; requests succeed without them.

---

## Reference Implementations

| Repo | API | Notes |
|---|---|---|
| `mem0ai/grok3-api` | grok.com | Minimal, no statsig, no search mode control |
| `boykopovar/Grok3API` | grok.com | Most complete: statsig, toolOverrides, conversation continuity |
| `EveripediaNetwork/grokit` | api.x.com (Grok 2) | Static bearer token, different cookie set, not targeted |
