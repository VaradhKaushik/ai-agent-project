import requests
import json
from typing import Dict, List, Any, Optional, Tuple
from langchain.tools import tool
import time
from datetime import datetime

from ..utils.config import get_config
from ..utils.logging_config import get_logger

logger = get_logger(__name__)
config = get_config()

@tool
def web_search(query: str, num_results: int = 5) -> str:
    """
    Search the web using DuckDuckGo (no API key required).
    Args:
        query: Search query string
        num_results: Number of results to return (max 10)
    Returns:
        Formatted string with search results
    """
    logger.info(f"Web search tool called with query: '{query[:50]}...'")
    
    try:
        # Using DuckDuckGo Instant Answer API (no key required)
        url = "https://api.duckduckgo.com/"
        params = {
            'q': query,
            'format': 'json',
            'no_redirect': '1',
            'no_html': '1',
            'skip_disambig': '1'
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            results = []
            # Get abstract if available
            if data.get('Abstract'):
                results.append(f"**Summary**: {data['Abstract']}")
                if data.get('AbstractURL'):
                    results.append(f"**Source**: {data['AbstractURL']}")
            
            # Get related topics
            if data.get('RelatedTopics'):
                results.append("\n**Related Information**:")
                for i, topic in enumerate(data['RelatedTopics'][:num_results]):
                    if isinstance(topic, dict) and topic.get('Text'):
                        text = topic['Text'][:200] + "..." if len(topic['Text']) > 200 else topic['Text']
                        results.append(f"{i+1}. {text}")
                        if topic.get('FirstURL'):
                            results.append(f"   Source: {topic['FirstURL']}")
            
            # Get answer if available
            if data.get('Answer'):
                results.append(f"\n**Direct Answer**: {data['Answer']}")
            
            if results:
                return "\n".join(results)
            else:
                return f"No detailed results found for query: {query}"
        
        else:
            logger.warning(f"DuckDuckGo API returned status code: {response.status_code}")
            return f"Search API temporarily unavailable (status: {response.status_code})"
            
    except Exception as e:
        logger.error(f"Error in web search: {e}")
        return f"Web search failed: {str(e)}"

@tool
def nrel_solar_data(lat: float, lon: float) -> str:
    """
    Get real solar irradiance data from NREL (National Renewable Energy Laboratory) API.
    This is a free API that provides actual solar resource data.
    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
    Returns:
        Solar resource information as formatted string
    """
    logger.info(f"NREL solar data tool called for lat={lat}, lon={lon}")
    
    try:
        # Try NREL Solar Resource API first
        import os
        api_key = os.getenv('NREL_API_KEY') or config.get('tools', {}).get('nrel_api_key')
        
        if api_key:
            url = "https://developer.nrel.gov/api/solar/solar_resource/v1.json"
            params = {
                'lat': lat,
                'lon': lon,
                'api_key': api_key
            }
        else:
            # Try without API key first (some endpoints allow this)
            url = "https://developer.nrel.gov/api/solar/solar_resource/v1.json"
            params = {
                'lat': lat,
                'lon': lon
            }
        
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            
            if 'outputs' in data:
                outputs = data['outputs']
                
                # Extract key solar metrics
                result = []
                result.append(f"**NREL Solar Resource Data for ({lat}, {lon})**")
                
                if 'avg_dni' in outputs:
                    result.append(f"Average Direct Normal Irradiance: {outputs['avg_dni']['annual']} kWh/m²/day")
                
                if 'avg_ghi' in outputs:
                    result.append(f"Average Global Horizontal Irradiance: {outputs['avg_ghi']['annual']} kWh/m²/day")
                
                if 'avg_lat_tilt' in outputs:
                    result.append(f"Average Latitude Tilt Irradiance: {outputs['avg_lat_tilt']['annual']} kWh/m²/day")
                
                # Monthly breakdown if available
                if 'avg_ghi' in outputs and 'monthly' in outputs['avg_ghi']:
                    monthly = outputs['avg_ghi']['monthly']
                    result.append("\n**Monthly GHI (kWh/m²/day)**:")
                    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                             'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    for i, month in enumerate(months):
                        if i < len(monthly):
                            result.append(f"{month}: {monthly[i]}")
                
                return "\n".join(result)
            else:
                return f"No solar data available for coordinates ({lat}, {lon})"
                
        elif response.status_code == 403:
            logger.warning(f"NREL API requires API key. Status: {response.status_code}")
            # Fall back to estimation based on latitude (rough approximation)
            return estimate_solar_resource(lat, lon)
        else:
            logger.warning(f"NREL API returned status code: {response.status_code}")
            return estimate_solar_resource(lat, lon)
            
    except Exception as e:
        logger.error(f"Error accessing NREL solar data: {e}")
        return estimate_solar_resource(lat, lon)

def estimate_solar_resource(lat: float, lon: float) -> str:
    """Provide rough solar resource estimates based on latitude."""
    abs_lat = abs(lat)
    
    # Rough estimates based on latitude zones
    if abs_lat <= 23.5:  # Tropics
        ghi_est = 6.0
        dni_est = 7.5
    elif abs_lat <= 35:  # Subtropics (like Phoenix, California)
        ghi_est = 5.5
        dni_est = 7.0
    elif abs_lat <= 45:  # Mid-latitudes
        ghi_est = 4.5
        dni_est = 5.5
    else:  # Higher latitudes
        ghi_est = 3.5
        dni_est = 4.0
    
    result = []
    result.append(f"**Estimated Solar Resource Data for ({lat}, {lon})**")
    result.append(f"Note: These are rough estimates. For accurate data, sign up for a free NREL API key.")
    result.append(f"Average Global Horizontal Irradiance: ~{ghi_est} kWh/m²/day")
    result.append(f"Average Direct Normal Irradiance: ~{dni_est} kWh/m²/day")
    result.append(f"Latitude zone: {abs_lat:.1f}° ({'tropical' if abs_lat <= 23.5 else 'subtropical' if abs_lat <= 35 else 'mid-latitude' if abs_lat <= 45 else 'high-latitude'})")
    
    return "\n".join(result)

@tool
def openweathermap_data(lat: float, lon: float) -> str:
    """
    Get weather data from OpenWeatherMap API (free tier available).
    Falls back to basic data if no API key is configured.
    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
    Returns:
        Weather information as formatted string
    """
    logger.info(f"OpenWeatherMap data tool called for lat={lat}, lon={lon}")
    
    # Try to get API key from environment or config
    import os
    api_key = os.getenv('OPENWEATHERMAP_API_KEY') or config.get('tools', {}).get('openweathermap_api_key')
    
    if not api_key:
        logger.info("No OpenWeatherMap API key found, using alternative weather source")
        return get_weather_alternative(lat, lon)
    
    try:
        # Current weather
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': api_key,
            'units': 'metric'
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            result = []
            result.append(f"**Current Weather for ({lat}, {lon})**")
            result.append(f"Location: {data.get('name', 'Unknown')}")
            result.append(f"Temperature: {data['main']['temp']}°C")
            result.append(f"Humidity: {data['main']['humidity']}%")
            result.append(f"Cloud Cover: {data['clouds']['all']}%")
            result.append(f"Weather: {data['weather'][0]['description'].title()}")
            
            if 'wind' in data:
                result.append(f"Wind Speed: {data['wind'].get('speed', 0)} m/s")
            
            return "\n".join(result)
        else:
            logger.warning(f"OpenWeatherMap API error: {response.status_code}")
            return get_weather_alternative(lat, lon)
            
    except Exception as e:
        logger.error(f"Error accessing OpenWeatherMap: {e}")
        return get_weather_alternative(lat, lon)

def get_weather_alternative(lat: float, lon: float) -> str:
    """Alternative weather data source that doesn't require API key."""
    try:
        # Use wttr.in service (free, no API key required)
        url = f"https://wttr.in/{lat},{lon}?format=j1"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            current = data['current_condition'][0]
            
            result = []
            result.append(f"**Weather Data for ({lat}, {lon})**")
            result.append(f"Temperature: {current['temp_C']}°C")
            result.append(f"Humidity: {current['humidity']}%")
            result.append(f"Cloud Cover: {current['cloudcover']}%")
            result.append(f"Weather: {current['weatherDesc'][0]['value']}")
            result.append(f"Wind Speed: {current['windspeedKmph']} km/h")
            result.append(f"UV Index: {current.get('uvIndex', 'N/A')}")
            
            return "\n".join(result)
        else:
            return f"Weather data temporarily unavailable for ({lat}, {lon})"
            
    except Exception as e:
        logger.error(f"Alternative weather source failed: {e}")
        return f"Weather lookup failed for ({lat}, {lon})"

@tool
def geocode_location(location_name: str) -> str:
    """
    Convert location name to coordinates using free Nominatim API (OpenStreetMap).
    Args:
        location_name: Name of location (e.g., "San Francisco, CA" or "Berlin, Germany")
    Returns:
        Coordinates and location details as formatted string
    """
    logger.info(f"Geocoding tool called for location: '{location_name}'")
    
    try:
        # Using Nominatim API (free, no API key required)
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': location_name,
            'format': 'json',
            'limit': 3,
            'addressdetails': 1
        }
        
        # Add user agent as required by Nominatim
        headers = {'User-Agent': 'SolarFeasibilityAgent/1.0'}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            if data:
                results = []
                for i, location in enumerate(data[:3]):  # Top 3 results
                    lat = float(location['lat'])
                    lon = float(location['lon'])
                    display_name = location['display_name']
                    
                    results.append(f"**Result {i+1}:**")
                    results.append(f"Location: {display_name}")
                    results.append(f"Coordinates: {lat}, {lon}")
                    
                    # Add address details if available
                    if 'address' in location:
                        addr = location['address']
                        if 'country' in addr:
                            results.append(f"Country: {addr['country']}")
                        if 'state' in addr:
                            results.append(f"State/Region: {addr['state']}")
                    results.append("")
                
                return "\n".join(results)
            else:
                return f"No locations found for: {location_name}"
        else:
            return f"Geocoding service temporarily unavailable (status: {response.status_code})"
            
    except Exception as e:
        logger.error(f"Error in geocoding: {e}")
        return f"Geocoding failed: {str(e)}"

@tool
def energy_news_search(topic: str = "solar energy market") -> str:
    """
    Search for recent energy industry news and market information.
    Args:
        topic: Search topic (default: "solar energy market")
    Returns:
        Recent news and market information
    """
    logger.info(f"Energy news search for topic: '{topic}'")
    
    try:
        # Combine web search with specific energy-focused search
        search_query = f"{topic} renewable energy latest news 2024"
        return web_search.func(query=search_query, num_results=5)
        
    except Exception as e:
        logger.error(f"Error in energy news search: {e}")
        return f"Energy news search failed: {str(e)}"

@tool
def real_solar_calculator(lat: float, lon: float, capacity_mw: float, tilt: float = None) -> str:
    """
    Calculate realistic solar energy production using real irradiance data and PV system modeling.
    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees  
        capacity_mw: System capacity in MW
        tilt: Panel tilt angle (optional, will use latitude if not provided)
    Returns:
        Detailed solar production analysis
    """
    logger.info(f"Real solar calculator called for lat={lat}, lon={lon}, capacity={capacity_mw}MW")
    
    try:
        # Get real solar irradiance data first
        solar_data = nrel_solar_data.func(lat=lat, lon=lon)
        
        # Extract GHI value from NREL data if possible
        ghi_annual = 5.0  # Default fallback
        if "Average Global Horizontal Irradiance:" in solar_data:
            try:
                ghi_line = [line for line in solar_data.split('\n') if "Average Global Horizontal Irradiance:" in line][0]
                ghi_annual = float(ghi_line.split(':')[1].split()[0])
            except:
                pass
        
        # Use optimal tilt (approximately equal to latitude) if not provided
        if tilt is None:
            tilt = abs(lat)
        
        # Tilt correction factor (simplified)
        if tilt <= 90:
            tilt_factor = 1 + (0.1 * (tilt / abs(lat) - 1)) if lat != 0 else 1.0
        else:
            tilt_factor = 1.0
            
        # System efficiency factors
        dc_ac_ratio = 1.2  # Typical DC/AC ratio
        system_efficiency = 0.85  # Inverter + wiring + soiling losses
        degradation_rate = 0.005  # 0.5% per year
        
        # Calculate first year production
        dc_capacity_mw = capacity_mw * dc_ac_ratio
        daily_production_mwh = dc_capacity_mw * ghi_annual * system_efficiency * tilt_factor
        annual_production_mwh = daily_production_mwh * 365
        
        # Calculate 25-year production with degradation
        total_25yr_production = 0
        for year in range(25):
            year_efficiency = system_efficiency * (1 - degradation_rate * year)
            year_production = dc_capacity_mw * ghi_annual * year_efficiency * tilt_factor * 365
            total_25yr_production += year_production
        
        # Performance metrics
        capacity_factor = (annual_production_mwh * 1000) / (capacity_mw * 8760) * 100
        specific_yield = annual_production_mwh / capacity_mw * 1000  # kWh/kWp
        
        result = []
        result.append(f"**Real Solar Production Analysis**")
        result.append(f"Location: ({lat}, {lon})")
        result.append(f"System Size: {capacity_mw} MW AC ({dc_capacity_mw:.1f} MW DC)")
        result.append(f"Panel Tilt: {tilt:.1f}°")
        result.append(f"")
        result.append(f"**Solar Resource:**")
        result.append(f"Annual GHI: {ghi_annual:.2f} kWh/m²/day")
        result.append(f"")
        result.append(f"**Performance Estimates:**")
        result.append(f"Year 1 Production: {annual_production_mwh:,.0f} MWh")
        result.append(f"Capacity Factor: {capacity_factor:.1f}%")
        result.append(f"Specific Yield: {specific_yield:.0f} kWh/kWp")
        result.append(f"25-Year Total: {total_25yr_production:,.0f} MWh")
        result.append(f"")
        result.append(f"**System Assumptions:**")
        result.append(f"DC/AC Ratio: {dc_ac_ratio}")
        result.append(f"System Efficiency: {system_efficiency*100:.1f}%")
        result.append(f"Annual Degradation: {degradation_rate*100:.1f}%")
        
        return "\n".join(result)
        
    except Exception as e:
        logger.error(f"Error in real solar calculator: {e}")
        return f"Solar calculation failed: {str(e)}"

@tool 
def market_analysis_search(location: str) -> str:
    """
    Search for market analysis and regulatory information for solar projects.
    Args:
        location: Location name or region
    Returns:
        Market analysis and regulatory information
    """
    logger.info(f"Market analysis search for location: '{location}'")
    
    try:
        # Search for specific market information
        queries = [
            f"{location} solar energy incentives regulations 2024",
            f"{location} renewable energy market analysis",
            f"{location} solar power purchase agreement rates"
        ]
        
        results = []
        for query in queries:
            search_result = web_search.func(query=query, num_results=3)
            results.append(f"**{query}:**")
            results.append(search_result)
            results.append("\n" + "="*50 + "\n")
            time.sleep(1)  # Be respectful to search API
        
        return "\n".join(results)
        
    except Exception as e:
        logger.error(f"Error in market analysis search: {e}")
        return f"Market analysis search failed: {str(e)}" 