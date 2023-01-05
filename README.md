# Online blog for the student newspaper at the HHG Ostfildern
## developed by Emil Schläger, Emil Grümer, Finn Österreicher
#### Using flask 2.0: https://flask.palletsprojects.com/en/2.0.x/

* * *
Now the thing is actually on the server. To understand and remember how tf I actually did that:
#### i. make sure file system and certain files are setup correctly:
everything is located in /var/www/heinews (this is also where the git repo is setup in)
```
heinews
    - everything docker needs
    |_ app
        - uwsgi.ini
        - main.py
        |_ app
            - the actual application (templates and python files)
        |_ static
```

#### Certain code has to be changed in order to suit production:
This includes:
> - `main.py`: For development, the working directory needs to be explicitly stated in order for it to work. This code needs to be removed on the server. Furthermore, the `__HOST__` tuple needs to represent the correct ip or domain.
> - `_lib/send_mail.py`: For development purposes, mails should not actually be sent - rather, their content is printed out. This is achieved via a print statement and an early return in `send_mail()`, which again should be removed for production.

#### ii. build docker image 
`sudo docker build -t heinews .`

#### iii. run docker container
`sudo docker run -d -it -p 80:80 -v $"(pwd)"/app:/app --name heinews heinews:latest`

#### (iv) after any change has been made, restart the container
`sudo docker restart heinews`

* * *
Before running locally for the first time, do the following steps: <br>
##### I. activate virtual environment with the following terminal commands (for windows):<br>
>1.`pip install virtualenv`<br>
>2.`virtualenv venv`<br>
>3.`cd venv/Scripts`<br>
>4.`activate.bat`<br>
>(5.`cd ../../` to get back to original location)<br>

##### II. run `pip install -r requirements.txt` to install required modules<br>

Once these steps have been executed, continue by executing main.py.

* * *
## Here I'll write a little about how this thing actually works. Maybe. At some point.
	
