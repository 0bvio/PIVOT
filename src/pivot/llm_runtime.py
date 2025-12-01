from __future__ import annotations

import json
import logging
import shutil
import subprocess
from typing import Iterable, Generator, Optional

from . import config

logger = logging.getLogger(__name__)

# Try vLLM
_HAS_VLLM = False
try:
    import vllm  # type: ignore
    _HAS_VLLM = True
except Exception:
    _HAS_VLLM = False


def _ollama_available() -> bool:
    # simple check: `ollama` cli exists
    return shutil.which("ollama") is not None


def _llama_cpp_available() -> bool:
    # check for `llama` cli (not standardized); fallback to false
    return shutil.which("llama") is not None


class LLMRuntime:
    def __init__(self):
        self.has_vllm = _HAS_VLLM
        self.has_ollama = _ollama_available()
        self.has_llama_cpp = _llama_cpp_available()
        logger.info("LLMRuntime availability vllm=%s ollama=%s llama_cpp=%s", self.has_vllm, self.has_ollama, self.has_llama_cpp)

    def generate(self, prompt: str, model: Optional[str] = None, max_tokens: int = 512) -> str:
        """Synchronous generation that returns final text."""
        # vLLM path
        if self.has_vllm:
            try:
                from vllm import SamplingParams, Client  # type: ignore

                client = Client(model=model or config.getenv("LLM_MODEL") or "meta-llama/Llama-2-7b-chat")
                params = SamplingParams(max_tokens=max_tokens)
                res = client.generate(prompt, sampling_params=params)
                # collect text
                texts = []
                for r in res:
                    texts.append(r.output[0].text)
                return "".join(texts)
            except Exception as e:
                logger.warning("vLLM generation failed: %s", e)
        # Ollama path
        if self.has_ollama:
            try:
                model_name = model or config.getenv("LLM_MODEL") or "llama2"
                proc = subprocess.run([
                    "ollama",
                    "generate",
                    model_name,
                    "--json"
                ], input=prompt.encode("utf-8"), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
                if proc.returncode == 0:
                    out = proc.stdout.decode("utf-8")
                    try:
                        j = json.loads(out)
                        return j.get("output", "")
                    except Exception:
                        return out
                else:
                    logger.warning("ollama generate failed: %s", proc.stderr.decode("utf-8"))
            except Exception as e:
                logger.warning("ollama generation exception: %s", e)
        # llama.cpp / fallback
        if self.has_llama_cpp:
            try:
                proc = subprocess.run(["llama", "-p", prompt], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
                if proc.returncode == 0:
                    return proc.stdout.decode("utf-8")
            except Exception as e:
                logger.warning("llama.cpp generation failed: %s", e)
        # Last-resort: echo prompt (safe fallback)
        logger.warning("No LLM runtime available; returning prompt as fallback")
        return prompt

    def generate_stream(self, prompt: str, model: Optional[str] = None, max_tokens: int = 512) -> Generator[str, None, None]:
        """Yield tokens/chunks as they are produced. If streaming not available, yield single final text."""
        # vLLM streaming via client streaming API
        if self.has_vllm:
            try:
                from vllm import SamplingParams, Client  # type: ignore

                client = Client(model=model or config.getenv("LLM_MODEL") or "meta-llama/Llama-2-7b-chat")
                params = SamplingParams(max_tokens=max_tokens)
                for output in client.generate(prompt, sampling_params=params):
                    # each output has output[0].text which may be incremental
                    yield output.output[0].text
                return
            except Exception as e:
                logger.warning("vLLM streaming failed: %s", e)
        # Ollama streaming: not implemented here – use generate
        final = self.generate(prompt, model=model, max_tokens=max_tokens)
        yield final


# module-level default
_runtime = LLMRuntime()


def generate(prompt: str, model: Optional[str] = None, max_tokens: int = 512) -> str:
    return _runtime.generate(prompt, model=model, max_tokens=max_tokens)


def generate_stream(prompt: str, model: Optional[str] = None, max_tokens: int = 512) -> Iterable[str]:
    return _runtime.generate_stream(prompt, model=model, max_tokens=max_tokens)

