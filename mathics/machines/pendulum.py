import math

import scipy.constants

from basic import Machine, Point, Vector

class Pendulum(Machine):
    def __init__(self, pivot, weight):
        """
        pivot : Point
        weight : Vector
        """
        super(Pendulum, self).__init__()
        self.pivot = pivot
        self.weight = weight
        # note: rotate by 90degrees (math.radians(90) +...) so our math maps to normal visual quadrants
        self._angle_zero = weight.theta() + math.radians(90)

    def __str__(self):
        return "Pendulum: (%s pivot, %s weight)" % (self.pivot, self.weight)

    def set_time(self, t):
        super(Pendulum, self).set_time(t)

        # manually update time and values
        self.pivot.set_time(t)
        self.weight.set_time(t)

        # align to new position unrotate angle zero by 90 degrees
        self.weight.do_align(Vector.from_polar(1, self._angle_zero * math.cos(t / (math.sqrt(self.weight.r() / scipy.constants.g))) - math.radians(90)))

    def _weight_point(self, translate=None):
        if translate is None:
            translate = [0, 0]
        return Point.from_point(self.pivot).translate(self.weight).translate(Point(translate[0], translate[1]))

    def _weight_coords_text(self):
        p = Point.from_point(self.pivot).translate(self.weight)
        return "(%0.3f, %0.3f)" % (p.x, p.y)

    def visualization_basic(self, vp, data={}):
        Viewport = vp
        vp.add_object(Viewport.Line(self.pivot, self._weight_point,
                                    0.01, Viewport.BLACK))

        topleft = Point.from_point(self.pivot).translate(Point(-0.1,0.1))
        bottomright = Point.from_point(self.pivot).translate(Point(0.1,0))
        vp.add_object(Viewport.Rectangle(topleft, bottomright, Viewport.BLACK))
        vp.add_object(Viewport.Circle(self._weight_point, 0.05, Viewport.BLACK))
        vp.add_object(Viewport.Text((self._weight_point,(-0.5,-0.1)), self._weight_coords_text,(0,0,170)))

    def _time_velocity(self):
        curtime = self.t
        x = self.t

        self.set_time(curtime-0.1)
        oldweight = Vector.from_vector(self.weight)
        self.set_time(curtime)
        y = Vector(self.weight.x - oldweight.x, self.weight.y - oldweight.y).r()
        return Point(x, y)

    def visualization_different(self, vp):
        Viewport = vp
        vp.add_object(Viewport.Circle(self._time_velocity, 0.05, Viewport.BLACK))
