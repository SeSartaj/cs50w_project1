import os, csv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open('books.csv')
    reader = csv.reader(f) # parse file into list of rows

    for isbn,title,author,year in reader:
        db.execute("INSERT INTO book(isbn,title, author, year) VALUES (:isbn,:title,:author,:year)",{"isbn": isbn, "title":title, "author":author, "year":year})
        print(f"added {isbn}, title: {title}, author: {author}, year: {year} into table flight")
        db.commit()



if __name__ == '__main__':
    main()
