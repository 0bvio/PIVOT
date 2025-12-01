#!/usr/bin/env bash
# Pull a model into Ollama either using local `ollama` CLI or by exec-ing into the pivot-ollama container.
# Usage: ./scripts/pull-ollama-model.sh <model-slug-or-search-term>
set -euo pipefail
MODEL=${1:-}
if [ -z "$MODEL" ]; then
  echo "Usage: $0 <OLLAMA_MODEL_SLUG or search term>"
  exit 1
fi

CONTAINER_NAME="pivot-ollama"

run_pull_local() {
  echo "Trying local ollama CLI to pull: $MODEL"
  if ! command -v ollama >/dev/null 2>&1; then
    echo "Local ollama CLI not found"
    return 2
  fi
  if ollama pull "$MODEL"; then
    echo "Model pulled locally with host ollama CLI."
    return 0
  else
    echo "Local ollama pull failed."
    return 1
  fi
}

run_pull_container() {
  echo "Attempting to pull model $MODEL inside container $CONTAINER_NAME"
  if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Container $CONTAINER_NAME not running. Starting it now..."
    docker compose --profile llm up -d "$CONTAINER_NAME"
    echo "Waiting for container to initialize..."
    sleep 5
  fi

  # Try pull inside container
  if docker exec -i "$CONTAINER_NAME" ollama pull "$MODEL" 2>&1 | tee /tmp/ollama-pull.log; then
    echo "Model pulled successfully inside container."
    return 0
  else
    echo "Container pull failed. Captured output below:"
    tail -n +1 /tmp/ollama-pull.log
    return 1
  fi
}

try_search_registry_in_container() {
  echo "Attempting to search Ollama registry for '$MODEL' (if supported by CLI)..."
  if docker exec -i "$CONTAINER_NAME" ollama registry search "$MODEL" 2>&1 | tee /tmp/ollama-search.log; then
    echo "Registry search output:"
    tail -n +1 /tmp/ollama-search.log
    return 0
  else
    echo "Registry search not supported or failed inside container. Output:"
    tail -n +1 /tmp/ollama-search.log || true
    return 1
  fi
}

# 1) Try local ollama CLI
run_pull_local && exit 0 || true

# 2) Try inside container
if run_pull_container; then
  exit 0
else
  # On failure, inspect the error and try to suggest alternatives
  echo "\nModel pull failed inside container. Trying to provide diagnostics...\n"
  echo "If you see 'file does not exist' or 'manifest' errors, the model slug is likely incorrect or not available in the Ollama registry."

  # Try to run a registry search inside the container if available
  if try_search_registry_in_container; then
    echo "\nIf the search results show model candidates, pick the exact slug and re-run this script with that slug."
    exit 1
  fi

  echo "\nDiagnostics:"
  echo "- Confirm the exact Ollama model slug on https://ollama.com/models or in your provider's docs."
  echo "- Try common variations, for example:"
  echo "    qwen/qwen-2.5-32b"
  echo "    qwen/qwen-2.5-32b-weights"
  echo "    qwen/qwen-2.5"
  echo "- If you have the host 'ollama' CLI, install it and run: ollama pull <slug>"
  echo "- Check container logs: docker compose logs -f pivot-ollama"
  echo "- Inspect container path for ollama binary: docker exec -it pivot-ollama which ollama || ls -la /usr/local/bin /usr/bin /bin"
  exit 1
fi
