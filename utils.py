import matplotlib.pyplot as plt
import numpy as np

def drawPieMarker(xpos, ypos, ratios, size, colors, plot=plt):
    markers = []
    previous = 0
    # calculate the points of the pie pieces
    for color, ratio in zip(colors, ratios):
        this = 2 * np.pi * ratio + previous
        x  = [0] + np.cos(np.linspace(previous, this, 10)).tolist() + [0]
        y  = [0] + np.sin(np.linspace(previous, this, 10)).tolist() + [0]
        xy = np.column_stack([x, y])
        previous = this
        markers.append({'marker':xy, 's':size, 'facecolor':color})
    # scatter each of the pie pieces to create pies
    for marker in markers:
        plot.scatter(xpos, ypos, **marker)