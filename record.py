"""Record data from the NeoHub to a database."""

import functools
import os
import time
import typing as tp
from pymongo import MongoClient

from neohub_sync import NeoHubSync

DEVICE_NAME = 'Vlads Room'

@functools.lru_cache()
def get_db(mongo_uri="mongodb://localhost:27017/"):
  mongo_uri = mongo_uri or os.environ['MONGO_URI']
  client = MongoClient(mongo_uri)
  return client.deep_end_thermostat

hub = NeoHubSync(
    host=os.environ['NEOHUB_IP'],
    token=os.environ['NEOHUB_TOKEN'])

D = tp.TypeVar('D')  # NeoStat or SyncObject

def find_device(devices: tp.Dict[str, tp.List[D]], name: str = DEVICE_NAME) -> D:
  for device in devices['thermostats']:
    if device.name == name:
      return device
  raise RuntimeError(f"Device '{DEVICE_NAME}' not found.")

def get_device(name: str = DEVICE_NAME):
  _, devices = hub.get_live_data_sync()
  return find_device(devices, name)

def get_data():
  hub_data, devices = hub.get_live_data()
  device = find_device(devices)

  data = {
    'timestamp': hub_data.HUB_TIME,
    'heat_on': device.heat_on,
    'temperature': float(device.temperature),
    'target_temperature': float(device.target_temperature),
  }

  return data

def record(collection='test', db=None):
  """Reads and records data."""
  data = get_data()
  print(data)
  db = db or get_db()
  db[collection].insert_one(data)


if __name__ == '__main__':
  FREQUENCY = 2 * 60

  while True:
    try:
      record()
    except Exception as e:
      print(e)
    time.sleep(FREQUENCY)
