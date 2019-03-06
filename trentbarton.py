from tempfile import gettempdir
from pathlib import Path
from io import BytesIO
from PIL import Image
import requests
import re


TRENT_BARTON_API = 'https://www.trentbarton.co.uk/RTILiveTimings.aspx'
TEMP_DIRECTORY = Path(gettempdir()) / 'trent_barton_live'
TEMP_DIRECTORY.mkdir(parents=True, exist_ok=True)


class Bus:
    """Represents a bus"""

    def __init__(self, data, bus_stop):
        self.data = data
        self.service = Service(self.data['serviceName'], self.data['ServiceId'])
        self.name = self.service.name
        self.position = (data['longitude'], data['latitude'])
        self.bus_stop = bus_stop

    @property
    def due(self):
        """Returns the time until the bus is due in minutes"""
        return 0 if self.data['dueIn'] == 'due' else int(self.data['dueIn'][:-4])

    @property
    def icon(self):
        """Downloads the service icon and returns the Path of the file"""
        icon_url = re.findall(r'<img src="(.*?)"', self.data['serviceIcon'])[0]
        icon_local = TEMP_DIRECTORY / (Path(icon_url).name[:-4] + '.ico')
        response = requests.get(f'https://www.trentbarton.co.uk{icon_url}')
        image = Image.open(BytesIO(response.content))
        image.save(icon_local)
        return icon_local

    def __str__(self):
        return f'{self.name} ({self.bus_stop})'


class BusStop:
    """Represents a Trent Barton bus stop"""

    def __init__(self, name, stop_id):
        self.name = name
        self.stop_id = stop_id

    def get_live_times(self):
        """Gets the live times for the buses at this stop"""
        response = requests.get(TRENT_BARTON_API, {'m': 'GetRtiFull',
                                                   'stop': self.stop_id})
        return [Bus(data, bus_stop=self) for data in response.json()[0]['result']]

    def get_position(self):
        """Gets the position of the bus stop in longitude and latitude"""
        response = requests.get(TRENT_BARTON_API, {'m': 'GetLongLat',
                                                   'stopId': self.stop_id})
        return response.json()

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'BusStop({repr(self.name)}, {repr(self.stop_id)})'

class Service:
    """Represents a Trent Barton bus service"""

    def __init__(self, name, service_id):
        self.name = name
        self.service_id = service_id

    def get_directions(self):
        """Gets all the directions for the service"""
        response = requests.get(TRENT_BARTON_API, {'m': 'GetDirections',
                                                   'service': self.service_id})
        return response.json()

    def get_stops(self, directions=None):
        """Gets all the bus stops for the service, you may specify the specific direction(s) you want"""
        if not directions:
            directions = self.get_directions()
        stops = []
        for direction in directions:
            response = requests.get(TRENT_BARTON_API, {'m': 'GetStops',
                                                       'direction': direction['Id'],
                                                       'locality': -1})
            stops.extend([BusStop(data['Name'], data['Id']) for data in response.json()])
        return stops

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'Service({repr(self.name)}, {repr(self.service_id)})'

    @classmethod
    def get_service(cls, name):
        response = requests.get(TRENT_BARTON_API, {'m': 'GetServices'})
        for service_data in response.json():
            if service_data['Name'] == name:
                return Service(service_data['Name'], service_data['Id'])


if __name__ == '__main__':
    harlequin = Service.get_service('harlequin')
    stops = harlequin.get_stops()
    for stop in stops:
        if stop.name == 'Chain Lane':
            chain_lane = stop
            break

    for times in chain_lane.get_live_times():
        print(times)