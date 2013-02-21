import math

from machines.basic import Point

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

    # decorator
    def drawobject(*args):
        def wrap(cls):
            def __init__(self, *vargs):
                for attr,arg in zip(args,vargs):
                    if hasattr(arg, '__call__'):
                        setattr(self, '_get_%s'%attr, (arg, ()))
                    elif isinstance(arg, tuple) and hasattr(arg[0], '__call__'):
                        setattr(self, '_get_%s'%attr, (arg[0], arg[1]))
                    else:
                        setattr(self, '_%s'%attr, arg)
            setattr(cls, '__init__', __init__)
            for attr in args:
                setattr(cls, '_%s'%attr, None)
                setattr(cls, 'get_%s'%attr, None)
                setattr(cls, '_get_%s'%attr, (None,()))
                # if a function argument exists call _get_attr(arg)
                # elif a function exists call _get_attr()
                # else return _attr
                get_function = eval("lambda self: getattr(self, '_get_%s'%attr)[1] and getattr(self, '_get_%s'%attr)[0](getattr(self, '_get_%s'%attr)[1]) or getattr(self, '_get_%s'%attr)[0] and getattr(self, '_get_%s'%attr)[0]() or getattr(self, '_%s'%attr)",{'attr':attr})
                setattr(cls, 'get_%s'%attr, get_function)

#            str_function = lambda self: 'Viewport.' + self._name_
#            setattr(cls, '__str__', str_function)
            setattr(cls, '_name_', cls.__name__)

            str_function = lambda self: eval('"Viewport.%s (' + ', '.join(['%s '+arg for arg in args])+')"%(self._name_, '+', '.join(['self.get_'+arg+'()' for arg in args])+')')
            setattr(cls, '__str__', str_function)


            return cls
        return wrap

    @drawobject('center', 'radius', 'color')
    class Circle(object):
        def draw(self, draw, transform):
            x = Viewport.transform_x(self.get_center().x, transform)
            y = Viewport.transform_y(self.get_center().y, transform)
            radius_x = self.get_radius() * math.fabs(transform['scale_x'])
            radius_y = self.get_radius() * math.fabs(transform['scale_y'])

            box = (x - radius_x, y - radius_y, x + radius_x, y + radius_y)
            draw.ellipse(box, fill=self.get_color())

    @drawobject('start', 'end', 'width', 'color')
    class Line(object):
        def draw(self, draw, transform):
            start = self.get_start()
            end = self.get_end()

            box = (Viewport.transform_x(start.x, transform),
                   Viewport.transform_y(start.y, transform),
                   Viewport.transform_x(end.x, transform),
                   Viewport.transform_y(end.y, transform))

            width = int(math.ceil(self.get_width()*transform['scale_x']))
            draw.line(box, fill=self.get_color(), width=width)

    @drawobject('topleft', 'bottomright', 'color')
    class Rectangle(object):
        def draw(self, draw, transform):
            topleft = self.get_topleft()
            bottomright = self.get_bottomright()

            box = (Viewport.transform_x(topleft.x, transform),
                   Viewport.transform_y(topleft.y, transform),
                   Viewport.transform_x(bottomright.x, transform),
                   Viewport.transform_y(bottomright.y, transform))
            draw.rectangle(box, fill=self.get_color())

    @drawobject('point', 'text', 'color')
    class Text(object):
        def draw(self, draw, transform):
            point = self.get_point()
            text = self.get_text()

            x = Viewport.transform_x(point.x, transform)
            y = Viewport.transform_y(point.y, transform)

            draw.text((x, y), text, fill=self.get_color())


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
