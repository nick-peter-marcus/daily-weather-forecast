import matplotlib.pyplot as plt
import numpy as np


def degree_to_cardinal_direction(x: int) -> str:
    """ Converts degree of wind origin into compass direction """
    if x > 11.25 and x <= 33.75: return "NNE"
    if x > 33.75 and x <= 56.25: return "NE"
    if x > 56.25 and x <= 78.75: return "ENE"
    if x > 78.75 and x <= 101.25: return "E"
    if x > 101.25 and x <= 123.75: return "ESE"
    if x > 123.75 and x <= 146.25: return "SE"
    if x > 146.25 and x <= 168.75: return "SSE"
    if x > 168.75 and x <= 191.25: return "S"
    if x > 191.25 and x <= 213.75: return "SSW"
    if x > 213.75 and x <= 236.25: return "SW"
    if x > 236.25 and x <= 258.75: return "WSW"
    if x > 258.75 and x <= 281.25: return "W"
    if x > 281.25 and x <= 303.75: return "WNW"
    if x > 303.75 and x <= 326.25: return "NW"
    if x > 326.25 and x <= 348.75: return "NNW"
    return "N"


def draw_pie(dist: list[int], xpos: int, ypos: int, size: int, colors: list[str], ax=None) -> None:
    """ 
    Draws scatterplot with pie charts as markers 
    Adapted from: https://stackoverflow.com/questions/56337732/
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10,8))

    # for incremental pie slices
    cumsum = np.cumsum(dist)
    cumsum = cumsum/cumsum[-1]
    pie = [0] + cumsum.tolist()
    markers = []

    for r1, r2, color in zip(pie[:-1], pie[1:], colors):
        angles = np.linspace(2*np.pi*r1, 2*np.pi*r2)
        x = [0] + np.cos(angles).tolist()
        y = [0] + np.sin(angles).tolist()
        xy = np.column_stack([x, y])

        markers.append({'marker':xy, 's':size, 'facecolor':color})
        
        # scatter each of the pie pieces to create pies
        for marker in markers:
            ax.scatter(xpos, ypos, **marker)