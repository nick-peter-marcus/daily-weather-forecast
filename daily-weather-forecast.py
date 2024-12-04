# import libraries
import matplotlib.pyplot as plt
import os
import pandas as pd
import requests
import smtplib
from dotenv import load_dotenv
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

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
                    'Temperature': hour['temp'], 
                    'UV-Index': hour['uvi'], 
                    'Wind Speed': hour['wind_speed'],
                    'Cloudiness (%)': hour['clouds'],
                    'Probability of precipitation': hour['pop'],
                    'Rain (mm/h)': hour['rain']['1h'] if 'rain' in hour else 0,
                    'Snow (mm/h)': hour['snow']['1h'] if 'snow' in hour else 0
                    } for id, hour in enumerate(hourly_data)}
data = pd.DataFrame.from_dict(data_dictionary, orient='index')

# Store today's data
todays_date_latest_hour = datetime.today().replace(hour=LATEST_HOUR_OF_THE_DAY)
todays_data = data[data['Time'] <= todays_date_latest_hour].copy()
todays_data_html = todays_data.to_html()

todays_data['Hour'] = todays_data['Time'].dt.strftime("%H:%M")
todays_data['UV-Index (rounded)'] = round(todays_data['UV-Index'])
todays_data['Probability of precipitation (10% steps)'] = todays_data['Probability of precipitation']*10


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
ax2 = plt.twinx()
ax2.plot(todays_data.index, todays_data['Temperature'], color='orange', marker='o', label='Temperature')

# Label data points
for index in todays_data.index:
    temp = todays_data['Temperature'][index]
    if temp > 0:
        plt.text(index, temp+0.5, f'{round(temp)}°', color='orange', weight='bold', ha='center')

# Plot styling
y2_max = max(todays_data['Temperature'])+2.5
y2_min = min(todays_data['Temperature'])-2.5
ax2.set_ylim(y2_min, y2_max)
plt.yticks([])
plt.legend(loc='upper right')

# Export plot
plt.savefig('todays_weather.png', bbox_inches='tight')
plt.close()



#### SEND EMAIL ####

text_body = 'plain text: <img src="cid:image1">'
html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1 user-scalable=no">
</head>
<body>
<img src="cid:image1", alt="weather forecast">
<br><hr><br>
{todays_data_html.replace('class="dataframe"', 'class="dataframe" width="100%" cellpadding="0" cellspacing="0" style="min-width: 100%;"')}
</body>
</html>
"""

# include mail account credentials from environment variables
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_TO = os.getenv('EMAIL_TO')

# set up email message
msg = MIMEMultipart('alternative')
msg['Subject'] = "Today's weather forecast"
msg['From'] = EMAIL_ADDRESS
msg['To'] = EMAIL_TO
msg.attach(MIMEText(text_body, 'plain'))
msg.attach(MIMEText(html_body, 'html'))

fp = open('todays_weather.png', 'rb')
msgImage = MIMEImage(fp.read())
fp.close()

msgImage.add_header('Content-ID', '<image1>')
msg.attach(msgImage)

# send email
with smtplib.SMTP('smtp.gmail.com', 587) as server:
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    server.sendmail(EMAIL_ADDRESS, EMAIL_TO, msg.as_string())

print('Mail sent')