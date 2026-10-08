"""Range Drill — a Flask app for practising multiple-choice theory tests."""
import os
import random
from datetime import datetime, timedelta, timezone

from flask import (Flask, abort, flash, jsonify, redirect, render_template,
                   request, send_file, url_for)
from flask_login import (LoginManager, UserMixin, current_user, login_required,
                         login_user, logout_user)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash

from i18n import (LANGUAGES, count_questions, get_lang, js_strings, t, tp)
from quiz_parser import ParseError, build_template, content_hash, parse_workbook

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)


def _database_url():
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        return "sqlite:///" + os.path.join(INSTANCE_DIR, "range_drill.db")
    # Always use the psycopg 3 driver explicitly (works with SQLAlchemy 2.0 and 2.1).
    # Providers hand out "postgres://" or "postgresql://" URLs.
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            url = "postgresql+psycopg://" + url[len(prefix):]
            break
    return url


def _engine_options():
    options = {"pool_pre_ping": True, "pool_recycle": 280}
    if _database_url().startswith("postgresql+psycopg://"):
        # Connection poolers (Neon "-pooler" hosts, PgBouncer) can break server-side
        # prepared statements; plain queries are fast enough for this app.
        options["connect_args"] = {"prepare_threshold": None}
    return options


def _local_secret_key():
    """Random secret key kept in instance/secret_key, so logins survive restarts on a local server."""
    path = os.path.join(INSTANCE_DIR, "secret_key")
    try:
        with open(path, encoding="utf-8") as f:
            key = f.read().strip()
            if key:
                return key
    except FileNotFoundError:
        pass
    import secrets
    key = secrets.token_hex(32)
    with open(path, "w", encoding="utf-8") as f:
        f.write(key)
    return key


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

secure_cookies = os.environ.get("SECURE_COOKIES", "0") == "1"
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY") or _local_secret_key(),
    SQLALCHEMY_DATABASE_URI=_database_url(),
    # pre_ping + recycle: survive Neon/Postgres closing idle connections while it sleeps
    SQLALCHEMY_ENGINE_OPTIONS=_engine_options(),
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,  # 5 MB upload limit
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=secure_cookies,
    REMEMBER_COOKIE_SECURE=secure_cookies,
    WTF_CSRF_TIME_LIMIT=None,
)

APP_NAME = os.environ.get("APP_NAME", "Range Drill")
REGISTRATION_CODE = os.environ.get("REGISTRATION_CODE", "").strip()
EASY_PASS_RATIO = float(os.environ.get("EASY_PASS_RATIO", "0.8"))
MAX_BANKS = int(os.environ.get("MAX_BANKS", "5"))                 # question banks per user
INACTIVITY_DAYS = int(os.environ.get("INACTIVITY_DAYS", "30"))    # then banks + history are deleted
ACTIVITY_WRITE_EVERY = timedelta(minutes=10)                      # throttle last_active_at updates
CLEANUP_EVERY = timedelta(hours=6)                                # how often the global purge runs

db = SQLAlchemy(app)

if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
    from sqlalchemy import event

    with app.app_context():
        @event.listens_for(db.engine, "connect")
        def _sqlite_pragmas(dbapi_conn, _record):
            # WAL + busy timeout: several people can take tests at once without "database is locked"
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA busy_timeout=5000")
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "flash.login_required"
login_manager.login_message_category = "info"
login_manager.localize_callback = t  # translate the key at request time

# allowed = how many mistakes the shooter may make; None means unlimited.
# Display names/descriptions live in i18n.py under "mode.<key>" and "mode.<key>.desc".
MODES = {
    "easy": {"allowed": None, "rank": 1},
    "medium": {"allowed": 5, "rank": 2},
    "hard": {"allowed": 2, "rank": 3},
    "impossible": {"allowed": 0, "rank": 4},
}


def utcnow():
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    last_active_at = db.Column(db.DateTime(timezone=True), default=utcnow, index=True)

    quizzes = db.relationship("Quiz", backref="owner", cascade="all, delete-orphan")


class Quiz(db.Model):
    __table_args__ = (db.Index("ix_quiz_user_hash", "user_id", "file_hash"),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    filename = db.Column(db.String(255))
    file_hash = db.Column(db.String(64))  # content fingerprint, see quiz_parser.content_hash
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    questions = db.relationship("Question", backref="quiz", cascade="all, delete-orphan",
                                order_by="Question.position")
    attempts = db.relationship("Attempt", backref="quiz", cascade="all, delete-orphan")


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False, index=True)
    position = db.Column(db.Integer, nullable=False)
    external_id = db.Column(db.String(64))
    text = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=False)   # list of 3 strings (may contain "")
    correct = db.Column(db.Integer, nullable=False)  # 0-based index into options


class Attempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False, index=True)
    mode = db.Column(db.String(20), nullable=False)
    order = db.Column(db.JSON, nullable=False)          # list of question ids
    option_orders = db.Column(db.JSON, default=dict)    # {question_id: [option indices]}
    position = db.Column(db.Integer, default=0, nullable=False)
    errors = db.Column(db.Integer, default=0, nullable=False)
    correct_count = db.Column(db.Integer, default=0, nullable=False)
    status = db.Column(db.String(20), default="active", nullable=False)  # active/passed/failed/abandoned
    started_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    finished_at = db.Column(db.DateTime(timezone=True))

    answers = db.relationship("AttemptAnswer", backref="attempt", cascade="all, delete-orphan")

    @property
    def mode_info(self):
        return MODES[self.mode]

    @property
    def total(self):
        return len(self.order)


class AttemptAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("attempt.id"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id", ondelete="CASCADE"), nullable=False)
    chosen = db.Column(db.Integer, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)


def _upgrade_schema():
    """Add columns introduced after the first release to an existing database (SQLite or Postgres).

    db.create_all() only creates missing tables, it never alters existing ones.
    """
    from sqlalchemy import inspect, text

    engine = db.engine
    prep = engine.dialect.identifier_preparer
    inspector = inspect(engine)
    with engine.begin() as conn:
        for model, column in ((User, "last_active_at"), (Quiz, "file_hash")):
            table = model.__table__
            existing = {c["name"] for c in inspector.get_columns(table.name)}
            if column not in existing:
                col = table.c[column]
                conn.execute(text(f"ALTER TABLE {prep.format_table(table)} ADD COLUMN "
                                  f"{prep.format_column(col)} {col.type.compile(dialect=engine.dialect)}"))
                app.logger.info("Schema upgrade: added %s.%s", table.name, column)
    for index in list(User.__table__.indexes) + list(Quiz.__table__.indexes):
        index.create(bind=engine, checkfirst=True)

    # Backfill: existing users count as active now, existing banks get their fingerprint
    User.query.filter(User.last_active_at.is_(None)).update({User.last_active_at: utcnow()},
                                                            synchronize_session=False)
    for quiz in Quiz.query.filter(Quiz.file_hash.is_(None)).all():
        quiz.file_hash = content_hash([{"text": q.text, "options": q.options, "correct": q.correct}
                                       for q in quiz.questions])
    db.session.commit()


with app.app_context():
    db.create_all()
    _upgrade_schema()

if os.environ.get("RENDER") and not os.environ.get("DATABASE_URL"):
    # Render's free disk is wiped on every deploy/restart, so SQLite would lose all accounts
    app.logger.warning("DATABASE_URL is not set: using temporary SQLite. Data WILL be lost on restart. "
                       "Set DATABASE_URL to a Postgres connection string (e.g. Neon).")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.context_processor
def inject_globals():
    return {"APP_NAME": APP_NAME, "MODES": MODES, "LANGUAGES": LANGUAGES, "lang": get_lang(),
            "t": t, "tp": tp, "count_questions": count_questions}


@app.route("/lang/<code>")
def set_language(code):
    """Switch UI language and return to the page the user came from."""
    target = request.referrer or url_for("index")
    # Only redirect back to our own host
    if not target.startswith(request.host_url):
        target = url_for("index")
    resp = redirect(target)
    if code in LANGUAGES:
        resp.set_cookie("lang", code, max_age=60 * 60 * 24 * 365, samesite="Lax",
                        secure=secure_cookies, httponly=True)
    return resp


def owned_or_404(model, obj_id):
    obj = db.session.get(model, obj_id)
    if obj is None or obj.user_id != current_user.id:
        abort(404)
    return obj


# --------------------------------------------------------------------------- #
# Retention: delete banks + history of inactive users (accounts are kept)
# --------------------------------------------------------------------------- #
def as_utc(value):
    """SQLite returns naive datetimes; treat them as UTC so comparisons work everywhere."""
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def purge_user_data(user_ids):
    """Delete all question banks, questions, attempts and answers of the given users."""
    user_ids = list(user_ids)
    if not user_ids:
        return 0
    attempt_ids = db.select(Attempt.id).where(Attempt.user_id.in_(user_ids))
    quiz_ids = db.select(Quiz.id).where(Quiz.user_id.in_(user_ids))
    # Children first, so foreign keys are satisfied on every database
    AttemptAnswer.query.filter(AttemptAnswer.attempt_id.in_(attempt_ids)).delete(synchronize_session=False)
    Attempt.query.filter(Attempt.user_id.in_(user_ids)).delete(synchronize_session=False)
    Question.query.filter(Question.quiz_id.in_(quiz_ids)).delete(synchronize_session=False)
    removed = Quiz.query.filter(Quiz.user_id.in_(user_ids)).delete(synchronize_session=False)
    db.session.commit()
    return removed


def purge_inactive_users():
    """Remove data of every user inactive for INACTIVITY_DAYS who still has something stored."""
    cutoff = utcnow() - timedelta(days=INACTIVITY_DAYS)
    stale = db.select(User.id).where(User.last_active_at < cutoff)
    owners = {uid for (uid,) in db.session.query(Quiz.user_id).filter(Quiz.user_id.in_(stale)).distinct()}
    owners |= {uid for (uid,) in db.session.query(Attempt.user_id).filter(Attempt.user_id.in_(stale)).distinct()}
    removed = purge_user_data(owners)
    if owners:
        app.logger.info("Retention: removed data of %d inactive user(s), %d bank(s)", len(owners), removed)
    return len(owners)


_last_cleanup = None  # per process; the purge is idempotent, so several workers are fine


@app.before_request
def track_activity_and_cleanup():
    global _last_cleanup
    if request.endpoint in (None, "static", "healthz"):
        return
    now = utcnow()
    if _last_cleanup is None or now - _last_cleanup > CLEANUP_EVERY:
        _last_cleanup = now
        try:
            purge_inactive_users()
        except Exception:  # never block a page because of housekeeping
            db.session.rollback()
            app.logger.exception("Retention cleanup failed")

    if current_user.is_authenticated:
        last = as_utc(current_user.last_active_at)
        if last is not None and now - last > timedelta(days=INACTIVITY_DAYS):
            # Came back after the retention period: data goes, the account stays
            if purge_user_data([current_user.id]):
                flash(t("flash.data_expired", days=INACTIVITY_DAYS), "info")
        if last is None or now - last > ACTIVITY_WRITE_EVERY:
            current_user.last_active_at = now
            db.session.commit()


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
@app.route("/")
def index():
    return redirect(url_for("dashboard" if current_user.is_authenticated else "login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        code = request.form.get("code", "").strip()

        error = None
        if REGISTRATION_CODE and code != REGISTRATION_CODE:
            error = t("flash.bad_code")
        elif not (3 <= len(username) <= 40) or not username.replace("_", "").replace(".", "").replace("-", "").isalnum():
            error = t("flash.bad_username")
        elif len(password) < 6:
            error = t("flash.short_password")
        elif password != confirm:
            error = t("flash.password_mismatch")
        elif User.query.filter(db.func.lower(User.username) == username.lower()).first():
            error = t("flash.username_taken")

        if error:
            flash(error, "error")
        else:
            user = User(username=username, password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=True)
            flash(t("flash.welcome", name=username), "success")
            return redirect(url_for("dashboard"))
    return render_template("register.html", needs_code=bool(REGISTRATION_CODE))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter(db.func.lower(User.username) == username.lower()).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=bool(request.form.get("remember")))
            last = as_utc(user.last_active_at)
            if last is not None and utcnow() - last > timedelta(days=INACTIVITY_DAYS):
                if purge_user_data([user.id]):
                    flash(t("flash.data_expired", days=INACTIVITY_DAYS), "info")
            user.last_active_at = utcnow()
            db.session.commit()
            next_url = request.args.get("next", "")
            if not next_url.startswith("/") or next_url.startswith("//"):
                next_url = url_for("dashboard")
            return redirect(next_url)
        flash(t("flash.bad_login"), "error")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash(t("flash.signed_out"), "info")
    return redirect(url_for("login"))


# --------------------------------------------------------------------------- #
# Dashboard & question banks
# --------------------------------------------------------------------------- #
@app.route("/dashboard")
@login_required
def dashboard():
    quizzes = (Quiz.query.filter_by(user_id=current_user.id)
               .order_by(Quiz.created_at.desc()).all())
    counts = dict(db.session.query(Question.quiz_id, db.func.count(Question.id))
                  .filter(Question.quiz_id.in_([q.id for q in quizzes] or [0]))
                  .group_by(Question.quiz_id).all())
    attempts = (Attempt.query.filter_by(user_id=current_user.id)
                .order_by(Attempt.started_at.desc()).limit(10).all())
    return render_template("dashboard.html", quizzes=quizzes, counts=counts, attempts=attempts,
                           max_banks=MAX_BANKS, limit_reached=len(quizzes) >= MAX_BANKS,
                           inactivity_days=INACTIVITY_DAYS)


@app.route("/upload", methods=["POST"])
@login_required
def upload():
    file = request.files.get("file")
    if not file or not file.filename:
        flash(t("flash.choose_file"), "error")
        return redirect(url_for("dashboard"))
    if not file.filename.lower().endswith((".xlsx", ".xlsm")):
        flash(t("flash.only_xlsx"), "error")
        return redirect(url_for("dashboard"))

    try:
        parsed = parse_workbook(file.stream)
    except ParseError as exc:
        flash(t(exc.key, **exc.params), "error")
        for key, params in exc.details:
            if "answer" in params and not params["answer"]:
                params = dict(params, answer=t("parse.empty_value"))
            flash(t(key, **params), "detail")
        return redirect(url_for("dashboard"))

    fingerprint = content_hash(parsed)
    existing = Quiz.query.filter_by(user_id=current_user.id, file_hash=fingerprint).first()
    if existing:
        flash(t("flash.duplicate", title=existing.title), "info")
        return redirect(url_for("briefing", quiz_id=existing.id))
    if Quiz.query.filter_by(user_id=current_user.id).count() >= MAX_BANKS:
        flash(t("flash.limit_reached", max=MAX_BANKS), "error")
        return redirect(url_for("dashboard"))

    title = request.form.get("title", "").strip() or os.path.splitext(file.filename)[0]
    quiz = Quiz(user_id=current_user.id, title=title[:120], filename=file.filename[:255],
                file_hash=fingerprint)
    for pos, q in enumerate(parsed):
        quiz.questions.append(Question(position=pos, external_id=q["external_id"][:64], text=q["text"],
                                       options=q["options"], correct=q["correct"]))
    db.session.add(quiz)
    db.session.commit()
    flash(t("flash.loaded", n=len(parsed)), "success")
    return redirect(url_for("briefing", quiz_id=quiz.id))


@app.route("/template.xlsx")
@login_required
def download_template():
    return send_file(build_template(get_lang(), t("tpl.sheet")), as_attachment=True, download_name=t("tpl.filename"),
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.route("/quiz/<int:quiz_id>/delete", methods=["POST"])
@login_required
def delete_quiz(quiz_id):
    quiz = owned_or_404(Quiz, quiz_id)
    # Delete answers first so FK order is safe on every database backend
    attempt_ids = [a.id for a in quiz.attempts]
    if attempt_ids:
        AttemptAnswer.query.filter(AttemptAnswer.attempt_id.in_(attempt_ids)).delete(synchronize_session=False)
    db.session.delete(quiz)
    db.session.commit()
    flash(t("flash.deleted", title=quiz.title), "info")
    return redirect(url_for("dashboard"))


# --------------------------------------------------------------------------- #
# Attempts
# --------------------------------------------------------------------------- #
def create_attempt(quiz, mode, question_ids, shuffle_questions, shuffle_options):
    if shuffle_questions:
        random.shuffle(question_ids)
    option_orders = {}
    if shuffle_options:
        for q in Question.query.filter(Question.id.in_(question_ids)).all():
            idx = [i for i, text in enumerate(q.options) if text]
            random.shuffle(idx)
            option_orders[str(q.id)] = idx
    attempt = Attempt(user_id=current_user.id, quiz_id=quiz.id, mode=mode,
                      order=question_ids, option_orders=option_orders)
    db.session.add(attempt)
    db.session.commit()
    return attempt


@app.route("/quiz/<int:quiz_id>", methods=["GET", "POST"])
@login_required
def briefing(quiz_id):
    quiz = owned_or_404(Quiz, quiz_id)
    total = len(quiz.questions)
    if request.method == "POST":
        mode = request.form.get("mode")
        if mode not in MODES:
            flash(t("flash.select_mode"), "error")
            return redirect(url_for("briefing", quiz_id=quiz.id))
        try:
            limit = int(request.form.get("limit") or total)
        except ValueError:
            limit = total
        limit = max(1, min(limit, total))

        ids = [q.id for q in quiz.questions]
        shuffle_q = bool(request.form.get("shuffle_questions"))
        if limit < total:
            ids = random.sample(ids, limit)  # random subset; order handled below
            if not shuffle_q:
                ids.sort(key=lambda i: next(q.position for q in quiz.questions if q.id == i))
        attempt = create_attempt(quiz, mode, ids, shuffle_q, bool(request.form.get("shuffle_options")))
        return redirect(url_for("run_attempt", attempt_id=attempt.id))
    return render_template("briefing.html", quiz=quiz, total=total)


def hp_info(attempt):
    allowed = MODES[attempt.mode]["allowed"]
    if allowed is None:
        return None, None
    total = allowed + 1  # last HP point = the mistake that ends the test
    return total, max(total - attempt.errors, 0)


def finish_attempt(attempt, status):
    attempt.status = status
    attempt.finished_at = utcnow()


def state_payload(attempt):
    hp_total, hp_left = hp_info(attempt)
    data = {
        "finished": attempt.status != "active",
        "status": attempt.status,
        "results_url": url_for("results", attempt_id=attempt.id),
        "mode": {"key": attempt.mode, "name": t("mode." + attempt.mode),
                 "unlimited": hp_total is None},
        "hp_total": hp_total,
        "hp_left": hp_left,
        "errors": attempt.errors,
        "correct_count": attempt.correct_count,
        "position": attempt.position,
        "total": attempt.total,
    }
    if attempt.status == "active":
        qid = attempt.order[attempt.position]
        q = db.session.get(Question, qid)
        order = (attempt.option_orders or {}).get(str(qid)) or [i for i, t in enumerate(q.options) if t]
        data["question"] = {
            "id": q.id,
            "external_id": q.external_id,
            "text": q.text,
            "options": [{"index": i, "text": q.options[i]} for i in order],
        }
    return data


@app.route("/attempt/<int:attempt_id>")
@login_required
def run_attempt(attempt_id):
    attempt = owned_or_404(Attempt, attempt_id)
    if attempt.status != "active":
        return redirect(url_for("results", attempt_id=attempt.id))
    return render_template("test.html", attempt=attempt, js_strings=js_strings())


@app.route("/api/attempt/<int:attempt_id>/state")
@login_required
def api_state(attempt_id):
    attempt = owned_or_404(Attempt, attempt_id)
    return jsonify(state_payload(attempt))


@app.route("/api/attempt/<int:attempt_id>/answer", methods=["POST"])
@login_required
def api_answer(attempt_id):
    attempt = owned_or_404(Attempt, attempt_id)
    if attempt.status != "active":
        return jsonify({"error": "finished", "state": state_payload(attempt)}), 409

    payload = request.get_json(silent=True) or {}
    current_qid = attempt.order[attempt.position]
    if payload.get("question_id") != current_qid:
        # Double click or stale tab — send the real state back
        return jsonify({"error": "stale", "state": state_payload(attempt)}), 409

    q = db.session.get(Question, current_qid)
    choice = payload.get("choice")
    if not isinstance(choice, int) or not (0 <= choice < len(q.options)) or not q.options[choice]:
        return jsonify({"error": "invalid choice"}), 400

    is_correct = choice == q.correct
    db.session.add(AttemptAnswer(attempt_id=attempt.id, question_id=q.id, chosen=choice, is_correct=is_correct))
    if is_correct:
        attempt.correct_count += 1
    else:
        attempt.errors += 1
    attempt.position += 1

    allowed = attempt.mode_info["allowed"]
    if allowed is not None and attempt.errors > allowed:
        finish_attempt(attempt, "failed")
    elif attempt.position >= attempt.total:
        if allowed is None:
            passed = attempt.correct_count / attempt.total >= EASY_PASS_RATIO
        else:
            passed = True
        finish_attempt(attempt, "passed" if passed else "failed")
    db.session.commit()

    return jsonify({"correct": is_correct, "correct_index": q.correct, "chosen": choice,
                    "state": state_payload(attempt)})


@app.route("/attempt/<int:attempt_id>/abandon", methods=["POST"])
@login_required
def abandon_attempt(attempt_id):
    attempt = owned_or_404(Attempt, attempt_id)
    if attempt.status == "active":
        finish_attempt(attempt, "abandoned")
        db.session.commit()
    return redirect(url_for("results", attempt_id=attempt.id))


@app.route("/attempt/<int:attempt_id>/results")
@login_required
def results(attempt_id):
    attempt = owned_or_404(Attempt, attempt_id)
    if attempt.status == "active":
        return redirect(url_for("run_attempt", attempt_id=attempt.id))

    questions = {q.id: q for q in Question.query.filter(Question.id.in_(attempt.order)).all()}
    answers = {a.question_id: a for a in attempt.answers}
    rows = []
    for number, qid in enumerate(attempt.order, start=1):
        q = questions.get(qid)
        if q is None:
            continue
        a = answers.get(qid)
        state = "unanswered" if a is None else ("correct" if a.is_correct else "wrong")
        rows.append({"n": number, "q": q, "answer": a, "state": state})

    wrong = sum(1 for r in rows if r["state"] == "wrong")
    unanswered = sum(1 for r in rows if r["state"] == "unanswered")
    duration = None
    if attempt.finished_at and attempt.started_at:
        start = attempt.started_at
        end = attempt.finished_at
        if start.tzinfo is None:  # SQLite drops tzinfo
            end = end.replace(tzinfo=None)
        duration = int((end - start).total_seconds())
    score_pct = round(100 * attempt.correct_count / attempt.total) if attempt.total else 0
    return render_template("results.html", attempt=attempt, rows=rows, wrong=wrong,
                           unanswered=unanswered, duration=duration, score_pct=score_pct,
                           easy_pass_pct=round(EASY_PASS_RATIO * 100))


@app.route("/attempt/<int:attempt_id>/retry", methods=["POST"])
@login_required
def retry_attempt(attempt_id):
    """Start a new attempt from a finished one: all questions again, or only the missed ones."""
    old = owned_or_404(Attempt, attempt_id)
    mode = request.form.get("mode", old.mode)
    if mode not in MODES:
        mode = old.mode
    if request.form.get("scope") == "missed":
        correct_ids = {a.question_id for a in old.answers if a.is_correct}
        ids = [qid for qid in old.order if qid not in correct_ids]
        if not ids:
            flash(t("flash.nothing_to_retry"), "info")
            return redirect(url_for("results", attempt_id=old.id))
    else:
        ids = list(old.order)
    attempt = create_attempt(old.quiz, mode, ids, True, bool(old.option_orders))
    return redirect(url_for("run_attempt", attempt_id=attempt.id))


# --------------------------------------------------------------------------- #
# Errors & template helpers
# --------------------------------------------------------------------------- #
@app.errorhandler(413)
def too_large(_):
    flash(t("flash.too_large"), "error")
    return redirect(url_for("dashboard"))


@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404, message=t("error.not_found")), 404


@app.template_filter("dt")
def format_dt(value):
    return value.strftime("%d.%m.%Y %H:%M") if value else ""


@app.template_filter("duration")
def format_duration(seconds):
    if seconds is None:
        return "—"
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02d}:{sec:02d}" if hours else f"{minutes}:{sec:02d}"


@app.route("/healthz")
def healthz():
    return "ok"


if __name__ == "__main__":
    app.run(debug=True)
