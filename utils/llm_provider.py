"""
LLM Provider — AWS Bedrock (Claude) + Azure OpenAI
Credentials loaded from .env with hardcoded fallback defaults.
"""
import os
import json
from pathlib import Path


def _load_env():
    search_paths = [
        Path(__file__).resolve().parent.parent,
        Path(__file__).resolve().parent,
        Path.cwd(),
        Path.cwd().parent,
    ]
    for folder in search_paths:
        env_file = folder / ".env"
        if env_file.exists():
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, val = line.partition("=")
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key:
                        os.environ[key] = val
            return env_file
    return None


_env_file_loaded = _load_env()


def _get_region():
    return (os.getenv("AWS_DEFAULT_REGION") or
            os.getenv("AWS_REGION") or
            "ap-southeast-2")


def _get_model():
    return os.getenv("BEDROCK_MODEL_ID",
                     "au.anthropic.claude-haiku-4-5-20251001-v1:0")


def _build_bedrock(config: dict = None):
    import boto3
    config = config or {}

    ak     = config.get("aws_access_key_id")     or os.getenv("AWS_ACCESS_KEY_ID", "")
    sk     = config.get("aws_secret_access_key") or os.getenv("AWS_SECRET_ACCESS_KEY", "")
    region = config.get("aws_region")            or _get_region()
    model  = "au.anthropic.claude-haiku-4-5-20251001-v1:0"  # hardcoded — fastest AU model

    session = boto3.Session(
        aws_access_key_id=ak,
        aws_secret_access_key=sk,
        region_name=region
    )
    client = session.client("bedrock-runtime")

    class BedrockLLM:
        def __init__(self, client, model_id):
            self.client   = client
            self.model_id = model_id

        def invoke(self, prompt: str, max_tokens: int = 400,
                   temperature: float = 0) -> str:
            resp = self.client.converse(
                modelId=self.model_id,
                messages=[{
                    "role": "user",
                    "content": [{"text": prompt}]
                }],
                inferenceConfig={
                    "maxTokens": max_tokens,
                    "temperature": temperature,
                }
            )
            return resp["output"]["message"]["content"][0]["text"].strip()

    return BedrockLLM(client, model)


def _build_azure(config: dict = None):
    from openai import AzureOpenAI
    config = config or {}
    endpoint   = config.get("azure_endpoint")    or os.getenv("AZURE_OPENAI_ENDPOINT", "")
    api_key    = config.get("azure_api_key")     or os.getenv("AZURE_OPENAI_API_KEY", "")
    deployment = config.get("azure_deployment")  or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    api_ver    = config.get("azure_api_version") or os.getenv("AZURE_OPENAI_API_VERSION",
                    "2024-08-01-preview")
    client = AzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version=api_ver)

    class AzureLLM:
        def __init__(self, client, deployment):
            self.client     = client
            self.deployment = deployment

        def invoke(self, prompt: str, max_tokens: int = 1000,
                   temperature: float = 0) -> str:
            resp = self.client.chat.completions.create(
                model=self.deployment,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return resp.choices[0].message.content.strip()

    return AzureLLM(client, deployment)


def build_llm(config: dict = None):
    config   = config or {}
    provider = config.get("provider") or os.getenv("LLM_PROVIDER", "bedrock")
    if provider == "bedrock":
        return _build_bedrock(config)
    elif provider == "azure":
        return _build_azure(config)
    raise ValueError(f"Unknown provider: {provider}")


def get_provider_status() -> dict:
    return {
        "provider":   os.getenv("LLM_PROVIDER", "bedrock"),
        "bedrock_ok": bool(os.getenv("AWS_ACCESS_KEY_ID") and
                          os.getenv("AWS_SECRET_ACCESS_KEY")),
        "azure_ok":   bool(os.getenv("AZURE_OPENAI_ENDPOINT") and
                          os.getenv("AZURE_OPENAI_API_KEY")),
        "region":     _get_region(),
        "model":      _get_model(),
        "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
        "env_file":   str(_env_file_loaded) if _env_file_loaded else "NOT FOUND",
    }
