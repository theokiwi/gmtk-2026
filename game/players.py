import os
import sys

# ponytail: no packaging yet (see physics.py/movement.py's bare imports); add repo root
# so config.py is importable regardless of whether this runs as `python players.py`
# (cwd=game/) or `python game/players.py` (cwd=repo root).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
import pymunk

from config import KEYBINDS
from movement import Movement
from physics import Layer, PhysicsBody
from render import Animator
from skills import Dig, Grapple, Roll


class Player:
    """Combines a PhysicsBody, Movement, Animator and one character skill, driven by pygame input."""

    def __init__(self, physics_body, movement, animator,
                 skill_press, skill_release, skill_update=None, keybinds=None):
        self.physics_body = physics_body
        self.movement = movement
        self.animator = animator
        self.skill_press = skill_press
        self.skill_release = skill_release
        self.skill_update = skill_update
        self.keybinds = keybinds or KEYBINDS
        self.facing = 1
        self.acting = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in self.keybinds["jump"]:
                self.movement.jump()
            elif event.key in self.keybinds["action"]:
                self.acting = True
                self.skill_press()
        elif event.type == pygame.KEYUP:
            if event.key in self.keybinds["jump"]:
                self.movement.release_jump()
            elif event.key in self.keybinds["action"]:
                self.acting = False
                self.skill_release()

    def update(self, dt, keys):
        direction = int(any(keys[k] for k in self.keybinds["right"])) - \
                    int(any(keys[k] for k in self.keybinds["left"]))
        self.movement.walk(direction)
        self.movement.update(dt)
        if self.skill_update:
            self.skill_update(dt)
        if direction:
            self.facing = 1 if direction > 0 else -1
        self._sync_animation(direction, dt)

    def _sync_animation(self, direction, dt):
        if self.acting:
            state = "action"
        elif not self.movement.grounded:
            state = "jump"
        elif direction:
            state = "walk"
        else:
            state = "still"
        self.animator.play(state, dir=self.facing)
        self.animator.update(dt)


CHARACTERS = {
    "marmot": dict(radius=12, density=2.0, friction=1.0, speed=110, jump_speed=260,
                   air_control=0.4, coyote_time=0.1, skill_cls=Dig),
    "monkey": dict(radius=8, density=0.6, friction=0.8, speed=190, jump_speed=320,
                   air_control=1.0, coyote_time=0.12, skill_cls=Grapple),
    "crocodile": dict(radius=14, density=2.5, friction=1.2, speed=90, jump_speed=240,
                       air_control=0.3, coyote_time=0.08, skill_cls=Roll),
}


def make_player(kind, physics_space, position, animations, keybinds=None):
    cfg = CHARACTERS[kind]
    body = PhysicsBody(physics_space, position, lambda b: pymunk.Circle(b, cfg["radius"]),
                        cfg["density"], cfg["friction"], layer=Layer.PLAYER)
    movement = Movement(body, cfg["speed"], cfg["jump_speed"], cfg["air_control"], cfg["coyote_time"])
    skill = cfg["skill_cls"](body, physics_space)
    animator = Animator(animations)

    if cfg["skill_cls"] is Dig:
        press, release, upd = skill.dig, (lambda: None), None
    elif cfg["skill_cls"] is Grapple:
        press, release, upd = skill.start_grapple, skill.stop_grapple, skill.update
    else:  # Roll
        press, release, upd = skill.start_roll, skill.stop_roll, skill.update

    return Player(body, movement, animator, press, release, upd, keybinds)


if __name__ == "__main__":
    from collections import defaultdict

    from physics import PhysicsSpace

    animations = {"still": [0], "walk": [0, 1], "jump": [0], "action": [0]}
    dt = 1 / 60

    def key_event(kind, key):
        return pygame.event.Event(kind, key=key)

    # --- jump keybind ---
    physics_space = PhysicsSpace()
    ground = PhysicsBody(physics_space, (0, 50), lambda b: pymunk.Segment(b, (-200, 0), (200, 0), 1),
                          1, 1, layer=Layer.NORMAL, body_type=pymunk.Body.STATIC)
    marmot = make_player("marmot", physics_space, (0, 0), animations)
    for _ in range(120):
        physics_space.space.step(dt)
        marmot.movement.update(dt)
    assert marmot.movement.grounded
    marmot.handle_event(key_event(pygame.KEYDOWN, pygame.K_SPACE))
    assert marmot.physics_body.body.velocity.y < 0, "space should trigger a jump"
    print("ok: jump keybind moves the marmot upward")

    # --- action keybind: press starts the monkey's grapple, release stops it ---
    physics_space = PhysicsSpace()
    body = PhysicsBody(physics_space, (0, 0), lambda b: pymunk.Circle(b, 8), 0.6, 0.8, layer=Layer.PLAYER)
    movement = Movement(body, speed=190, jump_speed=320, air_control=1.0, coyote_time=0.12)
    grapple = Grapple(body, physics_space)
    monkey = Player(body, movement, Animator(animations), grapple.start_grapple, grapple.stop_grapple,
                    grapple.update)
    anchor = PhysicsBody(physics_space, (100, 0), lambda b: pymunk.Circle(b, 10), 1, 1,
                          layer=Layer.GRAPPLE_TARGET, body_type=pymunk.Body.STATIC)

    monkey.handle_event(key_event(pygame.KEYDOWN, pygame.K_q))
    assert monkey.acting and grapple.target is anchor.shape, "q should start the grapple"
    monkey.handle_event(key_event(pygame.KEYUP, pygame.K_q))
    assert not monkey.acting and grapple.target is None, "releasing q should stop the grapple"
    print("ok: q keybind starts/stops the monkey's grapple")

    # --- animation state follows acting/airborne/walk/still ---
    physics_space = PhysicsSpace()
    croc = make_player("crocodile", physics_space, (0, 0), animations)
    keys = defaultdict(bool)
    croc.update(dt, keys)
    assert croc.animator.state == "jump", "airborne with no input should play the jump/fall state"
    croc.handle_event(key_event(pygame.KEYDOWN, pygame.K_q))
    croc.update(dt, keys)
    assert croc.animator.state == "action", "holding the action key should override to the action state"
    print("ok: animation state tracks acting/airborne/walk/still")
