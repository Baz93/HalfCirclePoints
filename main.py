import random
import json
import threading
import itertools
from filelock import FileLock
import tkinter as tk


data_filename = 'data.json'
data_filename_lock = FileLock(data_filename + '.lock')


def save_points(points):
    with data_filename_lock:
        with open(data_filename, 'w') as f:
            json.dump(points, f)


def load_points():
    with data_filename_lock:
        with open(data_filename) as f:
            return json.load(f)


def sqr_dist(pt1, pt2):
    return (pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2


def add_end_points(points):
    return [(-1, 0)] + points + [(1, 0)]


def calc_score(points):
    points = add_end_points(points)
    score = 0
    for i in range(len(points) - 1):
        score += sqr_dist(points[i], points[i + 1])
    return score


def score_gradient(points):
    points = add_end_points(points)
    result = []
    for i in range(len(points) - 2):
        pts = points[i:i + 3]
        result.append(tuple(2 * (x1 - x2) + 2 * (x3 - x2) for x1, x2, x3 in zip(*pts)))
    return result


def regularization_gradient(points):
    points = add_end_points(points)
    result = []
    for i in range(1, len(points) - 1):
        g = (0, 0)
        for j in range(len(points)):
            if i == j:
                continue
            d = sqr_dist(points[i], points[j])
            g = tuple(g[k] + (points[j][k] - points[i][k]) / d for k in range(2))
        result.append(g)
    return result


def find_path(points):
    best_val = (len(points) + 1) * 100
    best_pts = points
    for pts in map(list, itertools.permutations(points)):
        val = calc_score(pts)
        if val < best_val:
            best_val = val
            best_pts = pts
    return best_pts, best_val


def random_point():
    while True:
        pt = (random.uniform(-1, 1), random.uniform(0, 1))
        if sqr_dist((0, 0), pt) <= 1:
            return pt


def generate_initial_state(k):
    return [random_point() for i in range(k)]


def calc_data():
    k = 6
    step_coef = 0.01
    regularization_coef = 0.3
    regularization_coef /= (k ** 0.5)
    points = generate_initial_state(k)
    while True:
        points, val = find_path(points)
        save_points(points)
        # gradient = [tuple(
        #     v1[i] + v2[i] * regularization_coef for i in range(2)
        # ) for v1, v2 in zip(
        #     score_gradient(points),
        #     regularization_gradient(points),
        # )]
        gradient = score_gradient(points)
        for i in range(len(points)):
            points[i] = tuple(points[i][j] - gradient[i][j] * step_coef for j in range(2))
            if points[i][1] < 0:
                points[i] = (points[i][0], 0)
            d = sqr_dist(points[i], (0, 0))
            if d > 1:
                d = d ** 0.5
                points[i] = tuple(points[i][j] / d for j in range(2))


class Canvas(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry('500x500')
        self.w = 500
        self.h = 500
        self.border_width = 2
        self.line_width = self.border_width * 0.5
        self.point_width = self.border_width * 2
        self.canvas = tk.Canvas(self, width=self.w, height=self.h, bg='white')
        self.canvas.pack(anchor=tk.CENTER, expand=True)
        self.x0 = self.w / 2
        self.y0 = self.h / 2
        self.r = min(self.x0, self.w - self.x0, self.y0, self.h - self.y0) * 0.8

    def to_canvas_xy(self, x, y):
        return self.x0 + self.r * x, self.y0 - self.r * y

    def draw(self, points):
        self.canvas.delete('all')
        self.canvas.create_arc(
            self.to_canvas_xy(-1, 1),
            self.to_canvas_xy(1, -1),
            style=tk.CHORD,
            width=self.border_width,
            start=0,
            extent=180,
        )
        score = calc_score(points)
        points = add_end_points(points)
        for i in range(len(points) - 1):
            self.canvas.create_line(
                self.to_canvas_xy(*points[i]),
                self.to_canvas_xy(*points[i + 1]),
                fill='red',
                width=self.line_width,
            )
        self.canvas.create_text((5, 5), font=("Arial Bold", 20), text=str(score), anchor=tk.NW)
        for x, y in points:
            pos = self.to_canvas_xy(x, y)
            pos1 = (pos[0] - self.point_width, pos[1] - self.point_width)
            pos2 = (pos[0] + self.point_width, pos[1] + self.point_width)
            self.canvas.create_oval(pos1, pos2, fill='blue', outline='')

    def update(self):
        self.draw(load_points())
        self.after(10, self.update)

    def run(self):
        calc_thread = threading.Thread(target=calc_data)
        calc_thread.start()
        self.after(0, self.update)
        self.mainloop()


def main():
    canvas = Canvas()
    canvas.run()


if __name__ == '__main__':
    main()