from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import neh
import graph_neh

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads/"
app.secret_key = "hello"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.permanent_session_lifetime = timedelta(minutes=5)

db = SQLAlchemy(app)


class users(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))

    def __init__(self, name, email):
        self.name = name
        self.email = email


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST", "GET"])
def upload():
    return render_template("upload.html")


@app.route("/display", methods=["GET", "POST"])
def save_file():
    row_colors= ['bg-primary', 'bg-warning', 'bg-success', 'bg-danger']
    tasks = []
    tab_print = []
    if request.method == "POST":
        f = request.files["file"]
        filename = secure_filename(f.filename)
        f.save(app.config["UPLOAD_FOLDER"] + filename)
        file = open(app.config["UPLOAD_FOLDER"] + filename, "r")
        display = file.read()
        file.close()

        jobs, machines, o = neh.file(app.config["UPLOAD_FOLDER"] + filename)
        seq, cmax, cmax2 = neh.neh(o, jobs, machines)

        for i in range(1, len(seq), 4):
            tasks.append('Zadanie ' + str(i) + ' - Belki')
            tasks.append('Zadanie ' + str(i + 1) + ' - Stropy')
            tasks.append('Zadanie ' + str(i + 2) + ' - Ściany')
            tasks.append('Zadanie ' + str(i + 3) + ' - Słupy')
        for j in range(0, len(seq)):
            tab_print.extend(row_colors)
        print(tab_print)
        print("NEH:", seq, '\nBest makespan:', cmax2)
        img = "static/" + filename + ".png"
        _3D, _2D, _Validation = graph_neh.graph(cmax2, seq, img)

    return render_template("display.html", display=display, img=img, seq=seq, cmax2=cmax2, o=o, tasks=tasks,
                           tab_print=tab_print, _2D=_2D, _3D=_3D, _Validation=_Validation, filename=filename)


@app.route("/view")
def view():
    return render_template("view.html", values=users.query.all())


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        session.permanent = True
        user = request.form["nm"]
        session["user"] = user
        found_user = users.query.filter_by(name=user).delete()
        # for user in found_user:
        #     user.delete()
        if found_user:
            session["email"] = found_user.email
        else:
            usr = users(user, "")
            db.session.add(usr)
            db.session.commit()
        flash("Login succesful!")
        return redirect(url_for("user"))
    else:
        if "user" in session:
            flash("Name was saved!")
            return redirect(url_for("user"))
        return render_template("login.html")


@app.route("/user", methods=["POST", "GET"])
def user():
    email = None
    if "user" in session:
        user = session["user"]

        if request.method == "POST":
            email = request.form["email"]
            session["email"] = email
            found_user = users.query.filter_by(name=user).first()
            found_user.email = email
            db.session.commit()
            flash("Email was saved!")
        else:
            if "email" in session:
                email = session["email"]
        return render_template("user.html", email=email)
    else:
        flash("You are not logged in!")
        return render_template(url_for("login"))


@app.route("/logout")
def logout():
    if "user" in session:
        user = session["user"]
        flash("You have been logged out!", "info")
    session.pop("user", None)
    session.pop("email", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
