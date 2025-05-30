import re
from typing import Dict, List, Any, Tuple
from math import radians, sin, cos, sqrt, atan2
from langchain.tools import tool

from utils.config import get_config
from utils.logging_config import get_logger

logger = get_logger(__name__)
config = get_config()
tool_config = config.get('tools', {})

# Helper function for distance calculation (more accurate than simple degree diff)
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points on Earth using Haversine formula."""
    R = 6371  # Radius of Earth in kilometers

    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    logger.debug(f"Haversine distance between ({lat1},{lon1}) and ({lat2},{lon2}): {distance:.2f} km")
    return distance

@tool
def future_weather(lat: float, lon: float) -> str:
    """
    Return placeholder 10-year monthly weather CSV for any coordinate.
    This is a STUBBED tool and returns hard-coded data.
    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
    Returns:
        CSV string with monthly temperature and global horizontal irradiance data
    """
    logger.info(f"Tool '{future_weather.name}' called for lat={lat}, lon={lon}. Using STUBBED data.")
    # Hard-coded weather data based on California averages
    weather_data = [
        "month,temp_C,ghi_kWh_m2_day", # Assuming GHI is daily average for the month
        "1,12.5,3.8",
        "2,14.2,4.9", 
        "3,16.8,6.2",
        "4,19.1,7.4",
        "5,22.3,8.1",
        "6,25.1,8.7",
        "7,27.8,8.9",
        "8,27.2,8.2",
        "9,24.9,6.8",
        "10,20.7,5.1",
        "11,16.1,4.0",
        "12,12.8,3.5"
    ]
    return "\n".join(weather_data)

@tool
def solar_yield(lat: float, lon: float, ac_mw: float = 20.0) -> float:
    """
    Return annual MWh based on a fixed 1600 kWh/kWp-yr specific yield.
    This is a STUBBED tool and uses a simplified calculation.
    Args:
        lat: Latitude in decimal degrees (currently unused by stub)
        lon: Longitude in decimal degrees (currently unused by stub)
        ac_mw: AC capacity in megawatts
    Returns:
        Annual energy production in MWh
    """
    logger.info(f"Tool '{solar_yield.name}' called for lat={lat}, lon={lon}, capacity={ac_mw}MW. Using STUBBED calculation.")
    # Specific yield assumption: 1600 kWh/kWp/year (good for California)
    # Assuming DC_AC_ratio of 1.0 for simplicity in this stub (kWp = kW_ac)
    specific_yield_kwh_per_kwp_yr = 1600
    dc_capacity_kwp = ac_mw * 1000 # Convert MW AC to kWp (assuming 1:1 for stub)
    
    annual_kwh = dc_capacity_kwp * specific_yield_kwh_per_kwp_yr
    annual_mwh = annual_kwh / 1000
    
    logger.debug(f"Calculated annual yield: {annual_mwh:.0f} MWh for {ac_mw} MW AC capacity.")
    return annual_mwh

@tool
def cost_model(ac_mw: float) -> Tuple[float, float]:
    """
    Return (capex_$M, opex_$M_per_yr) as simple multiples of capacity.
    This is a STUBBED tool and uses hard-coded cost factors.
    Args:
        ac_mw: AC capacity in megawatts
    Returns:
        Tuple of (capital expenditure in $M, annual operating expenditure in $M/year)
    """
    logger.info(f"Tool '{cost_model.name}' called for capacity={ac_mw}MW. Using STUBBED cost factors.")
    # Fixed cost assumptions from config or defaults
    capex_per_mw = tool_config.get('cost_model_capex_per_mw', 1.0)  # $1M per MW
    opex_per_mw_per_year_k = tool_config.get('cost_model_opex_per_mw_k', 20)  # $20k per MW per year
    
    opex_per_mw_per_year = opex_per_mw_per_year_k / 1000 # Convert k$ to M$
    
    capex_millions = ac_mw * capex_per_mw
    opex_millions_per_year = ac_mw * opex_per_mw_per_year
    
    logger.debug(f"Calculated CapEx: ${capex_millions:.2f}M, OpEx: ${opex_millions_per_year:.3f}M/year for {ac_mw} MW.")
    return capex_millions, opex_millions_per_year

@tool
def transmission_cost(src_lat: float, src_lon: float, dst_lat: float, dst_lon: float, mwh_year: float) -> float:
    """
    Compute airline distance and apply $0.03/kWh/100km transmission cost.
    This is a STUBBED tool and uses a simplified cost model.
    Args:
        src_lat: Source latitude in decimal degrees
        src_lon: Source longitude in decimal degrees
        dst_lat: Destination latitude in decimal degrees  
        dst_lon: Destination longitude in decimal degrees
        mwh_year: Annual energy in MWh
    Returns:
        Annual transmission cost in dollars
    """
    logger.info(f"Tool '{transmission_cost.name}' called for source=({src_lat},{src_lon}), dest=({dst_lat},{dst_lon}), energy={mwh_year}MWh. Using STUBBED model.")
    
    dist_km = haversine_distance(src_lat, src_lon, dst_lat, dst_lon)
    
    # Transmission cost model from config or defaults
    cost_per_kwh_per_100km = tool_config.get('transmission_cost_per_kwh_per_100km', 0.03) # $0.03/kWh per 100km
    cost_per_kwh = cost_per_kwh_per_100km * (dist_km / 100.0)
    
    kwh_year = mwh_year * 1000
    annual_transmission_cost_usd = cost_per_kwh * kwh_year
    
    logger.debug(f"Calculated transmission distance: {dist_km:.2f} km, Cost/kWh: ${cost_per_kwh:.4f}, Annual cost: ${annual_transmission__cost_usd:,.0f}")
    return annual_transmission_cost_usd

@tool
def grid_connection_info(lat: float, lon: float) -> str:
    """
    Return information about grid connection requirements and nearby substations.
    This is a STUBBED tool and returns hard-coded regional data.
    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
    Returns:
        String with grid connection information
    """
    logger.info(f"Tool '{grid_connection_info.name}' called for lat={lat}, lon={lon}. Using STUBBED regional data.")
    # Simplified grid connection info based on California regions
    # These boundaries and data are illustrative
    if 36.0 <= lat <= 38.0 and -122.5 <= lon <= -120.0:
        region = "Central Valley (Stubbed)"
        nearest_substation = "Los Banos 230kV (Stubbed)"
        connection_cost_estimate = "$75,000 - $150,000 per MW (Stubbed)"
    elif 34.0 <= lat <= 36.0 and -118.0 <= lon <= -115.0:
        region = "Mojave Desert (Stubbed)"  
        nearest_substation = "Kramer 500kV (Stubbed)"
        connection_cost_estimate = "$50,000 - $100,000 per MW (Stubbed)"
    else:
        region = "Other California Region (Stubbed)"
        nearest_substation = "Regional 115kV Substation (Stubbed)"
        connection_cost_estimate = "$100,000 - $300,000 per MW (Stubbed)"
    
    response = f"Region: {region}, Nearest substation: {nearest_substation}, Est. connection cost: {connection_cost_estimate}. Note: This is stubbed data."
    logger.debug(f"Grid connection info for ({lat},{lon}): {response}")
    return response


if __name__ == '__main__':
    from src.utils.logging_config import setup_logging
    setup_logging() # Ensure logging is set up

    logger.info("--- Testing Stubbed Tools ---")
    
    test_lat = tool_config.get('default_latitude', 37.2)
    test_lon = tool_config.get('default_longitude', -121.9)
    test_capacity_mw = tool_config.get('default_capacity_mw', 15.0) # Use a different capacity for test
    dest_lat = tool_config.get('default_target_latitude', 37.3)
    dest_lon = tool_config.get('default_target_longitude', -122.0)

    print(f"\nTesting with Lat: {test_lat}, Lon: {test_lon}, Capacity: {test_capacity_mw}MW")
    
    print(f"\nWeather data:")
    weather = future_weather.func(lat=test_lat, lon=test_lon)
    print(weather)
    
    print(f"\nSolar yield:")
    yield_mwh = solar_yield.func(lat=test_lat, lon=test_lon, ac_mw=test_capacity_mw)
    print(f"{yield_mwh:,.0f} MWh/year")
    
    print(f"\nCost model:")
    capex, opex = cost_model.func(ac_mw=test_capacity_mw)
    print(f"CapEx: ${capex:.2f}M, OpEx: ${opex:.3f}M/year")
    
    print(f"\nTransmission cost to ({dest_lat}, {dest_lon}):")
    trans_cost_usd = transmission_cost.func(src_lat=test_lat, src_lon=test_lon, dst_lat=dest_lat, dst_lon=dest_lon, mwh_year=yield_mwh)
    print(f"${trans_cost_usd:,.0f}/year")
    
    print(f"\nGrid connection info:")
    grid_info = grid_connection_info.func(lat=test_lat, lon=test_lon)
    print(grid_info) 