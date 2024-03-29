#import mysql.connector
import base64
from datetime import date, timedelta, timezone
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import config
from urllib.parse import urlencode
import os
import pathlib
import numpy as np

#import psycopg2

# def connect_to_database(password, database, user, port, host):
#     '''Connects to mysql database'''
#
#     cnx = mysql.connector.connect(user=user,
#                                   password=password,
#                                   host=host,
#                                   port=port,
#                                   database=database)
#     cursor = cnx.cursor()
#
#     return(cnx, cursor)

# def connect_to_postgres_database(password, database, user, port, host):
#     '''Connects to postgres database'''
#
#     cnx = psycopg2.connector.connect(user=user,
#                                   password=password,
#                                   host=host,
#                                   port=port,
#                                   database=database)
#     cursor = cnx.cursor()
#
#     return(cnx, cursor)

def connect_to_toggl(api_token):
    """Connect to toggl and get response containing information to the
    :param api_token:   Token for you user profile, you can find the token at
                        Toggl.com at the end of the profile settings page
    """

    string = api_token + ':api_token'
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(string.encode('ascii')).decode("utf-8")}
    url = 'https://api.track.toggl.com/api/v8/me'

    response = requests.get(url, headers=headers)
    response = response.json()
    email = response['data']['email']
    workspaces = [{'name': item['name'], 'id': item['id']} for item in response['data']['workspaces'] if
                  item['admin'] == True]

    my_workspace = workspaces[0]['id']

    return email, my_workspace, headers

def get_all_clients_and_projects(my_workspace, headers):
    '''Gets all clients and projects for your workspace id'''

    url = 'https://api.track.toggl.com/api/v8/workspaces/' + str(my_workspace) + '/clients'
    clients = requests.get(url, headers=headers).json()

    url = 'https://api.track.toggl.com/api/v8/workspaces/' + str(my_workspace) + '/projects'
    projects = requests.get(url, headers=headers).json()

    return clients, projects

def get_all_time_entries(headers, start_date, end_date):
    '''Finds all time entries in the time frame [start_date - end_date]'''

    start_date = start_date.replace(tzinfo=timezone.utc).isoformat()
    end_date = end_date.replace(tzinfo=timezone.utc).isoformat()

    url = 'https://api.track.toggl.com/api/v8/time_entries?'
    params = {'start_date': start_date, 'end_date': end_date}
    url = url + '{}'.format(urlencode(params))

    time_entries = requests.get(url, headers=headers).json()
    return time_entries

def data_processing(clients,projects,time_entries):
    '''Join clients, projects and time entries to a data frame with all time entries
    and the corresponding information to clients and projects'''

    projects_filtered = [{'pid': item['id'],
                          'cid': item['cid'],
                          'project_name': item['name']} for item in projects]

    clients_filtered = [{'cid': item['id'],
                         'client_name': item['name']} for item in clients]

    projects_df = pd.DataFrame(data=projects_filtered)
    clients_df = pd.DataFrame(data=clients_filtered)
    time_entries_df = pd.DataFrame(data=time_entries)

    join_projects_clients = projects_df.set_index('cid').join(clients_df.set_index('cid'))
    time_entries_extended_df = time_entries_df.set_index('pid').join(join_projects_clients.set_index('pid'))

    return time_entries_extended_df

# def query_public_holidays_from_db():
#     '''
#     Queries data from table public_holidays and saves them in a list
#     :return: public_holidays_df
#     '''
#
#     # cnx = mysql.connector.connect(
#     #             host=config.mysql["host"],
#     #             user=config.mysql["user"],
#     #             password=config.mysql["password"],
#     #             port=config.mysql["port"],
#     # )
#
#     cnx = psycopg2.connect(
#                 host=config.postgres["host"],
#                 user=config.postgres["user"],
#                 password=config.postgres["password"],
#                 port=config.postgres["port"],
#                 database=config.postgres["database"]
#     )
#
#     cur = cnx.cursor()
#
#     cur.execute("SELECT * FROM public.public_holidays")
#
#     myresult = cur.fetchall()
#
#     public_holidays = []
#
#     for x in myresult:
#         public_holidays.append(x[0])
#
#     # public_holidays_df = pd.DataFrame(data=public_holidays)
#     # public_holidays_df = public_holidays_df.rename(columns={0: "days"})
#
#     return public_holidays

def query_public_holidays_from_csv():
    '''
    Queries data from file public_holidays and saves them in a list
    :return: public_holidays_df
    '''

    dir = pathlib.Path(__file__).parent.absolute()
    filename = r'/public_holidays.csv'
    path = str(dir) + filename

    public_holidays = pd.read_csv(path)
    #public_holidays['date'] = pd.to_datetime(public_holidays['date'], format='%d.%m.%Y')

    value_list = public_holidays.values.tolist()
    public_holidays_list = []

    for value in value_list:
        value = datetime.strptime(value[0], "%d.%m.%Y")
        public_holidays_list.append(value)

    return public_holidays_list

# def query_vacation_days_from_db():
#     '''
#     Queries data from table vacation_days and saves them in a list
#     :return: vacation_days
#     '''
#
#     # cnx = mysql.connector.connect(
#     #             host=config.mysql["host"],
#     #             user=config.mysql["user"],
#     #             password=config.mysql["password"],
#     #             port=config.mysql["port"],
#     # )
#
#
#     cnx = psycopg2.connect(
#                 host=config.postgres["host"],
#                 user=config.postgres["user"],
#                 password=config.postgres["password"],
#                 port=config.postgres["port"],
#                 database=config.postgres["database"]
#     )
#
#     mycursor = cnx.cursor()
#
#     mycursor.execute("SELECT vacation_days FROM public.vacation_days;")
#
#     myresult = mycursor.fetchall()
#
#     vacation_days = []
#
#     for x in myresult:
#         vacation_days.append(x[0])
#
#     return vacation_days

def query_vacation_days_from_csv():
    '''
    Queries data from table vacation_days and saves them in a list
    :return: vacation_days
    '''

    dir = pathlib.Path(__file__).parent.absolute()
    filename = r'/vacation_days.csv'
    path = str(dir) + filename

    vacation_days = pd.read_csv(path)

    value_list = vacation_days.values.tolist()
    vacation_days_list = []

    for value in value_list:
        value = datetime.strptime(value[0], "%d.%m.%Y")
        vacation_days_list.append(value)

    return vacation_days_list

def define_working_days_table(start_date, end_date):
    """
    :return:    Returns a data frame with all days in the defined time frame (start_date - end_date)
                The data frame has two columns: days and type
                :Days: contains all dates in the time frame
                :Type: the information if the day is a
                        - working day (WD)
                        - vacation day (paid time off - PTO)
                        - public holiday (PH)
                        - weekend (WE) - saturday and sunday
    """

    public_holidays = query_public_holidays_from_csv()
    vacation_days = query_vacation_days_from_csv()

    all_days = []
    for n in range(int((end_date - start_date).days)):
        day = start_date + timedelta(n)
        all_days.append({'days': day, 'type': "WD"})

    workdays_index = [0, 1, 2, 3, 4]
    all_days_we = []
    for item in all_days:
        if date.weekday(item['days']) in workdays_index:
            all_days_we.append({'days': item['days'], 'type': item['type']})
        else:
            all_days_we.append({'days': item['days'], 'type': "WE"})

    all_days_we_ph = []
    for item in all_days_we:
        if np.datetime64(item['days']) in public_holidays:
            all_days_we_ph.append({'days': item['days'], 'type': "PH"})
        else:
            all_days_we_ph.append({'days': item['days'], 'type': item['type']})


    all_days_we_ph_pto = []
    for item in all_days_we_ph:
        if item['days'] in vacation_days:
            all_days_we_ph_pto.append({'days': item['days'], 'type': "PTO"})
        else:
            all_days_we_ph_pto.append({'days': item['days'], 'type': item['type']})

    print(f"Number of days between start and end date: {len(all_days_we_ph_pto)}")
    print(f"Number of weekend days between start and end date: {len([1 for item in all_days_we_ph_pto if item['type'] == 'WE'])}")
    print(f"Number of public holidays between start and end date (minus public holidays): {len([1 for item in all_days_we_ph_pto if item['type'] == 'PH'])}")
    print(f"Number of vacation days between start and end date (minus public holidays and vacation days): {len([1 for item in all_days_we_ph_pto if item['type'] == 'PTO'])}")

    working_days = []
    for item in all_days_we_ph_pto:
        if item['type'] == "WD":
            working_days.append({'days': item['days'], 'type': item['type'], 'working_hours': config.target_hours_per_day})
        else:
            working_days.append({'days': item['days'], 'type': item['type'], 'working_hours': 0})

    working_days_df = pd.DataFrame(data=working_days)
    return working_days_df

# def write_toggl_data_in_database(cursor, cnx, time_entries_extended):
#     return_messages=[]
#     try:
#         cursor.execute("CREATE TABLE `dashboard`.`toggl_time_entries` ("
#                        "`id` INT NOT NULL,"
#                        "`start` DATETIME NULL,"
#                        "`stop` DATETIME NULL,"
#                        "`duration` INT NULL,"
#                        "`description` VARCHAR(45) NULL,"
#                        "`project_name` VARCHAR(45) NULL,"
#                        "`client_name` VARCHAR(45) NULL,"
#                        "PRIMARY KEY (`id`));")
#         cnx.commit()
#     except mysql.connector.Error as e:
#         return_messages.append("Error code:" + str(e.errno))
#         return_messages.append("SQLSTATE value:" + str(e.sqlstate))
#         return_messages.append("Error message:" + str(e.msg))
#         return_messages.append("Error:" + str(e))
#
#         try:
#             cursor.execute("DROP TABLE `dashboard`.`toggl_time_entries`")
#             return_messages.append("Current table toggl_time_entries was deleted successfully")
#         except:
#             return_messages.append("Error while deleting table toggl_time_entries")
#
#         try:
#             cursor.execute("CREATE TABLE `dashboard`.`toggl_time_entries` ("
#                            "`id` INT NOT NULL,"
#                            "`start` DATETIME NULL,"
#                            "`stop` DATETIME NULL,"
#                            "`duration` INT NULL,"
#                            "`description` VARCHAR(45) NULL,"
#                            "`project_name` VARCHAR(45) NULL,"
#                            "`client_name` VARCHAR(45) NULL,"
#                            "PRIMARY KEY (`id`));")
#             cnx.commit()
#             return_messages.append("Table toggl_time_entries was created successfully")
#         except:
#             return_messages.append("Error while creating table toggl_time_entries")
#
#     # Create a new record
#     sql = "INSERT INTO `toggl_time_entries` (`id`, `start`, `stop`, `duration`, `description`, `project_name`, `client_name`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
#     for index, line in time_entries_extended.iterrows():
#         if int(line['duration']) > 0:
#             try:
#                 cursor.execute(sql, (line['id'],
#                                      line['start'],
#                                      line['stop'],
#                                      line['duration'],
#                                      line['description'],
#                                      line['project_name'],
#                                      line['client_name']))
#                 cnx.commit()
#             except mysql.connector.Error as e:
#                 return(return_messages.append("Fail during ADDING ROWS to table toggl_time_entries"))
#                 return_messages.append("Error code:" + str(e.errno))
#                 return_messages.append("SQLSTATE value:" + str(e.sqlstate))
#                 return_messages.append("Error message:" + str(e.msg))
#                 return_messages.append("Error:" + str(e))
#
#     return return_messages

# def write_working_days_list(cursor, cnx, working_days_df):
#     '''Creates the table working_days in the mysql database'''
#
#     return_messages=[]
#     try:
#         cursor.execute("CREATE TABLE `dashboard`.`working_days` ("
#                        "`id` INT NOT NULL,"
#                        "`days` DATETIME NULL,"
#                        "`type` VARCHAR(45) NULL,"
#                        "`working_hours` INT NULL,"
#                        "PRIMARY KEY (`id`));")
#         cnx.commit()
#     except mysql.connector.Error as e:
#         return_messages.append("Error code:" + str(e.errno))
#         return_messages.append("SQLSTATE value:" + str(e.sqlstate))
#         return_messages.append("Error message:" + str(e.msg))
#         return_messages.append("Error:" + str(e))
#
#         try:
#             cursor.execute("DROP TABLE `dashboard`.`working_days`")
#             return_messages.append("Current table working_days was deleted successfully")
#         except:
#             return_messages.append("Error while deleting table working_days")
#
#         try:
#             cursor.execute("CREATE TABLE `dashboard`.`working_days` ("
#                            "`id` INT NOT NULL,"
#                            "`days` DATETIME NULL,"
#                            "`type` VARCHAR(45) NULL,"
#                            "`working_hours` INT NULL,"
#                            "PRIMARY KEY (`id`));")
#             cnx.commit()
#             return_messages.append("Table working_days was created successfully")
#         except:
#             return_messages.append("Error while creating table working_days")
#
#     # Create a new record
#     sql = "INSERT INTO `working_days` (`id`, `days`, `type`, `working_hours`) VALUES (%s, %s, %s, %s)"
#     for index, line in working_days_df.iterrows():
#         try:
#             cursor.execute(sql, (index,
#                                  line['days'],
#                                  line['type'],
#                                  line['working_hours']))
#             cnx.commit()
#         except:
#             return(return_messages.append("Fail during ADDING ROWS to table working_days"))
#             return_messages.append("Error code:" + str(e.errno))
#             return_messages.append("SQLSTATE value:" + str(e.sqlstate))
#             return_messages.append("Error message:" + str(e.msg))
#             return_messages.append("Error:" + str(e))
#
#     return return_messages

