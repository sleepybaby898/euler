import pygame
import random
import math
print(pygame.version.ver)

pygame.init()
# constants
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
shadow_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 18, bold=True)

# set icon
icon = pygame.image.load('images/cat.png')
pygame.display.set_icon(icon)

# gravity = 9.8m/s * 144 pixels = 1411.2 pixels/s
# fps = 60^2 = 3600
# 1411.2 / 3600 = 0.392 px
gravity = 0.392

# colours
RED = (255, 0, 0)

# circle
x = HEIGHT // 2
y = 50
radius = 20

def get_colour(speed, max_speed=10):
    # clamp speed
    speed = min(speed, max_speed)
    ratio = speed / max_speed  # 0 -> 1

    if ratio < 0.33:  # blue -> green
        r = int(0 * (1 - ratio / 0.33) + 0 * (ratio / 0.33))  # stays 0
        g = int(0 * (1 - ratio / 0.33) + 255 * (ratio / 0.33))
        b = int(255 * (1 - ratio / 0.33) + 0 * (ratio / 0.33))
    elif ratio < 0.66:  # green -> yellow
        r = int(0 * (1 - (ratio - 0.33)/0.33) + 255 * ((ratio - 0.33)/0.33))
        g = 255
        b = 0
    else:  # yellow -> red
        r = 255
        g = int(255 * (1 - (ratio - 0.66)/0.34))
        b = 0

    return (r, g, b)

def fps_counter():
    fps = str(int(clock.get_fps()))
    pygame.display.set_caption(f'FPS: {fps}')

class Planet:
    def __init__(self, x, y, radius=30, strength=50000):
        self.x = x
        self.y = y
        self.radius = radius
        self.strength = strength
    def draw(self, surface):
        pygame.draw.circle(surface, RED, (int(self.x), int(self.y)), self.radius)

class Obstacle:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    def draw(self, surface):
        pygame.draw.rect(surface, (45, 200, 50), (self.x, self.y, self.width, self.height)) # green colour rectangle

class Circle:
    def __init__(self, x, y, radius, colour):
        self.x = x
        self.y = y
        self.radius = radius
        self.colour = colour
        self.x_velocity = 0
        self.y_velocity = 0
        self.settled = False  # mark if circle has come to rest

    def update(self):
        # only apply gravity if not settled
        if not self.settled:
            # apply gravity
            self.y_velocity += gravity

            # update position
            self.x += self.x_velocity
            self.y += self.y_velocity

            # planet logic
            for planet in planets:
                dx = planet.x - self.x
                dy = planet.y - self.y
                distance = math.hypot(dx, dy)
                if distance == 0:
                    continue

                # normalize direction
                nx = dx / distance
                ny = dy / distance

                # gravitational force (inverse-square)
                force = planet.strength / (distance**2)

                force = min(force, 5) # avoid retarded shooting out of circles

                # apply to velocity (don’t stick)
                self.x_velocity += nx * force
                self.y_velocity += ny * force


            # bounce off floor
            if self.y + self.radius >= HEIGHT:
                self.y = HEIGHT - self.radius
                self.y_velocity *= -(random.uniform(0.3, 0.8))  # lose energy and bounce
                self.x_velocity *= 0.9  # horizontal energy loss

                # if nearly stopped, mark as settled
                if abs(self.y_velocity) < 0.5 and abs(self.x_velocity) < 0.5:
                    self.y_velocity = 0
                    self.x_velocity = 0
                    self.settled = True  # mark as stopped

            # bounce off left wall
            if self.x - self.radius <= 0:
                self.x = self.radius
                self.x_velocity *= -0.9  # bounce with energy loss

            # bounce off right wall
            if self.x + self.radius >= WIDTH:
                self.x = WIDTH - self.radius
                self.x_velocity *= -0.9
            
            # obstacle logic 
            for obj in obstacles:
                closest_x = max(obj.x, min(self.x, obj.x + obj.width)) # find closest point on rectangle to the circle
                closest_y = max(obj.y, min(self.y, obj.y + obj.height))

                # distance from rectangle to circle
                dx = self.x - closest_x
                dy = self.y - closest_y
                distance = math.hypot(dx, dy)

                if distance < self.radius:
                    overlap = self.radius - distance
                    if distance == 0:
                        distance = 0.1
                    self.x += dx / distance * overlap
                    self.y += dy / distance * overlap

                    self.x_velocity *= -0.7
                    self.y_velocity *= -0.7


    def draw(self, surface):
        # draw shadow
        shadow_color = (0, 0, 0, 80)  # black with alpha
        shadow_y = HEIGHT - self.radius * 0.5
        scale = max(0.3, 1 - (self.y / HEIGHT))  # smaller shadow for higher circles
        shadow_width = int(self.radius * 2 * scale)
        shadow_height = int(self.radius * 0.5 * scale)
        shadow_surf = pygame.Surface((shadow_width, shadow_height), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, shadow_color, (0, 0, shadow_width, shadow_height))
        surface.blit(shadow_surf, (int(self.x - shadow_width / 2), int(shadow_y)))
        # draw ball

        # calculate the speed and the colour
        speed = math.hypot(self.x_velocity, self.y_velocity)
        colour = get_colour(speed)
        pygame.draw.circle(surface, colour, (int(self.x), int(self.y)), self.radius)

def isColliding(c1, c2):  # check if 2 circles are colliding ( check if distance less than c1 radius + c2 radius )
    dx = c2.x - c1.x 
    dy = c2.y - c1.y
    distance = math.hypot(dx, dy)
    if(distance < c1.radius + c2.radius):
        return True
    else:
        return False

def resolveCollision(c1, c2):
    # skip if both circles are settled
    if c1.settled and c2.settled:
        return

    dx = c2.x - c1.x
    dy = c2.y - c1.y
    distance = math.hypot(dx, dy)

    if distance == 0:
        distance = 0.1

    # normal vector (direction of collision)
    nx = dx / distance
    ny = dy / distance

    # relative velocity
    dvx = c1.x_velocity - c2.x_velocity
    dvy = c1.y_velocity - c2.y_velocity
    relVel = dvx * nx + dvy * ny

    # if moving apart, do nothing
    if relVel > 0:
        return

    # for when it hits ground - adds negative velocity
    restitution = 0.8
    p = (2 * relVel / 2) * restitution  # equal mass

    # apply impulse
    c1.x_velocity -= p * nx
    c1.y_velocity -= p * ny
    c2.x_velocity += p * nx
    c2.y_velocity += p * ny

    # push circles apart
    overlap = (c1.radius + c2.radius - distance) / 2
    push_factor = 1.05  # push slightly more than needed
    c1.x -= overlap * nx * push_factor
    c1.y -= overlap * ny * push_factor
    c2.x += overlap * nx * push_factor
    c2.y += overlap * ny * push_factor

    # damping, reduce velocity to simulate energy loss
    damping = 0.9  # 0 < damping <= 1, smaller = more energy lost
    c1.x_velocity *= damping
    c1.y_velocity *= damping
    c2.x_velocity *= damping
    c2.y_velocity *= damping

    # zero very small velocities to prevent jittery ugly bs
    if abs(c1.x_velocity) < 0.01: c1.x_velocity = 0
    if abs(c1.y_velocity) < 0.01: c1.y_velocity = 0
    if abs(c2.x_velocity) < 0.01: c2.x_velocity = 0
    if abs(c2.y_velocity) < 0.01: c2.y_velocity = 0

circles = []
obstacles = []
planets = []
drawing = False # is user drawing
start_pos = (0, 0)
end_pos = (0, 0)
for i in range(2):
    circles.append(Circle(random.randint(0, WIDTH), y, radius, RED))

while True:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if(event.button == 1): # left mouse
                mouse_x, mouse_y = event.pos
                circ = Circle(mouse_x, mouse_y, radius, RED)
                circles.append(circ)
            elif(event.button == 3): # right mouse
                drawing = True
                start_pos = pygame.mouse.get_pos()
        elif event.type == pygame.MOUSEBUTTONUP:
            if(event.button == 3 and drawing):
                end_pos = event.pos
                x1, y1 = start_pos
                x2, y2 = end_pos
                rect_x = min(x1, x2)
                rect_y = min(y1, y2)
                rect_w = abs(x2 - x1)
                rect_h = abs(y2 - y1)
                obstacles.append(Obstacle(rect_x, rect_y, rect_w, rect_h))
                drawing = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                circles = []
                obstacles = []
                planets = []
            if event.key == pygame.K_e:
                mx, my = pygame.mouse.get_pos()
                planets.append(Planet(mx, my))
    
    instructions = font.render("space to reset, e to spawn a planet, right click to spawn an obstacle", True, (0, 0, 0))
    screen.fill("white")
    screen.blit(instructions, (10, 10))

    # draw obstacles logic
    for ob in obstacles:
        ob.draw(screen)
    
    if drawing:
        x1, y1 = start_pos
        x2, y2 = pygame.mouse.get_pos()
        rect_x = min(x1, x2)
        rect_y = min(y1, y2)
        rect_w = abs(x2 - x1)
        rect_h = abs(y2 - y1)
        pygame.draw.rect(screen, (45, 200, 50, 50), (rect_x, rect_y, rect_w, rect_h), 2)


    # draw circles logic
    for circle in circles:
        circle.update()
    for i in range(len(circles)):
        for j in range(i + 1, len(circles)): # collision checks bruv
            if isColliding(circles[i], circles[j]):
                resolveCollision(circles[i], circles[j]) 
    for circle in circles:
        circle.draw(screen) # draw the circle

    # planet logic
    for planet in planets:
        planet.draw(screen)

    # render graphics
    fps_counter()

    pygame.display.flip()  # refresh display
