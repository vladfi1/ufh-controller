import asyncio
import dataclasses
import functools
import inspect
import typing as tp
from typing import Any

from neohubapi import neohub

def wrap_async_function(coroutine_function):
  assert asyncio.iscoroutinefunction(coroutine_function)

  @functools.wraps(coroutine_function)
  def function(*args, **kwargs):
    return asyncio.run(coroutine_function(*args, **kwargs))

  return function

class SyncObject:
  """Synchronous object."""

  def __init__(self, obj: tp.Any):
    self._base_obj = obj

    for name, member in inspect.getmembers(obj):
      if name.startswith('__'):
        continue

      if asyncio.iscoroutinefunction(member):
        setattr(self, name, wrap_async_function(member))
      else:
        setattr(self, name, member)

class NeoHubSync(SyncObject):
  """Synchronous NeoHub."""

  def __init__(self, host: str, token: tp.Optional[str]):
    port = 4242 if token is None else 4243
    super().__init__(neohub.NeoHub(host, port, token=token))

  def get_live_data_sync(self) -> tp.Tuple[object, tp.Dict[str, tp.List[SyncObject]]]:
    hub_data, devices = self.get_live_data()
    return hub_data, {
        key: [SyncObject(device) for device in devices]
        for key, devices in devices.items()
    }
