import logging

import board
import busio
import displayio
import fourwire
from adafruit_st7735r import ST7735R


def init_display() -> ST7735R:
    # Release any resources currently in use for the displays
    displayio.release_displays()
    logging.info("Released diplays")

    # Initialize the SPI bus and the display
    spi = busio.SPI(clock=board.SCLK, MOSI=board.MOSI)

    display_bus = fourwire.FourWire(
        spi,
        command=board.D24,
        chip_select=board.CE0,
        reset=board.D25,
    )
    logging.info("Initialized SPI bus and display")

    # Create the display object
    display = ST7735R(display_bus, width=128, height=160, bgr=True)
    # Create a group for displaying UI elements
    ui = displayio.Group()
    display.root_group = ui
    logging.info("Added group to display")
    return display
