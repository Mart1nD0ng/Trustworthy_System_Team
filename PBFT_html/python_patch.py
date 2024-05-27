import pygame
import math
import random
from pygame.locals import *

# Constants
HONEST_COLOR = (40, 167, 69)
MALICE_COLOR = (220, 53, 69)
REJECTED_COLOR = (255, 193, 7)
UNKNOWN_COLOR = (136, 136, 136)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (136, 136, 136)

# Initialize Pygame
pygame.init()

# Screen settings
screen_size = (800, 800)
screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption('PBFT Simulation')

# Load images
honest_img = pygame.image.load('pbft/honest.png')
malice_img = pygame.image.load('pbft/malice.png')

# Function to draw text
def draw_text(surface, text, position, color, font_size):
    font = pygame.font.SysFont(None, font_size)
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, position)

# Function to create nodes and draw messages
def draw_message(surface, msg, x, y):
    text1 = f"{msg['src']+1}{'→' + str(msg['dst']+1) if msg['dst'] is not None else ''}:"
    text2 = "😈" if msg['tampered'] else "😇"
    text3 = text(msg['value'])
    color = MALICE_COLOR if msg['value'] is None else REJECTED_COLOR if msg['value'] < 0 else (HONEST_COLOR if msg['value'] == 0 else MALICE_COLOR)

    draw_text(surface, text1, (x, y), BLACK, 12)
    draw_text(surface, text2, (x + 50, y), BLACK, 12)
    draw_text(surface, text3, (x + 80, y), color, 12)

# Main function to execute the simulation
def exec():
    n = 10  # Number of nodes
    m = 3   # Number of Byzantine nodes
    malicious_origin = False
    falsehood_message = False
    w = min(screen_size)
    iw = 40
    th = 12
    phase = 3
    phase_interval = 2.2
    phase_fps = 15.0
    phase_step = int(phase_interval * phase_fps)
    nodes = []

    def is_honest(i):
        if m == 0:
            return True
        if malicious_origin:
            return i != 0 and i <= n - m
        return i == 0 or i < n - m

    def text(value):
        if value is None:
            return "ARBITRARY"
        if value == 0:
            return "TRUTH"
        if value == 1:
            return "FALSEHOOD"
        return "Rejected"

    def order(value):
        label = text(value)
        color = "danger" if value is None else "success" if value in [0, 1] else "warning"
        return f"<span class='text-{color}'>{label}</span>"

    # Define prePrepare messages
    pre_prepare = [{'src': 0, 'dst': i if i != 0 else None, 'value': 0 if is_honest(0) else (0 if random.random() < 0.5 else 1), 'tampered': not is_honest(0)} for i in range(n)]
    prepare = [[{'src': pre_prepare[src]['src'], 'dst': pre_prepare[src]['dst'], 'value': pre_prepare[src]['value'] if is_honest(src) else (0 if random.random() < 0.5 else 1), 'tampered': pre_prepare[src]['value'] != (0 if random.random() < 0.5 else 1)} for src in range(n) if src != dst and pre_prepare[src]['dst'] is not None] for dst in range(n)]

    def accepted_value_in_prepare(i):
        if not is_honest(i):
            return None
        valid = len([x for x in prepare[i] if x['dst'] != i and x['src'] != x['dst'] and x['value'] == pre_prepare[i]['value']])
        return pre_prepare[i]['value'] if (valid + 1) / (len(prepare[i]) + 1) >= 2 / 3 else -1

    # Define commit messages
    commit = [[{'src': src, 'dst': None, 'value': accepted_value_in_prepare(src) if is_honest(src) or not falsehood_message else (0 if random.random() < 0.5 else 1), 'tampered': not is_honest(src)} for src in range(n) if src != dst] for dst in range(n)]

    def accepted_value_in_commit(i):
        if not is_honest(i):
            return None
        values = [x['value'] for x in commit[i]] + [accepted_value_in_prepare(i)]
        values = [v for v in values if v is not None and v >= 0]
        zero = values.count(0)
        one = values.count(1)
        if zero / n >= 2 / 3:
            return 0
        if one / n >= 2 / 3:
            return 1
        return -1

    def draw_background():
        screen.fill(WHITE)
        for i in range(len(nodes)):
            for j in range(len(nodes)):
                if i != j:
                    pygame.draw.line(screen, GREY, (nodes[i]['x'], nodes[i]['y']), (nodes[j]['x'], nodes[j]['y']))

    def draw_foreground(phase):
        for i in range(n):
            img = honest_img if is_honest(i) else malice_img
            screen.blit(img, (nodes[i]['x'] - iw // 2, nodes[i]['y'] - iw // 2))
            draw_text(screen, str(i + 1), (nodes[i]['x'], nodes[i]['y'] + iw // 2), BLACK, 12)
            value = pre_prepare[i]['value'] if phase == 0 and i == 0 else accepted_value_in_prepare(i) if phase == 2 else accepted_value_in_commit(i)
            draw_text(screen, text(value), (nodes[i]['x'], nodes[i]['y'] + iw // 2 + 20), HONEST_COLOR if value == 0 else MALICE_COLOR if value == 1 else REJECTED_COLOR if value == -1 else MALICE_COLOR, 12)

    def draw_pre_prepare_phase(d):
        for i in range(1, n):
            x = nodes[0]['x'] + d * (nodes[i]['x'] - nodes[0]['x'])
            y = nodes[0]['y'] + d * (nodes[i]['y'] - nodes[0]['y'])
            draw_message(screen, pre_prepare[i], x, y)

    def draw_prepare_phase(d):
        for i in range(1, n):
            for j in range(n):
                msg = next((m for m in prepare[j] if m['dst'] == i), None)
                if msg:
                    x = nodes[i]['x'] + d * (nodes[j]['x'] - nodes[i]['x'])
                    y = nodes[i]['y'] + d * (nodes[j]['y'] - nodes[i]['y'])
                    draw_message(screen, msg, x, y)

    def draw_commit_phase(d):
        for i in range(n):
            for j in range(n):
                msg = next((m for m in commit[j] if m['src'] == i), None)
                if msg:
                    x = nodes[i]['x'] + d * (nodes[j]['x'] - nodes[i]['x'])
                    y = nodes[i]['y'] + d * (nodes[j]['y'] - nodes[i]['y'])
                    draw_message(screen, msg, x, y)

    def animation(step):
        draw_background()
        if step <= phase_step:
            draw_pre_prepare_phase(step / phase_step)
        elif step <= 2 * phase_step:
            draw_prepare_phase((step - phase_step) / phase_step)
        elif step <= 3 * phase_step:
            draw_commit_phase((step - 2 * phase_step) / phase_step)
        draw_foreground(step // phase_step)
        pygame.display.update()
        if step < phase * phase_step:
            pygame.time.wait(int(1000 / phase_fps))
            animation(step + 1)

    # Calculate nodes' positions
    r = (w - iw - th) / 2.0
    nodes = [{'x': w / 2 + r * math.sin(math.pi - (2 * math.pi / n) * i), 'y': w / 2 - (th / 2) + r * math.cos(math.pi - (2 * math.pi / n) * i)} for i in range(n)]

    animation(0)

    print(n, m, int((n - 1) / 3.0), screen_size[0], screen_size[1], nodes, malicious_origin)

# Run the simulation
exec()

# Pygame main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

pygame.quit()
