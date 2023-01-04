"""
# uncomment this to run on your own machine 
from os import getcwd, chdir
print(getcwd())

#set this path to the directory `main.py` is in
chdir("C:\\Coding Stuff\\GAP\\hhg-news\\heiNEws\\app")
"""
from app import create_app
# specifies application host as (domain, port)
__HOST__ = ("127.0.0.1", 5000)

app = create_app(host=__HOST__)

if __name__ == "__main__":
    app.run(debug=True, host=__HOST__[0], port=__HOST__[1])