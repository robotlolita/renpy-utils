#! requires store.rpy
init -99 python:

  class StateMachineDisplayable(renpy.Displayable, StoreBackedObject):
    #: (self, str, a, { a: Displayable }) -> unit
    def __init__(self, slot, initial_state, states, **properties):
      super(StateMachineDisplayable, self).__init__(**properties)
      StoreBackedObject.__init__(self, "smd_state__" + slot)

      self.old_state = None
      self.current_state = None
      self.states = states

      self.transition = None
      self.displayable = None

      self.shown_time = 0
      self.anim_time = 0

      self.reset = False
      self.set_state(initial_state)

    #: (self, a) -> Displayable
    def snapshot(self, state=None):
      if state is None:
        state = self.current_state
      return self.states.get(state) or Null()

    #: (self) -> unit
    def redraw(self):
      self.reset = True
      renpy.redraw(self, 0)

    #: (self, a, Transition) -> unit
    def set_state(self, new_state, transition=None):
      self.current_state = new_state
      self.old_state = self.load()
      self.store(new_state)

      old_d = self.states.get(self.old_state) or Null()
      cur_d = renpy.easy.displayable(self.states.get(new_state) or Null())
      self.displayable = cur_d
      self.transition = anim.TransitionAnimation(old_d, 0.0, transition, cur_d)
      self.redraw()

    #: (self) -> a | None
    def state(self):
      return self.load()

    #: (self) -> unit
    def per_interact(self):
      new_state = self.load()

      if self.current_state != new_state:
        self.set_state(new_state)

      if renpy.is_start_interact() and not self.reset:
        self.transition = None
        self.redraw()

    #: (self) -> Displayable
    def current_displayable(self):
      return self.transition or self.displayable

    #: (self, int, int, int, int) -> renpy.Render
    def render(self, width, height, st, at):
      if self.reset:
        self.reset = False
        self.shown_time = st
        self.anim_time = at

      d = self.current_displayable()
      if d:
        return renpy.render(d, width, height, st - self.shown_time, at - self.anim_time)
      else:
        return renpy.Render(0, 0)

    #: (self) -> list(Displayable)
    def visit(self):
      return [self.transition, self.displayable]


  class ComposedSpriteAccessor(object):
    #: (self) -> a | None
    def state(self):
      pass

    #: (self, a, Transition?) -> unit
    def update(self, new_state, transition=None):
      pass


  class ComposedSpriteIdentityAccessor(object):
    #: (StateMachineDisplayable(a)) -> unit
    def __init__(self, displayable):
      self.displayable = displayable

    #: (self) -> a | None
    def state(self):
      return self.displayable.current_state

    #: (self, a, Transition?) -> unit
    def update(self, new_state, transition=None):
      self.displayable.set_state(new_state, transition)


  class ComposedSpriteTupleAccessor(object):
    #: (StateMachineDisplayable(a), int, int) -> unit
    def __init__(self, displayable, length, index):
      self.displayable = displayable
      self.index = index
      self.length = length

    #: (self) -> a | None
    def state(self):
      if self.displayable.current_state is not None:
        return self.displayable.current_state[self.index]
    
    #: (self, a, Transition?) -> unit
    def update(self, new_state, transition=None):
      state = self.displayable.current_state
      if state is None:
        state = [None for x in xrange(0, self.length)]
      else:
        state = list(state)

      state[self.index] = new_state
      self.displayable.set_state(tuple(state), transition)



  class ComposedSprite(object):
    #: (self, (int, int), (a | None, (int, int), Displayable)...) -> unit
    def __init__(self, size, *layers):
      self.size = size
      self.layers = layers
      self.layer_map = {}

      for (name, _, displayable) in layers:
        if isinstance(name, tuple):
          for (index, layer_name) in enumerate(name):
            self.layer_map[layer_name] = ComposedSpriteTupleAccessor(displayable, len(name), index)
        elif name is not None:
          self.layer_map[name] = ComposedSpriteIdentityAccessor(displayable)

    #: (self, Transition?, **{ a: any }) -> unit
    def set_state(self, transition=None, **kwargs):
      for key in kwargs:
        self.layer_map[key].update(kwargs[key], transition)

    #: (self) -> (any...)
    def state(self):
      return tuple([d.state() for (name, _, d) in self.layers if name is not None])

    # TODO: snapshots

    #: (self) -> Displayable
    def displayable(self):
      flatten = lambda xss: reduce(lambda r, x: r + x, xss, [])

      return LiveComposite(
        self.size,
        *flatten([[pos, displayable] for (_, pos, displayable) in self.layers])
      )