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

    # Common questions
    common_questions: list = [
        {"question": "What are ADA paratransit eligibility requirements?", "category": "ADA_Complementary_Paratransit"},
        {"question": "What are the DBE program requirements?", "category": "Disadvantaged_Business_Enterprise"},
        {"question": "What are Title VI compliance obligations?", "category": "Title_VI"},
        {"question": "What procurement methods are allowed?", "category": "Procurement"},
        {"question": "What are the financial management requirements?", "category": "Financial_Management_and_Capacity"},
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
