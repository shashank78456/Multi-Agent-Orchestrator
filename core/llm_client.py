
import asyncio
import json
import os
import urllib.error
import urllib.request


class LLMClient:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        self.model = os.getenv("LLM_MODEL", "gemini-2.5-flash")
        self.api_key = os.getenv("LLM_API_KEY")

        if not self.api_key:
            raise ValueError("LLM_API_KEY is not set.")

        self.base_url = os.getenv("LLM_BASE_URL", "").rstrip("/")

        if self.provider == "gemini":
            self.base_url = (self.base_url or "https://generativelanguage.googleapis.com/v1beta")
        elif self.provider == "openai":
            self.base_url = (self.base_url or "https://api.openai.com/v1")
        elif self.provider == "anthropic":
            self.base_url = (self.base_url or "https://api.anthropic.com/v1")
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    async def generate_text(self, prompt: str) -> str:
        return await asyncio.to_thread(self._generate, prompt, False)

    async def generate_json(self, prompt: str) -> dict:
        response = await asyncio.to_thread(self._generate, prompt, True)

        try:
            result = json.loads(response)
        except json.JSONDecodeError as exc:
            raise ValueError("LLM returned invalid JSON.") from exc

        if not isinstance(result, dict):
            raise ValueError("LLM response must be a JSON object.")

        return result

    def _generate(self, prompt: str, json_mode: bool) -> str:
        if self.provider == "gemini":
            return self._gemini_request(prompt, json_mode)

        if self.provider == "openai":
            return self._openai_request(prompt, json_mode)

        if self.provider == "anthropic":
            return self._anthropic_request(prompt, json_mode)

        raise ValueError("Unsupported provider.")

    def _post(self, url, headers, payload):
        data = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))

        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM API error ({exc.code}): {error_body}") from exc

        except urllib.error.URLError as exc:
            raise RuntimeError(f"Could not connect to LLM provider: {exc.reason}") from exc

    def _gemini_request(self, prompt, json_mode):
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }

        if json_mode:
            payload["generationConfig"] = {
                "responseMimeType": "application/json"
            }

        response = self._post(
            f"{self.base_url}/models/{self.model}:generateContent",
            {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            payload,
        )

        try:
            return response["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Unexpected Gemini response format.") from exc

    def _openai_request(self, prompt, json_mode):
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
        }

        if json_mode:
            payload["response_format"] = {
                "type": "json_object"
            }

        response = self._post(
            f"{self.base_url}/chat/completions",
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            payload,
        )

        try:
            return response["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            raise RuntimeError("Unexpected OpenAI-compatible response format.") from exc

    def _anthropic_request(self, prompt, json_mode):
        if json_mode:
            prompt += ("\n\nReturn only a valid JSON object. Do not include Markdown code fences.")

        response = self._post(
            f"{self.base_url}/messages",
            {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            {
                "model": self.model,
                "max_tokens": 4096,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
            },
        )

        try:
            return response["content"][0]["text"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Unexpected Anthropic response format.") from exc
