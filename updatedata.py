from helper_functions import connect_to_database, connect_to_toggl, \
    get_all_clients_and_projects, get_all_time_entries, data_processing, \
    define_working_days_table, write_toggl_data_in_database
import os
import sqlalchemy
import mysql.connector
import pprint

cnx, cursor = connect_to_database(password=str(os.environ['MYSQL_SECRET']), schema='dashboard')

email, my_workspace, headers = connect_to_toggl(os.environ['TOGGL_API'])

clients, projects = get_all_clients_and_projects(my_workspace, headers)

time_entries = get_all_time_entries(headers, start_date='2020-08-01')

#process the information
time_entries_extended = data_processing(clients, projects, time_entries)
#fill NaN fields with "-"
time_entries_extended = time_entries_extended.fillna("-")

return_messages = write_toggl_data_in_database(cursor, cnx, time_entries_extended)
for line in return_messages:
    print(line)

workdays = define_working_days_table()

cnx.close()




