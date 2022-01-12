import os
import smtplib
import matplotlib.pyplot as plt
import mysql.connector
import config
import pandas as pd


# g_secret = os.environ['G-PW']
# mail1 = os.environ['MAIL1']
# mail2 = os.environ['MAIL2']
#
# gmail_user = mail1
# gmail_password = g_secret
#
# sent_from = gmail_user
# to = [mail1, mail2]
# subject = 'Subject'
# body = 'test'
#
# email_text = """\
# From: %s
# To: %s
# Subject: %s
#
# %s
# """ % (sent_from, ", ".join(to), subject, body)
#
# try:
#     server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
#     server.ehlo()
#     server.login(gmail_user, gmail_password)
#     server.sendmail(sent_from, to, email_text)
#     server.close()
#
#     print('Email sent!')
# except:
#     print('Something went wrong...')
#
#
# fig = plt.figure(1)
# ax = fig.add_subplot(111)
#
# # Need to do this so we don't have to worry about how many lines we have -
# # matplotlib doesn't like one x and multiple ys, so just repeat the x
# lines = []
#
# x = [1,2,3]
# y = [1,2,3]
# ax.plot(x,y)
#
# fig.savefig(r"./results/filename.png")

# cnx = mysql.connector.connect(
#             host="dashboardserver.germanywestcentral.cloudapp.azure.com",
#             user=config.mysql["user"],
#             password=config.mysql["password"],
#             port=config.mysql["port"],
# )
#
#
# mycursor = cnx.cursor()
#
# mycursor.execute("SELECT date FROM calc_working_hours.public_holidays;")
#
# myresult = mycursor.fetchall()
#
# public_holidays = []
#
# for x in myresult:
#     public_holidays.append(x[0])
#
# public_holidays_df = pd.DataFrame(data=public_holidays)
# public_holidays_df = public_holidays_df.rename(columns={0: "days"})
# pass

import psycopg2


# cnx = psycopg2.connect(
#             host='127.0.0.1',
#             user='postgres',
#             password=os.environ['Postgres_secret'],
#             port='5432',
#             database='calc_working_hours'
# )

cnx = psycopg2.connect(
    host=config.postgres["host"],
    user=config.postgres["user"],
    password=config.postgres["password"],
    port=config.postgres["port"],
    database=config.postgres["database"]
)


cur = cnx.cursor()

cur.execute("SELECT * FROM public.public_holidays")

myresult = cur.fetchall()

test="test"