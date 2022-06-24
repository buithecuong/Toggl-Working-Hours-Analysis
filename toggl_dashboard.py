from helper_functions import connect_to_toggl, \
    get_all_clients_and_projects, get_all_time_entries, data_processing, \
    define_working_days_table
import config
from datetime import datetime, date
import pandas as pd
import numpy as np
import copy
import os
import smtplib
import matplotlib.pyplot as plt

from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

import pathlib

'''
Collects the data from config.py and your Toggl acc and calculates worked hours and overtime
'''

def collect_data_from_toggl():
    email, my_workspace, headers = connect_to_toggl(config.toggl_api)

    clients, projects = get_all_clients_and_projects(my_workspace, headers)

    time_entries_extended_df = get_all_time_entries(headers, start_date=config.start_date,
                                                    end_date=config.end_date)
    #process the information
    time_entries_extended_df = data_processing(clients, projects, time_entries_extended_df)

    #fill NaN fields with "-"
    time_entries_extended_df = time_entries_extended_df.fillna("-")
    #connect_to_database
    return time_entries_extended_df

time_entries_extended_df = collect_data_from_toggl()
#drop row where stop isnt defined yet (if time event is still running)
time_entries_extended_df = time_entries_extended_df[time_entries_extended_df.duration > 0]

working_days_df = define_working_days_table(config.start_date, config.end_date)
working_days_df["week"] = [item.strftime("%Y-%V") for item in working_days_df['days']]
working_days_sum_by_week_df = working_days_df.groupby(['week'])
working_days_sum_by_week_df = working_days_sum_by_week_df['working_hours'].agg(np.sum)
working_days_sum_by_week_df = pd.DataFrame(working_days_sum_by_week_df)

# def write_tables_to_mysql(time_entries_extended, working_days_df):
#     '''write the collected and processed data to tables in the MySQL database'''
#
#     try:
#         cnx, cursor = connect_to_postgres_database(password=config.postgres["user"],
#                                                       database=config.postgres["database"],
#                                                       user=config.postgres["user"],
#                                                       port=config.postgres["port"],
#                                                       host=config.postgres["host"])
#
#         # cnx, cursor = connect_to_database(password=config.mysql["user"],
#         #                                   database=config.mysql["database"],
#         #                                   user=config.mysql["user"],
#         #                                   port=config.mysql["port"],
#         #                                   host=config.mysql["host"])
#
#         return_messages_time_entries = write_toggl_data_in_database(cursor, cnx, time_entries_extended)
#         for item in return_messages_time_entries:
#             print(item)
#
#         return_messages_working_days = write_working_days_list(cursor, cnx, working_days_df)
#         for item in return_messages_working_days:
#             print(item)
#     finally:
#         cnx.close()

# if config.write_to_mysql == True:
#     write_tables_to_mysql(time_entries_extended_df, working_days_df)


def sum_worked_hours_by_week(time_entries_extended_df):
    '''
    Sums up the hours in the Toggl time entries by the calendar week
    :return: DataFrame with CW and the sum of the time entries duration in this week
    '''

    time_entries = copy.deepcopy(time_entries_extended_df)

    time_entries.loc[:, 'week'] = time_entries.start.map(lambda x: datetime.date(datetime.strptime(x, '%Y-%m-%dT%H:%M:%S+00:00')).strftime("%Y-%V"))
    time_entries.loc[:, 'duration_hours'] = time_entries.duration.map(lambda x: x/3600)

    time_entries_sum_per_week_df = time_entries.groupby(['week']).agg("sum")

    return time_entries_sum_per_week_df

'''
Calculates hours worked per calendar week
'''

#calculate worked hours for a certain client
time_entries_sum_only_DI_df = sum_worked_hours_by_week(
    time_entries_extended_df[time_entries_extended_df.client_name == "DI"]
)

worked_hours = time_entries_sum_only_DI_df["duration_hours"].sum()
target_hours = working_days_sum_by_week_df["working_hours"].sum()
over_hours =round((worked_hours - target_hours),1)

#plot diagram with matplotlib
fig, ax = plt.subplots(figsize=(15, 7))
x_target = working_days_sum_by_week_df.index.tolist()
y_target = working_days_sum_by_week_df["working_hours"].tolist()

#ax.bar(range(len(x_target)), y_target, width=0.35, label="Target working hours", color="grey")
ax.bar([item.replace("-","") for item in x_target], y_target, width=0.35, label="Target working hours", color="grey")


for i, client in enumerate(time_entries_extended_df.client_name.unique()):
    time_entries_sum_per_week_df = sum_worked_hours_by_week(
        time_entries_extended_df[time_entries_extended_df.client_name == client]
    )

    x_actual = time_entries_sum_per_week_df.index.tolist()
    y_actual = time_entries_sum_per_week_df["duration_hours"].tolist()

    bar = ax.plot([item.replace("-","") for item in x_actual], y_actual, "-o", label=client)
    #bar = ax.plot(range(len(x_actual)), y_actual, "-o", label=client)

ax.set(xlabel='Calendar week', ylabel='Hours',
       title=f'Working hours (total overhours: {over_hours})')

ax.legend(title="Clients")
plt.xticks(range(len(x_target)), x_target, size='small')
plt.xticks(rotation=45)
# plt.show()
# filename = current date (e.g.
filename = str(date.today()) + ".png"

dir = pathlib.Path(__file__).parent.absolute()
folder = r"/results/"
path = str(dir) + folder + filename
fig.savefig(path, dpi=fig.dpi)

'''
    Send results via email
'''
def send_results_via_mail():
    COMMASPACE = ', '

    g_secret = os.environ['GPW']
    mail1 = os.environ['MAIL1']
    mail2 = os.environ['MAIL2']

    gmail_user = os.environ['MAIL1']
    gmail_password = os.environ['GPW']

    # Create the container (outer) email message.
    msg = MIMEMultipart()
    msg['Subject'] = 'Working Hours Calc'
    msg['From'] = gmail_user
    msg['To'] = COMMASPACE.join([mail1, mail2])
    msg.preamble = 'Working Hours Calc'

    # Open the files in binary mode.  Let the MIMEImage class automatically
    # guess the specific image type.
    fp = open(path, 'rb')
    img = MIMEImage(fp.read())
    fp.close()
    msg.attach(img)

    # Send the email via our own SMTP server
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login(gmail_user, gmail_password)

    server.sendmail(gmail_user, [mail1, mail2], msg.as_string())
    server.quit()

def send_mail_via_aws():
    #send results via mail using AWS SES
    import os
    import boto3
    from botocore.exceptions import ClientError
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.application import MIMEApplication

    # Replace sender@example.com with your "From" address.
    # This address must be verified with Amazon SES.
    #SENDER = "dmnkplzr@googlemail.com"
    SENDER = os.environ['MAIL1']

    # Replace recipient@example.com with a "To" address. If your account
    # is still in the sandbox, this address must be verified.
    # RECIPIENT = "dmnkplzr@googlemail.com"
    RECIPIENT = os.environ['MAIL3']

    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    AWS_REGION = "eu-central-1"

    # The subject line for the email.
    SUBJECT = "Working Hours Calc"

    # The full path to the file that will be attached to the email.
    ATTACHMENT = path

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = "Hello,\r\nPlease see the attached file for a list of customers to contact."

    # The HTML body of the email.
    BODY_HTML = """\
    <html>
    <head></head>
    <body>
    <h1>Hello!</h1>
    <p>Please see the attached file for a list of customers to contact.</p>
    </body>
    </html>
    """

    # The character encoding for the email.
    CHARSET = "utf-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses',region_name=AWS_REGION)

    # Create a multipart/mixed parent container.
    msg = MIMEMultipart('mixed')
    # Add subject, from and to lines.
    msg['Subject'] = SUBJECT
    msg['From'] = SENDER
    msg['To'] = RECIPIENT

    # Create a multipart/alternative child container.
    msg_body = MIMEMultipart('alternative')

    # Encode the text and HTML content and set the character encoding. This step is
    # necessary if you're sending a message with characters outside the ASCII range.
    textpart = MIMEText(BODY_TEXT.encode(CHARSET), 'plain', CHARSET)
    htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)

    # Add the text and HTML parts to the child container.
    msg_body.attach(textpart)
    msg_body.attach(htmlpart)

    # Define the attachment part and encode it using MIMEApplication.
    att = MIMEApplication(open(ATTACHMENT, 'rb').read())

    # Add a header to tell the email client to treat this part as an attachment,
    # and to give the attachment a name.
    att.add_header('Content-Disposition','attachment',filename=os.path.basename(ATTACHMENT))

    # Attach the multipart/alternative child container to the multipart/mixed
    # parent container.
    msg.attach(msg_body)

    # Add the attachment to the parent container.
    msg.attach(att)
    #print(msg)
    try:
        #Provide the contents of the email.
        response = client.send_raw_email(
            Source=SENDER,
            Destinations=[
                RECIPIENT
            ],
            RawMessage={
                'Data':msg.as_string(),
            },
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])

send_mail_via_aws()



