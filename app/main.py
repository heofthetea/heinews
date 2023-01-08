from app import create_app, get_host
# specifies application host as (domain, port)
#__HOST__ = ("217.78.162.125", 80)

__HOST__ = get_host()

app = create_app(host=__HOST__)

if __name__ == "__main__":
    app.run(debug=True, host=__HOST__[0], port=__HOST__[1])