import yagmail

mailer=yagmail.SMTP(user="ebongloveis", oauth2_file='creds.json')

recipients=['tabejoel3@gmail.com','jeffyouashi@gmail.com','clintjeff1@gmail.com','jeffyouashi2@gmail.com']
subject="Welcome to the LSS bulk email test2"
contents=["<h1>Wake up to reality...</h1>", "Nothing ever goes as planned in this acursed world"]

for r in recipients:
    mailer.send(to=r, subject=subject, contents=contents)

print("Messages sent sucessfully!!")
#jeffyouashi@gmail.com
#jeffyouashi2@gmail.com
#clintjeff1@gmail.com
#clintjeff2@gmail.com