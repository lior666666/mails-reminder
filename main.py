import imaplib
import email
import pandas
from email.header import decode_header
import smtplib
import datetime as dt
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os



# create an IMAP4 class with SSL
mail = imaplib.IMAP4_SSL("imap.gmail.com")
my_sub = "new massage before your army"
now = dt.datetime.now()
today = now.weekday()
my_email = "beforeyourarmyinfo@gmail.com"
password = os.environ.get("PSM")

# authenticate
mail.login(my_email, password)
mail.select("INBOX")
#exctract all unseen massages.
_, search_data = mail.search(None, 'UNSEEN')
my_message = []

#go through each massage that is unseen
for num in search_data[0].split():
        email_data = {}
        _, data = mail.fetch(num, '(RFC822)')
        _, b = data[0]
        email_message = email.message_from_bytes(b)
        for header in ['subject']:
            email_data[header] = email_message[header]
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True)
                email_data['body'] = body.decode()
        my_message.append(email_data)
        
# sort only the relevant massages by the subject
relevant_massage = [massage['body'].strip().replace('Email:', '').replace('Date:', '').split() for massage in my_message if massage['subject'] == my_sub]
new_data = pandas.DataFrame(relevant_massage)

#creating the file first time
if not os.path.isfile("file.csv"):
   if len(relevant_massage)!=0:
        new_data.to_csv("file.csv", header=["Email","Date"])
else: # else it exists so append without writing the header
   new_data.to_csv("file.csv", mode='a', header=False)
   
# send the massages to relevant emails on relevant dates
if os.path.isfile("file.csv"):
    new_data = pandas.read_csv("file.csv")
    now = dt.datetime.now()
    year = now.year
    month = now.month
    day = now.day
    new_dates_list = new_data['Date'].to_list()
    for dates in new_dates_list:
        splited_date = dates.split('-')
        # format in month is diferent 08 against 8, so converting to int
        int_splited_date = [int(date_atribute) for date_atribute in splited_date]
        if day-1 in int_splited_date and month in int_splited_date and year in int_splited_date:
            # extract all emails corresponding with the date
            send_to_list = new_data[new_data['Date'] == dates]
            send_to_list = send_to_list['Email'].to_list()
            with smtplib.SMTP("smtp.gmail.com") as connection:
                connection.starttls()
                connection.login(user=my_email, password=password)
                for send_to in send_to_list:
                    msg = MIMEMultipart()
                    msg['From'] = my_email
                    msg['Subject'] = "תזכורת: איך היו המיונים שלך אתמול?"
                    html = """\
                    <html>
                      <head></head>
                      <body>
                        <p dir="rtl">היי, זה ליאור מהאתר לפני צבא.<br> </p>
                        <p dir="rtl">אני שולח את ההודעה הזאת כי נרשמת דרך האתר שלי במטרה לעזור ולשתף את החוויה שהייתה לך במיון הצבאי שעשית.<br> </p>
                        <p dir ="rtl">אז אעריך מאוד אם תוכל/י לשתף אותי במיון שעשית, בחוויה הכללית שלך, בסוגי השאלות ובכל דבר אחר שתרצה/י. זה יעזור מאוד להשאיר את האתר מעודכן ויעזור לקוראים בעתיד כמו שהאתר עזר לך.<br> </p>
                        <p dir="rtl">תודה והמשך יום מעולה,<br> </p>
                        <p dir="rtl">ליאור<br> </p>
                      </body>
                    </html>
                    """
                    msg.attach(MIMEText(html, 'html'))
                    msg['To'] = send_to
                    connection.send_message(msg)
                    
            #remove unnecessary data from file.csv of those who already received a mail
            index_list_delete = new_data.index[new_data['Date'] == dates]
            header = ["Email","Date"]
            new_data.drop(index_list_delete, axis=0, inplace=True)
            new_data.drop("Unnamed: 0",axis=1, inplace=True)
            if new_data.empty:
                os.remove("file.csv")
            else:
               new_data.to_csv("file.csv", mode='w', header=header)
            break
