def main():
    # import libraries
    import matplotlib.pyplot as plt
    import numpy as np
    import os
    import pandas as pd
    import requests
    import smtplib
    from dotenv import load_dotenv
    from datetime import datetime, timedelta
    from email.message import EmailMessage
    from email.utils import make_msgid
    from scipy.interpolate import make_interp_spline
    from utils import drawPieMarker, degree_to_cardinal_direction


    #### ENVIRONMENT VARIABLES ####
    load_dotenv()
    UTC_OFFSET = int(os.getenv('UTC_OFFSET'))
    LATEST_HOUR_OF_THE_DAY = 20
    EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    EMAIL_TO = os.getenv('EMAIL_TO')
    API_KEY = os.getenv('API_KEY')
    LATITUDE = os.getenv('LATITUDE')
    LONGITUDE = os.getenv('LONGITUDE')


    #### API CALL ####
    url = 'https://api.openweathermap.org/data/3.0/onecall'
    params = dict(
        lat=LATITUDE,
        lon=LONGITUDE,
        exclude='minutely',
        units='metric',
        appid=API_KEY
    )
    r = requests.get(url, params)


    #### PREPARE DATA ####
    raw_json_data = r.json()
    hourly_data = raw_json_data['hourly']

    data_dictionary = {
        id: {
            'Time': datetime.fromtimestamp(int(hour['dt'])) + timedelta(hours=UTC_OFFSET),
            'Temperature': round(hour['temp'], 1),
            'UV-Index': hour['uvi'],
            'UV-Index (rounded)': int(round(hour['uvi'])),
            'Wind Speed (m/s)': hour['wind_speed'],
            'Wind Speed (km/h)': round(hour['wind_speed']*(60*60)/1000),
            'Wind direction (degree)': hour['wind_deg'],
            'Cloudiness (%)': hour['clouds'],
            'Sunniness (%)': 100-hour['clouds'],
            'Probability of precipitation (%)': int(hour['pop']*100),
            'Probability of precipitation (10% steps)': hour['pop']*10,
            'Rain (mm/h)': hour['rain']['1h'] if 'rain' in hour else 0,
            'Snow (mm/h)': hour['snow']['1h'] if 'snow' in hour else 0
        } for id, hour in enumerate(hourly_data)
    }
    data = pd.DataFrame.from_dict(data_dictionary, orient='index')

    # Create one measure of quantity of precipitation (amount of rain + amount of snow)
    data["Prec. (mm/h)"] = data[["Rain (mm/h)", "Snow (mm/h)"]].sum(axis=1)

    # Determine cardinal direction from degree of wind
    data["Wind direction (cardinal direction)"] = data["Wind direction (degree)"].apply(degree_to_cardinal_direction)


    # Store/filter today's data
    todays_date_latest_hour = datetime.today().replace(hour=LATEST_HOUR_OF_THE_DAY)
    todays_data = data[data['Time'] <= todays_date_latest_hour].copy()
    todays_data['Hour'] = todays_data['Time'].dt.strftime("%H:%M")


    # Store data as html table
    table_columns_label = {
        "Hour": "Hour",
        "Temperature": "Temp",
        "UV-Index (rounded)" : "UV",
        "Probability of precipitation (%)": "POP (%)",
        "Cloudiness (%)": "Clouds (%)",
        "Prec. (mm/h)": "Prec. (mm/h)",
        "Wind Speed (km/h)": "Wind (km/h)",
        "Wind direction (cardinal direction)": "Wind (from)"
    }

    todays_data_for_html = todays_data.filter(table_columns_label.keys())
    todays_data_for_html = todays_data_for_html.rename(columns=table_columns_label)
    todays_data_html = todays_data_for_html.to_html()
    html_inline_style = 'class="dataframe" width="100%" cellpadding="2" cellspacing="0" style="min-width: 100%;"'
    todays_data_html = todays_data_html.replace('class="dataframe"', html_inline_style)


    #### PLOT ####
    fig, (ax0, ax1) = plt.subplots(figsize=(9,6), nrows=2, height_ratios=[10, 1], sharex=True)
    plt.subplots_adjust(hspace=0)

    ## TOP FIGURE: UV, POP, TEMPERATURE
    # LEFT Y-AXIS: UV, POP
    bar_width = 0.35
    bar_offset = bar_width / 2
    ax0.bar(todays_data.index - bar_offset, 
            todays_data['UV-Index (rounded)'], 
            bar_width, 
            color='firebrick',
            label='UV-Index')
    ax0.bar(todays_data.index + bar_offset, 
            todays_data['Probability of precipitation (10% steps)'], 
            bar_width, 
            color='lightblue', 
            label='Chance of Rain')

    # Label data points
    for index in todays_data.index:
        uvi = todays_data['UV-Index (rounded)'][index]
        if uvi > 0:
            ax0.text(index - bar_offset, uvi/2, int(uvi), color='white', weight='bold', ha='center')
        
        pop = todays_data['Probability of precipitation (10% steps)'][index]
        if pop > 0:
            prec = todays_data['Prec. (mm/h)'][index]
            ax0.text(index + bar_offset, pop+0.1, f'{round(pop*10)}%', color='darkblue', ha='center')
            ax0.text(index + bar_offset, pop-1, f'{round(prec,1)}\nmm/h', color='darkblue', ha='center')

    # Plot styling
    ax0.set_ylim(0,11)
    ax0.set_yticks([])
    ax0.legend(loc='upper left')


    # RIGHT Y-AXIS: TEMPERATURE
    ax0_twin = ax0.twinx()

    # Interpolate data for smoothened temperature curve
    x2 = todays_data.index
    y2 = todays_data['Temperature']
    x2_new = np.linspace(x2.min(), x2.max(), 100)
    interpolate = make_interp_spline(x2, y2, k=3)
    y2_new = interpolate(x2_new)

    # Plot data
    ax0_twin.plot(x2_new, y2_new, color="orange", label='Temperature')
    ax0_twin.scatter(x2, y2, color="orange", marker="o")

    # Label data points
    for index in todays_data.index:
        temp = y2[index]
        ax0_twin.text(index, temp+0.5, f'{round(temp)}°', color='orange', weight='bold', ha='center')

    # Plot styling
    y2_lim_max = y2.max()+2.5
    y2_lim_min = y2.min()-2.5
    ax0_twin.set_ylim(y2_lim_min, y2_lim_max)
    if y2_lim_min < 0 and y2_lim_max > 0: # Add 0 degree line
        ax0_twin.axhline(y=0, color='lightgrey')
    ax0_twin.set_yticks([])
    ax0_twin.legend(loc='upper right')


    ## BOTTOM FIGURE - CLOUDINESS
    for index in todays_data.index:
        c, s = todays_data.loc[index, ['Cloudiness (%)', 'Sunniness (%)']] / 100
        drawPieMarker(xpos=index, ypos=0, ratios=[s, c], size=250, colors=['yellow', 'grey'], plot=ax1)
    ax1.set_yticks([])
    ax1.set_xticks(todays_data.index, todays_data['Hour'])


    # EXPORT PLOT
    plt.savefig('todays_weather.png', bbox_inches='tight')
    plt.close()


    #### SEND EMAIL ####
    # set up email message
    msg = EmailMessage()
    msg['Subject'] = "Today's weather forecast"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = EMAIL_TO

    image_cid = make_msgid()

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=yes">
    <meta name="x-apple-disable-message-reformatting">
    </head>
    <body>
    <img src="cid:{image_cid[1:-1]}", alt="weather_forecast">
    <br><hr><br>
    {todays_data_html}
    </body>
    </html>
    """

    msg.set_content(html_content, subtype="html")

    with open('todays_weather.png', 'rb') as fp:
        msg.add_related(fp.read(), 'image', 'png', cid=image_cid)

    # send email
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, EMAIL_TO, msg.as_string())

    print('Mail sent')

if __name__ == '__main__':
    main()