import os

from flask import Flask, session
from flask import render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

users = {"ahmad":"123"}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login")
def loginpage():
    return render_template("login.html")

@app.route("/Success")
def login():
    return "Logined successfully"


@app.route("/register")
def registerpage():
    return render_template("register.html")

@app.route("/Success")
def register():
    return "Registered Successfully"


@app.route("/search")
def search():
    name = ["Book One", "Book Two", "Book Three"]
    return render_template("search.html", search_result=name)
