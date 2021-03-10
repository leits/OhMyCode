from flask import Flask, _app_ctx_stack, jsonify
from sqlalchemy.orm import scoped_session

from db import Repository, init_db_session
from constants import PORT

app = Flask(__name__)

app.session = scoped_session(init_db_session(), scopefunc=_app_ctx_stack.__ident_func__)


@app.route("/")
def home():
    repo = Repository.get(app.session, "leits", "MeetingBar")
    if repo:
        return jsonify({"name": repo.name, "owner": repo.owner, "stats": repo.stats})
    else:
        return "Oh no"


@app.teardown_appcontext
def remove_session(*args, **kwargs):
    app.session.remove()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
