from app import create_app
# specifies application host as (domain, port)
#__HOST__ = ("217.78.162.125", 80)
__HOST__ = ("127.0.0.1", 80)

app = create_app(host=__HOST__)

if __name__ == "__main__":
    app.run(debug=True, host=__HOST__[0], port=__HOST__[1])