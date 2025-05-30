from langchain.schema import HumanMessage, AIMessage
from langchain.llms.base import LLM
from langchain_openai import ChatOpenAI
from typing import Any, List, Mapping, Optional, Dict
import os

from ..utils.config import get_config
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

def load_llm() -> Any:
    """Set up OpenAI GPT-3.5-turbo language model for tool calling."""
    config_data = get_config()
    llm_config = config_data.get('llm', {})
    
    # Ensure we're using OpenAI
    provider = llm_config.get('provider', 'openai').lower()
    if provider != 'openai':
        logger.warning(f"Configuration specifies provider '{provider}', but this system exclusively uses OpenAI. Using OpenAI instead.")
    
    try:
        # Check for OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY') or llm_config.get('openai_api_key')
        if not api_key:
            logger.error("No OpenAI API key found. Please set OPENAI_API_KEY environment variable.")
            return None
        
        # Use GPT-3.5-turbo exclusively
        model_name = "gpt-3.5-turbo"
        temperature = llm_config.get('temperature', 0.1)
        
        logger.info(f"Loading OpenAI model: {model_name}")
        
        llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=api_key,
            model_kwargs={}
        )
        
        logger.info(f"OpenAI {model_name} loaded successfully.")
        return llm
        
    except ImportError:
        logger.error("langchain-openai not installed. Install with 'pip install langchain-openai'")
        return None
    except Exception as e:
        logger.error(f"Error loading OpenAI model: {e}", exc_info=True)
        return None

if __name__ == '__main__':
    from ..utils.logging_config import setup_logging
    setup_logging()
    
    print("\n--- Testing OpenAI LLM Loader ---")
    
    llm_instance = load_llm()
    if llm_instance:
        print(f"LLM Instance type: {type(llm_instance)}")
        print(f"Model: GPT-3.5-turbo")
        
        test_prompt = "What is the main purpose of a solar panel?"
        print(f"Test Prompt: {test_prompt}")
        
        try:
            response = llm_instance.invoke(test_prompt)
            print(f"Response from LLM:\n{response.content if hasattr(response, 'content') else response}")
        except Exception as e:
            print(f"Error invoking LLM: {e}")
    else:
        print("Failed to load OpenAI LLM. Check configuration and API keys.") 