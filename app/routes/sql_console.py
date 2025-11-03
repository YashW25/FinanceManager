from flask import Blueprint, session, redirect, url_for


bp = Blueprint("sql", __name__)


@bp.post("/clear")
def clear_log():
    session.pop("last_sql", None)
    return redirect(url_for("main.index"))
