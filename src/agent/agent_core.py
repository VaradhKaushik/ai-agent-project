import re
from typing import Dict, List, Any, Optional, Literal

from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage
from langchain.tools import BaseTool

from ..llm.llm_loader import load_llm
from ..tools import (
    # Original tools
    future_weather, solar_yield, cost_model, transmission_cost, grid_connection_info,
    # New API tools
    web_search, nrel_solar_data, openweathermap_data, geocode_location, 
    energy_news_search, real_solar_calculator, market_analysis_search,
    get_enhanced_tools
)
from ..rag.rag_pipeline import get_rag_context
from ..utils.config import get_config
from ..utils.logging_config import get_logger

logger = get_logger(__name__)
config = get_config()

class SolarFeasibilityAgent:
    """True LLM-driven agent for solar feasibility analysis using tool calling."""
    
    def __init__(self):
        """Initialize the agent with LLM and tools."""
        self.llm = load_llm()
        if not self.llm:
            raise RuntimeError("Failed to load LLM. Please check configuration and API keys.")
        
        # Get all available tools
        self.tools = get_enhanced_tools()
        logger.info(f"Loaded {len(self.tools)} tools for agent: {[tool.name for tool in self.tools]}")
        
        # Create the agent prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create the agent
        try:
            self.agent = create_openai_tools_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=self.prompt
            )
            
            # Create the agent executor
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=True,
                max_iterations=10,
                early_stopping_method="generate"
            )
            
            logger.info("LLM Agent with tool calling initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to create agent: {e}", exc_info=True)
            raise RuntimeError(f"Failed to create agent: {e}")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent."""
        return """You are an expert solar energy consultant with access to specialized tools for analyzing solar projects.

Your role is to provide comprehensive feasibility analysis for solar energy projects by intelligently using the available tools.

APPROACH:
1. Analyze the user's query to understand what information they need
2. Use the appropriate tools to gather relevant data:
   - For locations: Use geocode_location to find coordinates, then get solar and weather data
   - For solar analysis: Use nrel_solar_data and real_solar_calculator for accurate estimates
   - For market info: Use market_analysis_search and energy_news_search
   - For costs: Use cost_model for financial estimates
   - For weather: Use openweathermap_data for current conditions
   - For research: Use web_search for general information

3. Provide a comprehensive analysis based on the data you collect

FORMAT YOUR RESPONSE:
**FEASIBILITY ANALYSIS**

**Location & Solar Resource:**
[Location details and solar potential]

**Technical Assessment:**
[Production estimates, system specifications]

**Financial Analysis:**
[Capital costs, operating costs, payback period]

**Market Conditions:**
[Relevant market information and incentives]

**Recommendation:**
[Clear recommendation with next steps]

Be thorough but concise. Always base your analysis on actual data from the tools."""

    def analyze(self, query: str) -> str:
        """Analyze a solar project query using LLM tool calling."""
        logger.info(f"Starting LLM-driven analysis for query: {query}")
        
        try:
            # Let the LLM decide which tools to call and how to use them
            result = self.agent_executor.invoke({"input": query})
            
            # Extract the final output
            final_response = result.get("output", "Unable to complete analysis.")
            
            logger.info(f"LLM analysis completed successfully. Response length: {len(final_response)}")
            return final_response
            
        except Exception as e:
            logger.error(f"Error during LLM analysis: {e}", exc_info=True)
            return f"Error during analysis: {str(e)}. Please check your API configuration and try again."

    def get_rag_context(self, query: str) -> str:
        """Get RAG context for knowledge-based queries."""
        try:
            return get_rag_context(query)
        except Exception as e:
            logger.error(f"Error getting RAG context: {e}")
            return "No additional context available."

# Convenience function for standalone execution
def run_solar_agent_from_query(query: str) -> str:
    """
    Initialize and run the SolarFeasibilityAgent for a single query.
    """
    try:
        agent = SolarFeasibilityAgent()
        return agent.analyze(query)
    except Exception as e:
        logger.error(f"Failed to run solar agent: {e}", exc_info=True)
        return f"Failed to initialize agent: {str(e)}"

if __name__ == '__main__':
    # Test the agent
    from ..utils.logging_config import setup_logging
    setup_logging()

    logger.info("--- Testing True LLM Tool Calling Agent ---")
    
    try:
        test_agent = SolarFeasibilityAgent()
        
        test_queries = [
            "What's the solar potential for a 25MW project in Austin, Texas?",
            "Analyze the feasibility of a 50MW solar farm at coordinates 33.4484, -112.0741",
            "What are the latest solar energy market trends and incentives?",
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*80}")
            print(f"Test Query {i}: {query}")
            print('='*80)
            
            response = test_agent.analyze(query)
            print(f"Agent Response:\n{response}")
            
            if i < len(test_queries):
                input("\nPress Enter to continue to next test...")
                
    except Exception as e:
        print(f"Failed to test agent: {e}")
        print("Make sure you have:")
        print("1. Set OPENAI_API_KEY environment variable")
        print("2. Installed langchain-openai: pip install langchain-openai")
        print("3. Valid OpenAI API access") 