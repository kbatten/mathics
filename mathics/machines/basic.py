import math

class Machine(object):
    def __init__(self):
        self.t = 0.0

    def __str__(self):
        return "Machine: None"

    def set_time(self, t):
        self.t = t


class Point(Machine):
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __str__(self):
        return "Point: (%f x, %f y)" % (self.x, self.y)

    @classmethod
    def from_point(cls, point):
        return cls(point.x, point.y)

    def do_translate(self, point):
        self.x += point.x
        self.y += point.y

    def translate(self, point):
        return type(self)(self.x + point.x, self.y + point.y)

class Vector(Point):
    def __str__(self):
        return "Vector: (%f r, %f theta)" % (self.r(), math.degrees(self.theta()))

    @classmethod
    def from_vector(cls, vector):
        return cls.from_point(vector)

    @classmethod
    def from_polar(self, magnitude, angle):
        return Vector(magnitude * math.cos(angle), magnitude * math.sin(angle))

    def r(self):
        x = self.x
        y = self.y
        return math.sqrt(x * x + y * y)

    def theta(self):
        return (self.y>=0 and 1 or -1) * math.acos(self.x / self.r())

    def do_align(self, vector):
        scale = self.r() / vector.r()
        self.x = vector.x * scale
        self.y = vector.y * scale

    def align(self, vector):
        scale = self.r() / vector.r()
        x = vector.x * scale
        y = vector.y * scale
        return type(self)(x, y)
