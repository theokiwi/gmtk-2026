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
    def _trigger(self):
        event = self.triggers.get(self.state, {}).get(self.index)
        if event and self.on_trigger:
            self.on_trigger(event)

    # define which strip from the spritesheet is playing, recognizes changes
    def play(self, state, dir=1):
        self.dir = dir
        if state != self.state:
            self.index, self.time, self.state = 0, 0.0, state
            self._trigger()

    # changes to next frame after a certain predefined time
    def update(self, dt):
        self.time += dt
        while self.time >= self.frame_duration:
            self.time -= self.frame_duration
            self.index = (self.index + 1) % len(self.animations[self.state])
            self._trigger()


if __name__ == "__main__":
    animations = {"still": [0], "walk": [0, 1, 2]}
    triggers = {"walk": {1: "footstep"}}
    animator = Animator(animations, fps=60, triggers=triggers)

    fired = []
    animator.on_trigger = fired.append

    animator.play("walk")
    assert animator.state == "walk", "play() should switch state"
    assert animator.index == 0

    dt = 1 / 60
    for _ in range(3):
        animator.update(dt)
    assert animator.index == 0, "3 frames at fps=60 should wrap back to frame 0 of a 3-frame strip"
    assert fired == ["footstep"], "on_trigger should fire once when index reaches 1"

    animator.play("still")
    assert animator.state == "still" and animator.index == 0
    print("ok: play() switches state, update() advances/wraps frames, on_trigger fires")