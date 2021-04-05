import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import pandas as pd
import mysql.connector
import config
import pprint

'''
The following code retrieves the source code from https://www.ferienwiki.de/feiertage/de/bayern and
saves the german (bavarian) public holidays in database.
:return:public_holidays_df: (data frame with a entry for each public holiday
                            in bavaria)
'''

url = 'https://www.ferienwiki.de/feiertage/de/bayern'
response = requests.get(url)

soup = BeautifulSoup(response.text, 'html.parser')
td = soup.findAll('td')

public_holidays = []

for line in td:
    try:
        match = re.search(r'\d{2}.\d{2}.\d{4}', str(line))
        date = datetime.strptime(match.group(), '%d.%m.%Y').date()
        public_holidays.append(date)
    except:
        pass

public_holidays_df = pd.DataFrame(data=public_holidays)
public_holidays_df = public_holidays_df.rename(columns={0: "date"})

'''Connects to mysql database'''

# cnx = mysql.connector.connect(password=config.mysql["user"],
#                               database=config.mysql["database"],
#                               user=config.mysql["user"],
#                               port=config.mysql["port"],
#                               host=config.mysql["host"])

cnx = mysql.connector.connect(
            host="dashboardserver.germanywestcentral.cloudapp.azure.com",
            user=config.mysql["user"],
            password=config.mysql["password"],
            port=config.mysql["port"],
)

cursor = cnx.cursor()

'''Save the public holidays in table in database'''

return_messages=[]
try:
    cursor.execute("CREATE TABLE `calc_working_hours`.`public_holidays` ("
                   "`id` INT NOT NULL,"
                   "`date` DATETIME NULL,"
                   "PRIMARY KEY (`id`));")
    cnx.commit()

except mysql.connector.Error as e:
    return_messages.append("Error code:" + str(e.errno))
    return_messages.append("SQLSTATE value:" + str(e.sqlstate))
    return_messages.append("Error message:" + str(e.msg))
    return_messages.append("Error:" + str(e))

    #if there is a error when creating the table because there is an existing, drop it first
    try:
        cursor.execute("DROP TABLE `calc_working_hours`.`public_holidays`")
        return_messages.append("Current table public_holidays was deleted successfully")
    except:
        return_messages.append("Error while deleting table public_holidays")

    try:
        cursor.execute("CREATE TABLE `calc_working_hours`.`public_holidays` ("
                       "`id` INT NOT NULL,"
                       "`date` DATETIME NULL,"
                       "PRIMARY KEY (`id`));")
        cnx.commit()
        return_messages.append("Table public_holidays was created successfully")
    except:
        return_messages.append("Error while creating table public_holidays")

# Create a new record
sql =   '''
        INSERT INTO `calc_working_hours`.`public_holidays` (`id`, `date`) 
        VALUES (%s, %s)
        '''

for index, line in public_holidays_df.iterrows():
    try:
        cursor.execute(sql, (index,
                             line['date']
                             ))
        cnx.commit()
    except mysql.connector.Error as e:
        return_messages.append("Fail during ADDING ROWS to table public_holidays")
        return_messages.append("Error code:" + str(e.errno))
        return_messages.append("SQLSTATE value:" + str(e.sqlstate))
        return_messages.append("Error message:" + str(e.msg))
        return_messages.append("Error:" + str(e))

pp = pprint.PrettyPrinter(depth=6)
pp.pprint(return_messages)

