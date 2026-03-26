from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "secret123"  # needed for session

# Temporary sample users
users = {
    "admin@example.com": {
        "name": "Admin User",
        "password": "admin123",
        "role": "admin"
    },
    "player@example.com": {
        "name": "Player User",
        "password": "player123",
        "role": "player"
    }
}


@app.route("/")
def login():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def handle_login():
    email = request.form.get("email")
    password = request.form.get("password")

    if email in users and users[email]["password"] == password:
        session["email"] = email
        session["name"] = users[email]["name"]
        session["role"] = users[email]["role"]

        if users[email]["role"] == "admin":
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for("player_dashboard"))

    return render_template("login.html", error="Invalid email or password.")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/signup", methods=["POST"])
def handle_signup():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")

    if not username or not email or not password or not confirm_password:
        return render_template("signup.html", error="Please fill in all fields.")

    if password != confirm_password:
        return render_template("signup.html", error="Passwords do not match.")

    if email in users:
        return render_template("signup.html", error="Account already exists.")

    users[email] = {
        "name": username,
        "password": password,
        "role": "player"
    }

    return redirect(url_for("login"))

@app.route("/guest")
def guest():
    return render_template("guest.html")

@app.route("/admin_dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    return render_template("admin_dashboard.html", name=session.get("name"))

@app.route("/player_dashboard")
def player_dashboard():
    if session.get("role") != "player":
        return redirect(url_for("login"))
    return render_template("player_dashboard.html", name=session.get("name"))

@app.route("/guest_dashboard")
def guest_dashboard():
    if session.get("role") != "guest":
        return redirect(url_for("login"))
    return render_template("guest_dashboard.html", name=session.get("name"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)