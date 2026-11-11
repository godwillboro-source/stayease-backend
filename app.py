import os

from flask import Flask, jsonify
from flask_migrate import Migrate

from config import bcrypt, db

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URI", "sqlite:///app.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
app.config["BCRYPT_LOG_ROUNDS"] = int(os.environ.get("BCRYPT_LOG_ROUNDS", 12))
app.json.compact = False

db.init_app(app)
bcrypt.init_app(app)
migrate = Migrate(app, db)



@app.route("/")
def home():
    return jsonify("Welcome to the property rental API")    

if __name__ == "__main__":
    app.run(debug=True)