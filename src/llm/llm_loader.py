from langchain.schema import HumanMessage, AIMessage # LLMResult no longer needed here
from langchain.llms.base import LLM # For custom LLM wrapper
from typing import Any, List, Mapping, Optional, Dict # Removed ChatOllama import

from utils.config import get_config
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Custom HuggingFace Pipeline LLM Wrapper (simplified)
class HuggingFacePipelineLLM(LLM):
    pipeline: Any # Transformers pipeline
    model_id: str

    def __init__(self, pipeline: Any, model_id: str):
        super().__init__(model_id=model_id)
        self.pipeline = pipeline
        self.model_id = model_id

    @property
    def _llm_type(self) -> str:
        return f"huggingface_pipeline_{self.model_id}"

    def _call(
        self, 
        prompt: str, 
        stop: Optional[List[str]] = None, 
        **kwargs: Any
    ) -> str:
        logger.debug(f"HuggingFacePipelineLLM invoking with prompt (first 100 chars): {prompt[:100]}")
        try:
            generated_outputs = self.pipeline(prompt, max_new_tokens=kwargs.get("max_new_tokens", 250), do_sample=True, temperature=kwargs.get("temperature", 0.7), top_k=kwargs.get("top_k",50) )
            if generated_outputs and isinstance(generated_outputs, list) and "generated_text" in generated_outputs[0]:
                full_text = generated_outputs[0]["generated_text"]
                if full_text.startswith(prompt):
                    response_text = full_text[len(prompt):].strip()
                else:
                    response_text = full_text.strip()
                logger.debug(f"HuggingFacePipelineLLM got response (first 100 chars): {response_text[:100]}")
                return response_text
            else:
                logger.warning(f"HuggingFace pipeline did not return expected output format: {generated_outputs}")
                return "Error: LLM did not return expected output."
        except Exception as e:
            logger.error(f"Error during HuggingFace pipeline call: {e}", exc_info=True)
            return f"Error: Exception during LLM call - {e}"
            
    def invoke(self, input: Any, stop: Optional[List[str]] = None, **kwargs: Any) -> AIMessage:
        prompt_text = ""
        if isinstance(input, str):
            prompt_text = input
        elif isinstance(input, list) and input and isinstance(input[-1], HumanMessage):
            prompt_text = input[-1].content
        else:
            prompt_text = str(input) # Best guess
        
        response_content = self._call(prompt_text, stop=stop, **kwargs)
        return AIMessage(content=response_content)

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {"model_id": self.model_id, "pipeline_type": self.pipeline.task}

class MockLLM:
    """Mock LLM class that mimics the interface of a real LLM."""
    
    def invoke(self, input: Any, **kwargs: Any) -> AIMessage:
        """Mock invoke method that returns a detailed response showing all tool data."""
        content = ""
        if isinstance(input, str):
            content = input
        elif isinstance(input, list) and input and hasattr(input[-1], 'content'):
            content = input[-1].content
        else:
            content = str(input)
        
        logger.info(f"Mock LLM received: {content[:100]}...")
        
        # Extract and display the PROJECT DATA section clearly
        if "PROJECT DATA:" in content:
            project_data_start = content.find("PROJECT DATA:")
            project_data_end = content.find("ANALYSIS REQUIREMENTS:")
            if project_data_end == -1:
                project_data_section = content[project_data_start:]
            else:
                project_data_section = content[project_data_start:project_data_end].strip()
            
            response = f"""**FEASIBILITY: FEASIBLE (Mock Analysis)**

**Mock LLM Analysis:**
This is a mock response showing the tool data that was gathered:

{project_data_section}

**Mock Recommendation:**
Based on the tool data above, this would be analyzed by a real LLM to provide detailed feasibility assessment, financial analysis, technical evaluation, and recommendations."""
        else:
            response = f"Mock LLM Response: Received prompt of {len(content)} characters. Content preview: {content[:500]}..."
            
        return AIMessage(content=response)
    
    @property
    def _llm_type(self) -> str:
        return "mock_llm"

def _mock_llm(messages_or_prompt: Any) -> AIMessage:
    """Mock LLM for testing when other providers fail or are not configured."""
    content = ""
    if isinstance(messages_or_prompt, list):
        content = messages_or_prompt[-1].content if messages_or_prompt and hasattr(messages_or_prompt[-1], 'content') else str(messages_or_prompt)
    else:
        content = str(messages_or_prompt)
    
    logger.info(f"Mock LLM received: {content[:50]}...")
    return AIMessage(content=f"Mock response analyzing: {content[:200]}...")

def load_llm() -> Any: # Return type can be HuggingFacePipelineLLM or the mock function
    """Set up the language model based on configuration."""
    config_data = get_config()
    llm_config = config_data.get('llm', {})
    provider = llm_config.get('provider', 'huggingface').lower() # Default to huggingface if not specified

    if provider == "huggingface":
        try:
            from transformers import pipeline
            import torch

            model_id = llm_config.get('huggingface_model_id', 'distilgpt2')
            task = llm_config.get('huggingface_task', 'text-generation')
            # temperature is passed via **kwargs in _call if needed by pipeline
            
            logger.info(f"Loading Hugging Face model: {model_id} for task: {task}")
            
            device = 0 if torch.cuda.is_available() else -1 
            if device == 0:
                logger.info(f"CUDA available. Using GPU for Hugging Face model: {model_id}.")
            else:
                logger.info(f"CUDA not available. Using CPU for Hugging Face model: {model_id}. This might be slow.")

            hf_pipeline = pipeline(task, model=model_id, device=device, trust_remote_code=True)
            logger.info(f"Hugging Face pipeline for {model_id} loaded successfully.")
            
            # Test the pipeline
            test_output = hf_pipeline("Hello!", max_new_tokens=10) # Using max_new_tokens for testing
            logger.info(f"Hugging Face pipeline test output: {test_output}")

            return HuggingFacePipelineLLM(pipeline=hf_pipeline, model_id=model_id)

        except ImportError:
            logger.error("Transformers or PyTorch library not found. Please install them with 'pip install transformers torch'.")
            logger.info("Falling back to mock LLM due to missing libraries.")
            return MockLLM() # Return the MockLLM instance instead of function
        except Exception as e:
            logger.error(f"Error loading Hugging Face model '{model_id}': {e}", exc_info=True)
            logger.info("Falling back to mock LLM due to Hugging Face model loading error.")
            return MockLLM()
            
    # Default to mock if provider is "mock" or not recognized
    logger.info(f"LLM provider set to '{provider}'. Using mock LLM.")
    return MockLLM()

if __name__ == '__main__':
    from src.utils.logging_config import setup_logging
    setup_logging()
    
    print("\n--- Testing LLM Loader ---")
    # To test, ensure `provider: "huggingface"` or `provider: "mock"` in config.yaml
    
    llm_instance = load_llm()
    print(f"LLM Instance type: {type(llm_instance)}")

    test_prompt = "What is the main purpose of a solar panel?"
    print(f"Test Prompt: {test_prompt}")

    if isinstance(llm_instance, MockLLM):
        response_obj = llm_instance.invoke(test_prompt)
        print(f"Response from Mock LLM: {response_obj.content}")
    elif hasattr(llm_instance, 'invoke'):
        try:
            response_obj = llm_instance.invoke(test_prompt, temperature=get_config().get('llm',{}).get('temperature', 0.7))
            print(f"Response from LLM ({llm_instance._llm_type}):\n{response_obj.content}")
        except Exception as e:
            print(f"Error invoking LLM: {e}", exc_info=True)
    else:
        print("Failed to load a recognizable LLM instance or mock.") 