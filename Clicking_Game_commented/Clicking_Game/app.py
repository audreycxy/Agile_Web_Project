from flask import Flask, render_template, request, redirect, url_for, session

# Create the Flask app object.
app = Flask(__name__)

# Secret key is required for using session data.
# In a real project, do not hardcode this in source code.
app.secret_key = "secret123"

# Temporary in-memory users for testing.
# These users disappear when the Flask app restarts.
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


# Show the login page when the user visits the home route.
@app.route("/")
def login():
    return render_template("login.html")


# Handle login form submission.
@app.route("/login", methods=["POST"])
def handle_login():
    # Get the submitted email and password from the form.
    email = request.form.get("email")
    password = request.form.get("password")

    # Check whether the email exists and the password matches.
    if email in users and users[email]["password"] == password:
        # Store basic user information in the session after successful login.
        session["email"] = email
        session["name"] = users[email]["name"]
        session["role"] = users[email]["role"]

        # Redirect user based on their role.
        if users[email]["role"] == "admin":
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for("player_dashboard"))

    # Show an error if login details are invalid.
    return render_template("login.html", error="Invalid email or password.")


# Show the signup page.
@app.route("/signup")
def signup():
    return render_template("signup.html")


# Handle signup form submission.
@app.route("/signup", methods=["POST"])
def handle_signup():
    # Read form data.
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")

    # Check that no field is empty.
    if not username or not email or not password or not confirm_password:
        return render_template("signup.html", error="Please fill in all fields.")

    # Check that both password fields match.
    if password != confirm_password:
        return render_template("signup.html", error="Passwords do not match.")

    # Prevent duplicate accounts with the same email.
    if email in users:
        return render_template("signup.html", error="Account already exists.")

    # Add the new user to the temporary users dictionary.
    # New users are given the default role of player.
    users[email] = {
        "name": username,
        "password": password,
        "role": "player"
    }

    # Redirect back to login page after successful signup.
    return redirect(url_for("login"))


# Guest route.
# Right now this tries to open guest.html, so that template must exist.
@app.route("/guest")
def guest():
    return render_template("guest.html")


# Admin dashboard route.
# Only logged-in users with role = admin can access this page.
@app.route("/admin_dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    return render_template("admin_dashboard.html", name=session.get("name"))


# Player dashboard route.
# Only logged-in users with role = player can access this page.
@app.route("/player_dashboard")
def player_dashboard():
    if session.get("role") != "player":
        return redirect(url_for("login"))
    return render_template("player_dashboard.html", name=session.get("name"))


# Guest dashboard route.
# Only logged-in users with role = guest can access this page.
@app.route("/guest_dashboard")
def guest_dashboard():
    if session.get("role") != "guest":
        return redirect(url_for("login"))
    return render_template("guest_dashboard.html", name=session.get("name"))


# Clear session data and send the user back to login page.
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# Run the app in debug mode when this file is executed directly.
if __name__ == "__main__":
    app.run(debug=True)
