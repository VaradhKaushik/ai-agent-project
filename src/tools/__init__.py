# src/tools/__init__.py

# Import tools to make them available through the tools module
# This allows the agent to do `from ..tools import future_weather`

from .stubbed_tools import (
    future_weather,
    solar_yield,
    cost_model,
    transmission_cost,
    grid_connection_info,
    haversine_distance # if you want to expose helper too, otherwise keep it internal to stubbed_tools
)

# Import new API tools
from .api_tools import (
    web_search,
    nrel_solar_data,
    openweathermap_data,
    geocode_location,
    energy_news_search,
    real_solar_calculator,
    market_analysis_search
)

# You can add other tool modules here, e.g.:
# from .weather_api_tool import get_weather_from_api

__all__ = [
    # Original stubbed tools (kept as fallbacks)
    'future_weather',
    'solar_yield',
    'cost_model',
    'transmission_cost',
    'grid_connection_info',
    'haversine_distance',
    
    # New API tools
    'web_search',
    'nrel_solar_data',
    'openweathermap_data',
    'geocode_location',
    'energy_news_search',
    'real_solar_calculator',
    'market_analysis_search'
]

# Optional: A function to get all LangChain decorated tools
from langchain.tools import BaseTool

def get_all_langchain_tools() -> list[BaseTool]:
    """Returns a list of all LangChain tools defined in this module."""
    lc_tools = []
    for name in __all__:
        item = globals().get(name)
        if isinstance(item, BaseTool):
            lc_tools.append(item)
    # Add tools from other submodules if any, e.g.:
    # lc_tools.append(get_weather_from_api)
    return lc_tools

def get_enhanced_tools() -> list[BaseTool]:
    """Returns the enhanced tool set prioritizing real APIs over stubbed tools."""
    enhanced_tools = [
        # Prioritize real API tools
        web_search,
        nrel_solar_data,
        real_solar_calculator,
        openweathermap_data,
        geocode_location,
        energy_news_search,
        market_analysis_search,
        
        # Keep useful stubbed tools
        cost_model,
        transmission_cost,
        grid_connection_info
    ]
    return enhanced_tools 