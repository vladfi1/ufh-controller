import asyncio
import functools
import inspect
import typing as tp
from typing import Any

from neohubapi import neohub, neostat

def wrap_async_function(coroutine_function):
  assert asyncio.iscoroutinefunction(coroutine_function)

  @functools.wraps(coroutine_function)
  def function(*args, **kwargs):
    return asyncio.run(coroutine_function(*args, **kwargs))

  return function

T = tp.TypeVar('T')

class SyncObject(tp.Generic[T]):
  """Synchronous object."""

  def __init__(self, obj: T):
    self._base_obj = obj

    for name, member in inspect.getmembers(obj):
      if name.startswith('__'):
        continue

      if asyncio.iscoroutinefunction(member):
        setattr(self, name, wrap_async_function(member))
      else:
        setattr(self, name, member)

class NeoStatSync(SyncObject[neostat.NeoStat], neostat.NeoStat):
  """Fake class for type hinting."""

class NeoHubSync(SyncObject[neohub.NeoHub], neohub.NeoHub):
  """Synchronous NeoHub."""

  def __init__(self, host: str, token: tp.Optional[str] = None):
    port = 4242 if token is None else 4243
    super().__init__(neohub.NeoHub(host, port, token=token))

  def get_neostats(self) -> tuple[dict, tp.List[NeoStatSync]]:
    neostats = []
    hub_data = self.get_live_data()

    for device in hub_data.devices:
      neostats.append(SyncObject(neostat.NeoStat(self._base_obj, device)))

    return hub_data, neostats
