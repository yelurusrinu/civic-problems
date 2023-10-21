from flask import Flask
from pymongo import MongoClient
from gridfs import GridFS
import os

app = Flask(__name__)
app.secret_key = "Varun"


cluster = MongoClient("mongodb://localhost:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false")
db = cluster["BetterIndia"]
users = db["Users"]
issues = db["Issues"]

grid_fs = GridFS(db)


from Application import routes