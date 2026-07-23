class Movement:
    """Side-walk + jump for any entity that owns a PhysicsBody."""

    def __init__(self, physics_body, speed, jump_speed, air_control=1.0,
                 coyote_time=0.1, min_jump_speed=None):
        self.physics_body = physics_body
        self.speed = speed
        self.jump_speed = jump_speed
        self.air_control = air_control        # multiplier on `speed` while airborne
        self.coyote_time = coyote_time        # seconds of post-ledge grace window
        self.min_jump_speed = min_jump_speed if min_jump_speed is not None else jump_speed * 0.5
        self.grounded = False
        self.time_since_grounded = self.coyote_time  # start "expired"

    def update(self, dt):
        self.grounded = self._check_grounded()
        self.time_since_grounded = 0.0 if self.grounded else self.time_since_grounded + dt

    # direction: -1 (left), 0 (stop), 1 (right)
    # ponytail: sets velocity directly (snappy/arcade feel), not force-based acceleration
    def walk(self, direction):
        body = self.physics_body.body
        speed = self.speed if self.grounded else self.speed * self.air_control
        body.velocity = (direction * speed, body.velocity.y)

    def jump(self):
        if not (self.grounded or self.time_since_grounded < self.coyote_time):
            return
        body = self.physics_body.body
        body.velocity = (body.velocity.x, -self.jump_speed)
        self.time_since_grounded = self.coyote_time  # consume the grace window
        self.grounded = False

    def release_jump(self):
        body = self.physics_body.body
        if body.velocity.y < -self.min_jump_speed:
            body.velocity = (body.velocity.x, -self.min_jump_speed)

    def _check_grounded(self, threshold=0.5):
        grounded = False

        def check(arbiter):
            nonlocal grounded
            if arbiter.normal.y > threshold:
                grounded = True

        self.physics_body.body.each_arbiter(check)
        return grounded


if __name__ == "__main__":
    import pymunk
    from physics import PhysicsBody, PhysicsSpace, Layer

    physics_space = PhysicsSpace()
    ground = PhysicsBody(physics_space, (0, 50), lambda b: pymunk.Segment(b, (-100, 0), (100, 0), 1),
                          1, 1, layer=Layer.NORMAL, body_type=pymunk.Body.STATIC)
    player = PhysicsBody(physics_space, (0, 0), lambda b: pymunk.Circle(b, 10), 1, 1, layer=Layer.PLAYER)
    movement = Movement(player, speed=150, jump_speed=300, air_control=0.5,
                         coyote_time=0.1, min_jump_speed=100)
    dt = 1 / 60

    movement.jump()
    assert player.body.velocity.y == 0, "should not jump while airborne"

    # --- grounded state + air control ---
    for _ in range(120):
        physics_space.space.step(dt)
        movement.update(dt)
    assert movement.grounded, "expected player resting on ground"

    movement.walk(1)
    assert player.body.velocity.x == 150, "full speed while grounded"

    movement.grounded = False
    movement.walk(1)
    assert player.body.velocity.x == 150 * 0.5, "air_control should scale horizontal speed while airborne"

    # --- coyote time ---
    movement.grounded = False
    movement.time_since_grounded = 0.05  # just left the ground, inside the 0.1s window
    movement.jump()
    assert player.body.velocity.y == -300, "coyote jump should succeed inside the grace window"
    assert movement.time_since_grounded >= movement.coyote_time, "window should be consumed after jumping"

    movement.grounded = False
    movement.time_since_grounded = movement.coyote_time  # window expired
    player.body.velocity = (player.body.velocity.x, 0)
    movement.jump()
    assert player.body.velocity.y == 0, "jump should be denied once the coyote window has expired"

    # --- variable jump height ---
    movement.grounded = True
    movement.time_since_grounded = 0.0
    player.body.velocity = (0, 0)
    movement.jump()
    held_vy = player.body.velocity.y
    assert held_vy == -300

    movement.grounded = True
    movement.time_since_grounded = 0.0
    player.body.velocity = (0, 0)
    movement.jump()
    movement.release_jump()
    released_vy = player.body.velocity.y
    assert released_vy == -100, "early release should clamp toward min_jump_speed"
    assert released_vy > held_vy, "releasing early should yield a smaller upward speed than holding"

    print("ok: air_control, coyote time, variable jump height all verified")
