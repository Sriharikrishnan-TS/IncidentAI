"""LLM Factory module for IncidentOS AI Engine using Groq / LangChain."""

import os
import logging
from typing import Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def get_llm(model_name: str | None = None, temperature: float = 0.2) -> Any:
    """Get initialized ChatGroq LLM instance.
    
    Args:
        model_name: Optional override for model name (defaults to llama-3.3-70b-versatile)
        temperature: Sampling temperature (default 0.2 for deterministic code reasoning)
        
    Returns:
        ChatGroq model instance or mock LLM if key is missing
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    selected_model = model_name or os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    
    if groq_api_key and groq_api_key != "gsk_test":
        try:
            from langchain_groq import ChatGroq
            logger.info(f"Initializing ChatGroq LLM with model: {selected_model}")
            return ChatGroq(
                model=selected_model,
                groq_api_key=groq_api_key,
                temperature=temperature,
                max_retries=3
            )
        except Exception as e:
            logger.warning(f"Failed to initialize ChatGroq ({e}). Falling back to mock LLM mode.")
    else:
        logger.info("GROQ_API_KEY not configured. Running in local mock LLM mode.")
        
    return None
