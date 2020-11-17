import mysql.connector
import base64
from datetime import date, timedelta
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

def connect_to_database(password,schema,user='root',port='3308',host='127.0.0.1'):
    '''Connects to mysql database'''

    cnx = mysql.connector.connect(user=user,
                                  password=password,
                                  host=host,
                                  port=port,
                                  database=schema)
    cursor = cnx.cursor()

    return(cnx, cursor)

def connect_to_toggl(api_token):
    """Connect to toggl and get response containing information to the
    :param api_token:   Token for you user profile, you can find the token at
                        Toggl.com at the end of your profile page
    """

    string = api_token + ':api_token'
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(string.encode('ascii')).decode("utf-8")}
    url = 'https://www.toggl.com/api/v8/me'

    response = requests.get(url, headers=headers)
    response = response.json()

    email = response['data']['email']
    workspaces = [{'name': item['name'], 'id': item['id']} for item in response['data']['workspaces'] if
                  item['admin'] == True]

    my_workspace = workspaces[0]['id']

    return email, my_workspace, headers

def get_all_clients_and_projects(my_workspace, headers):
    '''Gets all clients and projects for your workspace id'''

    url = 'https://www.toggl.com/api/v8/workspaces/' + str(my_workspace) + '/clients'
    clients = requests.get(url, headers=headers).json()

    url = 'https://www.toggl.com/api/v8/workspaces/' + str(my_workspace) + '/projects'
    projects = requests.get(url, headers=headers).json()

    return clients, projects

def get_all_time_entries(headers, start_date):
    '''Finds all time entries in the time frame [start_date - end_date]'''

    today = date.today()
    end_date = today.strftime("%Y-%m-%d")

    url = 'https://api.track.toggl.com/api/v8/time_entries?start_date=' + start_date + 'T15%3A42%3A46%2B02%3A00&end_date=' + end_date + 'T15%3A42%3A46%2B02%3A00'
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
    time_entries_extended = time_entries_df.set_index('pid').join(join_projects_clients.set_index('pid'))

    return time_entries_extended

def define_working_days_table(start_date = date(2020, 8, 17), end_date = date.today()):

    def web_scraper_puplic_holidays():
        '''
        The following code retrieves the source code from https://www.ferienwiki.de/feiertage/de/bayern and
        saves the german (bavarian) puplic holidays in a MySQL database.
        :return:puplic_holidays_df: (data frame with a entry for each puplic holiday
                                    in bavaria)
        '''
        url = 'https://www.ferienwiki.de/feiertage/de/bayern'
        response = requests.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')
        td = soup.findAll('td')

        puplic_holidays = []

        for line in td:
            try:
                match = re.search(r'\d{2}.\d{2}.\d{4}', str(line))
                date = datetime.strptime(match.group(), '%d.%m.%Y').date()
                puplic_holidays.append(date)
            except:
                pass

        puplic_holidays_df = pd.DataFrame(data=puplic_holidays)
        return puplic_holidays_df.rename(columns={0: "days"})

    puplic_holidays_df = web_scraper_puplic_holidays()

    all_days = []
    for n in range(int((end_date - start_date).days)):
        day = start_date + timedelta(n)
        all_days.append(day)

    print(f"Number of days between start and end date: {len(all_days)}")

    workdays_index = [0, 1, 2, 3, 4]
    workdays = []
    for day in all_days:
        if date.weekday(day) in workdays_index:
            workdays.append(day)

    print(f"Number of workdays between start and end date: {len(workdays)}")

    workdays_df = pd.DataFrame(data=workdays)
    workdays_df = workdays_df.rename(columns={0: "days"})

    def anti_join(x, y, on):
        """Return rows in x which are not present in y"""
        ans = pd.merge(left=x, right=y, how='left', indicator=True, on=on)
        ans = ans.loc[ans._merge == 'left_only', :].drop(columns='_merge')
        return ans

    workdays_without_puplic_holidays_df = anti_join(workdays_df, puplic_holidays_df, on="days")

    print(f"Number of workdays between start and end date (minus puplic holidays): {len(workdays_without_puplic_holidays_df)}")

    return workdays_without_puplic_holidays_df

def input_vacation_days():
    pass


def write_toggl_data_in_database(cursor, cnx, time_entries_extended):
    return_messages=[]
    try:
        cursor.execute("CREATE TABLE `dashboard`.`toggl_time_entries` ("
                       "`id` INT NOT NULL,"
                       "`start` DATETIME NULL,"
                       "`stop` DATETIME NULL,"
                       "`duration` INT NULL,"
                       "`description` VARCHAR(45) NULL,"
                       "`project_name` VARCHAR(45) NULL,"
                       "`client_name` VARCHAR(45) NULL,"
                       "PRIMARY KEY (`id`));")
        cnx.commit()
    except mysql.connector.Error as e:
        return_messages.append("Error code:" + str(e.errno))
        return_messages.append("SQLSTATE value:" + str(e.sqlstate))
        return_messages.append("Error message:" + str(e.msg))
        return_messages.append("Error:" + str(e))

        try:
            cursor.execute("DROP TABLE `dashboard`.`toggl_time_entries`")
            return_messages.append("Current table toggl_time_entries was deleted successfully")
        except:
            return_messages.append("Error while deleting table toggl_time_entries")

        try:
            cursor.execute("CREATE TABLE `dashboard`.`toggl_time_entries` ("
                           "`id` INT NOT NULL,"
                           "`start` DATETIME NULL,"
                           "`stop` DATETIME NULL,"
                           "`duration` INT NULL,"
                           "`description` VARCHAR(45) NULL,"
                           "`project_name` VARCHAR(45) NULL,"
                           "`client_name` VARCHAR(45) NULL,"
                           "PRIMARY KEY (`id`));")
            cnx.commit()
            return_messages.append("Table toggl_time_entries was created successfully")
        except:
            return_messages.append("Error while creating table toggl_time_entries")

    # Create a new record
    sql = "INSERT INTO `toggl_time_entries` (`id`, `start`, `stop`, `duration`, `description`, `project_name`, `client_name`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    for index, line in time_entries_extended.iterrows():
        # import pdb; pdb.set_trace()
        if int(line['duration']) > 0:
            try:
                cursor.execute(sql, (line['id'],
                                     line['start'],
                                     line['stop'],
                                     line['duration'],
                                     line['description'],
                                     line['project_name'],
                                     line['client_name']))
                cnx.commit()
            except mysql.connector.Error as e:
                return(return_messages.append("Fail during ADDING ROWS to table toggl_time_entries"))
                return_messages.append("Error code:" + str(e.errno))
                return_messages.append("SQLSTATE value:" + str(e.sqlstate))
                return_messages.append("Error message:" + str(e.msg))
                return_messages.append("Error:" + str(e))

    return return_messages

def write_puplic_holidays_in_database(cursor, cnx, time_entries_extended):
    return_messages=[]

    try:
        cursor.execute("CREATE TABLE `dashboard`.`toggl_time_entries` ("
                       "`id` INT NOT NULL,"
                       "`start` DATETIME NULL,"
                       "`stop` DATETIME NULL,"
                       "`duration` INT NULL,"
                       "`description` VARCHAR(45) NULL,"
                       "`project_name` VARCHAR(45) NULL,"
                       "`client_name` VARCHAR(45) NULL,"
                       "PRIMARY KEY (`id`));")
        cnx.commit()
    except mysql.connector.Error as e:
        return_messages.append("Error code:" + str(e.errno))
        return_messages.append("SQLSTATE value:" + str(e.sqlstate))
        return_messages.append("Error message:" + str(e.msg))
        return_messages.append("Error:" + str(e))

        try:
            cursor.execute("DROP TABLE `dashboard`.`toggl_time_entries`")
            return_messages.append("Current table toggl_time_entries was deleted successfully")
        except:
            return_messages.append("Error while deleting table toggl_time_entries")

        try:
            cursor.execute("CREATE TABLE `dashboard`.`toggl_time_entries` ("
                           "`id` INT NOT NULL,"
                           "`start` DATETIME NULL,"
                           "`stop` DATETIME NULL,"
                           "`duration` INT NULL,"
                           "`description` VARCHAR(45) NULL,"
                           "`project_name` VARCHAR(45) NULL,"
                           "`client_name` VARCHAR(45) NULL,"
                           "PRIMARY KEY (`id`));")
            cnx.commit()
            return_messages.append("Table toggl_time_entries was created successfully")
        except:
            return_messages.append("Error while creating table toggl_time_entries")

    # Create a new record
    sql = "INSERT INTO `toggl_time_entries` (`id`, `start`, `stop`, `duration`, `description`, `project_name`, `client_name`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    for index, line in time_entries_extended.iterrows():
        # import pdb; pdb.set_trace()
        if int(line['duration']) > 0:
            try:
                cursor.execute(sql, (line['id'],
                                     line['start'],
                                     line['stop'],
                                     line['duration'],
                                     line['description'],
                                     line['project_name'],
                                     line['client_name']))
                cnx.commit()
            except mysql.connector.Error as e:
                return(return_messages.append("Fail during ADDING ROWS to table toggl_time_entries"))
                return_messages.append("Error code:" + str(e.errno))
                return_messages.append("SQLSTATE value:" + str(e.sqlstate))
                return_messages.append("Error message:" + str(e.msg))
                return_messages.append("Error:" + str(e))

    return return_messages

