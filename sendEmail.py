import yagmail

def sendEmail(email):
    mailer=yagmail.SMTP(user="ebongloveis", oauth2_file= "client.json")

    recipients=[email,'jeffyouashi@gmail.com','clintjeff1@gmail.com','jeffyouashi2@gmail.com']
    subject="Meeting with Competent Property Group Ltd"
    contents=["<h1>You have been invited to a meeting with Competent Property Group Ltd</h1>"]

    for r in recipients:
        mailer.send(to=r, subject=subject, contents=contents)

    print("Messages sent sucessfully!!")
#jeffyouashi@gmail.com
#jeffyouashi2@gmail.com
#clintjeff1@gmail.com
#clintjeff2@gmail.com