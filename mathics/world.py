from PIL import Image, ImageDraw

class World(object):
    def __init__(self, width, height, background):
        self.machines = []
        self.viewports = []
        self.width = float(width)
        self.height = float(height)
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
        image = Image.new('RGB', (int(self.width), int(self.height)), self.background)
        draw = ImageDraw.Draw(image)
        for vp in self.viewports:
            vp["viewport"].draw(draw, vp)

        del draw
        return image
