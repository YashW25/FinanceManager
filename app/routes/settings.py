import os
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from ..extensions import db


bp = Blueprint("settings", __name__)


def _current_info():
    engine = db.engine
    url = engine.url
    dialect = engine.dialect.name  # 'sqlite', 'mysql', etc.
    driver = engine.dialect.driver  # 'pymysql', 'pysqlite', etc.

    info = {
        "dialect": dialect,
        "driver": driver,
        "uri": str(url).replace(url.password or "", "***") if getattr(url, "password", None) else str(url),
    }

    if dialect == "sqlite":
        db_path = url.database or ""
        exists = os.path.exists(db_path) if db_path else False
        size = os.path.getsize(db_path) if exists else None
        info.update({
            "sqlite_path": db_path,
            "sqlite_exists": exists,
            "sqlite_size": size,
        })
    else:
        # For MySQL and others, show safe parts only
        info.update({
            "host": getattr(url, "host", None),
            "port": getattr(url, "port", None),
            "database": getattr(url, "database", None),
            "username": getattr(url, "username", None),
        })

    return info


def _env_path():
    # Project root .env
    import os
    here = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.join(here, ".env")


def _load_env_lines():
    path = _env_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().splitlines()
    except FileNotFoundError:
        return []


def _save_env_vars(updates: dict, remove_keys: list):
    lines = _load_env_lines()
    out = []
    seen = set()
    remove = set(remove_keys)
    for line in lines:
        m = re.match(r"^([A-Z0-9_]+)=(.*)$", line)
        if not m:
            out.append(line)
            continue
        key = m.group(1)
        if key in remove:
            continue
        if key in updates and key not in seen:
            val = updates[key]
            out.append(f"{key}={val}")
            seen.add(key)
        elif key not in updates:
            out.append(line)
    # Append new keys not present
    for k, v in updates.items():
        if k not in seen and all(not l.startswith(k + "=") for l in out):
            out.append(f"{k}={v}")
    with open(_env_path(), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + ("\n" if out and not out[-1].endswith("\n") else ""))


@bp.route("/", methods=["GET", "POST"])
def view_settings():
    info = _current_info()
    import os
    default_sqlite_path = os.path.join(current_app.instance_path, "ministore.sqlite3")
    if request.method == "POST":
        db_choice = request.form.get("db_choice", "sqlite")
        action = request.form.get("action", "save")
        if db_choice == "sqlite":
            sqlite_path = request.form.get("sqlite_path", "").strip()
            if not sqlite_path:
                flash("Please provide a valid SQLite path.")
                return render_template("settings.html", info=info, active=db_choice, default_sqlite_path=default_sqlite_path)
            if action == "test":
                # Test SQLite by ensuring directory exists and touching file
                try:
                    os.makedirs(os.path.dirname(sqlite_path) or ".", exist_ok=True)
                    # Attempt to connect
                    from sqlalchemy import create_engine, text
                    engine = create_engine(f"sqlite:///{sqlite_path}")
                    with engine.connect() as conn:
                        conn.execute(text("select 1"))
                    flash("SQLite connection OK.")
                except Exception as e:
                    flash(f"SQLite connection failed: {e}")
                return render_template("settings.html", info=info, active=db_choice, default_sqlite_path=default_sqlite_path)
            # Save: clear DATABASE_URL; set DB_DIALECT & SQLITE_PATH
            updates = {"DB_DIALECT": "sqlite", "SQLITE_PATH": sqlite_path}
            remove = ["DATABASE_URL", "MYSQL_HOST", "MYSQL_PORT", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DB"]
            _save_env_vars(updates, remove)
            flash("Saved SQLite settings to .env. Restart server to apply.")
            return redirect(url_for("settings.view_settings"))
        else:
            host = request.form.get("mysql_host", "127.0.0.1").strip()
            port = request.form.get("mysql_port", "3306").strip()
            user = request.form.get("mysql_user", "root").strip()
            password = request.form.get("mysql_password", "").strip()
            dbname = request.form.get("mysql_db", "ministore").strip()
            # Build DATABASE_URL and save
            from urllib.parse import quote_plus
            pwd = quote_plus(password)
            database_url = f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{dbname}?charset=utf8mb4"
            if action == "test":
                try:
                    from sqlalchemy import create_engine, text
                    engine = create_engine(database_url)
                    with engine.connect() as conn:
                        conn.execute(text("select 1"))
                    flash("MySQL connection OK.")
                except Exception as e:
                    flash(f"MySQL connection failed: {e}")
                return render_template("settings.html", info=info, active=db_choice, default_sqlite_path=default_sqlite_path)
            updates = {"DATABASE_URL": database_url}
            remove = ["DB_DIALECT", "SQLITE_PATH"]
            _save_env_vars(updates, remove)
            flash("Saved MySQL settings to .env. Restart server to apply.")
            return redirect(url_for("settings.view_settings"))
    return render_template("settings.html", info=info, default_sqlite_path=default_sqlite_path)
