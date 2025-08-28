import pygame
import math

pygame.init()
WIDTH, HEIGHT = 1000, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# ---------------- Mirrors ----------------
# Primary mirror (facing right, left side)
primary_center = pygame.math.Vector2(300, HEIGHT // 2)
primary_radius = 250  # bigger mirror
primary_start_deg = 140  # angles for arc facing right
primary_end_deg = 220

# Focal point (approx f = R/2)
focal_point = pygame.math.Vector2(primary_center.x + primary_radius / 2, primary_center.y)

# Secondary mirror (45° flat, near focal point)
sec_center = pygame.math.Vector2(focal_point.x - 15, focal_point.y - 5)
sec_length = 40
sec_angle_rad = math.radians(45)
sec_dx = sec_length * math.cos(sec_angle_rad)
sec_dy = sec_length * math.sin(sec_angle_rad)
sec_start = pygame.math.Vector2(sec_center.x - sec_dx, sec_center.y - sec_dy)
sec_end = pygame.math.Vector2(sec_center.x + sec_dx, sec_center.y + sec_dy)

# Eyepiece position (below secondary for downward rays)
eyepiece_pos = pygame.math.Vector2(sec_center.x, sec_center.y + 120)

# ---------------- Light rays ----------------
num_rays = 200
ray_spacing = 3
speed = 2
y_start = HEIGHT // 2 - (num_rays // 2) * ray_spacing

def create_rays():
    rays = []
    for i in range(num_rays):
        y = y_start + i * ray_spacing
        x = WIDTH - 10
        rays.append({'pos': pygame.math.Vector2(x, y),
                     'dir': pygame.math.Vector2(-1, 0),
                     'state': 'to_primary'})
    return rays

rays = create_rays()

# ---------------- Utility functions ----------------
def point_hits_arc(px, py, center, radius, start_deg, end_deg, tol=1.5):
    dx = px - center.x
    dy = py - center.y
    dist = math.hypot(dx, dy)
    if abs(dist - radius) <= tol:
        angle = math.degrees(math.atan2(dy, dx))
        if angle < 0:
            angle += 360
        s = start_deg % 360
        e = end_deg % 360
        if s <= e:
            return s <= angle <= e
        else:
            return angle >= s or angle <= e
    return False

def point_hits_line(px, py, start, end, tol=2):
    line_vec = end - start
    point_vec = pygame.math.Vector2(px, py) - start
    line_len = line_vec.length()
    if line_len == 0:
        return False
    proj = point_vec.dot(line_vec) / line_len
    if 0 <= proj <= line_len:
        closest = start + line_vec.normalize() * proj
        return (pygame.math.Vector2(px, py) - closest).length() <= tol
    return False

# ---------------- Main loop ----------------
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((255, 255, 255))

    # Draw primary mirror
    arc_points = []
    for deg in range(primary_start_deg, primary_end_deg + 1):
        rad = math.radians(deg)
        x = int(primary_center.x + primary_radius * math.cos(rad))
        y = int(primary_center.y + primary_radius * math.sin(rad))
        arc_points.append((x, y))
    pygame.draw.lines(screen, (30, 100, 255), False, arc_points, 3)

    # Draw secondary mirror
    pygame.draw.line(screen, (0, 120, 0), (sec_start.x, sec_start.y), (sec_end.x, sec_end.y), 4)
    pygame.draw.circle(screen, (50, 50, 50), (int(eyepiece_pos.x), int(eyepiece_pos.y)), 6)

    # Flag to check if all rays are out
    all_out = True

    # Update rays
    for i, ray in enumerate(rays):
        pos = ray['pos']
        dirv = ray['dir']
        next_pos = pos + dirv * speed

        if ray['state'] == 'to_primary':
            steps = int(speed) + 1
            hit = False
            hit_point = None
            for s in range(1, steps+1):
                sample = pos + dirv * (s / steps * speed)
                if point_hits_arc(sample.x, sample.y, primary_center, primary_radius,
                                  primary_start_deg, primary_end_deg):
                    hit = True
                    hit_point = sample
                    break
            if hit:
                normal = (hit_point - primary_center).normalize()
                # aim toward focal point
                ray['dir'] = (focal_point - hit_point).normalize()
                ray['state'] = 'to_secondary'
                ray['pos'] = hit_point + ray['dir'] * 0.5
            else:
                ray['pos'] = next_pos

        elif ray['state'] == 'to_secondary':
            steps = int(speed) + 1
            hit = False
            hit_point = None
            for s in range(1, steps+1):
                sample = pos + ray['dir'] * (s / steps * speed)
                if point_hits_line(sample.x, sample.y, sec_start, sec_end):
                    hit = True
                    hit_point = sample
                    break
            if hit:
                # redirect downward toward eyepiece
                ray['dir'] = (eyepiece_pos - hit_point).normalize()
                ray['state'] = 'to_eyepiece'
                ray['pos'] = hit_point + ray['dir'] * 0.5
            else:
                ray['pos'] = next_pos

        elif ray['state'] == 'to_eyepiece':
            ray['pos'] = next_pos

        # Draw ray
        tail = ray['pos'] - ray['dir'] * 6
        pygame.draw.line(screen, (255, 50, 50),
                         (int(tail.x), int(tail.y)), (int(ray['pos'].x), int(ray['pos'].y)), 2)

        # Check if still on screen
        if -50 < ray['pos'].x < WIDTH + 50 and -100 < ray['pos'].y < HEIGHT + 100:
            all_out = False

    # If ALL rays left the screen → reset all together
    if all_out:
        rays = create_rays()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
