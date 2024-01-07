import requests
import logging

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

weather_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Drizzle: Light intensity",
        53: "Drizzle: Moderate intensity",
        55: "Drizzle: Dense intensity",
        56: "Freezing Drizzle: Light intensity",
        57: "Freezing Drizzle: Dense intensity",
        61: "Rain: Slight intensity",
        63: "Rain: Moderate intensity",
        65: "Rain: Heavy intensity",
        66: "Freezing Rain: Light intensity",
        67: "Freezing Rain: Heavy intensity",
        71: "Snowfall: Slight intensity",
        73: "Snowfall: Moderate intensity",
        75: "Snowfall: Heavy intensity",
        77: "Snow grains",
        80: "Rain showers: Slight intensity",
        81: "Rain showers: Moderate intensity",
        82: "Rain showers: Violent intensity",
        85: "Snow showers: Slight intensity",
        86: "Snow showers: Heavy intensity",
        95: "Thunderstorm: Slight intensity",
        96: "Thunderstorm: Slight hail",
        99: "Thunderstorm: Heavy hail"
    }

wind_ranges = [
        (20, 28, "Moderate breeze", "Raises dust and loose paper; small branches moved"),
        (29, 38, "Fresh breeze", "Small trees in leaf begin to sway; crested wavelets form on inland waters"),
        (39, 49, "Strong breeze", "Large branches in motion; whistling heard in telegraph wires; umbrellas used with difficulty"),
        (50, 61, "High wind, moderate gale, near gale", "Whole trees in motion; inconvenience felt when walking against the wind"),
        (62, 74, "Gale, fresh gale", "Twigs break off trees; generally impedes progress"),
        (75, 88, "Strong/severe gale", "Slight structural damage (chimney pots and slates removed)"),
        (89, 102, "Storm, whole gale", "Considerable structural damage; trees uprooted; very rarely experienced"),
        (103, 117, "Violent storm", "Very rarely experienced; accompanied by widespread damage"),
        (118, float('inf'), "Hurricane-force", "Devastation")
    ]

def request_weather_api(latitude=45.25, longitude=19.83):
    """
    Request open-meteo API endpoint with Novi-Sad location by default. Return json response.
    """
    meteo_url = f'https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,rain,showers,snowfall,weather_code,wind_speed_10m&hourly=temperature_2m,rain,showers,snowfall,weather_code,wind_speed_10m&daily=uv_index_max,uv_index_clear_sky_max,precipitation_sum,rain_sum,showers_sum,snowfall_sum,precipitation_probability_max,wind_speed_10m_max&timezone=Europe%2FBerlin&forecast_days=1'
    response = requests.get(meteo_url)
    try:
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error occurred during API request: HTTP {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error occurred during API request: {e}")
        return None

def weather_one_time_forecast():
    response = request_weather_api()
    temperatures = response["hourly"]["temperature_2m"]
    hourly_codes = response["hourly"]["weather_code"]
    wind_speed_max = response["daily"]["wind_speed_10m_max"][0]
    uv_index_clear_sky_max = response["daily"]["uv_index_clear_sky_max"][0]

    forecast = f'''
Morning temperature: {temperatures[8]}°C
Day temperature: {temperatures[13]}°C
Evening temperature: {temperatures[18]}°C
Night temperature: {temperatures[23]}°C

Morning weather: {weather_codes[hourly_codes[8]]}
Day weather: {weather_codes[hourly_codes[13]]}
Evening weather: {weather_codes[hourly_codes[18]]}
'''
    if uv_index_clear_sky_max > 3:
        forecast += f'''
UV index with clear sky today is {uv_index_clear_sky_max}
Seek shade during midday hours! Slip on a shirt, slop on sunscreen and slap on hat!
'''
    for range_start, range_end, name, effects in wind_ranges:
        if wind_speed_max >= range_start and (wind_speed_max <= range_end or range_end == float('inf')):
            forecast += f'''
Maximux wind speed today is {wind_speed_max}
It is qualified as {name}. Possible effects: {effects}
'''
    return forecast

if __name__ == '__main__':
    weather_one_time_forecast()
