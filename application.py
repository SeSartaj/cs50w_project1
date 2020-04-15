import os, hashlib, random, requests, json

from flask import Flask, session, redirect, jsonify
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


@app.route("/")
def index():
    # if login, continue
    if session.get("is_login") is None:
        session["is_login"] = False
    if session.get("is_login") is True:
        return render_template("index.html", is_login=session["is_login"])
    return render_template("login.html")


@app.route("/api/<string:isbn>")
def book_api(isbn):
    book = db.execute("select tb_book.title, tb_book.author, tb_book.year, tb_book.isbn, count(tb_review.review_id) as review_count, avg(tb_review.rating) as average_score from tb_book   left join tb_review on tb_book.id = tb_review.book_id where isbn = :isbn group by title, author, year, isbn", {"isbn":isbn}).fetchone()

    if book is None:
        return jsonify({"error" : "Invalid flight_id"}), 422

    if book.average_score is  None:
        book.average_score = 0

    return jsonify({
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "isbn": book.isbn,
        "review_count": book.review_count,
        "average_score": float(book.average_score)
    })




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
    session["user"] =  db.execute("Select * from tb_user where username = :name", {"name":name}).fetchone()
    if session["user"] is None:
        return "User does not exist"
    # make sure password is correct
    if session["user"].password != hash_password:
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
        return render_template("login.html")
    except RuntimeError:
        return "There was a problem, please try again"

@app.route("/book/<string:isbn>", methods=["GET", "POST"])
def book(isbn):

    if request.method == "GET":
        session["book"] = db.execute("select * from tb_book where isbn = :isbn", {"isbn":isbn}).fetchone()

        if session["book"] is None:
            return render_template("error.html", message="The book you are looking is not found")

        reviews = db.execute("select tb_review.rating, tb_review.review_text, tb_user.username from tb_review inner join tb_user on tb_review.user_id = tb_user.id where tb_review.book_id = :book_id", {"book_id":session["book"].id})
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key" : os.getenv("grKey"), "isbns" : isbn})
        if res.status_code != 200:
            return render_template("error.html", text= "API does not work. {}".format(res.status_code))
        res = res.json()
        average_rating = res["books"][0]["average_rating"]
        ratings_count = res["books"][0]["ratings_count"]

        return render_template("book.html", book=session["book"], reviews=reviews, is_login=session["is_login"], average_rating = average_rating, ratings_count=ratings_count)

    elif request.method == "POST":
        session["rating5"] = request.form.get("rating5")
        session["rating_text"] = request.form.get("rating_text")

        if session["is_login"] is False:
            return render_template("error.html", text="In order to make reviews, you must login first.")

        # One review per user
        review_count = db.execute("select count(*) from tb_review where user_id = :user_id and book_id = :book_id", {"user_id":session["user"].id, "book_id":session["book"].id}).fetchone()[0]
        if review_count > 0:
            return render_template("error.html", text = "Sorry, One user cannot submit more than one review. ")
        # try:
        #     db.execute("UPDATE table tb_review set rating = :rating, review_text = :review_text where book_id = :book_id and user_id = :user_id;", {"rating":session["rating5"], "review_text":session["rating_text"], "book_id":session["book"].id, "user_id" = session["user"].id})
        #     return redirect("/bok/{}".format(isbn))
        # except:
        try:
            db.execute("insert into tb_review (book_id, user_id, rating, review_text) values(:book_id, :user_id, :rating, :review_text)", {"book_id":session["book"].id, "user_id":session["user"].id, "rating":session["rating5"], "review_text":session["rating_text"]})
            db.commit()
            return redirect('/book/'+ isbn)
        except RuntimeError:
            return render_template("error.html", text="We couldn't save your review. Try again later");


@app.route("/Logout")
def logout():
    session["is_login"] = False
    return redirect("/login")


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
