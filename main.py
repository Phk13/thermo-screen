import asyncio
import io
import logging
import time

import aiohttp
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text import label
from adafruit_display_shapes.rect import Rect
import adafruit_imageload.bmp as imageload
import displayio
from PIL import Image
import RPi.GPIO as GPIO

import config
import display
import openweathermap


async def get_sensor_reading():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(config.SENSOR_URI, timeout=3) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Error getting reading: {response.status}")
                    return None
        except Exception as e:
            print(f"Request failed: {e}")
            return None

class Display:
    def __init__(self):
        # GPIO setup
        self.BACKLIGHT_PIN = 4
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.BACKLIGHT_PIN, GPIO.OUT)
        GPIO.output(self.BACKLIGHT_PIN, GPIO.LOW)
        self.display_on = True  # Track the display state
        self.blink_on = False  # Track the blink state
        self.display = display.init_display()

        # Load the font file for text rendering
        
        font = bitmap_font.load_font(config.FONT_FILE)
        if not font:
            logging.error("Invalid font")
        logging.info("Font loaded")
        
        self.outside_temperature = "0ºC"
        self.temperature = "0ºC"
        self.outside_humidity = "0%"
        self.humidity = "0%"
        self.outside_pressure = "0 hPa"
        self.pressure = "0 hPa"

        # Create outside label
        self.outside_label = label.Label(font, color=0xFFA500, text = "OUTSIDE")
        self.outside_label.anchor_point = (0.5, 0.0)
        self.outside_label.anchored_position = (64, 5)

        # Create temperature label
        self.inside_label = label.Label(font, color=0xFFA500, text = "INSIDE")
        self.inside_label.anchor_point = (0.5, 0.0)
        self.inside_label.anchored_position = (64, 64)
        
        # Create outside label
        self.outside_sec_label = label.Label(font, color=0xFFA500, text = "OUT")
        self.outside_sec_label.anchor_point = (0.3, 0.0)
        self.outside_sec_label.anchored_position = (70, 125)

        # Create inside label
        self.inside_sec_label = label.Label(font, color=0xFFA500, text = "IN")
        self.inside_sec_label.anchor_point = (0.3, 0.0)
        self.inside_sec_label.anchored_position = (70, 140)

        # Create humidity label
        self.humidity_label = label.Label(font, color=0x1E90FF, text = "HUM")
        self.humidity_label.anchor_point = (1.0, 0.0)
        self.humidity_label.anchored_position = (110, 110)

        # Create pressure label
        self.pressure_label = label.Label(font, color=0x32CD32, text = "PRESS")
        self.pressure_label.anchor_point = (0.0, 0.0)
        self.pressure_label.anchored_position = (18, 110)

        # Create outside value label
        self.temperature_out_value_label = label.Label(font, color=0xFFFFFF)
        self.temperature_out_value_label.anchor_point = (0.5, 0.0)
        self.temperature_out_value_label.anchored_position = (64, 20)
        self.temperature_out_value_label.scale = 3

        # Create temperature value label
        self.temperature_in_value_label = label.Label(font, color=0xFFFFFF)
        self.temperature_in_value_label.anchor_point = (0.5, 0.0)
        self.temperature_in_value_label.anchored_position = (64, 75)
        self.temperature_in_value_label.scale = 3

        # Create outside humidity value label
        self.humidity_out_value_label = label.Label(font, color=0xFFFFFF)
        self.humidity_out_value_label.anchor_point = (1.0, 0.0)
        self.humidity_out_value_label.anchored_position = (120, 125)

        # Create humidity value label
        self.humidity_in_value_label = label.Label(font, color=0xFFFFFF)
        self.humidity_in_value_label.anchor_point = (1.0, 0.0)
        self.humidity_in_value_label.anchored_position = (120, 140)

        # Create pressure value label
        self.pressure_out_value_label = label.Label(font, color=0xFFFFFF)
        self.pressure_out_value_label.anchor_point = (0.0, 0.0)
        self.pressure_out_value_label.anchored_position = (10, 125)

        # Create pressure value label
        self.pressure_in_value_label = label.Label(font, color=0xFFFFFF)
        self.pressure_in_value_label.anchor_point = (0.0, 0.0)
        self.pressure_in_value_label.anchored_position = (10, 140)

        # Status square
        self.status_square = Rect(118, 0, 10, 10, fill=0xFF0000)

        # self.display.root_group.append(self.time_label)
        # self.display.root_group.append(self.date_label)
        self.display.root_group.append(self.outside_label)
        self.display.root_group.append(self.temperature_out_value_label)
        self.display.root_group.append(self.inside_label)
        self.display.root_group.append(self.temperature_in_value_label)
        self.display.root_group.append(self.humidity_label)
        self.display.root_group.append(self.humidity_out_value_label)
        self.display.root_group.append(self.humidity_in_value_label)
        self.display.root_group.append(self.pressure_label)
        self.display.root_group.append(self.pressure_out_value_label)
        self.display.root_group.append(self.pressure_in_value_label)
        self.display.root_group.append(self.outside_sec_label)
        self.display.root_group.append(self.inside_sec_label)
        self.display.root_group.append(self.status_square)
        logging.info("Created labels")

        self.inside_lock = asyncio.Lock()
        self.outside_lock = asyncio.Lock()
        self.inside_updated = False
        self.outside_updated = False
    
    def is_display_active(self) -> bool:
        current_hour = time.localtime().tm_hour
        if current_hour > 23 or current_hour < 9:
            if self.display_on:
                GPIO.output(self.BACKLIGHT_PIN, GPIO.HIGH)
                self.display_on = False
            return False
        else:
            if not self.display_on:
                GPIO.output(self.BACKLIGHT_PIN, GPIO.LOW)
                self.display_on = True
            return True

    async def update_outside_values(self):
        while True:
            if not self.display_on:
                await asyncio.sleep(3600)
                continue
            try:
                reading = await openweathermap.get_owm_reading()
                if reading:
                    async with self.outside_lock:
                        self.outside_temperature = f"{reading.get('main').get('temp'):.1f}ºC"
                        self.outside_humidity = f"{reading.get('main').get('humidity')}%"
                        self.outside_pressure = f"{reading.get('main').get('pressure')} hPa"
                        # logging.info(reading)
                        self.weather_icon = f"icons/{reading.get('weather')[0].get('icon')}@2x.bmp"
                        # logging.info(f"Icon: {self.weather_icon}")
                        # self.update_weather_icon()
                        self.outside_updated = True
            except Exception as e:
                logging.error(e)
                self.ouside_updated = False
            await asyncio.sleep(10)

    def update_weather_icon(self):
        # Clear existing icon from display
        if len(self.display.root_group) > 12:  # Ensure that an icon is already added
            self.display.root_group.pop()     # Remove the last item (icon) from the UI

        icon = Image.open(self.weather_icon)
        with io.BytesIO() as buf:
            icon.save(buf, 'bmp')
            icon_bitmap, icon_palette = imageload.load(buf, bitmap=displayio.Bitmap, palette=displayio.Palette)

        # Correct color conversion
        icon_palette.make_transparent(0)

        # Create an icon sprite and position it
        icon_tilegrid = displayio.TileGrid(icon_bitmap, pixel_shader=icon_palette)
        icon_tilegrid.x = 96  # X position
        icon_tilegrid.y = 40  # Y position
        

        # Append the icon to the display group
        self.display.root_group.append(icon_tilegrid)

    async def update_temperature(self):
        while True:
            if not self.display_on:
                await asyncio.sleep(3600)
                continue
            try:
                # Retrieve temperature, humidity, and pressure from the JSON response
                reading = await get_sensor_reading()
                async with self.inside_lock:
                    self.temperature = f"{reading['temperature']:.1f}ºC"
                    self.humidity = f"{reading['humidity']:.1f}%"
                    self.pressure = f"{reading['pressure']:.0f} hPa"
                    self.inside_updated = True
            except Exception as e:
                logging.error(e)
                self.inside_updated = False
            await asyncio.sleep(3)


    async def update_labels(self):
        if not self.display_on:
            return
        
        async with self.outside_lock:
            self.temperature_out_value_label.text = self.outside_temperature.ljust(5, " ")
            self.humidity_out_value_label.text = self.outside_humidity
            self.pressure_out_value_label.text = self.outside_pressure

        async with self.inside_lock:
            self.temperature_in_value_label.text = self.temperature.ljust(5, " ")
            self.humidity_in_value_label.text = self.humidity
            self.pressure_in_value_label.text = self.pressure

async def main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    try:

        display = Display()
        tasks = [
            asyncio.create_task(display.update_temperature()),
            asyncio.create_task(display.update_outside_values()),
        ]

        logging.info("Entering loop")
        while True:
            if not display.is_display_active():
                await asyncio.sleep(3600)
                continue
            try:
                await display.update_labels()
                if display.blink_on:
                    display.status_square.fill = 0x00FF00 if display.outside_updated and display.inside_updated else 0xFF0000
                else:
                    display.status_square.fill = 0x000000
                display.blink_on = not display.blink_on
            except Exception as e:
                logging.error(e, exc_info=True)
                display.status_square.fill = 0xFF0000
            await asyncio.sleep(1)
    except Exception as e:
        logging.error(e, exc_info=True)
        [task.cancel() for task in tasks]


if __name__ == "__main__":
    # Loop in case of a crash
    while True:
        asyncio.run(main())
