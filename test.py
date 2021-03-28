import os
import smtplib
import matplotlib.pyplot as plt

g_secret = os.environ['G-PW']
mail1 = os.environ['MAIL1']
mail2 = os.environ['MAIL2']

gmail_user = mail1
gmail_password = g_secret

sent_from = gmail_user
to = [mail1, mail2]
subject = 'Subject'
body = 'test'

email_text = """\
From: %s
To: %s
Subject: %s

%s
""" % (sent_from, ", ".join(to), subject, body)

try:
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login(gmail_user, gmail_password)
    server.sendmail(sent_from, to, email_text)
    server.close()

    print('Email sent!')
except:
    print('Something went wrong...')


fig = plt.figure(1)
ax = fig.add_subplot(111)

# Need to do this so we don't have to worry about how many lines we have -
# matplotlib doesn't like one x and multiple ys, so just repeat the x
lines = []

x = [1,2,3]
y = [1,2,3]
ax.plot(x,y)

fig.savefig(r"./results/filename.png")