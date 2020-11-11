from helper_functions import *
import os

cnx, cursor = connect_to_database(password=str(os.environ['MYSQL_SECRET']), schema='dashboard')

email, my_workspace, headers = connect_to_toggl(os.environ['TOGGL_API'])

clients, params = get_all_clients(email, my_workspace, headers)

url='https://www.toggl.com/api/v8/workspaces/'+str(my_workspace)+'/projects'
project_list=requests.get(url,headers=headers,params=params).json()