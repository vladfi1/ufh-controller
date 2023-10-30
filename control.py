import datetime
import time

from absl import app, flags

from record_lib import get_device

FREQUENCY = flags.DEFINE_integer('frequency', 15 * 60, 'in seconds')
TARGET = flags.DEFINE_float('target', 21.0, 'target temperature')

class PIDController:
  def __init__(self, K_p, K_i, K_d, set_point):
    self.K_p = K_p
    self.K_i = K_i
    self.K_d = K_d
    self.set_point = set_point
    self.integral = 0
    self.previous_error = 0

  def update(self, current_temperature, dt) -> float:
    error = self.set_point - current_temperature
    self.integral += error * dt
    derivative = (error - self.previous_error) / dt
    output = self.K_p * error + self.K_i * self.integral + self.K_d * derivative
    self.previous_error = error
    stats = {'p': error, 'i': self.integral, 'd': derivative, 'output': output}
    return output, stats

def turn_on(device):
  device.set_temperature(22)

def turn_off(device):
  device.set_temperature(15)

def default_controller(set_point) -> PIDController:
  return PIDController(K_p=1, K_i=0.1, K_d=5, set_point=set_point)

def main(_):
  controller = default_controller(TARGET.value)

  dt = FREQUENCY.value
  while True:
    device = get_device()
    control, stats = controller.update(float(device.temperature), 1)

    stats['t'] = device.temperature
    stats['h'] = device.heat_on

    template = 't={t} on={h} p={p:.1f} i={i:.1f} d={d:.1f} o={output:.1f}'
    now = datetime.datetime.today()
    print(now.isoformat(timespec='seconds'), template.format(**stats))

    if control > 0 and not device.heat_on:
      turn_on(device)
    elif control <= 0 and device.heat_on:
      turn_off(device)

    time.sleep(dt)

if __name__ == '__main__':
  app.run(main)
