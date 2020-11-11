import smtplib, ssl
import mysql.connector
import imaplib
import pprint
import os
from toggl.TogglPy import Toggl
import requests
import base64

def connect_to_database(password,schema,user='root',port='3308',host='127.0.0.1'):
    '''This function connects to mysql database

    :arg:
        param: user, password, schema
        type: str

        default param: user='root', port='3308',host='127.0.0.1'
        type: str

    :returns
        cnx: mysql.connector
        cursor: cnx.cursor()
    '''

    cnx = mysql.connector.connect(user=user,
                                  password=password,
                                  host=host,
                                  port=port,
                                  database=schema)
    cursor = cnx.cursor()

    return(cnx, cursor)

def connect_to_toggl(api_token):
    '''Connect to toggl and get response containing information to the
    :arg:
        api_token: Token for you user profile, you can find the token at Toggl.com at the end of your profile page

    :returns
    '''

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

def get_all_clients(email, my_workspace, headers):
    """
    :returns:
        clients: dict with all clients
        params: parameter for the request (email and workspace_id)
    """
    url = 'https://www.toggl.com/api/v8/workspaces/' + str(my_workspace) + '/clients'
    params = {'user_agent': email, 'workspace_id': my_workspace}
    clients = requests.get(url, headers=headers, params=params).json()

    return clients, params