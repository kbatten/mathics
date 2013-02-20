#!/usr/bin/env python

import math
import time

from PIL import Image, ImageDraw
import numpy
import scipy.constants



class World(object):
    def __init__(self, width, height, background):
        self.machines = []
        self.viewports = []
        self.width = width
        self.height = height
        self.background = background

    def __str__(self):
        r = "machines: "
        for machine in self.machines:
            r += machine.__str__()
        r += "\nviewports: "
        for viewport in self.viewports:
            r += viewport.__str__()
        return r

    def add_machine(self, machine):
        self.machines.append(machine)

    def add_viewport(self, viewport, x1, y1, x2, y2):
        scale_x = (x2-x1) / (viewport.x2_internal-viewport.x1_internal)
        scale_y = (y1-y2) / (viewport.y1_internal-viewport.y2_internal)
        shift_x = x1
        shift_y = y1
        shift_x_internal = -viewport.x1_internal
        shift_y_internal = -viewport.y1_internal

        self.viewports.append({
                "viewport": viewport,
                "shift_x": shift_x,
                "shift_y": shift_y,
                "scale_x": scale_x,
                "scale_y": scale_y,
                "shift_x_internal": shift_x_internal,
                "shift_y_internal": shift_y_internal,
                })

    def set_time(self, t):
        for machine in self.machines:
            machine.set_time(t)

    def get_frame(self):
        image = Image.new('RGB', (self.width, self.height), self.background)
        draw = ImageDraw.Draw(image)
        for vp in self.viewports:
            vp["viewport"].draw(draw, vp["shift_x"], vp["shift_y"], vp["scale_x"], vp["scale_y"], vp["shift_x_internal"], vp["shift_y_internal"])

        del draw
        return image


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


class Viewport(object):
    NONE = 0
    SOLID = 1

    BLACK=(0, 0, 0)
    GRAY=(200, 200, 200)
    BEIGE=(245, 245, 220)
    WHITE=(255, 255, 255)
    def __init__(self, x1, y1, x2, y2, background=None):
        self.objects = []
        self.x1_internal = x1
        self.y1_internal = y1
        self.x2_internal = x2
        self.y2_internal = y2
        self.background = background

        if self.background:
            self.add_rectangle(Point(x1,y1), Point(x2,y2), Viewport.NONE, 0, background)

    def __str__(self):
        r = ""
        for obj in self.objects:
            r += str(obj)
        return r

    class Circle(object):
        def __init__(self, center, styles, radius, color):
            if hasattr(center, '__call__'):
                self.get_center = center
            else:
                self.center = center
            self.styles = styles
            self.radius = radius
            self.color = color

        def get_center(self):
            return self.center

        def draw(self, draw, shift_x, shift_y, scale_x, scale_y, shift_x_internal, shift_y_internal):
            x = (self.get_center().x + shift_x_internal) * scale_x + shift_x
            y = (self.get_center().y + shift_y_internal) * scale_y + shift_y
            radius_x = self.radius * math.fabs(scale_x)
            radius_y = self.radius * math.fabs(scale_y)

            box = (x - radius_x, y - radius_y, x + radius_x, y + radius_y)
            draw.ellipse(box, fill=self.color)

        def __str__(self):
            return "Viewport.Circle: (%s %f)" % (self.get_center(), self.radius)

    class Line(object):
        def __init__(self, start, end, styles, width, color):
            if hasattr(start, '__call__'):
                self.get_start = start
            else:
                self.start = start
            if hasattr(end, '__call__'):
                self.get_end = end
            else:
                self.end = end
            self.styles = styles
            self.width = width
            self.color = color

        def get_start(self):
            return self.start

        def get_end(self):
            return self.end

        def draw(self, draw, shift_x, shift_y, scale_x, scale_y, shift_x_internal, shift_y_internal):
            start = self.get_start()
            end = self.get_end()

            box = ((start.x + shift_x_internal) * scale_x + shift_x,
                   (start.y + shift_y_internal) * scale_y + shift_y,
                   (end.x + shift_x_internal) * scale_x + shift_x,
                   (end.y + shift_y_internal) * scale_y + shift_y)
            draw.line(box, fill=self.color, width=int(math.ceil(self.width*scale_x)))

        def __str__(self):
            return "Viewport.Line: (%s start %s end)" % (self.get_start(), self.get_end())

    class Rectangle(object):
        def __init__(self, topleft, bottomright, styles, color):
            if hasattr(topleft, '__call__'):
                self.get_topleft = topleft
            else:
                self.topleft = topleft
            if hasattr(bottomright, '__call__'):
                self.get_bottomright = bottomright
            else:
                self.bottomright = bottomright
            self.styles = styles
            self.color = color

        def get_topleft(self):
            return self.topleft

        def get_bottomright(self):
            return self.bottomright

        def draw(self, draw, shift_x, shift_y, scale_x, scale_y, shift_x_internal, shift_y_internal):
            topleft = self.get_topleft()
            bottomright = self.get_bottomright()

            box = ((topleft.x + shift_x_internal) * scale_x + shift_x,
                   (topleft.y + shift_y_internal) * scale_y + shift_y,
                   (bottomright.x + shift_x_internal) * scale_x + shift_x,
                   (bottomright.y + shift_y_internal) * scale_y + shift_y)
            draw.rectangle(box, fill=self.color)

        def __str__(self):
            return "Viewport.Line: (%s start %s end)" % (self.get_start(), self.get_end())

    class Text(object):
        def __init__(self, point, text, color):
            if hasattr(point, '__call__'):
                self.get_point = point
            else:
                self.point = point
            if hasattr(text, '__call__'):
                self.get_text = text
            else:
                self.text = text
            self.color = color

        def get_point(self):
            return self.point

        def get_text(self):
            return self.text

        def draw(self, draw, shift_x, shift_y, scale_x, scale_y, shift_x_internal, shift_y_internal):
            point = self.get_point()
            text = self.get_text()

            x = (point.x + shift_x_internal) * scale_x + shift_x
            y = (point.y + shift_y_internal) * scale_y + shift_y

            draw.text((x, y), text, fill=self.color)

        def __str__(self):
            return "Viewport.Line: (%s start %s end)" % (self.get_start(), self.get_end())

    def add_circle(self, center, styles, radius, color):
        self.objects.append(Viewport.Circle(center, styles, radius, color))

    def add_rectangle(self, topleft, bottomright, styles, radius, color):
        self.objects.append(Viewport.Rectangle(topleft, bottomright, styles, color))

    def add_line(self, start, end, styles, width, color):
        self.objects.append(Viewport.Line(start, end, styles, width, color))

    def add_text(self, point, text, color):
        self.objects.append(Viewport.Text(point, text, color))

    def add_axis(self, smallhash=1, largehash=5, color=GRAY):
        self.add_line(Point(0,self.y1_internal), Point(0,self.y2_internal), Viewport.SOLID, 0, color)
        self.add_line(Point(self.x1_internal,0), Point(self.x2_internal,0), Viewport.SOLID, 0, color)

        def frange(start, end, step):
            distance = end - start
            distance = step * math.floor(distance/step)
            for i in range(1 + int(distance / step)):
                yield start + i*step

        y = smallhash/4.0
        for x in frange(0, self.x1_internal, -smallhash):
            self.add_line(Point(x,-y), Point(x,y), Viewport.SOLID, 0, color)
        for x in frange(0, self.x2_internal, smallhash):
            self.add_line(Point(x,-y), Point(x,y), Viewport.SOLID, 0, color)
        x = smallhash/4.0
        for y in frange(0, self.y1_internal, smallhash):
            self.add_line(Point(-x,y), Point(x,y), Viewport.SOLID, 0, color)
        for y in frange(0, self.y2_internal, -smallhash):
            self.add_line(Point(-x,y), Point(x,y), Viewport.SOLID, 0, color)

        y = smallhash/2.0
        for x in frange(0, self.x1_internal, -largehash):
            self.add_line(Point(x,-y), Point(x,y), Viewport.SOLID, 0, color)
        for x in frange(0, self.x2_internal, largehash):
            self.add_line(Point(x,-y), Point(x,y), Viewport.SOLID, 0, color)
        x = smallhash/2.0
        for y in frange(0, self.y1_internal, largehash):
            self.add_line(Point(-x,y), Point(x,y), Viewport.SOLID, 0, color)
        for y in frange(0, self.y2_internal, -largehash):
            self.add_line(Point(-x,y), Point(x,y), Viewport.SOLID, 0, color)

    def add_visualization(self, visualization):
        visualization(self)

    def draw(self, draw, shift_x, shift_y, scale_x, scale_y, shift_x_internal, shift_y_internal):
        for obj in self.objects:
            obj.draw(draw, shift_x, shift_y, scale_x, scale_y, shift_x_internal, shift_y_internal)

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
        self.weight.do_align(Vector().from_polar(1, self._angle_zero * math.cos(t / (math.sqrt(self.weight.r() / scipy.constants.g))) - math.radians(90)))

    def _weight(self):
        p = Point().from_point(self.pivot)
        p.do_translate(self.weight)
        return p

    def _weight_offset(self):
        p = Point().from_point(self.pivot)
        p.do_translate(self.weight)
        p.do_translate(Point(-0.5, -0.2))
        return p

    def _weight_x_y(self):
        p = Point().from_point(self.pivot)
        p.do_translate(self.weight)
        return "(%0.3f, %0.3f)" % (p.x, p.y)

    def visualization_basic(self, vp):
        vp.add_line(self.pivot, self._weight, Viewport.SOLID, 0.01, Viewport.BLACK)

        # todo: should be able to chain these
        topleft = Point().from_point(self.pivot)
        bottomright = Point().from_point(self.pivot)
        topleft.do_translate(Point(-0.1,0.1))
        bottomright.do_translate(Point(0.1,0))
        vp.add_rectangle(topleft, bottomright, Viewport.SOLID, 0.1, Viewport.BLACK)

        vp.add_circle(self._weight, Viewport.SOLID, 0.05, Viewport.BLACK)
        vp.add_text(self._weight_offset, self._weight_x_y, (0,0,170))

    def _time_velocity(self):
        curtime = self.t
        x = self.t

        self.set_time(curtime-0.1)
        oldweight = Vector().from_vector(self.weight)
        self.set_time(curtime)
        y = Vector(self.weight.x - oldweight.x, self.weight.y - oldweight.y).r()
        return Point(x, y)

    def visualization_different(self, vp):
        vp.add_circle(self._time_velocity, Viewport.SOLID, 0.05, Viewport.BLACK)


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
        vp.add_text(self.point, self._t, Viewport.BLACK)


def serve_gif(frames, duration):
    from PIL import Image
    from images2gif import writeGif
    filename = 'image.gif'
    writeGif(filename, frames, duration/len(frames))

    # server image.gif
    from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

    PORT_NUMBER = 8000

    #This class will handles any incoming request from
    #the browser 
    class myHandler(BaseHTTPRequestHandler):
    
        #Handler for the GET requests
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type','image/gif')
            self.end_headers()

            with open("image.gif") as f:
                self.wfile.write(f.read())
            return

    try:
        #Create a web server and define the handler to manage the
        #incoming request
        server = HTTPServer(('', PORT_NUMBER), myHandler)
    
        #Wait forever for incoming http requests
        server.serve_forever()

    except KeyboardInterrupt:
        print '^C received, shutting down the web server'
        server.socket.close()



if __name__ == '__main__':
    import sys

    x = 500
    y = 6 * x / 5

    world = World(x, y, (255,0,0))

    viewport_different = Viewport(-4, 1.9, 8, -0.5, (0,200,0))
    viewport = Viewport(-3, 3, 3, -3, Viewport.BEIGE)

    world.add_viewport(viewport, 0, y/6, x, y)
    world.add_viewport(viewport_different, 0, 0, x, y/6)

    seconds_pendulum = Pendulum(Point(0,1), Vector().from_polar((2/(2*math.pi)) * (2/(2*math.pi)) * scipy.constants.g, math.radians(320)))
    world.add_machine(seconds_pendulum)
    seconds2_pendulum = Pendulum(Point(0,2), Vector().from_polar((4/(2*math.pi)) * (4/(2*math.pi)) * scipy.constants.g, math.radians(300)))
    world.add_machine(seconds2_pendulum)

    timer = Timer(Point(2,2))
    world.add_machine(timer)

    viewport.add_axis(0.2, 1)
    viewport.add_visualization(seconds_pendulum.visualization_basic)
    viewport.add_visualization(seconds2_pendulum.visualization_basic)
    viewport.add_visualization(timer.visualization_basic)

    viewport_different.add_visualization(seconds_pendulum.visualization_different)
    viewport_different.add_visualization(seconds2_pendulum.visualization_different)

    frames = []

    step = 0.05
    duration = 4
    fps = 60

    blur = int(math.ceil(fps/(1.0/step)))

    timer_start = time.time()
    duration = step * math.ceil(duration/step)
    for i in range(1 + int(duration / step)):
        t = i * step

        frame = None
        for i in reversed(range(blur)):
            if t - (i * step/blur) >= 0:
                world.set_time(t - (i * step/blur))
                if not frame:
                    frame = world.get_frame()
                else:
                    frame = Image.blend(frame, world.get_frame(), 0.4)

        frames.append(frame)
    timer_end = time.time()
    print "generated %i frames in %i seconds. %f fps" % (len(frames) * blur, timer_end - timer_start, (len(frames)*blur)/duration)

    serve_gif(frames, duration)
