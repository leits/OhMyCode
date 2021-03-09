from flask import Flask, _app_ctx_stack, jsonify
from sqlalchemy.orm import scoped_session
from db import Repository, init_db_session

app = Flask(__name__)

app.session = scoped_session(init_db_session(), scopefunc=_app_ctx_stack.__ident_func__)


@app.route("/")
def home():
    repo = Repository.get(app.session, "leits", "MeetingBar")
    return jsonify({"name": repo.name, "owner": repo.owner, "stats": repo.stats})


@app.teardown_appcontext
def remove_session(*args, **kwargs):
    app.session.remove()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
