from PIL import Image, ImageDraw

class World(object):
    def __init__(self, width, height, background, font=None):
        self.machines = []
        self.viewports = []
        self.width = float(width)
        self.height = float(height)
        self.background = background
        self.font = font
        self.t = 0.0

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
                "font": self.font,
                })

    def set_time(self, t):
        self.t = float(t)
        for machine in self.machines:
            machine.set_time(float(t))

    def get_frame(self):
        image = Image.new('RGB', (int(self.width), int(self.height)), self.background)
        draw = ImageDraw.Draw(image)
        for vp in self.viewports:
            vp["viewport"].draw(draw, vp)

        del draw
        return image


    def get_frames(self, ts, te, step, blur=0, scale=1):
        frames = []
        for i in range(1 + int((te - ts) / step)):
            t = i * step

            frame = None
            for i in reversed(range(blur+1)):
                if t - (i * step/(blur+1)) >= 0:
                    self.set_time(t - (i * step/(blur+1)))
                    if not frame:
                        frame = self.get_frame()
                    else:
                        frame = Image.blend(frame, self.get_frame(), 0.4)

            if scale != 1:
                frame = frame.resize((int(self.width*scale),int(self.height*scale)), Image.ANTIALIAS)
            frames.append(frame)
        return frames
