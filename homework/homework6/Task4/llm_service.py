import http.client
import json
import math
import time
import urllib.error
import urllib.request

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_TIMEOUT_S = 300
ALLOWED_ROLES = {"system", "user", "assistant"}

# JSON Schema type names -> Python types (integer and number are handled separately).
_JSON_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "null": type(None),
}


class InvalidRequestError(Exception):
    """The request breaks the request schema."""


class LLMUnavailableError(Exception):
    """Ollama is unreachable, timed out, or returned a server error; the workflow may retry."""


class LLMModelError(Exception):
    """Ollama rejected the request (model not installed or another 4xx); not retryable."""


class LLMOutputError(Exception):
    """Ollama's answer is empty, unreadable, or does not satisfy the output schema."""


class LLMClient:
    """Sends chat messages to a local Ollama server and returns its output.

    General purpose: the caller supplies the messages, model, settings and output
    schema on every call. The client stores only the Ollama URL.
    """

    def __init__(self, base_url: str = DEFAULT_OLLAMA_URL):
        if not isinstance(base_url, str) or not base_url.strip():
            raise InvalidRequestError("base_url must be a non-empty string.")
        self.base_url = base_url.rstrip("/")

   
    def _validate_request(self, request: dict):
        """Raise InvalidRequestError unless request satisfies the request schema.

        Returns (messages, model, options, output_schema, timeout_s).
        """
        if not isinstance(request, dict):
            raise InvalidRequestError("Request must be a dictionary.")

        # messages
        messages = request.get("messages")
        if not isinstance(messages, list) or len(messages) == 0:
            raise InvalidRequestError("messages must be a non-empty list.")
        for message in messages:
            if not isinstance(message, dict) or set(message) != {"role", "content"}:
                raise InvalidRequestError("Each message must be a dict with exactly 'role' and 'content'.")
            if message["role"] not in ALLOWED_ROLES:
                raise InvalidRequestError("Each message role must be system, user or assistant.")
            if not isinstance(message["content"], str) or not message["content"].strip():
                raise InvalidRequestError("Each message content must be a non-blank string.")

        # model
        model = request.get("model")
        if not isinstance(model, str) or not model.strip():
            raise InvalidRequestError("model must be a non-blank string.")

        # options
        options = request.get("options", {})
        if not isinstance(options, dict):
            raise InvalidRequestError("options must be a dictionary.")
        for value in options.values():
            if isinstance(value, float) and not math.isfinite(value):
                raise InvalidRequestError("options values must be finite numbers.")

        # output_schema
        output_schema = request.get("output_schema")
        if output_schema is not None and not isinstance(output_schema, dict):
            raise InvalidRequestError("output_schema must be a dictionary or null.")

        # timeout_s
        timeout_s = request.get("timeout_s", DEFAULT_TIMEOUT_S)
        if (isinstance(timeout_s, bool) or not isinstance(timeout_s, (int, float))
                or not math.isfinite(timeout_s) or timeout_s <= 0):
            raise InvalidRequestError("timeout_s must be a positive, finite number.")

        return messages, model, options, output_schema, timeout_s

    
    def call_llm(self, request: dict) -> dict:
        """Send chat messages to Ollama and return the model's output.

        Returns:
            {"model": str, "text": str, "parsed": dict | None, "duration_ms": int}

        Raises:
            InvalidRequestError: the request breaks the request schema (Ollama is not called).
            LLMUnavailableError: Ollama is unreachable, timed out, or returned a 5xx.
            LLMModelError: Ollama rejected the request (404 model not found, or another 4xx).
            LLMOutputError: the answer is empty, unreadable, or does not satisfy output_schema.
        """
      
        messages, model, options, output_schema, timeout_s = self._validate_request(request)

        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": options,
        }
        if output_schema is not None:
            payload["format"] = output_schema

        http_request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        started = time.perf_counter()
        try:
            with urllib.request.urlopen(http_request, timeout=timeout_s) as response:
                raw_reply = response.read()
        except urllib.error.HTTPError as e:                  # must come BEFORE URLError
            if e.code >= 500:
                raise LLMUnavailableError("Ollama returned a server error.") from e
            raise LLMModelError("Ollama rejected the request.") from e
        except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException) as e:
            raise LLMUnavailableError("Ollama is unreachable or timed out.") from e
        duration_ms = int((time.perf_counter() - started) * 1000)

        try:
            reply = json.loads(raw_reply.decode("utf-8"))
            text = reply["message"]["content"]
            reply_model = reply["model"]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as e:
            raise LLMOutputError("Ollama reply was not in the expected format.") from e

        
        if not isinstance(text, str) or not text.strip():
            raise LLMOutputError("Ollama returned an empty answer.")
        if not isinstance(reply_model, str) or not reply_model.strip():
            raise LLMOutputError("Ollama reply was not in the expected format.")

       
        parsed = None
        if output_schema is not None:
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as e:
                raise LLMOutputError("The model output is not valid JSON.") from e
            if not isinstance(parsed, dict):
                raise LLMOutputError("The model output must be a JSON object.")
            self._check_against_schema(parsed, output_schema)

       
        return {"model": reply_model, "text": text, "parsed": parsed, "duration_ms": duration_ms}

   
    def _check_against_schema(self, value, schema: dict) -> None:
        """Raise LLMOutputError unless value satisfies the supported schema keywords.

        Supported: type, minLength, required, properties, additionalProperties: false, items.
        Other keywords are ignored.
        """
        expected = schema.get("type")
        if expected is not None:
            if expected == "integer":
                ok = isinstance(value, int) and not isinstance(value, bool)
            elif expected == "number":
                ok = isinstance(value, (int, float)) and not isinstance(value, bool)
            else:
                ok = isinstance(value, _JSON_TYPES.get(expected, object))
            if not ok:
                raise LLMOutputError("The model output does not match the output schema.")

        if isinstance(value, str) and len(value) < schema.get("minLength", 0):
            raise LLMOutputError("The model output does not match the output schema.")

        if isinstance(value, dict):
            properties = schema.get("properties", {})
            for name in schema.get("required", []):
                if name not in value:
                    raise LLMOutputError("The model output does not match the output schema.")
            if schema.get("additionalProperties") is False and set(value) - set(properties):
                raise LLMOutputError("The model output does not match the output schema.")
            for name, sub_schema in properties.items():
                if name in value:
                    self._check_against_schema(value[name], sub_schema)

        if isinstance(value, list) and "items" in schema:
            for item in value:
                self._check_against_schema(item, schema["items"])