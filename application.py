import os, hashlib, random

from flask import Flask, session
from flask import render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from random import seed
from random import randint

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

# Temporary data
users = {"ahmad":"123"}


@app.route("/")
def index():
    ## if login, continue
    if session.get("is_login") is None:
        session["is_login"] = False
    if session.get("is_login") is True:
        return render_template("index.html", is_login=session["is_login"])
    return render_template("login.html")


@app.route("/login")
def loginpage():
    return render_template("login.html")

@app.route("/Success", methods=["POST", "GET"])
def login():
    if request.method == 'GET':
        return "<h1>Please Fill the Form Instead</h1>"

    name = request.form.get("username")
    password = request.form.get("password")
    hash_object = hashlib.md5(password.encode())
    hash_password = hash_object.hexdigest()

    # Compare Name and Password with Database
    # make sure user exist
    user =  db.execute("Select * from tb_user where username = :name", {"name":name}).fetchone()
    if user is None:
        return "User does not exist"
    # make sure password is correct
    if user.password != hash_password:
        return "password is wrong"
    session["is_login"] = True
    return render_template("index.html", is_login=session["is_login"])


@app.route("/register")
def registerpage():
    return render_template("register.html")

@app.route("/accountCreated", methods=["POST", "GET"])
def register():
    if request.method == 'GET':
        return "Please fill the form instead"

    name = request.form.get("username")
    password = request.form.get("password")
    hash_object = hashlib.md5(password.encode())
    hash_password = hash_object.hexdigest()

    try:
        db.execute("insert into tb_user (username, password) values (:username, :password)", {"username":name, "password":hash_password})
        db.commit()
        session["is_login"] = True
        return render_template("index.html")
    except RuntimeError:
        return "There was a problem, please try again"

@app.route("/book/<string:isbn>", methods=["GET"])
def book(isbn):
    book = db.execute("select * from tb_book where isbn = :isbn", {"isbn":isbn}).fetchone()

    if book is None:
        return render_template("error.html", message="The book you are looking is not found")
    reviews = ["Very nice book", "must read bok", "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.", " Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."]
    return render_template("book.html", book=book, reviews=reviews, is_login=session["is_login"])
@app.route("/book/<string:isbn>", methods=["POST"])
def rating(isbn):
    session["rating5"] = request.form.get("rating5")
    session["rating_text"] = request.form.get("rating_text")

    if session["is_login"] is False:
        return render_template("error.html", text="In order to make reviews, you must login first. Click <a href='{ url_for(\"login\") }}'>here</a> to login")

    db.execute("insert into tb_rating (book_id, user_id, rating, review_text) values ")



@app.route("/Logout")
def logout():
    session["is_login"] = False
    return render_template("login.html")


@app.route("/search", methods=["POST"])
def search():
    seed(1)

    search_query = request.form.get('sq')
    if search_query is None:
        search_query= ""

    # Run search query on database and store result in search_result
    books = db.execute("Select isbn,title, author, year,average_rating from tb_book  where book_tokens @@ plainto_tsquery(:search_query) limit 10", {"search_query": search_query}).fetchall()

    if books is None:
        return render_template("search.html", text="Sorry! No result found. Try something else")


    return render_template("search.html", abcd=search_query,search_result=books, is_login=session["is_login"])
