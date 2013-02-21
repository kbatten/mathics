#!/usr/bin/env python

import sys
import math
import time

from PIL import Image
import scipy.constants

from mathics.world import World
from mathics.viewport import Viewport
from mathics.machines import Pendulum, Timer, Point, Vector

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
    blur = 2

    timer_start = time.time()
    duration = step * math.ceil(duration/step)
    # todo: add blur to mathics.World
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