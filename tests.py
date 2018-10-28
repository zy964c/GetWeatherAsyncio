import unittest
import get_weather
import json
import asyncio
from actions import Settings
from unittest.mock import patch

def _run(coro):
    """Run the given coroutine."""
    return asyncio.get_event_loop().run_until_complete(coro)

def AsyncMock(*args, **kwargs):
    """Create an async function mock."""
    m = unittest.mock.MagicMock(*args, **kwargs)

    async def mock_coro(*args, **kwargs):
        return m(*args, **kwargs)

    mock_coro.mock = m
    return mock_coro

get_weather.read_cities()

class TestData(unittest.TestCase):
    def setUp(self):
        with open('settings.json') as s:
            settings = json.load(s)
            Settings.update_opts(settings)
        with open('test_data.json') as t:
            self.test_data = json.load(t)

    def test_parse_cities(self):
        get_weather.read_cities()
        cities = [
        "Moskva", 
        "Novosibirsk",
        "Krasnodar"
        ]
        city_list = get_weather.parse_cities(cities)
        self.assertEqual(city_list, ['1220988', '1496747', '542420'])

    def test_main_loop(self):
        with patch('get_weather.get_data', new=AsyncMock(return_value=self.test_data)):
            get_weather.read_cities()
            try:
                with patch('model.add_record') as mock:
                    _run(get_weather.main_loop('arg'))
                    # from get_weather import get_data
            except AttributeError:
                pass
            args, _ = mock.call_args
            self.assertIn('name', args[1])
            for d in args:
                self.assertNotIn('snow_3h', d)

if __name__ == "__main__":
    unittest.main()
