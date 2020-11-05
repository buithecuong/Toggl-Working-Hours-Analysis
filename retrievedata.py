import smtplib, ssl
import mysql.connector
import imaplib
import pprint
import os
from toggl.TogglPy import Toggl


def connect_to_email_smtplib(host,user,password):
    '''This function connects to a email acc via smtplib to send emails

    Args:
        param host: Imap host e.g. Outlook.office365.com
        type host: str

        param user: login data e.g. example.email@outlook.com
        type host: str

        param host: password for the user
        type host: str

    Returns:
        server: connection to email host

    '''

    try:
        server = smtplib.SMTP('smtp.googlemail.com', 587)
        server.ehlo()
        server.starttls()
    except:
        print('Something went wrong...')

    return(server)

def connect_to_database(password,schema,user='root',port='3308',host='127.0.0.1'):
    '''This function connects to mysql database

    Args:
        param: user, password, schema
        type: str

        default param: user='root', port='3308',host='127.0.0.1'
        type: str

    return(cnx, cursor):
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

def connect_to_toggl():
    toggl = Toggl()
    toggl.setAuthCredentials('dmnkplzr@googlemail.com', 'Fcholzheim1995+')