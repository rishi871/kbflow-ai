import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL_DEFAULT_OPENAI = "gpt-3.5-turbo"
EMBEDDING_MODEL_DEFAULT_OPENAI = "text-embedding-ada-002"

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# You can set a default OpenRouter model, e.g., "mistralai/mistral-7b-instruct"
# Or let the user specify it. For now, let's make it configurable.
LLM_MODEL_DEFAULT_OPENROUTER = os.getenv("OPENROUTER_DEFAULT_MODEL", "mistralai/mistral-7b-instruct-v0.2") # Example
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1" # Standard base URL

# --- Global Defaults (can be overridden by environment variables or chosen at runtime) ---
# Choose your preferred LLM provider: "openai" or "openrouter"
LLM_PROVIDER_DEFAULT = os.getenv("LLM_PROVIDER_DEFAULT", "openai").lower()


# Embedding model configuration (OpenRouter doesn't directly offer a dedicated embedding endpoint like OpenAI's)
# So, for embeddings, we'll likely stick to OpenAI or SentenceTransformers for now.
# If you find an OpenRouter model that's good for embeddings and accessible via chat completions,
# you might adapt, but it's less straightforward.
EMBEDDING_PROVIDER_DEFAULT = os.getenv("EMBEDDING_PROVIDER_DEFAULT", "openai").lower() # or "sentence_transformers"
SENTENCE_TRANSFORMER_MODEL_DEFAULT = "all-MiniLM-L6-v2"

# Select actual models based on provider choice
if LLM_PROVIDER_DEFAULT == "openrouter" and OPENROUTER_API_KEY:
    LLM_API_KEY_ACTIVE = OPENROUTER_API_KEY
    LLM_API_BASE_ACTIVE = OPENROUTER_API_BASE
    LLM_MODEL_ACTIVE = LLM_MODEL_DEFAULT_OPENROUTER
elif LLM_PROVIDER_DEFAULT == "openai" and OPENAI_API_KEY:
    LLM_API_KEY_ACTIVE = OPENAI_API_KEY
    LLM_API_BASE_ACTIVE = None # OpenAI client handles this
    LLM_MODEL_ACTIVE = LLM_MODEL_DEFAULT_OPENAI
else:
    # Fallback or warning if no provider is properly configured
    LLM_API_KEY_ACTIVE = None
    LLM_API_BASE_ACTIVE = None
    LLM_MODEL_ACTIVE = None
    print("Warning: LLM_PROVIDER_DEFAULT is not set or API key for the chosen provider is missing.")
    print("LLM functionality will be mocked or unavailable.")


# Embedding model selection
if EMBEDDING_PROVIDER_DEFAULT == "openai" and OPENAI_API_KEY:
    EMBEDDING_MODEL_ACTIVE = EMBEDDING_MODEL_DEFAULT_OPENAI
elif EMBEDDING_PROVIDER_DEFAULT == "sentence_transformers":
    EMBEDDING_MODEL_ACTIVE = SENTENCE_TRANSFORMER_MODEL_DEFAULT
else:
    EMBEDDING_MODEL_ACTIVE = None # Or a default mock
    print("Warning: Embedding provider not properly configured. Embeddings might be mocked.")

# For site_url when using OpenRouter with openai python client
# It's good to set your site URL or app name.
# See: https://openrouter.ai/docs#sdks
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "http://localhost:8000") # Or your app's URL
OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "AI-KB-Workflow")