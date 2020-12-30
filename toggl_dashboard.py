from helper_functions import connect_to_database, connect_to_toggl, \
    get_all_clients_and_projects, get_all_time_entries, data_processing, \
    define_working_days_table, write_toggl_data_in_database, \
    write_working_days_list
import config
from datetime import datetime
import pandas as pd
import sys
import matplotlib.pyplot as plt
import numpy as np
import copy

'''
Collects the data from config.py and your Toggl acc and calculates worked hours and overtime
'''

def collect_data_from_toggl():
    email, my_workspace, headers = connect_to_toggl(config.toggl_api)

    clients, projects = get_all_clients_and_projects(my_workspace, headers)

    time_entries_extended_df = get_all_time_entries(headers, start_date=config.start_date,
                                                    end_date=config.end_date)
    #process the information
    time_entries_extended_df = data_processing(clients, projects, time_entries_extended_df)

    #fill NaN fields with "-"
    time_entries_extended_df = time_entries_extended_df.fillna("-")
    connect_to_database
    return time_entries_extended_df

time_entries_extended_df = collect_data_from_toggl()
#drop row where stop isnt defined yet
time_entries_extended_df = time_entries_extended_df[time_entries_extended_df.duration > 0]

working_days_df = define_working_days_table(config.start_date, config.end_date)
working_days_df["week"] = [item.strftime("%Y-%V") for item in working_days_df['days']]
working_days_sum_by_week_df = working_days_df.groupby(['week'])
working_days_sum_by_week_df = working_days_sum_by_week_df['working_hours'].agg(np.sum)
working_days_sum_by_week_df = pd.DataFrame(working_days_sum_by_week_df)

def write_tables_to_mysql(time_entries_extended, working_days_df):
    '''write the collected and processed data to tables in the MySQL database'''

    try:
        cnx, cursor = connect_to_database(password=config.mysql["user"], database=config.mysql["database"],
                                          user=config.mysql["user"], port=config.mysql["port"], host=config.mysql["host"])

        return_messages_time_entries = write_toggl_data_in_database(cursor, cnx, time_entries_extended)
        for item in return_messages_time_entries:
            print(item)

        return_messages_working_days = write_working_days_list(cursor, cnx, working_days_df)
        for item in return_messages_working_days:
            print(item)
    finally:
        cnx.close()

if config.write_to_mysql == True:
    write_tables_to_mysql(time_entries_extended_df, working_days_df)


def sum_worked_hours_by_week(time_entries_extended_df):
    '''
    Sums up the hours in the Toogl time entries by the calendar week
    :return: DataFrame with CW and the sum of the time entries duration in this week
    '''

    time_entries = copy.deepcopy(time_entries_extended_df)

    time_entries.loc[:, 'week'] = time_entries.start.map(lambda x: datetime.date(datetime.strptime(x, '%Y-%m-%dT%H:%M:%S+00:00')).strftime("%Y-%V"))
    time_entries.loc[:, 'duration_hours'] = time_entries.duration.map(lambda x: x/3600)

    time_entries_sum_per_week_df = time_entries.groupby(['week']).agg("sum")

    return time_entries_sum_per_week_df


#calculate worked hours for a certain client
time_entries_sum_per_week_df = sum_worked_hours_by_week(
    time_entries_extended_df[time_entries_extended_df.client_name == "DI"]
)

worked_hours = time_entries_sum_per_week_df["duration_hours"].sum()
target_hours = working_days_sum_by_week_df["working_hours"].sum()
over_hours =round((worked_hours - target_hours),1)

#plot diagram with matplotlib
fig, ax = plt.subplots(figsize=(15, 7))
ax.bar(working_days_sum_by_week_df.index.tolist(), working_days_sum_by_week_df["working_hours"].tolist(), width=0.35, label="Target working hours", color="grey")

for i, client in enumerate(time_entries_extended_df.client_name.unique()):
    time_entries_sum_per_week_df = sum_worked_hours_by_week(
        time_entries_extended_df[time_entries_extended_df.client_name == client]
    )

    bar = ax.plot(time_entries_sum_per_week_df.index.tolist(), time_entries_sum_per_week_df["duration_hours"].tolist(),
                  "-o", label=client)

ax.set(xlabel='Calendar week', ylabel='Hours',
       title=f'Working hours (total overhours: {over_hours})')

ax.legend(title="Clients")
plt.xticks(rotation=45)
plt.show()