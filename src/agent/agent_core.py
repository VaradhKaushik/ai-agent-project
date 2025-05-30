import re
from typing import Dict, List, Any, Optional, Literal

from llm.llm_loader import load_llm
from tools import future_weather, solar_yield, cost_model, transmission_cost, grid_connection_info
from rag.rag_pipeline import get_rag_context
from utils.config import get_config
from utils.logging_config import get_logger

logger = get_logger(__name__)
config = get_config()
tool_config = config.get('tools', {})

class SiteFeasibilityAgent:
    """Main agent for site feasibility analysis."""
    
    def __init__(self):
        """Initialize the site feasibility agent."""
        self.llm = load_llm()
        
    def _extract_coordinates(self, text: str) -> Optional[tuple]:
        """Extract latitude and longitude from text."""
        coord_patterns = [
            r'(-?\d+\.?\d*)\s*[°]?\s*[NnSs]?,?\s*(-?\d+\.?\d*)\s*[°]?\s*[WwEe]?',
            r'(-?\d+\.?\d*),\s*(-?\d+\.?\d*)'
        ]
        
        for pattern in coord_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    lat_str, lon_str = match.group(1), match.group(2)
                    lat = float(lat_str)
                    lon = float(lon_str)

                    # Adjust for N/S/E/W designators if present in the broader text matching the pattern
                    matched_text = match.group(0)
                    if 'S' in matched_text.upper() or 's' in matched_text: # Check within the matched part
                        lat = -abs(lat)
                    if 'W' in matched_text.upper() or 'w' in matched_text: # Check within the matched part
                        lon = -abs(lon)
                    
                    logger.debug(f"Extracted coordinates: ({lat}, {lon}) from text: '{text}' using pattern: '{pattern}'")
                    return lat, lon
                except ValueError:
                    logger.warning(f"Could not convert extracted coordinates to float: {lat_str}, {lon_str}")
                    continue # Try next pattern
        logger.info(f"Could not extract coordinates from text: '{text}'")
        return None

    def _extract_capacity(self, text: str) -> float:
        """Extract capacity in MW from text."""
        capacity_pattern = r'(\d+\.?\d*)\s*MW'
        match = re.search(capacity_pattern, text, re.IGNORECASE)
        if match:
            try:
                capacity = float(match.group(1))
                logger.debug(f"Extracted capacity: {capacity} MW from text: '{text}'")
                return capacity
            except ValueError:
                logger.warning(f"Could not convert extracted capacity to float: {match.group(1)}")
        
        default_capacity = tool_config.get('default_capacity_mw', 20.0)
        logger.info(f"Could not extract capacity, using default: {default_capacity} MW")
        return default_capacity

    def route_query(self, query: str) -> Literal["feasibility_analysis", "transmission_analysis", "rag_query", "general_query"]:
        """Route the query to appropriate tools based on content."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["feasible", "feasibility", "build", "solar farm", "solar project"]):
            logger.info("Routing query to feasibility_analysis")
            return "feasibility_analysis"
        elif any(word in query_lower for word in ["cost", "deliver", "transmission", "send power"]):
            logger.info("Routing query to transmission_analysis")
            return "transmission_analysis"
        elif any(word in query_lower for word in ["grid", "interconnection", "caiso", "california iso", "tell me about", "what is", "explain"]):
            # Broader RAG trigger words
            logger.info("Routing query to rag_query")
            return "rag_query"
        else:
            logger.info("Routing query to general_query (will use RAG)")
            return "general_query"

    def feasibility_analysis(self, query: str) -> Dict[str, Any]:
        """Perform comprehensive feasibility analysis."""
        logger.info(f"Performing feasibility analysis for query: {query}")
        coords = self._extract_coordinates(query)
        capacity_mw = self._extract_capacity(query)
        
        if not coords:
            error_msg = "Could not extract coordinates from query for feasibility analysis."
            logger.error(error_msg)
            return {
                "error": error_msg,
                "tool_results": {}
            }
            
        lat, lon = coords
        
        tool_results = {
            "coordinates": f"{lat}, {lon}",
            "capacity_mw": capacity_mw,
        }
        
        try:
            logger.debug(f"Calling weather tool for {lat}, {lon}")
            tool_results["weather_data"] = future_weather.func(lat=lat, lon=lon)
            
            logger.debug(f"Calling solar yield tool for {lat}, {lon}, {capacity_mw} MW")
            tool_results["annual_yield_mwh"] = solar_yield.func(lat=lat, lon=lon, ac_mw=capacity_mw)
            
            logger.debug(f"Calling cost model tool for {capacity_mw} MW")
            capex, opex = cost_model.func(ac_mw=capacity_mw)
            tool_results["capex_millions"] = capex
            tool_results["opex_millions_per_year"] = opex
            
            logger.debug(f"Calling grid connection info tool for {lat}, {lon}")
            tool_results["grid_connection"] = grid_connection_info.func(lat=lat, lon=lon)
            
            logger.info(f"Feasibility analysis successful for query: {query}")
            return {"tool_results": tool_results}
            
        except Exception as e:
            error_msg = f"Error during feasibility analysis tool execution: {e}"
            logger.error(error_msg, exc_info=True)
            return {
                "error": error_msg,
                "tool_results": tool_results # Return partial results if any
            }

    def transmission_analysis(self, query: str) -> Dict[str, Any]:
        """Analyze transmission costs to destination."""
        logger.info(f"Performing transmission analysis for query: {query}")
        
        # Try to extract both source and destination coordinates
        # This regex is simplified; a more robust parser might be needed for complex queries
        coord_matches = list(re.finditer(r'(-?\d+\.?\d*\s*[NnSs]?)[,\s]+(-?\d+\.?\d*\s*[WwEe]?)', query))
        
        src_lat, src_lon, dst_lat, dst_lon = None, None, None, None

        if len(coord_matches) >= 2:
            # Assuming first match is source, second is destination
            logger.debug(f"Found {len(coord_matches)} coordinate pairs. Attempting to parse source and destination.")
            coords1 = self._extract_coordinates(coord_matches[0].group(0))
            coords2 = self._extract_coordinates(coord_matches[1].group(0))
            if coords1 and coords2:
                src_lat, src_lon = coords1
                dst_lat, dst_lon = coords2
                logger.info(f"Using extracted source ({src_lat},{src_lon}) and destination ({dst_lat},{dst_lon})")
        
        if not (src_lat and dst_lat): # If we couldn't get both from the query
            logger.debug("Could not parse src/dst from query reliably. Using defaults or single extraction.")
            # Attempt to get at least one coordinate pair (likely the source or the site of interest)
            primary_coords = self._extract_coordinates(query)
            if primary_coords:
                src_lat, src_lon = primary_coords
                logger.info(f"Using primary extracted coords as source: ({src_lat},{src_lon})")
            else:
                src_lat = tool_config.get('default_latitude', 37.2)
                src_lon = tool_config.get('default_longitude', -121.9)
                logger.info(f"No source coords extracted, using default source: ({src_lat},{src_lon})")

            # For destination, if not found, use default (e.g. San Jose from config)
            # This part may need more sophisticated logic to identify destination in query if not paired with source
            # For now, if only one set of coords found in query, assume it's the source, and use default destination
            if len(coord_matches) == 1 and primary_coords: # If query had one coord set, assume it's source
                 dst_lat = tool_config.get('default_target_latitude', 37.3)
                 dst_lon = tool_config.get('default_target_longitude', -122.0)
                 logger.info(f"Using default destination: ({dst_lat},{dst_lon})")
            elif not dst_lat: # if dst_lat is still None
                 # Try to find *any* other coordinate if the primary was set as source
                 # This is a simple attempt, could be made more robust
                 remaining_query_text = query
                 if primary_coords: # remove the part of query that matched primary_coords
                     # this is tricky, simple removal might break things.
                     # A better way would be to parse the query more structurally.
                     # For now, we'll be less aggressive to avoid errors.
                     pass # Not attempting to remove text for now

                 # Try extracting again, hoping it finds the destination if it exists
                 dest_coords_attempt = self._extract_coordinates(remaining_query_text) # this might re-extract source
                 if dest_coords_attempt and dest_coords_attempt != (src_lat, src_lon):
                     dst_lat, dst_lon = dest_coords_attempt
                     logger.info(f"Found potential destination through secondary extraction: ({dst_lat},{dst_lon})")
                 else:
                     dst_lat = tool_config.get('default_target_latitude', 37.3)
                     dst_lon = tool_config.get('default_target_longitude', -122.0)
                     logger.info(f"Using default destination after trying secondary extraction: ({dst_lat},{dst_lon})")
        
        capacity_mw = self._extract_capacity(query)
        
        # Solar yield at source is needed for transmission cost calculation
        logger.debug(f"Calculating solar yield at source ({src_lat}, {src_lon}) for {capacity_mw} MW")
        try:
            annual_yield = solar_yield.func(lat=src_lat, lon=src_lon, ac_mw=capacity_mw)
        except Exception as e:
            error_msg = f"Error calculating solar yield for transmission analysis: {e}"
            logger.error(error_msg, exc_info=True)
            return {"error": error_msg, "tool_results": {}}

        tool_results = {
            "source_coords": f"{src_lat}, {src_lon}",
            "destination_coords": f"{dst_lat}, {dst_lon}",
            "capacity_mw": capacity_mw,
            "annual_yield_mwh_at_source": annual_yield,
        }

        try:
            logger.debug(f"Calling transmission cost tool for src({src_lat},{src_lon}) to dst({dst_lat},{dst_lon}), yield {annual_yield} MWh")
            trans_cost = transmission_cost.func(
                src_lat=src_lat, src_lon=src_lon, 
                dst_lat=dst_lat, dst_lon=dst_lon, 
                mwh_year=annual_yield
            )
            tool_results["transmission_cost_per_year"] = trans_cost
            
            logger.info(f"Transmission analysis successful for query: {query}")
            return {"tool_results": tool_results}
            
        except Exception as e:
            error_msg = f"Error during transmission analysis tool execution: {e}"
            logger.error(error_msg, exc_info=True)
            return {
                "error": error_msg,
                "tool_results": tool_results # Return partial results
            }

    def rag_query_handler(self, query: str) -> Dict[str, Any]: # Renamed from rag_query to avoid conflict
        """Query the RAG pipeline for contextual information."""
        logger.info(f"Performing RAG query: {query}")
        try:
            rag_context = get_rag_context(query)
            
            tool_results = {
                "rag_context": rag_context,
                "query_type": "knowledge_base"
            }
            logger.info(f"RAG query successful, context length: {len(rag_context)}")
            return {"tool_results": tool_results}
            
        except Exception as e:
            error_msg = f"Error in RAG query: {e}"
            logger.error(error_msg, exc_info=True)
            return {
                "error": error_msg,
                "tool_results": {}
            }

    def general_query_handler(self, query: str) -> Dict[str, Any]: # Renamed from general_query
        """Handle general queries, typically by forwarding to RAG."""
        logger.info(f"Handling general query (forwarding to RAG): {query}")
        return self.rag_query_handler(query)

    def _format_tool_results_for_llm(self, tool_results: Dict[str, Any]) -> str:
        """Formats tool results into a string for the LLM prompt."""
        if not tool_results:
            return "No specific tool results were generated."

        formatted_parts = []
        if "annual_yield_mwh" in tool_results: # Indicates feasibility analysis
            formatted_parts.append("Feasibility Analysis Data:")
            formatted_parts.append(f"  - Location: {tool_results.get('coordinates', 'N/A')}")
            formatted_parts.append(f"  - Capacity: {tool_results.get('capacity_mw', 'N/A')} MW")
            formatted_parts.append(f"  - Annual Energy Production: {tool_results.get('annual_yield_mwh', 'N/A'):,.0f} MWh/year" if isinstance(tool_results.get('annual_yield_mwh'), (int,float)) else f"  - Annual Energy Production: {tool_results.get('annual_yield_mwh', 'N/A')}")
            formatted_parts.append(f"  - Capital Expenditure: ${tool_results.get('capex_millions', 'N/A')} million")
            formatted_parts.append(f"  - Operating Expenditure: ${tool_results.get('opex_millions_per_year', 'N/A')} million/year")
            formatted_parts.append(f"  - Grid Connection: {tool_results.get('grid_connection', 'N/A')}")
            if "weather_data" in tool_results:
                formatted_parts.append(f"  - Weather Data Summary: First few lines - {str(tool_results['weather_data']).splitlines()[0:3]}") # Keep it brief
        
        elif "transmission_cost_per_year" in tool_results: # Indicates transmission analysis
            formatted_parts.append("Transmission Cost Analysis Data:")
            formatted_parts.append(f"  - Source: {tool_results.get('source_coords', 'N/A')}")
            formatted_parts.append(f"  - Destination: {tool_results.get('destination_coords', 'N/A')}")
            formatted_parts.append(f"  - Project Capacity at Source: {tool_results.get('capacity_mw', 'N/A')} MW")
            formatted_parts.append(f"  - Annual Energy at Source: {tool_results.get('annual_yield_mwh_at_source', 'N/A'):,.0f} MWh/year" if isinstance(tool_results.get('annual_yield_mwh_at_source'), (int,float)) else f"  - Annual Energy at Source: {tool_results.get('annual_yield_mwh_at_source', 'N/A')}")
            formatted_parts.append(f"  - Annual Transmission Cost: ${tool_results.get('transmission_cost_per_year', 'N/A'):,.0f}" if isinstance(tool_results.get('transmission_cost_per_year'), (int,float)) else f"  - Annual Transmission Cost: {tool_results.get('transmission_cost_per_year', 'N/A')}")

        elif "rag_context" in tool_results:
            formatted_parts.append("Information from Knowledge Base:")
            rag_text = tool_results['rag_context']
            formatted_parts.append(f"  - Context: {rag_text[:1000]}{'...' if len(rag_text) > 1000 else ''}") # Truncate long RAG context

        return "\n".join(formatted_parts) if formatted_parts else "No specific data processed."


    def generate_response(self, query: str, processed_data: Dict[str, Any]) -> str:
        """Generate final response using LLM based on query and processed data (tool results/errors)."""
        
        error_message = processed_data.get("error")
        tool_results = processed_data.get("tool_results", {})

        if error_message:
            logger.error(f"Error before LLM generation: {error_message}")
            # Depending on severity, could return error directly or try to let LLM explain
            # For now, let LLM try to explain if there are partial results.
            if not tool_results: # If total failure
                 return f"I encountered an error: {error_message}. I am unable to provide a detailed answer for your query: '{query}'."
        
        formatted_tool_results = self._format_tool_results_for_llm(tool_results)

        prompt_template = f"""You are an expert solar energy consultant analyzing the feasibility of a solar power project.

TASK: Analyze the feasibility of the proposed solar project and provide a comprehensive assessment.

USER QUESTION: {query}

PROJECT DATA:
{formatted_tool_results}

ANALYSIS REQUIREMENTS:
1. **FEASIBILITY VERDICT**: Start with a clear YES/NO answer on whether this project is feasible
2. **FINANCIAL ANALYSIS**: 
   - Calculate payback period using annual yield and costs
   - Assess if the economics make sense
   - Comment on capital requirements vs expected returns
3. **TECHNICAL ASSESSMENT**:
   - Evaluate the location's solar resource quality
   - Assess grid connection requirements and costs
   - Identify any technical challenges
4. **RISK FACTORS**: Highlight any concerns or limitations
5. **RECOMMENDATIONS**: Provide actionable next steps

RESPONSE FORMAT:
**FEASIBILITY: [FEASIBLE/NOT FEASIBLE]**

**Financial Summary:**
[Your analysis of costs, revenues, payback period]

**Technical Assessment:**
[Your analysis of solar resource, grid connection, technical factors]

**Key Risks:**
[Major risks or concerns]

**Recommendation:**
[Clear next steps and overall advice]

Base your analysis strictly on the provided data. Do not invent numbers or information not present in the data."""
        logger.debug(f"Generating LLM prompt:\n{prompt_template}")
        
        try:
            response = self.llm.invoke(prompt_template) # Langchain AIMessage/HumanMessage convention not needed for direct invoke
            # For ChatOllama, response.content is the string. For mock, it's already a string or AIMessage.
            final_response = response.content if hasattr(response, 'content') else str(response)
            logger.info(f"LLM generated response successfully. Length: {len(final_response)}")
            return final_response
        except Exception as e:
            logger.error(f"Error during LLM response generation: {e}", exc_info=True)
            return f"I apologize, but I encountered an issue while generating the final response. Error: {e}"

    def run(self, query: str) -> str:
        """
        Main execution flow: route query, call tools/RAG, generate response.
        Returns a string response.
        """
        logger.info(f"Received query for agent execution: {query}")
        
        route = self.route_query(query)
        processed_data: Dict[str, Any] = {"tool_results": {}, "error": None}

        if route == "feasibility_analysis":
            processed_data = self.feasibility_analysis(query)
        elif route == "transmission_analysis":
            processed_data = self.transmission_analysis(query)
        elif route == "rag_query":
            processed_data = self.rag_query_handler(query)
        elif route == "general_query":
            processed_data = self.general_query_handler(query)
        else:
            logger.warning(f"Unknown route: {route}. Defaulting to general query.")
            processed_data = self.general_query_handler(query)
            
        return self.generate_response(query, processed_data)

# Convenience function for standalone execution if needed
def run_site_agent_from_query(query: str) -> str:
    """
    Initializes and runs the SiteFeasibilityAgent for a single query.
    This is a high-level wrapper.
    """
    # Ensure config and logging are set up (idempotent)
    from src.utils.logging_config import setup_logging 
    setup_logging() # Call this to ensure logging is configured
    
    logger.info("Creating SiteFeasibilityAgent instance for a single query.")
    agent = SiteFeasibilityAgent()
    return agent.run(query)

if __name__ == '__main__':
    # This is for basic testing of this module.
    # The main application entry point will be in app_main.py
    from src.utils.logging_config import setup_logging
    setup_logging()

    logger.info("--- Testing SiteFeasibilityAgent ---")
    test_agent = SiteFeasibilityAgent()

    test_queries = [
        "Is it feasible to build a 10 MW solar farm at 37.2 N, -121.9 W?",
        "What would it cost to deliver power from 37.2N, -121.9W to San José, CA (37.3 N, -122.0 W)? The farm is 10MW.",
        "Tell me about the California ISO interconnection queue.",
        "What are the challenges for solar energy?" # General query, should hit RAG
    ]

    for q in test_queries:
        print(f"\n{'='*60}\nQuery: {q}\n{'='*60}")
        response_text = test_agent.run(q)
        print(f"Agent Response:\n{response_text}")
        print(f"\n{'='*60}") 