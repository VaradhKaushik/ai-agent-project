"""
Site Feasibility Agent Tools
Stubbed implementations of weather, solar yield, cost, and transmission tools.
"""

from langchain.tools import tool
from math import sqrt
from typing import Tuple


@tool
def future_weather(lat: float, lon: float) -> str:
    """
    Return placeholder 10-year monthly weather CSV for any coordinate.
    
    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        
    Returns:
        CSV string with monthly temperature and global horizontal irradiance data
    """
    # Hard-coded weather data based on California averages
    weather_data = [
        "month,temp_C,ghi_kWh_m2",
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
    
    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees  
        ac_mw: AC capacity in megawatts
        
    Returns:
        Annual energy production in MWh
    """
    # Specific yield assumption: 1600 kWh/kWp/year (good for California)
    specific_yield_kwh_per_kwp = 1600
    annual_mwh = ac_mw * specific_yield_kwh_per_kwp
    
    return annual_mwh


@tool
def cost_model(ac_mw: float) -> Tuple[float, float]:
    """
    Return (capex_$M, opex_$M_per_yr) as simple multiples of capacity.
    
    Args:
        ac_mw: AC capacity in megawatts
        
    Returns:
        Tuple of (capital expenditure in $M, annual operating expenditure in $M/year)
    """
    # Fixed cost assumptions
    capex_per_mw = 1.0  # $1M per MW
    opex_per_mw_per_year = 0.020  # $20k per MW per year
    
    capex_millions = ac_mw * capex_per_mw
    opex_millions_per_year = ac_mw * opex_per_mw_per_year
    
    return capex_millions, opex_millions_per_year


@tool
def transmission_cost(src_lat: float, src_lon: float, dst_lat: float, dst_lon: float, mwh_year: float) -> float:
    """
    Compute airline distance and apply $0.03/kWh/100km transmission cost.
    
    Args:
        src_lat: Source latitude in decimal degrees
        src_lon: Source longitude in decimal degrees
        dst_lat: Destination latitude in decimal degrees  
        dst_lon: Destination longitude in decimal degrees
        mwh_year: Annual energy in MWh
        
    Returns:
        Annual transmission cost in dollars
    """
    # Crude distance calculation (degrees to km approximation)
    lat_diff = src_lat - dst_lat
    lon_diff = src_lon - dst_lon
    dist_km = sqrt(lat_diff**2 + lon_diff**2) * 111  # ~111 km per degree
    
    # Transmission cost model: $0.03/kWh per 100km
    cost_per_kwh_per_100km = 0.03
    cost_per_kwh = cost_per_kwh_per_100km * (dist_km / 100)
    
    # Convert MWh to kWh and calculate annual cost
    kwh_year = mwh_year * 1000
    annual_transmission_cost = cost_per_kwh * kwh_year
    
    return annual_transmission_cost


@tool
def grid_connection_info(lat: float, lon: float) -> str:
    """
    Return information about grid connection requirements and nearby substations.
    
    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        
    Returns:
        String with grid connection information
    """
    # Simplified grid connection info based on California regions
    if 36.0 <= lat <= 38.0 and -122.5 <= lon <= -120.0:
        region = "Central Valley"
        nearest_substation = "Los Banos 230kV"
        connection_cost = "$75,000 - $150,000 per MW"
    elif 34.0 <= lat <= 36.0 and -118.0 <= lon <= -115.0:
        region = "Mojave Desert"  
        nearest_substation = "Kramer 500kV"
        connection_cost = "$50,000 - $100,000 per MW"
    else:
        region = "Other California"
        nearest_substation = "Regional 115kV"
        connection_cost = "$100,000 - $300,000 per MW"
    
    return f"Region: {region}, Nearest substation: {nearest_substation}, Est. connection cost: {connection_cost}"


if __name__ == "__main__":
    # Test the tools
    print("Testing tools...")
    
    # Test coordinates: somewhere in Central California
    test_lat, test_lon = 37.2, -121.9
    
    print(f"\nWeather data for {test_lat}, {test_lon}:")
    print(future_weather.func(test_lat, test_lon))
    
    print(f"\nSolar yield for 20 MW:")
    yield_mwh = solar_yield.func(test_lat, test_lon, 20.0)
    print(f"{yield_mwh:,.0f} MWh/year")
    
    print(f"\nCost model for 20 MW:")
    capex, opex = cost_model.func(20.0)
    print(f"CapEx: ${capex:.1f}M, OpEx: ${opex:.3f}M/year")
    
    print(f"\nTransmission cost to San Jose (37.3, -122.0):")
    trans_cost = transmission_cost.func(test_lat, test_lon, 37.3, -122.0, yield_mwh)
    print(f"${trans_cost:,.0f}/year")
    
    print(f"\nGrid connection info:")
    print(grid_connection_info.func(test_lat, test_lon)) 