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

load_dotenv()
UTC_OFFSET = int(os.getenv('UTC_OFFSET'))
LATEST_HOUR_OF_THE_DAY = 20


#### API CALL ####
API_KEY = os.getenv('API_KEY')
LATITUDE = os.getenv('LATITUDE')
LONGITUDE = os.getenv('LONGITUDE')

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
data_dictionary = {id :
                   {'Time': datetime.fromtimestamp(int(hour['dt'])) + timedelta(hours=UTC_OFFSET),
                    'Temperature': round(hour['temp'], 1),
                    'UV-Index': hour['uvi'],
                    'UV-Index (rounded)': int(round(hour['uvi'])),
                    'Wind Speed (m/s)': hour['wind_speed'],
                    'Wind Speed (km/h)': round(hour['wind_speed']*(60*60)/1000),
                    'Wind direction (degree)': hour['wind_deg'],
                    'Cloudiness (%)': hour['clouds'],
                    'Probability of precipitation (%)': int(hour['pop']*100),
                    'Probability of precipitation (10% steps)': hour['pop']*10,
                    'Rain (mm/h)': hour['rain']['1h'] if 'rain' in hour else 0,
                    'Snow (mm/h)': hour['snow']['1h'] if 'snow' in hour else 0
                    } for id, hour in enumerate(hourly_data)}
data = pd.DataFrame.from_dict(data_dictionary, orient='index')

# Create 1 measure of quantity of precipitation (amount of rain + amount of snow)
data["Prec. (mm/h)"] = data[["Rain (mm/h)", "Snow (mm/h)"]].sum(axis=1)

# Convert degree of wind origin into compass direction
def degree_to_cardinal_direction(x):
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

data["Wind direction (cardinal direction)"] = data["Wind direction (degree)"].apply(degree_to_cardinal_direction)


# Store/filter today's data
todays_date_latest_hour = datetime.today().replace(hour=LATEST_HOUR_OF_THE_DAY)
todays_data = data[data['Time'] <= todays_date_latest_hour].copy()
todays_data['Hour'] = todays_data['Time'].dt.strftime("%H:%M")

# Store data as html table
table_columns_label = {"Hour": "Hour", 
                      "Temperature": "Temp", 
                      "UV-Index (rounded)" : "UV", 
                      "Probability of precipitation (%)": "POP (%)",
                      "Cloudiness (%)": "Clouds (%)",
                      # "Rain (mm/h)": "Rain (mm/h)", 
                      # "Snow (mm/h)": "Snow (mm/h)",
                      "Prec. (mm/h)": "Prec. (mm/h)",
                      # "Wind Speed (s/m)": "Wind (s/m)",
                      "Wind Speed (km/h)": "Wind (km/h)",
                      #"Wind direction (degree)": "Wind (degree)",
                      "Wind direction (cardinal direction)": "Wind (from)"}

todays_data_for_html = todays_data.filter(table_columns_label.keys())
todays_data_for_html = todays_data_for_html.rename(columns=table_columns_label)
todays_data_html = todays_data_for_html.to_html()
todays_data_html = todays_data_html.replace('class="dataframe"', 
                                            'class="dataframe" width="100%" cellpadding="2" cellspacing="0" style="min-width: 100%;"')



#### PLOT ####
plt.figure(figsize=(9,6))
plt.xticks(todays_data.index, todays_data['Hour'])

# Left y-axis: UV-Index and Chance of Rain
bar_width = 0.35
plt.bar(todays_data.index, todays_data['UV-Index (rounded)'], bar_width, color='firebrick', label='UV-Index')
plt.bar(todays_data.index+bar_width, todays_data['Probability of precipitation (10% steps)'], bar_width, color='lightblue', label='Chance of Rain')

# Label data points
for index in todays_data.index:
    uvi = todays_data['UV-Index (rounded)'][index]
    if uvi > 0:
        plt.text(index, uvi/2, int(uvi), color='white', weight='bold', ha='center')
    
    pop = todays_data['Probability of precipitation (10% steps)'][index]
    if pop > 0:
        plt.text(index+bar_width, pop+0.1, f'{round(pop*10)}%', color='darkblue', ha='center')

# Plot styling
plt.ylim(0,11)
plt.yticks([])
plt.legend(loc='upper left')


# Right axis: Temperature
x2 = todays_data.index
y2 = todays_data['Temperature']

# Interpolate data for smoothened temperature curve
x2_new = np.linspace(x2.min(), x2.max(), 100)
interpolate = make_interp_spline(x2, y2, k=3)
y2_new = interpolate(x2_new)

ax2 = plt.twinx()
ax2.plot(x2_new, y2_new, color="orange", label='Temperature')
ax2.scatter(x2, y2, color="orange", marker="o")

# Label data points
for index in todays_data.index:
    temp = y2[index]
    plt.text(index, temp+0.5, f'{round(temp)}°', color='orange', weight='bold', ha='center')

# Plot styling
y2_lim_max = y2.max()+2.5
y2_lim_min = y2.min()-2.5
ax2.set_ylim(y2_lim_min, y2_lim_max)
if y2_lim_min < 0 and y2_lim_max > 0:
    plt.axhline(y=0, color='lightgrey')
plt.yticks([])
plt.legend(loc='upper right')

# Export plot
plt.savefig('todays_weather.png', bbox_inches='tight')
plt.close()



#### SEND EMAIL ####
# include mail account credentials from environment variables
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_TO = os.getenv('EMAIL_TO')

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