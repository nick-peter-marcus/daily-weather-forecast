import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


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
    
    # Determine y-axis position
    text_y_pos = uv_scaled/2
    if uv_scaled < 0.8:
        text_y_pos = uv_scaled+0.4

    # Define font color for smaller graphs / those that are annotated above the bar
    if uv_scaled < 0.8:
        font_color = plot_color
    
    # Set path_effect (border outline / text shadow) if color is yellow
    path_effects = None
    if plot_color == "yellow":
        path_effects = [pe.withStroke(linewidth=1, foreground="black")]

    uv_style_dict = {
        "plot_color": plot_color, 
        "font_color": font_color, 
        "text_y_pos": text_y_pos,
        "path_effects": path_effects,
    }

    return uv_style_dict


def wind_styling(wind_degree: int, wind_speed: int) -> dict:
    # Proportionally size arrows according to wind speed
    arrow_size = min(30, max(wind_speed*1.5, 10))
    # Mark degrees 155-245 and 335-65 as purple, as they fall in my way of commute
    arrow_color = "purple" if wind_degree in range(155,245) or wind_degree > 335 or wind_degree < 65 else "black"
    # Style bold if below 10 (for better readability) and >30 (for emphasis)
    arrow_weight = "bold" if wind_speed < 10 or wind_speed > 30 else None

    # Position annotation based on degree
    wind_text_ha, wind_text_y_pos = ("left", 2.1)
    if wind_degree in range(105,180) or wind_degree in range(265,360):
        wind_text_ha, wind_text_y_pos = ("right", 2.1)

    wind_style_dict = {
        "arrow_size": arrow_size, 
        "arrow_color": arrow_color, 
        "arrow_weight": arrow_weight,
        "wind_text_ha": wind_text_ha,
        "wind_text_y_pos": wind_text_y_pos,
    }

    return wind_style_dict