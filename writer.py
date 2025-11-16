import neopixel

class Writer:
    def __init__(self, pin, x, y):
        self.neo = neopixel.NeoPixel(pin, x*y)
        self.index = []
        
        for xi in range(x):
            ylist = []
            if xi % 2 == 0:
                self.index.append(range(8*xi, 8*xi+8))
            else:
                self.index.append(range(8*xi+7,8*xi-1,-1))
            
        self.data = [[(0,0,0) for i in range(y)] for i in range(x)]

    def reset(self):
        for x in range(len(self.data)):
            for y in range(len(self.data[x])):
                self.data[x][y] = (0,0,0)

    def draw(self, x, y, image):
        for xi in range(len(image)):
            for yi in range(len(image[xi])):
                if len(self.data) > x+xi and len(self.data[x+xi]) > y+yi:
                    self.data[x+xi][y+yi] = image[xi][yi]

    def write(self):
        for x in range(len(self.data)):
            for y in range(len(self.data[x])):
                i = self.index[x][y]
                self.neo[i] = self.data[x][y]
        self.neo.write()

    def print(self):
        for y in range(len(self.data[0])):
            st = ""
            for x in range(len(self.data)):
                if self.data[x][y] == (0,0,0):
                    st += " "
                else:
                    st += "X"
            print(st)
