

import aiohttp

import config

async def get_owm_reading() -> dict|None:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                url = f"http://api.openweathermap.org/data/2.5/weather?lat={config.OWM_LAT}&lon={config.OWM_LON}&appid={config.OWM_API_KEY}&units=metric", 
                timeout = 3,
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Error getting reading: {response.status}")
                    return None
        except Exception as e:
            print(f"Request failed: {e}")
            return None
