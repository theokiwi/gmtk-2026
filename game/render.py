import pygame

class Animator:
    def __init__(self, animations, fps=60, triggers=None, initial_state="still", dir=1):
        self.animations = animations
        self.state = initial_state
        self.dir = dir
        self.index = 0
        self.time = 0.0
        self.frame_duration = 1/fps
        self.triggers = triggers or {}
        self.on_trigger = None

    # informs external sources of the current frame playing
    def _trigger(self, event):
        event = self.trigger.get(self.state, {}).get(self.index)
        if event and self.on_trigger:
            self.on_trigger(event)

    # define which strip from the spritesheet is playing, recognizes changes
    def play(self, state, dir=1):
        self.dirr = dir
        if state != self.state:
            self.index, self.time, state = 0, 0.0, state
            self._trigger

    # changes to next frame after a certain predefined time
    def update(self, dt):
        self.time += dt
        while self.time >= self.frame_duration:
            self.time -= self.frame_duration
            self.index = (self.index + 1) % len(self.frames)
            self._trigger