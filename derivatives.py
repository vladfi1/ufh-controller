import abc
import collections
import math
import numpy as np

class Derivative(abc.ABC):
  """Estimates derivative given historical data."""

  @abc.abstractmethod
  def update(self, x: float, t: float) -> float:
    """Add a new datapoint and get the current derivative estimate."""

class WindowDerivative(Derivative):
  """Estimates derivative given historical data."""

  def __init__(self, scale: float):
    self.history = collections.deque()
    self.scale = scale

  def update(self, x, t):
    self.history.append((t, x))
    if len(self.history) == 1:
      return 0

    cutoff = t - self.scale
    while (self.history[0][0] < cutoff) and len(self.history) > 2:
      self.history.popleft()

    t0, x0 = self.history[0]
    return (x - x0) / (t - t0)

def derivative_estimate(stencil, values, order=1):
  """Uses a custom stencil to estimate the derivative.

    Based on https://web.media.mit.edu/~crtaylor/calculator.html.
  """
  n = len(stencil)
  m = np.zeros((n, n))
  for i in range(n):
    m[i] = stencil ** i
  b = np.zeros(n)
  b[order] = math.factorial(order)
  c = np.linalg.solve(m, b)
  return np.dot(c, values)

class StencilDerivative(Derivative):

  def __init__(self, max_points: int, max_time: float):
    self.max_points = max_points
    self.max_time = max_time
    self.history = collections.deque()

  def update(self, x, t):
    self.history.append((t, x))

    while len(self.history) > self.max_points:
      self.history.popleft()

    while self.history[-1][0] - self.history[0][0] > self.max_time:
      self.history.popleft()

    if len(self.history) == 1:
      return 0

    ts, xs = zip(*self.history)
    stencil = np.asarray(ts)
    stencil -= stencil[-1]
    return derivative_estimate(stencil, xs)

# Do some tests.
if __name__ == '__main__':
  functions = [np.square, np.sqrt, np.sin, np.cos]
  derivatives = [
    lambda x: 2 * x,
    lambda x: 0.5 / np.sqrt(x),
    lambda x: np.cos(x),
    lambda x: -np.sin(x),
  ]

  for f, df in zip(functions, derivatives):
    ts = np.arange(10)
    endpoint = ts[-1]
    xs = f(ts)
    ts -= endpoint
    estimate = derivative_estimate(ts, xs)
    actual = df(endpoint)
    print(f, derivative_estimate(ts, xs, order=1), actual)
