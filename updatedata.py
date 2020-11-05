from retrievedata import *
import os

cnx, cursor = connect_to_database(password=str(os.environ['MYSQL_SECRET']), schema='dashboard')

