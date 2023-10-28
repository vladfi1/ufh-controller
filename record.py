import time

from absl import app, flags
from record_lib import record

FREQUENCY = flags.DEFINE_integer('frequency', 2 * 60, 'in seconds')
COLLECTION = flags.DEFINE_string('collection', 'test', 'mongodb collection')

def main(_):
  while True:
    try:
      record(collection=COLLECTION.value)
    except Exception as e:
      print(e)
    time.sleep(FREQUENCY.value)

if __name__ == '__main__':
  app.run(main)
