import multiprocessing


# _____________________________________________________________________________
class IncCounter(object):
    def __init__(self, value=0):
        self.val = multiprocessing.Value('i', value)

    def inc(self):
        with self.val.get_lock():
            self.val.value += 1

    @property
    def value(self):
        with self.val.get_lock():
            return self.val.value

    @property
    def inc_value(self):
        with self.val.get_lock():
            self.val.value += 1
            return self.val.value
