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

#### Certain things have to be present in order to suit production:
- in `__init__.py`, there's a global variable called `__HOST__`. This variable nees to be hard-coded to the current url of the website. 
- in the working directory `heinews/app` and the parent directory `heinews` there has to be a file called `__machine__.txt`. It contains the information where the code is run on the first line:
> set to `development` if in development
> set to `production` if on the server
I'm really sorry for that, but that was the best way to sort that out, because the location of the static folder and working directory is different depending on where it's run.
Due to that, you have to explicitly state your working directory: in `__init__.py` there's an if statement `if not __IN_PRODUCTION__` - here, set the `chdir` parameter to the file, main.py is located in.

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

## A short overview of what is to be found where
### Usage of libraries
I built the website mostly on the knowledge of this youtube tutorial: https://www.youtube.com/watch?v=dam0GPOAvVI&list=PL_AOVnPxyW8_Y88ZFeTvB3jajvaR0ICAC&index=4 
After watching this, more or less everything done in this code should make sense. nevertheless, here a quick overview of each module and what it does:

### /app
This is supposed to be the working directory. The only python file here should be `main.py`, which really only serves the purpose of starting the application. In production, this is also where the 
used static folder is located.

##### /app/static (or /app/app/static if in development)
This is where all _static_ files are located - i.e. files that are used by the application, but aren't supposed to change during its lifespan. File structure:
> `/css` self explanatory - holds every css file needed, including bootstrap
> `/img` images used all over the application, like logo, placeholder etc
> `/img/articles` for each article created, there is a corresponding folder (identified by the article's id), where the images the article uses are stored 
> `/temp` this is the only exception to the "not changed" rule. Here, the temporary .csv files used by the caching algorithm are stored (and deleted once deprecated)

### /app/app
This is the actual home of the application. Every python file located here will contain url endpoints, which - to put it blandly - do certain stuff: Either serve a template (= html file) or
serve POST requests. Here's a list for each file and its most important functionalities (check function comments (_if_ there are any xd) for more info):

##### `__init__.py`
> Configures the application and contains configuration information used by other files (e.g. the aforementioned `__HOST__` tuple)
> `create_app()`: Configures the application; is run as an import in `main.py`. Sets up every module as a flask "Blueprint" and creates the database.
> "injects" functionalities via `app.context_processor()`s - these are functions which can be used globally in each template and are recognized by jinja.

##### `admin.py`
> url prefix: "/admin"
> contains every functionality for users with advanced access rights - i.e. `upload`  and `validate` roles.
> actually: mostly contains upload procedure (starting with `upload_article()`)

##### `articles.py`
> contains everything needed for article loading and interaction (e.g. upvoting)
> also serves `tag` and `announcement` requests because I for some reason thought it was unnecessary to start a new file for that

##### `auth.py`
> contains everything necessary for authorization purposes (e.g. serves "login" and "signup" pages)
> also contains every functionalities necessary to allow users to change their accout settings (like `send_reset_mail()` to send a link to reset a users password)

##### `dev.py`
> serves, well - the dev panel.
> In trying to secure that panel by password I wrote which is probably the worst code of the entire website: 
>   have function `authorize_to_do_stuff()` receive the request, *redirect* to a password prompt and then to the actual `do_stuff()` function. I'm sorry.

##### `models.py`
> this file is just a bunch of classes represinting tables in the database (which are being used all over the application)
> for ERM (without attributes) see `heinews_erm.pdf`
> furthermore contains some functions, which help "ease" the usage of these classes

##### `surveys.py`
> contains everything needed to load and interact with surveys (i.e. vote, see results etc)
> however, upload process is still handled in `admin.py`

##### `views.py`
> a functionality quite simply ends up in this file if it does not fit in any of the other ones. More specifically:
> - `index.html`/landing page
> - the user's profile
> - the search function
> - error pages

##### (`heinews.db`)
> this is the database. Don't know why it ended up here instead of the working directory, but who cares (:shrug:)

### app/app/_lib
Stores all python files not directly serving the Flask application, but rather are used to do certain tasks:
- `cache.py` contains everything needed for caching during article upload process
- `docx_to_html.py` contains everything involved in converting a word document to the corresponding html
- `mail_contents.py` used more or less to get these clunky multiline-strings containing message contents to be sent per mail out of the main code
- `send_mail.py` sends, well, a mail using smtp servers

### app/app/templates
Here, all so-called "templates" are stored - Basically html files with some extra syntax which is used by the `jinja` templating language.
> - Navbar and Footer are defined in `base.html` (which is extended by every other template)
>    - exception: There's a second exact copy of the `<footer>` in `index.html` - For some reason there the base.html-footer did not work there
> - `/articles` everytime a new article is uploaded, its corresponding html file is stored here under the name of the article's randomly generated id (by which it is also identified in the database)
> - `/auth` every file connected to a user - including authorization and the profile
> - `/overview` stores the files rendered when viewing e.g. "all tags" on the website
> - `/survey` stores the files needed for surveys
> - `/upload` stores the files needed for article uploading


	
