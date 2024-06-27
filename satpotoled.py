from smbus import SMBus
from gpiozero import PWMLED
from datetime import datetime, timezone
from pyorbital.orbital import Orbital
import geocoder
import sys
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from time import sleep

bus = SMBus(1)
ads7830_commands = (0x84, 0xc4, 0x94, 0xd4, 0xa4, 0xe4, 0xb4, 0xf4)
serial = i2c(port=1, address=0x3C)
device = ssd1306(serial)

#startup loading screen
with canvas(device) as draw:
    draw.rectangle((0, 0, 128, 64), outline="black", fill="black")
    draw.text((20, 32), "Loading...", fill="white")

#potentiometer values
def read_ads7830(input):
    bus.write_byte(0x4b, ads7830_commands[input])
    return bus.read_byte(0x4b)

def values(input):
    while True:
        value = read_ads7830(input)
        sleep(0.5)
        return(value)
#initialize Orbital outside of loop to avoid 403 error
satdict = {
    "ISS (ZARYA)": Orbital("ISS (ZARYA)"), 
    "NOAA-15": Orbital("NOAA-15"), 
    "NOAA-18": Orbital("NOAA-18"), 
    "NOAA-19": Orbital("NOAA-19"), 
    "METEOR-M2 2": Orbital("METEOR-M2 2"), 
    "METEOR-M2 3": Orbital("METEOR-M2 3"), 
    "METEOR-M2 4": Orbital("METEOR-M2 4")
    }
#main loop
while True:
    with canvas(device) as draw:
        draw.rectangle((0, 0, 128, 64), outline="black", fill="black")
        draw.text((20, 32), "Loading...", fill="white")

#get potentiometer value and satellite
    value = values(0)
    satlist = ["ISS (ZARYA)", "NOAA-15", "NOAA-18", "NOAA-19", "METEOR-M2 2", "METEOR-M2 3", "METEOR-M2 4"]
    index1 = int(value / (255 / len(satlist)))
    index = min(len(satlist) - 1, max(0, index1))
    satval = satlist[index]

    def utc2local(utc_time):
        return utc_time.replace(tzinfo=timezone.utc).astimezone()

#get location
    g = geocoder.ip('me')
    lat = g.latlng[0]
    long = g.latlng[1]
    alt = float(10)

#get satellite and TLE data from dict for selected satellite
    sat = satdict[satval]


    now = datetime.now(timezone.utc)
    local_time = str(utc2local(now)).split(".")[0]
    try:
        next_passes = sat.get_next_passes(now, 8, long, lat, alt, tol=0.1, horizon=0)
        next_pass = utc2local(next_passes[0][0])
        second_pass = utc2local(next_passes[0][1])

        p_next_pass = str(utc2local(next_passes[0][0])).split(".")[0].split(" ")[1]
        p_second_pass = str(utc2local(next_passes[0][1])).split(".")[0].split(" ")[1]
        time_until = str(next_pass - now).split(".")[0]
        time_until2 = str((second_pass - now)-(next_pass - now)).split(".")[0]
    except (IndexError, NameError):
        pass

    with canvas(device) as draw:
        try:
            draw.rectangle((0, 0, 128, 64), outline="black", fill="black")
            draw.text((0, 0), f"Satellite: {satval}", fill="white")
            draw.text((0, 10), f"Next Pass: {p_next_pass}", fill="white")
            draw.text((0, 20), f"Until: {p_second_pass}", fill="white")
            draw.text((0, 30), f"Overhead in: {time_until}", fill="white")
            draw.text((0, 40), f"For: {time_until2}", fill="white")
        except (NameError, IndexError):
            draw.rectangle((0, 10, 128, 54), outline="black", fill="black")
            draw.text((0, 10), "No Data", fill="white")
            pass

#refresh when potentiometer value changes outside of +- 3 range
    while True:
        value2 = values(0)
        if not value-3 <= value2 <= value+3:
            break
        else:
            sleep(.1)
