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
        translate_x = x1
        translate_y = y1
        translate_x_internal = -viewport.x1_internal
        translate_y_internal = -viewport.y1_internal

        self.viewports.append({
                "viewport": viewport,
                "translate_x": translate_x,
                "translate_y": translate_y,
                "scale_x": scale_x,
                "scale_y": scale_y,
                "translate_x_internal": translate_x_internal,
                "translate_y_internal": translate_y_internal,
                })

    def set_time(self, t):
        for machine in self.machines:
            machine.set_time(t)

    def get_frame(self):
        image = Image.new('RGB', (self.width, self.height), self.background)
        draw = ImageDraw.Draw(image)
        for vp in self.viewports:
            vp["viewport"].draw(draw, vp)

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

class Viewport(object):
    BLACK=(0, 0, 0)
    GRAY=(200, 200, 200)
    BEIGE=(245, 245, 220)
    WHITE=(255, 255, 255)
    def __init__(self, x1, y1, x2, y2, background_color=None):
        self.objects = []
        self.x1_internal = x1
        self.y1_internal = y1
        self.x2_internal = x2
        self.y2_internal = y2
        self.background_color = background_color

        if self.background_color is not None:
            self.add_object(Viewport.Rectangle(Point(x1,y1), Point(x2,y2), background_color))

    def __str__(self):
        r = ""
        for obj in self.objects:
            r += str(obj)
        return r

    @classmethod
    def transform_x(cls, x, transform):
        return (x + transform['translate_x_internal']) * transform['scale_x'] + transform['translate_x']

    @classmethod
    def transform_y(cls, y, transform):
        return (y + transform['translate_y_internal']) * transform['scale_y'] + transform['translate_y']

    class DrawObject(object):
        def _create_functions(self, *args):
            for name, arg in zip(self.MEMBERS, args):
                func = """
import types
def get_{name}(self):
    if hasattr(self, '_get_{name}'):
        if len(self._get_{name}[1]) > 0:
            return self._get_{name}[0](self._get_{name}[1])
        else:
            return self._get_{name}[0]()
    return self._{name}
setattr(self, 'get_{name}', types.MethodType(get_{name}, self))

if hasattr(arg, '__call__'):
    self._get_{name} = (arg, ())
elif isinstance(arg, tuple) and hasattr(arg[0], '__call__'):
    self._get_{name} = (arg[0], arg[1])
else:
    setattr(self, '_{name}', arg)
""".format(name=name)
                exec(func)

    class Circle(DrawObject):
        MEMBERS = ['center', 'radius', 'color']
        def __init__(self, center, radius, color):
            self._create_functions(center, radius, color)

        def draw(self, draw, transform):
            x = Viewport.transform_x(self.get_center().x, transform)
            y = Viewport.transform_y(self.get_center().y, transform)
            radius_x = self.get_radius() * math.fabs(transform['scale_x'])
            radius_y = self.get_radius() * math.fabs(transform['scale_y'])

            box = (x - radius_x, y - radius_y, x + radius_x, y + radius_y)
            draw.ellipse(box, fill=self.get_color())

        def __str__(self):
            return "Viewport.Circle: (%s %f)" % (self.get_center(), self.radius)

    class Line(DrawObject):
        MEMBERS = ['start', 'end', 'width', 'color']
        def __init__(self, start, end, width, color):
            self._create_functions(start, end, width, color)

        def draw(self, draw, transform):
            start = self.get_start()
            end = self.get_end()

            box = (Viewport.transform_x(start.x, transform),
                   Viewport.transform_y(start.y, transform),
                   Viewport.transform_x(end.x, transform),
                   Viewport.transform_y(end.y, transform))

            width = int(math.ceil(self.get_width()*transform['scale_x']))
            draw.line(box, fill=self.get_color(), width=width)

        def __str__(self):
            return "Viewport.Line: (%s start %s end)" % (self.get_start(), self.get_end())

    class Rectangle(DrawObject):
        MEMBERS = ['topleft', 'bottomright', 'color']
        def __init__(self, topleft, bottomright, color):
            self._create_functions(topleft, bottomright, color)

        def draw(self, draw, transform):
            topleft = self.get_topleft()
            bottomright = self.get_bottomright()

            box = (Viewport.transform_x(topleft.x, transform),
                   Viewport.transform_y(topleft.y, transform),
                   Viewport.transform_x(bottomright.x, transform),
                   Viewport.transform_y(bottomright.y, transform))
            draw.rectangle(box, fill=self.get_color())

        def __str__(self):
            return "Viewport.Rectangle: (%s topleft %s bottomright)" % (self.get_topleft(), self.get_bottomright())

    class Text(DrawObject):
        MEMBERS = ['point', 'text', 'color']
        def __init__(self, point, text, color):
            self._create_functions(point, text, color)

        def draw(self, draw, transform):
            point = self.get_point()
            text = self.get_text()

            x = Viewport.transform_x(point.x, transform)
            y = Viewport.transform_y(point.y, transform)

            draw.text((x, y), text, fill=self.get_color())

        def __str__(self):
            return "Viewport.Text: (%s start %s end)" % (self.get_start(), self.get_end())


    def add_object(self, obj):
        self.objects.append(obj)

    def add_axis(self, smallhash=1, largehash=5, color=GRAY):
        self.add_object(Viewport.Line(Point(0,self.y1_internal), Point(0,self.y2_internal), 0, color))
        self.add_object(Viewport.Line(Point(self.x1_internal,0), Point(self.x2_internal,0), 0, color))

        def frange(start, end, step):
            distance = end - start
            distance = step * math.floor(distance/step)
            for i in range(1 + int(distance / step)):
                yield start + i*step

        y = smallhash/4.0
        for x in frange(0, self.x1_internal, -smallhash):
            self.add_object(Viewport.Line(Point(x,-y), Point(x,y), 0, color))
        for x in frange(0, self.x2_internal, smallhash):
            self.add_object(Viewport.Line(Point(x,-y), Point(x,y), 0, color))
        x = smallhash/4.0
        for y in frange(0, self.y1_internal, smallhash):
            self.add_object(Viewport.Line(Point(-x,y), Point(x,y), 0, color))
        for y in frange(0, self.y2_internal, -smallhash):
            self.add_object(Viewport.Line(Point(-x,y), Point(x,y), 0, color))

        y = smallhash/2.0
        for x in frange(0, self.x1_internal, -largehash):
            self.add_object(Viewport.Line(Point(x,-y), Point(x,y), 0, color))
        for x in frange(0, self.x2_internal, largehash):
            self.add_object(Viewport.Line(Point(x,-y), Point(x,y), 0, color))
        x = smallhash/2.0
        for y in frange(0, self.y1_internal, largehash):
            self.add_object(Viewport.Line(Point(-x,y), Point(x,y), 0, color))
        for y in frange(0, self.y2_internal, -largehash):
            self.add_object(Viewport.Line(Point(-x,y), Point(x,y), 0, color))

    def add_visualization(self, visualization):
        visualization(self)

    def draw(self, draw, transform):
        for obj in self.objects:
            obj.draw(draw, transform)

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
        vp.add_object(Viewport.Circle(self._time_velocity, 0.05, Viewport.BLACK))


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
        vp.add_object(Viewport.Text(self.point, self._t, Viewport.BLACK))


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

    seconds_pendulum = Pendulum(Point(0,1), Vector.from_polar((2/(2*math.pi)) * (2/(2*math.pi)) * scipy.constants.g, math.radians(320)))
    world.add_machine(seconds_pendulum)
    seconds2_pendulum = Pendulum(Point(0,2), Vector.from_polar((4/(2*math.pi)) * (4/(2*math.pi)) * scipy.constants.g, math.radians(300)))
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
    fps = 30

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
