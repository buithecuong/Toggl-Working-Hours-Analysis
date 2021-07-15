import os
from datetime import date, datetime

mysql = {'user': 'root',
         'password': os.environ['MYSQL_PW'],
         'host': '127.0.0.1',
         'port': '3308',
         'database': 'calc_working_hours',
         'raise_on_warnings': True}

write_to_mysql = False

#defines the time frame the script uses to calculate your over time
start_date = datetime(2021, 1, 1)
end_date = datetime.today()

#working hours per day
target_hours_per_day = 7

#needed for authentification, you can find the token to your acc at the the end of the profile
#settings page "https://track.toggl.com/profile"
toggl_api = os.environ['TOGGL_API'] #my toggl api token is saved as environmental variable