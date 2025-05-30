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

# You can add other tool modules here, e.g.:
# from .weather_api_tool import get_weather_from_api

__all__ = [
    'future_weather',
    'solar_yield',
    'cost_model',
    'transmission_cost',
    'grid_connection_info',
    'haversine_distance' # only if exposed
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