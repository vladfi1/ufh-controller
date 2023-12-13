import collections
import datetime
import enum
import time

from absl import app, flags

from neohub_sync import NeoStatSync
from record_lib import get_device, get_db
import derivatives

FREQUENCY = flags.DEFINE_integer('frequency', 20, 'in minutes')
TARGET = flags.DEFINE_float('target', 21.5, 'target temperature')
COLLECTION = flags.DEFINE_string('collection', 'control', 'mongodb collection')

P = flags.DEFINE_float('p', 1, 'proportional gain')
I = flags.DEFINE_float('i', 0, 'integral gain')
D = flags.DEFINE_float('d', 10, 'derivative gain')


class PIDController:
  def __init__(self, K_p, K_i, K_d, set_point, scale):
    self.K_p = K_p
    self.K_i = K_i
    self.K_d = K_d
    self.set_point = set_point
    self.integral = 0
    self.previous_time = None
    # self.derivative = derivatives.StencilDerivative(max_points=16, max_time=scale)
    self.derivative = derivatives.WindowDerivative(scale=scale)

  def update(self, current_temperature, current_time) -> float:
    dt = 0 if self.previous_time is None else current_time - self.previous_time
    self.previous_time = current_time
    error = self.set_point - current_temperature
    self.integral += error * dt
    derivative = -self.derivative.update(current_temperature, current_time)
    output = self.K_p * error + self.K_i * self.integral + self.K_d * derivative
    stats = {'p': error, 'i': self.integral, 'd': derivative, 'o': output}
    return output, stats

# Safe values so we don't do anything too crazy by accident.
MAX_TEMP = 22.5
MIN_TEMP = 20.0

def turn_on(device: NeoStatSync):
  device.set_target_temperature(MAX_TEMP)

def turn_off(device: NeoStatSync):
  device.set_target_temperature(MIN_TEMP)

def default_controller(set_point) -> PIDController:
  return PIDController(
    K_p=P.value,
    K_i=I.value,
    K_d=D.value,
    scale=10,  # minutes
    set_point=set_point)

class Control(enum.Enum):
  NONE = 0
  OFF = 1
  ON = 2

def main(_):
  db = get_db()
  controller = default_controller(TARGET.value)

  dt = FREQUENCY.value
  while True:
    device = get_device()
    current_temperature = float(device.temperature)
    current_time = time.time()
    current_time_minutes = current_time / 60
    output, stats = controller.update(
      current_temperature, current_time_minutes)

    stats['t'] = current_temperature
    stats['h'] = device.heat_on

    control = Control.NONE
    if output > 0 and not device.heat_on:
      turn_on(device)
      control = Control.ON
    elif output <= 0 and device.heat_on:
      turn_off(device)
      control = Control.OFF

    template = 't={t:.1f} on={h} p={p:.1f} i={i:.1f} d={d:.3f} o={o:.1f} c={c}'
    now = datetime.datetime.today()
    print(now.isoformat(timespec='seconds'), template.format(c=control.name, **stats))

    to_log = {
      'timestamp': int(current_time),
      'temperature': stats['t'],
      'target_temperature': float(device.target_temperature),
      'heat_on': stats['h'],
      'p': stats['p'],
      'i': stats['i'],
      'd': stats['d'],
      'output': stats['o'],
      'control': control.name,
      'set_point': TARGET.value,
    }
    db[COLLECTION.value].insert_one(to_log)

    time.sleep(dt * 60)

if __name__ == '__main__':
  app.run(main)
