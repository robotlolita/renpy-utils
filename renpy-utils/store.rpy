init -100 python:

  class StoreBackedObject(object):
    #: (self, str) -> unit
    def __init__(self, slot_name):
      self.slot_name = slot_name

    #: (self, a) -> unit
    def store(self, value):
      renpy.store.__setattr__(self.slot_name, value)

    #: (self, a?) -> a | None
    def load(self, default=None):
      try:
        return renpy.store.__getattribute__(self.slot_name)
      except AttributeError:
        return default


  class StoreBackedSet(StoreBackedObject):
    #: (self, str) -> unit
    def __init__(self, slot_name):
      super(StoreBackedSet, self).__init__("store_set__" + slot_name)

    #: (self) -> StoreBackedSet(a)
    def load(self):
      return super(StoreBackedSet, self).load(default=set())

    #: (self, a) -> bool
    def __contains__(self, value):
      return value in self.load()

    #: (self, a) -> StoreBackedSet(a)
    def add(self, value):
      old = self.load()
      old.add(value)
      self.store(old)
      return self

    #: (self) -> StoreBackedSet(a)
    def reset(self):
      self.store(set())
      return self

    #: (self, a) -> StoreBackedSet(a)
    def remove(self, value):
      old = self.load()
      if value in old:
        old.remove(value)
        self.store(old)
      return self

  