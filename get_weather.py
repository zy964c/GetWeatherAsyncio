#!/home/roman/.local/share/virtualenvs/get_weather_async-WkeQEiRa/bin/python3.7

import aiohttp
import asyncio
import model
import json
import time
import logging
import logging.handlers
import sys
import itertools
from pprint import pprint, pformat
from collections import defaultdict, abc
from actions import Settings

api_key = 'fill_this_out'
LOG_FILENAME = 'log'

my_logger = logging.getLogger('my_logger')
my_logger.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(
              LOG_FILENAME, maxBytes=1*10**6, backupCount=5)
handler_console = logging.StreamHandler()
handler_console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(threadName)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
handler_console.setFormatter(formatter)
my_logger.addHandler(handler)
my_logger.addHandler(handler_console)

async def get_data(payload):
    timeout = aiohttp.ClientTimeout(total=5)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get('http://api.openweathermap.org/data/2.5/group', params=payload) as resp:
            recieved_data = await resp.json()
            return recieved_data

async def read_settings(fp, timeout, event):
    """
    reads settings file every "timeout" seconds
    """
    while True:
        with open(fp) as s:
            settings = json.load(s)
            old_timeout = Settings.options['refresh_period']
            if settings != Settings.options:
                Settings.update_opts(settings)
                my_logger.info('Settings updated')
                if old_timeout != Settings.options['refresh_period']:
                    event.set()
                    event.clear()
        await asyncio.sleep(timeout)

async def main():
    with open('settings.json') as s:
            settings = json.load(s)
            Settings.update_opts(settings)
    read_cities()
    my_logger.info('cities data read complete')
    event = asyncio.Event()
    coros = [read_settings('settings.json', 10, event), main_loop(event), spinner()]
    tasks = {asyncio.ensure_future(coro) for coro in coros}
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
    for done_task in done:
        if done_task.exception() is not None:
            my_logger.exception(done_task.exception())
    for pending_task in pending:
        pending_task.cancel()
    
async def main_loop(event):
    while True:
        if len(Settings.options) != 0:
            cities = parse_cities(Settings.options['cities'])
            params = {'id': ','.join(cities), 'APPID': api_key}
            data_dl = await get_data(params)
            if data_dl.get('cod', None) == 401:
                raise(Exception('api key is incorrect'))
            for data_raw in data_dl['list']:
                    my_logger.debug(pformat(data_raw)) 
                    data = defaultdict(dict, data_raw)
                    data_weather_all = {'dt': data['dt'],
                                        'base': data['base'],
                                        'wind_speed': data['wind'].get('speed', {}),
                                        'wind_deg': data['wind'].get('deg', {}),
                                        'clouds_all': data['clouds'].get('all', {}),
                                        'rain_3h': data['rain'].get('3h', {}),
                                        'snow_3h': data['snow'].get('3h', {}),
                                        'cod': data['cod'],
                                        'main_temp': data['main'].get('temp', {}),
                                        'main_pressure': data['main'].get('pressure', {}),
                                        'main_humidity': data['main'].get('humidity', {}),
                                        'main_temp_min': data['main'].get('temp_min', {}),
                                        'main_temp_max': data['main'].get('temp_max', {}),
                                        'main_sea_level': data['main'].get('sea_level', {}),
                                        'main_grnd_level': data['main'].get('grnd_level', {}),}

                    data_filtered = filter_input(data_weather_all)
                    model.add_record(data_filtered, data_raw)
            try:
                    await asyncio.wait_for(event.wait(), int(Settings.options['refresh_period']))
            except asyncio.TimeoutError:
                    pass
                
def read_cities():
    with open('city.list.json') as s:
        all_cities_data = json.load(s)
        Settings.cities.update({d['name']: str(d['id']) for d in all_cities_data})

def parse_cities(cities):
    city_ids = []
    for city in cities:
        city_ids.append(Settings.cities[city])
    return city_ids
                
def filter_input(mapping):
    empty_keys = []
    for key in mapping:
        if isinstance(mapping[key], abc.Mapping):
            if len(mapping[key]) == 0:
                empty_keys.append(key)
    for key in empty_keys:
        mapping.pop(key)
    return mapping

async def spinner():
    write, flush = sys.stdout.write, sys.stdout.flush
    for c in itertools.cycle('|/-\\'):
        write(c)
        flush()
        write('\x08')
        try:
            await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            break
    write(' /x08')

if __name__ == "__main__":
    asyncio.run(main())
