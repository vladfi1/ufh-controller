"""Record data from the NeoHub to a database."""

import functools
import os
import typing as tp
from pymongo import MongoClient

from neohubapi import neohub
from neohub_sync import NeoHubSync, NeoStatSync

DEVICE_NAME = 'Vlads Room'

@functools.lru_cache()
def get_db(mongo_uri="mongodb://localhost:27017/"):
  mongo_uri = mongo_uri or os.environ['MONGO_URI']
  client = MongoClient(mongo_uri)
  return client.deep_end_thermostat

hub = NeoHubSync(
    host=os.environ['NEOHUB_IP'],
    token=os.environ.get('NEOHUB_TOKEN'))

D = tp.TypeVar('D')  # NeoStat or SyncObject

class DeviceNotFound(neohub.Error):
  pass

def find_device(devices: tp.List[D], name: str = DEVICE_NAME) -> D:
  for device in devices:
    if device.name == name:
      return device
  raise DeviceNotFound(f"Device '{DEVICE_NAME}' not found.")

def get_device(name: str = DEVICE_NAME):
  return find_device(hub.get_neostats()[1], name)

def device_and_time(name: str = DEVICE_NAME) -> tuple[int, NeoStatSync]:
  """Returns (timestamp, device)."""
  hub_data, devices = hub.get_neostats()
  device = find_device(devices, name)
  return hub_data.HUB_TIME, device

def get_data():
  hub_time, device = device_and_time()

  data = {
    'timestamp': hub_time,
    'heat_on': device.heat_on,
    'temperature': float(device.temperature),
    'target_temperature': float(device.target_temperature),
  }

  return data

def record(collection: str = 'test', db=None):
  """Reads and records data."""
  data = get_data()
  print(data)
  db = db or get_db()
  db[collection].insert_one(data)
