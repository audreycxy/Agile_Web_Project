from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def login():
    return render_template("login.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/administrator")
def administrator():
    return render_template("administrator.html")

@app.route("/guest")
def guest():
    return render_template("guest.html")

if __name__ == "__main__":
    app.run(debug=True)