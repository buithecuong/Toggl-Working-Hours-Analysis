import smtplib, ssl
import mysql.connector
import imaplib
import pprint
import os
from toggl.TogglPy import Toggl
import requests
import base64
from datetime import date

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
    pass