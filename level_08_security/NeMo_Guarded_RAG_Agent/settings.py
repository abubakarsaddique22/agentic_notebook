from pathlib import Path  # Project-independent paths manage karta hai.
from pydantic_settings import BaseSettings, SettingsConfigDict  # .env se typed configuration.
ROOT = Path(__file__).resolve().parent
class Settings(BaseSettings):
    ollama_model: str = "gpt-oss:20b-cloud"  # Cloud LLM ka model name.
    embedding_model: str = "nomic-embed-text"  # Local embedding model.
    ollama_base_url: str = "http://127.0.0.1:11434"  # Ollama API endpoint.
    chroma_dir: str = str(ROOT / ".chroma")  # Persistent vector database path.
    top_k: int = 3  # Retrieval ke maximum chunks.
    model_config = SettingsConfigDict(env_file=str(ROOT / '.env'), extra='ignore')
settings = Settings()
