from helper_functions import connect_to_database, connect_to_toggl, \
    get_all_clients_and_projects, get_all_time_entries, data_processing
import os
from models import TogglTimeEvents
import requests

cnx, cursor = connect_to_database(password=str(os.environ['MYSQL_SECRET']), schema='dashboard')

email, my_workspace, headers = connect_to_toggl(os.environ['TOGGL_API'])

clients, projects = get_all_clients_and_projects(my_workspace, headers)

time_entries = get_all_time_entries(headers,start_date='2020-08-01')

data_processing(clients,projects,time_entries)