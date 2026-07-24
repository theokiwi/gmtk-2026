import pymunk

from physics import Layer


def _shapes_touching(body, layer):
    matches = []

    def check(arbiter):
        if arbiter.shapes[1].collision_type == layer.value:
            matches.append(arbiter.shapes[1])

    body.each_arbiter(check)
    return matches


class Dig:
    """Marmot: destroys a touched DIGGABLE object and whatever rests on top of it."""

    def __init__(self, physics_body, physics_space):
        self.physics_body = physics_body
        self.physics_space = physics_space

    def dig(self):
        touching = _shapes_touching(self.physics_body.body, Layer.DIGGABLE)
        if not touching:
            return
        target = touching[0]
        to_remove = [target] + self._resting_on_top(target)
        for shape in to_remove:
            self.physics_space.remove_shape(shape)

    def _resting_on_top(self, shape):
        above = []
        digger_shape = self.physics_body.shape

        def check(arbiter):
            other = arbiter.shapes[1]
            if arbiter.normal.y < -0.5 and other is not digger_shape:
                above.append(other)

        shape.body.each_arbiter(check)
        return above


class Grapple:
    """Monkey: pulls toward (or pulls in) the nearest GRAPPLE_TARGET in range."""

    def __init__(self, physics_body, physics_space, range=200, pull_speed=400, release_distance=20):
        self.physics_body = physics_body
        self.physics_space = physics_space
        self.range = range
        self.pull_speed = pull_speed
        self.release_distance = release_distance
        self.target = None

    def start_grapple(self):
        self.target = self._find_target()

    def stop_grapple(self):
        self.target = None

    def update(self, dt):
        if self.target is None:
            return
        if self.target.space is None:  # target was destroyed elsewhere mid-pull
            self.target = None
            return
        body = self.physics_body.body
        offset = self.target.body.position - body.position
        if offset.length <= self.release_distance:
            self.target = None
            return
        pull = offset.normalized() * self.pull_speed
        if self.target.body.body_type == pymunk.Body.DYNAMIC:
            self.target.body.velocity = -pull  # pull the object toward the monkey
        else:
            body.velocity = pull  # pull the monkey toward the anchor

    def _find_target(self):
        body = self.physics_body.body
        hits = self.physics_space.space.point_query(body.position, self.range, pymunk.ShapeFilter())
        candidates = [h for h in hits if h.shape.collision_type == Layer.GRAPPLE_TARGET.value]
        if not candidates:
            return None
        return min(candidates, key=lambda h: h.distance).shape


class Roll:
    """Crocodile: while rolling, destroys any touched ROLL_BREAKABLE wall (no break-above)."""

    def __init__(self, physics_body, physics_space):
        self.physics_body = physics_body
        self.physics_space = physics_space
        self.rolling = False

    def start_roll(self):
        self.rolling = True

    def stop_roll(self):
        self.rolling = False

    def update(self, dt):
        if not self.rolling:
            return
        for shape in _shapes_touching(self.physics_body.body, Layer.ROLL_BREAKABLE):
            self.physics_space.remove_shape(shape)


if __name__ == "__main__":
    from physics import PhysicsBody, PhysicsSpace

    dt = 1 / 60

    # --- Dig ---
    # "resting on top" target must be dynamic.
    physics_space = PhysicsSpace()
    dirt = PhysicsBody(physics_space, (0, 50), lambda b: pymunk.Segment(b, (-100, 0), (100, 0), 1),
                        1, 1, layer=Layer.DIGGABLE, body_type=pymunk.Body.STATIC)
    marmot = PhysicsBody(physics_space, (-30, 0), lambda b: pymunk.Circle(b, 10), 1, 1, layer=Layer.PLAYER)
    rock = PhysicsBody(physics_space, (30, 0), lambda b: pymunk.Circle(b, 10), 1, 1, layer=Layer.NORMAL)

    for _ in range(120):
        physics_space.space.step(dt)

    dig = Dig(marmot, physics_space)
    dig.dig()
    assert dirt.shape.space is None, "diggable target should be removed"
    assert rock.shape.space is None, "object resting on top should also be removed"
    assert marmot.shape.space is not None, "the digger itself must not be destroyed"

    dig.dig()  # nothing diggable touching anymore, should be a no-op and not error
    print("ok: dig removed target + object on top, spared the marmot")

    # --- Grapple: pull self toward a static anchor ---
    physics_space = PhysicsSpace()
    monkey = PhysicsBody(physics_space, (0, 0), lambda b: pymunk.Circle(b, 10), 1, 1, layer=Layer.PLAYER)
    anchor = PhysicsBody(physics_space, (100, 0), lambda b: pymunk.Circle(b, 10), 1, 1,
                          layer=Layer.GRAPPLE_TARGET, body_type=pymunk.Body.STATIC)
    grapple = Grapple(monkey, physics_space, range=200, pull_speed=400, release_distance=25)

    grapple.start_grapple()
    assert grapple.target is anchor.shape
    for _ in range(60):
        physics_space.space.step(dt)
        grapple.update(dt)
        if grapple.target is None:  # released as soon as it's within range; don't keep free-falling
            break
    assert monkey.body.position.get_distance(anchor.body.position) <= 25
    assert grapple.target is None, "should auto-stop once within release_distance"
    print("ok: grapple pulled monkey to static anchor and stopped")

    # --- Grapple: pull a dynamic object toward the monkey ---
    physics_space = PhysicsSpace()
    monkey = PhysicsBody(physics_space, (0, 0), lambda b: pymunk.Circle(b, 10), 1, 1, layer=Layer.PLAYER)
    crate = PhysicsBody(physics_space, (100, 0), lambda b: pymunk.Circle(b, 10), 1, 1,
                         layer=Layer.GRAPPLE_TARGET, body_type=pymunk.Body.DYNAMIC)
    grapple = Grapple(monkey, physics_space, range=200, pull_speed=400)
    grapple.start_grapple()
    grapple.update(dt)
    assert crate.body.velocity.x < 0, "dynamic target should be pulled toward the monkey"
    assert monkey.body.velocity.x == 0, "monkey itself should not move for a dynamic target"
    print("ok: grapple pulled dynamic object toward monkey")

    # --- Roll ---
    physics_space = PhysicsSpace()
    croc = PhysicsBody(physics_space, (0, 0), lambda b: pymunk.Circle(b, 10), 1, 1, layer=Layer.PLAYER)
    wall = PhysicsBody(physics_space, (19, 0), lambda b: pymunk.Circle(b, 10), 1, 1,
                        layer=Layer.ROLL_BREAKABLE, body_type=pymunk.Body.STATIC)
    roll = Roll(croc, physics_space)

    physics_space.space.step(dt)  # populate arbiters for the overlapping croc/wall pair
    roll.update(dt)
    assert wall.shape.space is not None, "wall should survive while not rolling"

    roll.start_roll()
    physics_space.space.step(dt)
    roll.update(dt)
    assert wall.shape.space is None, "wall should break while rolling through it"
    print("ok: roll broke wall only while rolling")
