import math
from enum import IntEnum

import pymunk


class Layer(IntEnum):
    KILLS = 1
    STUNS = 2
    KNOCKBACKS = 3
    ENDS_LEVEL = 4
    NORMAL = 5
    INTERACTABLE = 6
    PLAYER = 7
    DIGGABLE = 8
    GRAPPLE_TARGET = 9
    ROLL_BREAKABLE = 10


class PhysicsBody:
    """Wraps a pymunk Body + Shape pair and adds it to a PhysicsSpace."""

    def __init__(self, physics_space, position, shape_factory, density, friction,
                 layer=Layer.NORMAL, body_type=pymunk.Body.DYNAMIC):
        self.body = pymunk.Body(body_type=body_type)
        self.body.position = position
        self.shape = shape_factory(self.body)
        self.shape.density = density
        self.shape.friction = friction
        self.shape.collision_type = layer.value
        physics_space.space.add(self.body, self.shape)

    @property
    def position(self):
        return self.body.position

    @position.setter
    def position(self, value):
        self.body.position = value

    @property
    def angle(self):
        return math.degrees(self.body.angle)

    @angle.setter
    def angle(self, degrees):
        self.body.angle = math.radians(degrees)


class PhysicsSpace:
    """Wraps a pymunk Space: owns entity lookup, layer collisions and the event log."""

    def __init__(self, gravity=(0, 900)):
        self.space = pymunk.Space()
        self.space.gravity = gravity
        self.entities = {}  # shape -> entity
        self.events = []    # collision events, in the order they happened

    def register_entity(self, shape, entity):
        self.entities[shape] = entity

    def remove_shape(self, shape):
        self.space.remove(shape.body, shape)
        self.entities.pop(shape, None)

    def add_event(self, event):
        self.events.append(event)

    def on_layers_collide(self, layer_a, layer_b):
        def begin(arbiter, space, data):
            shape_a, shape_b = arbiter.shapes
            self.add_event((layer_a, layer_b, self.entities.get(shape_a), self.entities.get(shape_b)))
            return True
        self.space.on_collision(layer_a.value, layer_b.value, begin=begin)


if __name__ == "__main__":
    physics_space = PhysicsSpace()
    physics_space.on_layers_collide(Layer.KILLS, Layer.PLAYER)

    hazard = PhysicsBody(physics_space, (0, 0), lambda b: pymunk.Circle(b, 10), 1, 0.5,
                          layer=Layer.KILLS, body_type=pymunk.Body.STATIC)
    physics_space.register_entity(hazard.shape, "hazard")

    player = PhysicsBody(physics_space, (0, 5), lambda b: pymunk.Circle(b, 10), 1, 0.5,
                          layer=Layer.PLAYER)
    physics_space.register_entity(player.shape, "player")

    for _ in range(5):
        physics_space.space.step(1 / 60)

    assert physics_space.events, "expected a KILLS/PLAYER collision event"
    assert physics_space.events[0][2:] == ("hazard", "player")
    assert player.angle == 0
    print("ok:", physics_space.events[0])
