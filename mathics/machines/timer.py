from .basic import Machine

class Timer(Machine):
    def __init__(self, point):
        super(Timer, self).__init__()

        self.point = point

    def __str__(self):
        return "Timer: (%f time %s)" % (self.t, self.point)

    def set_time(self, t):
        super(Timer, self).set_time(t)

    def _t(self):
        return "%0.2f s" % self.t

    def visualization_basic(self, vp):
        Viewport = vp
        vp.add_object(Viewport.Text(self.point, self._t, Viewport.BLACK))
