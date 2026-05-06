# Backward compatibility - re-export from ai_client
from src.core.ai_client import ai_client, AIClient

# Legacy export
openai_client = ai_client
OpenAIClient = AIClient
