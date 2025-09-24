import pygame
import math

polygon_points = [(100, 100), (350, 80), (450, 150), (400, 250), (500, 300),
                  (350, 350), (450, 450), (250, 400), (150, 450), (120, 250)]  # polygon vertices
guards = []  # list of guard positions

WIDTH, HEIGHT = 600, 600
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Art Gallery Problem")

EPS = 1e-9  # small number to avoid division by zero
RAY_LENGTH = WIDTH + HEIGHT  # long enough to always intersect


def point_in_polygon(point, poly):
    """
    Checks if point is inside polygon by using "Polygon Interior Algorithm" (Pg.4).
    The ray is horizontal and goes to the right.
    :param point: Coordinates of the point (x, y)
    :param poly: The vertices of the polygon
    :return: True if the point is inside the polygon, False otherwise
    """
    x, y = point
    cnt = 0
    n = len(poly)
    for i in range(n):
        # coordinates of the edge
        xi, yi = poly[i]
        xj, yj = poly[(i + 1) % n]

        between = (yi > y) != (yj > y)  # y coordinate should be between yi and yj
        intersect = (xj - xi) * (y - yi) / (
            (yj - yi) if abs(yj - yi) > EPS else EPS) + xi  # finds the intersection point of the ray with the edge

        # because the ray goes to the right, we should check if the intersection point is to the right of the point
        if between and (x < intersect):
            cnt += 1
    return True if cnt % 2 == 1 else False


def cross_product(p1, p2, p3, p4):
    """
    Calculate the cross-product of vectors p1 -> p2 and p3 -> p4: |p2 - p1| x |p4 - p3|
    :param p1: point 1 (x1, y1)
    :param p2: point 2 (x2, y2)
    :param p3: point 3 (x3, y3)
    :param p4: point 4 (x4, y4)
    :return:
    """
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    return (x2 - x1) * (y4 - y3) - (y2 - y1) * (x4 - x3)


def segment_ray_intersection(p1, p2, p3, p4):
    """
    Compute the intersection between segment p3 -> p4 and segment p1 -> p2.
    :param p1: Point 1 (x1, y1)
    :param p2: point 2 (x2, y2)
    :param p3: point 3 (x3, y3)
    :param p4: point 4 (x4, y4)
    :return: None if the segments are parallel,
    otherwise (t, u, (ix, iy)): intersection point (ix, iy) = p1 + t*(p2 - p1) = p3 + u*(p4 - p3)
    """
    x1, y1 = p1
    x2, y2 = p2

    den = cross_product(p1, p2, p3, p4)
    if abs(den) < EPS:
        return None  # parallel or almost parallel

    # Solve for t and u. See https://www.mjoldfield.com/atelier/2016/04/intersect-2d.html
    t = cross_product(p1, p3, p3, p4) / den
    u = cross_product(p1, p3, p1, p2) / den

    # Coordinates of intersection point
    ix = x1 + t * (x2 - x1)
    iy = y1 + t * (y2 - y1)
    return t, u, (ix, iy)


def cast_ray(guard, angle, polygon):
    """
    Cast a long enough ray from a guard at a given angle and find the first intersection with the polygon.
    :param guard: Coordinates of the guard
    :param angle: angle of the ray
    :param polygon: vertices of the polygon
    :return: the first intersection point between the ray and polygon, or
    None if no intersection is found
    """
    # constructing the end of the ray with the length of RAY_LENGTH
    ray_end = (guard[0] + RAY_LENGTH * math.cos(angle), guard[1] + RAY_LENGTH * math.sin(angle))

    # initialize the first intersection point
    first_t = float('inf')
    first_point = None

    for i in range(len(polygon)):
        # coordinates of the edge
        a = polygon[i]
        b = polygon[(i + 1) % len(polygon)]

        # the intersection of the ray with the edge
        res = segment_ray_intersection(guard, ray_end, a, b)
        # if the ray is not parallel to the edge
        if res is not None:
            t, u, ip = res

            # the intersection must be on the ray forward and on the edge segment
            if t > 1e-8 and -1e-8 <= u <= 1 + 1e-8:
                # check if it is the first intersection found
                if t < first_t:
                    first_t = t
                    first_point = ip
    return first_point


def dedupe_points(points, tol=1e-6):
    """
    Remove points that are too close to each other.
    :param points: List of points
    :param tol: tolerance level of being too close
    :return: list of deduplicated points
    """
    out = []
    for p in points:
        found = False
        for q in out:
            if (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 < tol * tol:
                found = True
                break
        if not found:
            out.append(p)
    return out


def visibility_polygon(guard, polygon):
    """
    Construct the polygon that is visible from the guard.
    :param guard: Position of the guard
    :param polygon: the vertices of the polygon
    :return: the vertices of the polygon that are visible from the guard in the sorted order
    """
    angles = []
    for v in polygon:
        # the angle from guard to vertex
        angle = math.atan2(v[1] - guard[1], v[0] - guard[0])
        # WITHOUT this, the ray won't go through the vertex
        angles.extend([angle - 1e-7, angle, angle + 1e-7])

    inters = []
    for a in angles:
        p = cast_ray(guard, a, polygon)
        # if the ray intersects the polygon
        if p is not None:
            inters.append(p)

    # remove points that are too close to each other
    inters = dedupe_points(inters, tol=1e-5)

    # sort by angle around the guard to allow drawing the polygon in the correct order
    inters.sort(key=lambda p: math.atan2(p[1] - guard[1], p[0] - guard[0]))
    return inters


# Main loop
running = True
while running:
    screen.fill((255, 255, 255))

    # Draw polygon with visible borders
    pygame.draw.polygon(screen, (200, 200, 200), polygon_points)
    pygame.draw.polygon(screen, (0, 0, 0), polygon_points, 2)

    for guard in guards:
        # place guard
        pygame.draw.circle(screen, (0, 0, 255), guard, 5)

        # compute the polygon that is visible from the guard and draw it semi-transparent
        vis = visibility_polygon(guard, polygon_points)
        if len(vis) >= 3:
            # create an overlay surface that is separate from the screen
            vis_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(vis_surf, (0, 255, 0, 50), vis)
            # shows the overlay surface on top of the screen
            screen.blit(vis_surf, (0, 0))
            pygame.draw.polygon(screen, (0, 255, 0, 50), vis, 1)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            # if the mouse click is inside the polygon, a guard is placed
            if point_in_polygon(pos, polygon_points):
                guards.append(pos)

    # update the display
    pygame.display.flip()

# quit after the loop finishes
pygame.quit()
