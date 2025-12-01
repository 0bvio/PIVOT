COMPOSE_FILE ?= docker-compose.yml

.PHONY: up down restart ps logs clean embed-test llm-ollama llm-vllm llm-llamacpp

up:
	@docker compose -f $(COMPOSE_FILE) up -d

down:
	@docker compose -f $(COMPOSE_FILE) down

restart: down up

ps:
	@docker compose -f $(COMPOSE_FILE) ps

logs:
	@docker compose -f $(COMPOSE_FILE) logs -f --tail=200

clean:
	@docker compose -f $(COMPOSE_FILE) down -v --remove-orphans

embed-test:
	@docker compose -f $(COMPOSE_FILE) --profile tools build embedtest
	@docker compose -f $(COMPOSE_FILE) --profile tools run --rm embedtest

llm-ollama:
	@docker compose -f $(COMPOSE_FILE) --profile llm up -d ollama

llm-vllm:
	@docker compose -f $(COMPOSE_FILE) --profile llm up -d vllm

llm-llamacpp:
	@docker compose -f $(COMPOSE_FILE) --profile llm up -d llama_cpp
