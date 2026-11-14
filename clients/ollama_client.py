#!/usr/bin/env python3

import asyncio
import os
from typing import Any

import httpx


def load_env() -> None:
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as env_file:
            for line in env_file:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()


load_env()


class QABotMCPClient:
    """Local Ollama Q&A client that uses the MCP knowledge-base server."""

    def __init__(self, mcp_url: str | None = None):
        self.mcp_url = mcp_url or os.getenv("MCP_SERVER_URL", "http://localhost:8000")
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.model_name = os.getenv("OLLAMA_MODEL", "llama3.2")
        self.current_industry: str | None = None
        self.conversation_history: list[dict[str, str]] = []

    async def initialize(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                mcp_response = await client.get(f"{self.mcp_url}/health")
                if mcp_response.status_code != 200:
                    print("✗ Failed to connect to MCP server")
                    return False
                ollama_response = await client.get(f"{self.ollama_url}/api/tags")
                if ollama_response.status_code != 200:
                    print("✗ Failed to connect to Ollama")
                    return False
                models = [model.get("name", "") for model in ollama_response.json().get("models", [])]
                if not any(name == self.model_name or name.startswith(f"{self.model_name}:") for name in models):
                    print(f"✗ Ollama model '{self.model_name}' is not installed")
                    print(f"  Run: ollama pull {self.model_name}")
                    return False
            print("✓ Connected to MCP server")
            print(f"✓ Connected to Ollama ({self.model_name})")
            return True
        except httpx.RequestError as error:
            print(f"✗ Connection error. Start MCP and Ollama first: {error}")
            return False

    async def get_industries(self) -> list[str]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.mcp_url}/industries")
                response.raise_for_status()
                return response.json().get("industries", [])
        except (httpx.HTTPError, ValueError) as error:
            print(f"Error fetching industries: {error}")
            return []

    async def select_industry(self, industry: str) -> bool:
        industries = await self.get_industries()
        if industry.lower() not in [item.lower() for item in industries]:
            print(f"✗ Industry '{industry}' not found")
            print(f"Available industries: {', '.join(industries)}")
            return False
        self.current_industry = industry.lower()
        self.conversation_history = []
        print(f"✓ Selected industry: {self.current_industry}")
        return True

    async def _search_knowledge(self, query: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{self.mcp_url}/search",
                    json={"industry": self.current_industry, "query": query},
                )
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, ValueError) as error:
            print(f"Knowledge search error: {error}")
            return {"results": []}

    async def _generate(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model_name, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            answer = response.json().get("response", "").strip()
            if not answer:
                raise RuntimeError("Ollama returned an empty response")
            return answer

    async def chat(self, user_message: str) -> str:
        if not self.current_industry:
            print("✗ Please select an industry first")
            return ""

        self.conversation_history.append({"role": "user", "content": user_message})
        knowledge = await self._search_knowledge(user_message)
        context = "\n".join(f"- {result}" for result in knowledge.get("results", [])[:3])
        prompt = (
            f"You are a helpful Q&A bot for the {self.current_industry.title()} industry.\n"
            "Answer using the knowledge-base context below. Be clear and practical. "
            "Do not invent policies or facts.\n\n"
            f"Knowledge-base context:\n{context or 'No matching context was found.'}\n\n"
            f"Conversation:\n{self.conversation_history}\n\n"
            f"User: {user_message}\nAssistant:"
        )
        try:
            answer = await self._generate(prompt)
            self.conversation_history.append({"role": "assistant", "content": answer})
            return answer
        except (httpx.HTTPError, RuntimeError, ValueError) as error:
            print(f"⚠ Ollama error: {error}")
            return "Ollama could not generate an answer. Confirm Ollama is running and the model is installed."


async def main() -> None:
    print("=" * 60)
    print("Q&A Bot with Ollama & MCP")
    print("=" * 60)
    client = QABotMCPClient()
    if not await client.initialize():
        return
    industries = await client.get_industries()
    if not industries:
        print("✗ No industries available")
        return
    print(f"\nAvailable industries: {', '.join(industries)}")
    for index, industry in enumerate(industries, 1):
        print(f"  {index}. {industry}")
    choice = input("\nEnter industry number or name: ").strip()
    industry = industries[int(choice) - 1] if choice.isdigit() and 0 < int(choice) <= len(industries) else choice
    if not industry or not await client.select_industry(industry):
        return
    print(f"\nStarting Q&A session for {industry}")
    print("Type 'switch' to change industry, or 'exit' to quit")
    while True:
        user_input = input("\nYou: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "exit":
            print("✓ Goodbye!")
            return
        if user_input.lower() == "switch":
            print("\nSelect a new industry:")
            for index, available_industry in enumerate(industries, 1):
                print(f"  {index}. {available_industry}")
            choice = input("Enter industry number or name: ").strip()
            if choice.isdigit() and 0 < int(choice) <= len(industries):
                selected_industry = industries[int(choice) - 1]
            else:
                selected_industry = choice
            if selected_industry and await client.select_industry(selected_industry):
                print(f"Starting Q&A session for {selected_industry}")
            else:
                print("✗ Invalid industry selection")
            continue
        print(f"\nBot: {await client.chat(user_input)}")


if __name__ == "__main__":
    asyncio.run(main())
