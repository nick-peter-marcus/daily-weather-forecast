def main():
    # import libraries
    import matplotlib.patheffects as pe
    import matplotlib.pyplot as plt
    import numpy as np
    import os
    import pandas as pd
    import requests
    import smtplib
    import time as t
    from dotenv import load_dotenv
    from datetime import date, datetime, time, timedelta
    from email.message import EmailMessage
    from email.utils import make_msgid
    from scipy.interpolate import make_interp_spline
    from utils import draw_pie, rescale_data, uv_styling, wind_styling

    APP_DIRECTORY = os.path.abspath(os.path.dirname(__file__))

    #### ENVIRONMENT VARIABLES ####
    load_dotenv()
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    EMAIL_TO = os.getenv("EMAIL_TO")
    API_KEY = os.getenv("API_KEY")
    N_CITIES = int(os.getenv("N_CITIES"))

    #### DATE SPECIFICATIONS ####    
    HOUR_FROM = 7
    HOUR_TO = 20


    #### CREATE DATA & CHARTS FOR ALL CITIES PASSED IN .ENV ####
    for N in range(N_CITIES):
        city_name = os.getenv(f"CITY_NAME{N}")
        city_lat = os.getenv(f"LATITUDE{N}")
        city_long = os.getenv(f"LONGITUDE{N}")
        img_file_path = f"{APP_DIRECTORY}/todays_weather{N}.png"
        
        #### API CALL ####
        url = "https://api.openweathermap.org/data/3.0/onecall"
        params = dict(
            lat=city_lat,
            lon=city_long,
            exclude="minutely",
            units="metric",
            appid=API_KEY
        )
        r = requests.get(url, params)


        #### PREPARE DATA ####
        raw_json_data = r.json()

        # Determine timezone offset (difference between local/machine and requested location timezone)
        location_timezone_offset = raw_json_data["timezone_offset"]
        local_timezone_offset = t.timezone if (t.localtime().tm_isdst == 0) else t.altzone
        utc_offset_hours = (local_timezone_offset + location_timezone_offset)/60/60

        hourly_data = raw_json_data["hourly"]
        data_dictionary = {
            id: {
                "Time": datetime.fromtimestamp(hour["dt"]) + timedelta(hours=utc_offset_hours),
                "Temperature": round(hour["temp"], 1),
                "UV-Index": hour["uvi"],
                "Wind Speed (km/h)": round(hour["wind_speed"]*(60*60)/1000),
                "Wind direction (degree)": hour["wind_deg"],
                "Cloudiness (%)": hour["clouds"],
                "Probability of precipitation (%)": int(hour["pop"]*100),
                "Rain (mm/h)": hour["rain"]["1h"] if "rain" in hour else 0,
                "Snow (mm/h)": hour["snow"]["1h"] if "snow" in hour else 0
            } for id, hour in enumerate(hourly_data)
        }
        data = pd.DataFrame.from_dict(data_dictionary, orient="index")
        
        # Create one measure of quantity of precipitation (amount of rain + amount of snow)
        data["Prec. (mm/h)"] = data[["Rain (mm/h)", "Snow (mm/h)"]].sum(axis=1)

        # Add time (hour) as string
        data["Hour"] = data["Time"].dt.strftime("%H:%M")

        # Store/filter today's data
        earliest_data_date = data["Time"].dt.date.min()
        earliest_data_hour = int(data["Time"].min().strftime("%H"))
        
        selected_date = earliest_data_date
        if earliest_data_hour >= HOUR_TO:
            selected_date = earliest_data_date + timedelta(days=1)

        todays_date_from = datetime.combine(selected_date, time(HOUR_FROM))
        todays_date_to = datetime.combine(selected_date, time(HOUR_TO))

        todays_data = data[(data["Time"] >= todays_date_from) & (data["Time"] <= todays_date_to)].copy()

        #### PLOT ####
        fig, (ax0, ax1) = plt.subplots(figsize=(9,6), nrows=2, height_ratios=[9, 3], sharex=True)
        plt.subplots_adjust(hspace=0)
        selected_date_str = selected_date.strftime("%A, %d. %B %Y")
        ax0.set_title(f"Weather Forecast for {city_name}\n{selected_date_str}")

        ## TOP FIGURE: POP & TEMPERATURE
        # LEFT Y-AXIS: POP
        pop_data = todays_data["Probability of precipitation (%)"]
        prec_data = todays_data["Prec. (mm/h)"]

        # Draw POP bars
        ax0.bar(
            x=todays_data.index,
            height=pop_data,
            color="lightblue", 
            label="Precipitation"
        )

        # Label POP data points
        for index in todays_data.index:
            pop = pop_data[index]
            if pop > 0:
                prec = prec_data[index]
                ax0.text(
                    x=index,
                    y=3,
                    s=f"{pop}%\n{round(prec,1):.1f}",
                    color="darkblue",
                    ha="center",
                    size=8,
                    linespacing=1.5
                )

        # Plot styling
        ax0.set_ylim(0,115)
        ax0.set_yticks([])
        ax0.legend(loc="upper left")


        # RIGHT Y-AXIS: TEMPERATURE
        ax0_twin = ax0.twinx()

        # Interpolate data for smoothened temperature curve
        x2 = todays_data.index
        y2 = todays_data["Temperature"]
        if len(x2) >= 3:
            x2_new = np.linspace(x2.min(), x2.max(), 100)
            interpolate = make_interp_spline(x2, y2, k=3)
            y2_new = interpolate(x2_new)
        else:
            x2_new, y2_new = x2, y2

        # Plot data
        ax0_twin.plot(x2_new, y2_new, color="orange", label="Temperature")
        ax0_twin.scatter(x=x2, y=y2, color="orange", marker="o")

        # Label temperature data points
        for index in todays_data.index:
            temp = y2[index]
            ax0_twin.text(
                x=index, 
                y=temp+0.5, 
                s=f"{round(temp)}°", 
                color="orange", 
                weight="bold", 
                ha="center"
            )

        # Plot styling
        y2_lim_max = y2.max()+2.5
        y2_lim_min = y2.min()-2.5
        ax0_twin.set_ylim(y2_lim_min, y2_lim_max)
        ax0_twin.set_yticks([])
        ax0_twin.legend(loc="upper right")
        # Add 0 degree line
        if y2_lim_min < 0 and y2_lim_max > 0:
            ax0_twin.axhline(y=0, color="lightgrey")
            ax0_twin.text(todays_data.index[0]-0.75, 0.2, "0°", color="lightgrey")


        ## BOTTOM FIGURE - CLOUDINESS, WIND & UV
        clouds_data = todays_data["Cloudiness (%)"] / 100
        wind_degree_data = todays_data["Wind direction (degree)"]
        wind_speed_data = todays_data["Wind Speed (km/h)"]
        uv_data = todays_data["UV-Index"]
        uv_data_scaled = rescale_data(uv_data, 0, 1.8)

        for index in todays_data.index:
            # CLOUDINESS
            clouds = clouds_data[index]
            # If there's 100% clouds, draw pie piece last so that only grey color is visible (and vice versa)
            pie_dist = [clouds, 1-clouds] if clouds < 1 else [1-clouds, clouds]
            pie_colors = ["grey", "yellow"] if clouds < 1 else ["yellow", "grey"]
            draw_pie(dist=pie_dist, xpos=index, ypos=5, size=250, colors=pie_colors, ax=ax1)
            
            # WIND
            wind_degree = wind_degree_data[index]
            wind_speed = wind_speed_data[index]
            wind_styles = wind_styling(wind_degree, wind_speed)

            # Draw arrows
            ax1.text(
                x=index, 
                y=3, 
                s="\u2192", 
                ha="center", 
                va="center", 
                color=wind_styles["arrow_color"], 
                size=wind_styles["arrow_size"], 
                weight=wind_styles["arrow_weight"], 
                rotation=(270-wind_degree)
            )
            # Annotate wind speed
            ax1.text(
                x=index, 
                y=wind_styles["wind_text_y_pos"], 
                s=f"{wind_speed:.0f}", 
                size=8, 
                ha=wind_styles["wind_text_ha"], 
                va="bottom"
            )
            
            # UV-INDEX
            uvi = uv_data[index] 
            uvi_scaled = uv_data_scaled[index] 
            uv_styles = uv_styling(uvi, uvi_scaled)
            # Draw UV bars
            ax1.bar(index, uvi_scaled, color=uv_styles["plot_color"])
            # Annotate UV data
            data_label = round(uvi)
            if data_label > 0:
                ax1.text(
                    x=index, 
                    y=uv_styles["text_y_pos"], 
                    s=data_label, 
                    color=uv_styles["font_color"],
                    path_effects=uv_styles["path_effects"],
                    weight="bold",  
                    ha="center", 
                    va="center"
                )

        # Plot styling
        ax1.set_ylim(0,6)
        ax1.axhline(4, color="black", linewidth=1)
        ax1.axhline(2, color="black", linewidth=1)
        ax1.set_yticks([])
        ax1.set_xticks(todays_data.index, todays_data["Hour"])


        # EXPORT PLOT
        plt.savefig(img_file_path, bbox_inches="tight")
        plt.close()


    #### SEND EMAIL ####
    # set up email message
    msg = EmailMessage()
    msg["Subject"] = "Today's weather forecast"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_TO

    # Create cids for images to embedd in html body of email
    image_cids = [make_msgid()[1:-1] for _ in range(N_CITIES)]
    embedded_img_html = "<br>".join(f'<img src="cid:{image_cids[N]}", alt="weather_forecast{N}">' for N in range(N_CITIES))

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=yes">
            <meta name="x-apple-disable-message-reformatting">
        </head>
        <body>
            {embedded_img_html}
        </body>
    </html>
    """

    msg.set_content(html_content, subtype="html")

    for N in range(N_CITIES):
        file_path = f"{APP_DIRECTORY}/todays_weather{N}.png"
        with open(file_path, "rb") as fp:
            msg.add_related(fp.read(), "image", "png", cid=image_cids[N])

    # Send email
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, EMAIL_TO, msg.as_string())

    print("Mail sent")

if __name__ == "__main__":
    main()