import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


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


def rescale_data(x: pd.Series, low: int, high: int):
    """ Min-max scales data from a Series object to specified range """
    return (high - low)*(x - min(x)) / (max(x) - min(x)) + low
    

def uv_styling(uv: int, uv_scaled: int) -> dict:
    """ Returns styling of UV-index data based on WHO classifications and plot paramters """
    if uv > 10: # 11+	Violet	"Extreme"  
        plot_color, font_color = ("violet", "white")
    if uv <= 10: # 8–10	Red	"Very high"
        plot_color, font_color = ("red", "white")
    if uv <= 7: # 6–7	Orange	"High"
        plot_color, font_color = ("orange", "white")
    if uv <= 5: # 3–5	Yellow	"Moderate"
        plot_color, font_color = ("yellow", "white")
    if uv <= 2: # 0–2	Green "Low"
        plot_color, font_color = ("green", "white")
    
    text_y_pos = uv_scaled/2

    if uv_scaled < 1:
        text_y_pos = uv_scaled+0.4
        font_color = plot_color

    return {"plot_color": plot_color, "font_color": font_color, "text_y_pos": text_y_pos}  