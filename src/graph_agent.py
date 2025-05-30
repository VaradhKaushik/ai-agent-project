"""
Site Feasibility Agent using LangChain Graph
Orchestrates tools and RAG pipeline to answer site feasibility queries.
"""

import os
import re
from typing import Dict, List, Any, Optional, Literal
from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, AIMessage

# Import our custom modules
from tools import (
    future_weather, solar_yield, cost_model, 
    transmission_cost, grid_connection_info
)
from rag import get_rag_context


class SiteFeasibilityAgent:
    """Main agent for site feasibility analysis."""
    
    def __init__(self, use_ollama: bool = True):
        """
        Initialize the site feasibility agent.
        
        Args:
            use_ollama: Whether to use Ollama (True) or mock LLM (False)
        """
        self.use_ollama = use_ollama
        self.llm = self._setup_llm()
        
    def _setup_llm(self):
        """Set up the language model (Ollama or mock)."""
        if self.use_ollama:
            try:
                llm = ChatOllama(
                    model="mistral:7b-instruct-q4_K_M",
                    temperature=0.2,
                    base_url="http://localhost:11434"
                )
                # Test connection
                test_response = llm.invoke([HumanMessage(content="Hello")])
                print("✅ Connected to Ollama successfully")
                return llm
            except Exception as e:
                print(f"⚠️  Could not connect to Ollama: {e}")
                print("📝 Using mock LLM instead")
                return self._mock_llm
        else:
            print("📝 Using mock LLM")
            return self._mock_llm
            
    def _mock_llm(self, messages):
        """Mock LLM for testing without Ollama."""
        if isinstance(messages, list):
            content = messages[-1].content if messages else ""
        else:
            content = str(messages)
            
        return AIMessage(content=f"Mock response analyzing: {content[:200]}...")

    def _extract_coordinates(self, text: str) -> Optional[tuple]:
        """Extract latitude and longitude from text."""
        # Look for patterns like "37.2 N, -121.9 W" or "37.2, -121.9"
        coord_patterns = [
            r'(-?\d+\.?\d*)\s*[°]?\s*[NnSs]?,?\s*(-?\d+\.?\d*)\s*[°]?\s*[WwEe]?',
            r'(-?\d+\.?\d*),\s*(-?\d+\.?\d*)'
        ]
        
        for pattern in coord_patterns:
            match = re.search(pattern, text)
            if match:
                lat, lon = float(match.group(1)), float(match.group(2))
                # Ensure proper signs for lat/lon
                if 'S' in text.upper() or 's' in text:
                    lat = -abs(lat)
                if 'W' in text.upper() or 'w' in text:
                    lon = -abs(lon)
                return lat, lon
        return None

    def _extract_capacity(self, text: str) -> float:
        """Extract capacity in MW from text."""
        capacity_pattern = r'(\d+\.?\d*)\s*MW'
        match = re.search(capacity_pattern, text, re.IGNORECASE)
        return float(match.group(1)) if match else 20.0  # Default 20 MW

    def route_query(self, query: str) -> Literal["feasibility_analysis", "transmission_analysis", "rag_query", "general_query"]:
        """Route the query to appropriate tools based on content."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["feasible", "feasibility", "build", "solar farm", "solar project"]):
            return "feasibility_analysis"
        elif any(word in query_lower for word in ["cost", "deliver", "transmission", "send power"]):
            return "transmission_analysis"
        elif any(word in query_lower for word in ["grid", "interconnection", "caiso", "california iso"]):
            return "rag_query"
        else:
            return "general_query"

    def feasibility_analysis(self, query: str) -> Dict[str, Any]:
        """Perform comprehensive feasibility analysis."""
        # Extract coordinates and capacity
        coords = self._extract_coordinates(query)
        capacity_mw = self._extract_capacity(query)
        
        if not coords:
            return {
                "error": "Could not extract coordinates from query",
                "tool_results": {}
            }
            
        lat, lon = coords
        
        # Call all relevant tools
        try:
            weather_data = future_weather.func(lat, lon)
            annual_yield = solar_yield.func(lat, lon, capacity_mw)
            capex, opex = cost_model.func(capacity_mw)
            grid_info = grid_connection_info.func(lat, lon)
            
            tool_results = {
                "coordinates": f"{lat}, {lon}",
                "capacity_mw": capacity_mw,
                "weather_data": weather_data,
                "annual_yield_mwh": annual_yield,
                "capex_millions": capex,
                "opex_millions_per_year": opex,
                "grid_connection": grid_info
            }
            
            return {"tool_results": tool_results}
            
        except Exception as e:
            return {
                "error": f"Error in feasibility analysis: {e}",
                "tool_results": {}
            }

    def transmission_analysis(self, query: str) -> Dict[str, Any]:
        """Analyze transmission costs to destination."""
        # Try to extract both source and destination coordinates
        coords_matches = list(re.finditer(r'(-?\d+\.?\d*)\s*[°]?\s*[NnSs]?,?\s*(-?\d+\.?\d*)\s*[°]?\s*[WwEe]?', query))
        
        if len(coords_matches) < 2:
            # Use default source from previous analysis or assume
            src_lat, src_lon = 37.2, -121.9  # Default location
            # Try to find destination
            dest_coords = self._extract_coordinates(query)
            if dest_coords:
                dst_lat, dst_lon = dest_coords
            else:
                # Default to San Jose
                dst_lat, dst_lon = 37.3, -122.0
        else:
            src_lat, src_lon = float(coords_matches[0].group(1)), float(coords_matches[0].group(2))
            dst_lat, dst_lon = float(coords_matches[1].group(1)), float(coords_matches[1].group(2))
        
        # Get capacity and annual yield
        capacity_mw = self._extract_capacity(query)
        annual_yield = solar_yield.func(src_lat, src_lon, capacity_mw)
        
        try:
            trans_cost = transmission_cost.func(src_lat, src_lon, dst_lat, dst_lon, annual_yield)
            
            tool_results = {
                "source_coords": f"{src_lat}, {src_lon}",
                "destination_coords": f"{dst_lat}, {dst_lon}",
                "capacity_mw": capacity_mw,
                "annual_yield_mwh": annual_yield,
                "transmission_cost_per_year": trans_cost
            }
            
            return {"tool_results": tool_results}
            
        except Exception as e:
            return {
                "error": f"Error in transmission analysis: {e}",
                "tool_results": {}
            }

    def rag_query(self, query: str) -> Dict[str, Any]:
        """Query the RAG pipeline for contextual information."""
        try:
            rag_context = get_rag_context(query)
            
            tool_results = {
                "rag_context": rag_context,
                "query_type": "knowledge_base"
            }
            
            return {"tool_results": tool_results}
            
        except Exception as e:
            return {
                "error": f"Error in RAG query: {e}",
                "tool_results": {}
            }

    def general_query(self, query: str) -> Dict[str, Any]:
        """Handle general queries with RAG context."""
        return self.rag_query(query)

    def generate_response(self, query: str, tool_results: Dict[str, Any], error: Optional[str] = None) -> str:
        """Generate final response using LLM."""
        if error:
            return f"Error: {error}"
        
        # Create prompt based on available tool results
        if "annual_yield_mwh" in tool_results:
            # Feasibility analysis
            prompt = f"""
            Based on the following solar project analysis data, provide a comprehensive feasibility assessment:
            
            Query: {query}
            
            Project Details:
            - Location: {tool_results.get('coordinates', 'N/A')}
            - Capacity: {tool_results.get('capacity_mw', 'N/A')} MW
            - Annual Energy Production: {tool_results.get('annual_yield_mwh', 'N/A'):,.0f} MWh/year
            - Capital Expenditure: ${tool_results.get('capex_millions', 'N/A')} million
            - Operating Expenditure: ${tool_results.get('opex_millions_per_year', 'N/A')} million/year
            - Grid Connection: {tool_results.get('grid_connection', 'N/A')}
            
            Weather Data:
            {tool_results.get('weather_data', 'N/A')}
            
            Please provide a detailed feasibility assessment including:
            1. Technical feasibility (solar resource quality, grid connection)
            2. Economic analysis (ROI, payback period estimates)
            3. Key considerations and recommendations
            """
            
        elif "transmission_cost_per_year" in tool_results:
            # Transmission analysis
            prompt = f"""
            Based on the following transmission cost analysis, provide a detailed assessment:
            
            Query: {query}
            
            Transmission Analysis:
            - Source: {tool_results.get('source_coords', 'N/A')}
            - Destination: {tool_results.get('destination_coords', 'N/A')}
            - Project Capacity: {tool_results.get('capacity_mw', 'N/A')} MW
            - Annual Energy: {tool_results.get('annual_yield_mwh', 'N/A'):,.0f} MWh/year
            - Annual Transmission Cost: ${tool_results.get('transmission_cost_per_year', 'N/A'):,.0f}
            
            Please analyze the transmission costs and delivery feasibility.
            """
            
        elif "rag_context" in tool_results:
            # RAG-based query
            prompt = f"""
            Based on the following context from the California ISO knowledge base, answer the user's question:
            
            Query: {query}
            
            Relevant Context:
            {tool_results.get('rag_context', 'N/A')}
            
            Please provide a comprehensive answer citing the relevant information.
            """
            
        else:
            prompt = f"Please answer the following query: {query}"
        
        try:
            if self.use_ollama and hasattr(self.llm, 'invoke'):
                response = self.llm.invoke([HumanMessage(content=prompt)])
                response_text = response.content
            else:
                response_text = self._mock_llm([HumanMessage(content=prompt)]).content
            
            return response_text
            
        except Exception as e:
            return f"Error generating response: {e}"

    def run(self, query: str) -> Dict[str, Any]:
        """Run the agent on a query using simplified workflow."""
        # Step 1: Route the query
        route = self.route_query(query)
        
        # Step 2: Execute appropriate analysis
        if route == "feasibility_analysis":
            result = self.feasibility_analysis(query)
        elif route == "transmission_analysis":
            result = self.transmission_analysis(query)
        elif route == "rag_query":
            result = self.rag_query(query)
        else:
            result = self.general_query(query)
        
        # Step 3: Generate response
        tool_results = result.get("tool_results", {})
        error = result.get("error")
        response = self.generate_response(query, tool_results, error)
        
        return {
            "query": query,
            "route": route,
            "tool_results": tool_results,
            "error": error,
            "response": response
        }


# Initialize global agent
print("Initializing Site Feasibility Agent...")
try:
    SITE_AGENT = SiteFeasibilityAgent(use_ollama=True)
    print("✅ Site Feasibility Agent initialized successfully")
except Exception as e:
    print(f"⚠️  Error initializing agent: {e}")
    print("🔄 Falling back to mock mode")
    SITE_AGENT = SiteFeasibilityAgent(use_ollama=False)


def run_site_agent(query: str) -> str:
    """
    Convenience function to run the site agent.
    
    Args:
        query: User query string
        
    Returns:
        Agent response string
    """
    if isinstance(query, dict) and "prompt" in query:
        query = query["prompt"]
    
    result = SITE_AGENT.run(query)
    return result.get("response", "No response generated")


def main():
    """Interactive main function for testing."""
    print("\n" + "="*60)
    print("🌞 Site Feasibility Agent - Interactive Mode")
    print("="*60)
    print("Ask questions about solar farm feasibility and transmission costs!")
    print("Type 'quit' to exit.\n")
    
    example_queries = [
        "Is it feasible to build a 20 MW solar farm at 37.2 N, -121.9 W?",
        "What would it cost to deliver that power to San José, CA (37.3 N, -122.0 W)?",
        "Tell me about California ISO interconnection queue",
        "What are typical LCOE values for solar projects?"
    ]
    
    print("Example queries:")
    for i, q in enumerate(example_queries, 1):
        print(f"{i}. {q}")
    print()
    
    while True:
        try:
            user_input = input("🤔 Your question: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            if not user_input:
                continue
                
            print(f"\n🔍 Processing: {user_input}")
            print("-" * 40)
            
            response = run_site_agent(user_input)
            print(f"🤖 Agent Response:\n{response}\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")


if __name__ == "__main__":
    # Test with example queries
    test_queries = [
        "Is it feasible to build a 20 MW solar farm at 37.2 N, -121.9 W?",
        "How much would it cost to deliver that power to San José, CA (37.3 N, -122.0 W)?"
    ]
    
    print("\n🧪 Testing with example queries:")
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"Query: {query}")
        print('='*50)
        response = run_site_agent(query)
        print(f"Response: {response}\n")
    
    # Start interactive mode
    main() 