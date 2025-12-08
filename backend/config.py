"""Application configuration."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    openai_api_key: str
    chroma_db_path: str = "./chroma_db"
    environment: str = "development"

    # Embedding config
    embedding_model: str = "text-embedding-3-large"
    embedding_dimensions: int = 3072

    # LLM config
    llm_model: str = "gpt-4-turbo-preview"
    llm_temperature: float = 0.0

    # Retrieval config
    top_k_retrieval: int = 5
    semantic_weight: float = 0.7
    keyword_weight: float = 0.3

    # Common questions (demonstrating DATABASE, RAG, and HYBRID queries with natural language)
    common_questions: list = [
        # DATABASE queries (structured data, 100% accurate) - Using natural section names
        {"question": "How many indicators are in the Legal section?", "category": "Database_Count"},
        {"question": "List all indicators for Title VI", "category": "Database_List"},
        {"question": "What are the Charter Bus compliance requirements?", "category": "Database_Structured"},

        # RAG queries (conceptual/contextual questions)
        {"question": "What are ADA paratransit eligibility requirements?", "category": "ADA_Conceptual"},
        {"question": "What is the purpose of the DBE program?", "category": "DBE_Conceptual"},
        {"question": "Explain procurement methods for transit agencies", "category": "Procurement_Conceptual"},

        # HYBRID queries (multi-section or aggregate)
        {"question": "How many deficiencies are in the Financial Management section?", "category": "Hybrid_Aggregate"},
        {"question": "How many total indicators are there in the compliance guide?", "category": "Hybrid_Total"},
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
