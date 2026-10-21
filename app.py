"""
Kiiraay America - site web complet (Flask + SQLite)

Lancer :   python app.py
Site :     http://127.0.0.1:5000
Admin :    http://127.0.0.1:5000/admin
"""
import csv
import getpass
import io
import os
import re
import secrets
import sqlite3
import sys
import time
from datetime import datetime, timezone
from functools import wraps

from flask import (Flask, Response, abort, flash, g, jsonify, redirect,
                   render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
UPLOADS = os.path.join(BASE, "static", "uploads")
os.makedirs(DATA, exist_ok=True)
os.makedirs(UPLOADS, exist_ok=True)
DB_PATH = os.path.join(DATA, "kiiraay.db")
KEY_PATH = os.path.join(DATA, "secret.key")

# --- COMPTE ADMINISTRATEUR (créé au premier lancement) --------------------------
# En production, préférez les variables d'environnement ADMIN_USER / ADMIN_PASSWORD
# et changez ce mot de passe avec :  python app.py set-password
ADMIN_USER_DEFAULT = "Mouhamedsakho"
ADMIN_PASSWORD_DEFAULT = "Mouhamedsakho@"

SETTINGS_DEFAULTS = {
    "hero_title": "Les Patriotes Républicains, aux États-Unis.",
    "hero_text": "Kiiraay America rassemble les Sénégalaises et les Sénégalais des États-Unis autour de leur parti. Rejoignez le groupe, demandez des informations, restez en lien avec la maison.",
    "hero_image": "images/tribune.webp",
    "about_title": "Qui sommes-nous",
    "about_text": "Kiiraay – Les Patriotes Républicains est un parti politique du Sénégal. Kiiraay America est le groupe qui le représente aux États-Unis : il réunit la diaspora sénégalaise de tout le pays.\n\nNous organisons des rencontres, nous nous mobilisons ensemble et nous partageons les nouvelles du parti. Que vous viviez à New York, en Géorgie, au Texas ou ailleurs, il y a une place pour vous.",
    "footer_text": "Les Patriotes Républicains – Groupe États-Unis",
}
SEED_POST_TITLE = "Reçu par Madame le Ministre de la Famille, de l’Action sociale et des Solidarités"
SEED_POST_TEXT = """J’ai eu l’honneur d’être reçu, ce vendredi 9 octobre 2026, par Madame le Ministre de la Famille, de l’Action sociale et des Solidarités, Marie Angélique Mame Selbé Diouf.

À cette occasion, nous avons échangé sur les préoccupations des Sénégalais de la diaspora, notamment celles exposées dans le mémorandum que j’ai eu l’honneur de partager avec Son Excellence Monsieur Bassirou Diomaye Diakhare Faye, Président de la République du Sénégal, ainsi qu’avec son gouvernement.

Ce mémorandum met en lumière la contribution économique, sociale, culturelle et religieuse de la communauté sénégalaise établie aux États-Unis depuis plus de quarante ans. Par leurs transferts de fonds, leurs entreprises, leurs associations et leurs structures communautaires, nos compatriotes soutiennent leurs familles, participent au développement national et font rayonner le Sénégal à l’étranger.

Il présente les principales difficultés rencontrées et propose plusieurs solutions concrètes :

1. Faciliter l’accès aux services consulaires et administratifs, notamment pour l’établissement et le renouvellement des passeports, des cartes nationales d’identité et des cartes consulaires, ainsi que pour les démarches d’état civil. Des missions consulaires régulières dans les différents États permettraient de réduire les déplacements coûteux vers New York.

2. Renforcer l’assistance consulaire aux compatriotes en difficulté, notamment ceux qui sont détenus ou accueillis dans des établissements de repos, et disposer de données fiables pour mieux répondre à leurs besoins.

3. Améliorer la représentation institutionnelle de la diaspora, afin que ses préoccupations soient davantage prises en compte dans les politiques publiques.

4. Soutenir les initiatives éducatives et culturelles destinées aux jeunes, notamment par la création d’une école sénégalaise permettant aux enfants de la diaspora de mieux connaître leur histoire, leur culture et leurs origines.

5. Créer un centre culturel et communautaire sénégalais aux États-Unis, destiné à accueillir des activités culturelles, éducatives, religieuses et associatives.

6. Faciliter l’accès aux fonds d’investissement, afin de permettre aux entrepreneurs sénégalais établis aux États-Unis de développer des projets productifs au Sénégal.

7. Mettre en place une banque sénégalaise de la diaspora, pour faciliter les transactions financières, mobiliser l’épargne et encourager l’investissement productif.

8. Accorder un quota officiel pour le Hajj aux Sénégalais vivant aux États-Unis, afin de leur éviter un détour coûteux et fatigant par Dakar.

9. Accompagner les projets communautaires, notamment les mosquées, les centres religieux et les programmes éducatifs qui contribuent à l’encadrement des familles et à la cohésion sociale.

Nous avons également discuté des moyens d’aider les groupements de femmes à accéder aux financements et à investir, notamment par l’achat d’actions et la prise de participations dans des entreprises, afin de renforcer leur autonomie économique et leur contribution au développement du pays.

La diaspora représente un potentiel considérable de compétences, d’épargne et d’investissement. Notre ambition est de promouvoir un partenariat gagnant-gagnant entre l’État et les Sénégalais de l’extérieur, permettant de soutenir des projets durables au bénéfice des femmes, des jeunes, des familles et de l’économie nationale.

Je remercie Madame le Ministre pour son accueil et son écoute. Je réaffirme ma disponibilité à contribuer, avec les institutions concernées et les acteurs de la diaspora, à la concrétisation de ces propositions.

Dr Mouhamed Mountakha Sakho
Imam et Président de l’Islamic Cultural Foundation of America — ICFA
PDG d’Al Madina International Travel

Publication d’origine : https://www.facebook.com/share/1DELAi4iFw/?mibextid=wwXIfr"""
SEED_FILES = ["rencontre-cover.jpg", "rencontre-2.jpg", "rencontre-3.jpg", "rencontre-4.jpg", "rencontre-5.jpg"]
TEXT_KEYS = ["hero_title", "hero_text", "about_title", "about_text", "footer_text"]

ALLOWED_IMG = {"jpg": b"\xff\xd8\xff", "jpeg": b"\xff\xd8\xff", "png": b"\x89PNG", "webp": b"RIFF"}
DEMANDES = ["Je veux rejoindre le groupe", "Je veux des informations", "Je veux être bénévole"]
ETATS = ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut",
         "Delaware", "District of Columbia", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois",
         "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland",
         "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana",
         "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York",
         "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania",
         "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah",
         "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"]

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 6 * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("PRODUCTION") == "1"


def load_secret():
    if not os.path.exists(KEY_PATH):
        with open(KEY_PATH, "w") as f:
            f.write(secrets.token_hex(32))
    with open(KEY_PATH) as f:
        return f.read().strip()


app.secret_key = load_secret()


# ---------------------------------------------------------------- base de données
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript("""
    CREATE TABLE IF NOT EXISTS admins(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS submissions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prenom TEXT, nom TEXT, telephone TEXT, email TEXT,
        etat TEXT, ville TEXT, demande TEXT, message TEXT,
        traite INTEGER DEFAULT 0,
        created_at TEXT);
    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
    CREATE TABLE IF NOT EXISTS gallery(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image TEXT NOT NULL, caption TEXT, created_at TEXT);
    CREATE TABLE IF NOT EXISTS post_images(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL, image TEXT NOT NULL, position INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS posts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, content TEXT NOT NULL,
        image TEXT, published INTEGER DEFAULT 1,
        created_at TEXT);
    """)
    user = os.environ.get("ADMIN_USER", ADMIN_USER_DEFAULT)
    pwd = os.environ.get("ADMIN_PASSWORD", ADMIN_PASSWORD_DEFAULT)
    if not db.execute("SELECT 1 FROM admins WHERE lower(username)=lower(?)", (user,)).fetchone():
        db.execute("INSERT INTO admins(username,password_hash) VALUES(?,?)",
                   (user, generate_password_hash(pwd)))
        if user.lower() != "admin":  # ancien compte par défaut de la première version
            db.execute("DELETE FROM admins WHERE username='admin'")
        print("Compte administrateur créé :", user)
    if (not db.execute("SELECT 1 FROM gallery").fetchone()
            and not db.execute("SELECT 1 FROM settings WHERE key='gallery_seeded'").fetchone()):
        for img, cap in [("images/rassemblement.jpeg", "Mobilisation de la diaspora à New York."),
                         ("images/rencontre.jpeg", "Une rencontre officielle."),
                         ("images/tribune.webp", "Une prise de parole du parti.")]:
            db.execute("INSERT INTO gallery(image,caption,created_at) VALUES(?,?,?)", (img, cap, now()))
        db.execute("INSERT INTO settings(key,value) VALUES('gallery_seeded','1')")
    if not db.execute("SELECT 1 FROM settings WHERE key='post_rencontre_seeded'").fetchone():
        import shutil
        names = []
        for f in SEED_FILES:
            src = os.path.join(BASE, "static", "seed", f)
            if os.path.exists(src):
                shutil.copyfile(src, os.path.join(UPLOADS, f))
                names.append(f)
        if names:
            cur = db.execute("INSERT INTO posts(title,content,image,published,created_at) VALUES(?,?,?,1,?)",
                             (SEED_POST_TITLE, SEED_POST_TEXT, names[0], "2026-10-09 12:00"))
            for i, n in enumerate(names[1:]):
                db.execute("INSERT INTO post_images(post_id,image,position) VALUES(?,?,?)", (cur.lastrowid, n, i))
        db.execute("INSERT INTO settings(key,value) VALUES('post_rencontre_seeded','1')")
    db.commit()
    db.close()


# ---------------------------------------------------------------- sécurité
def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


app.jinja_env.globals["csrf_token"] = csrf_token


def get_settings():
    s = dict(SETTINGS_DEFAULTS)
    for r in get_db().execute("SELECT key,value FROM settings"):
        if r["key"] in s:
            s[r["key"]] = r["value"]
    return s


@app.context_processor
def inject_settings():
    return {"S": get_settings()}
app.jinja_env.globals["ETATS"] = ETATS
app.jinja_env.globals["DEMANDES"] = DEMANDES


@app.before_request
def check_csrf():
    if request.method == "POST":
        sent = request.form.get("csrf", "")
        if not sent or not secrets.compare_digest(sent, session.get("csrf", "")):
            abort(400)


@app.after_request
def headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "same-origin"
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; "
        "style-src 'self' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; script-src 'self'; "
        "form-action 'self'; frame-ancestors 'none'")
    return resp


ATTEMPTS = {}


def too_many_attempts(ip):
    t = time.time()
    ATTEMPTS[ip] = [x for x in ATTEMPTS.get(ip, []) if t - x < 900]
    return len(ATTEMPTS[ip]) >= 5


def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return f(*a, **kw)
    return wrapper


# ---------------------------------------------------------------- pages publiques
@app.route("/")
def index():
    posts = get_db().execute(
        "SELECT * FROM posts WHERE published=1 ORDER BY id DESC LIMIT 6").fetchall()
    gallery = get_db().execute("SELECT * FROM gallery ORDER BY id DESC").fetchall()
    return render_template("index.html", posts=posts, gallery=gallery)


@app.route("/publications")
def publications():
    posts = get_db().execute(
        "SELECT * FROM posts WHERE published=1 ORDER BY id DESC").fetchall()
    return render_template("publications.html", posts=posts)


@app.route("/publication/<int:pid>")
def publication(pid):
    p = get_db().execute("SELECT * FROM posts WHERE id=? AND published=1", (pid,)).fetchone()
    if not p:
        abort(404)
    extras = get_db().execute("SELECT * FROM post_images WHERE post_id=? ORDER BY position, id", (pid,)).fetchall()
    return render_template("publication.html", p=p, extras=extras)


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@app.route("/contact", methods=["POST"])
def contact():
    f = request.form
    if f.get("_gotcha"):  # robot : on fait semblant que c'est OK
        return jsonify(ok=True)
    data = {k: f.get(k, "").strip() for k in
            ["prenom", "nom", "telephone", "email", "etat", "ville", "demande", "message"]}
    errors = []
    if not data["prenom"] or len(data["prenom"]) > 80:
        errors.append("Prénom obligatoire.")
    if not data["nom"] or len(data["nom"]) > 80:
        errors.append("Nom obligatoire.")
    digits = re.sub(r"\D", "", data["telephone"])
    if not 10 <= len(digits) <= 15 or len(data["telephone"]) > 30:
        errors.append("Numéro de téléphone invalide.")
    if not EMAIL_RE.match(data["email"]) or len(data["email"]) > 120:
        errors.append("E-mail invalide.")
    if data["etat"] not in ETATS:
        errors.append("Choisissez un État.")
    if not data["ville"] or len(data["ville"]) > 80:
        errors.append("Ville obligatoire.")
    if data["demande"] not in DEMANDES:
        errors.append("Choisissez le type de demande.")
    if len(data["message"]) > 2000:
        errors.append("Message trop long (2000 caractères maximum).")
    if not f.get("consent"):
        errors.append("Vous devez accepter d'être contacté.")
    if errors:
        return jsonify(ok=False, errors=errors), 400
    db = get_db()
    db.execute(
        "INSERT INTO submissions(prenom,nom,telephone,email,etat,ville,demande,message,created_at)"
        " VALUES(?,?,?,?,?,?,?,?,?)",
        (data["prenom"], data["nom"], data["telephone"], data["email"], data["etat"],
         data["ville"], data["demande"], data["message"], now()))
    db.commit()
    return jsonify(ok=True)


# ---------------------------------------------------------------- admin : connexion
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        ip = request.remote_addr or "?"
        if too_many_attempts(ip):
            flash("Trop de tentatives. Réessayez dans 15 minutes.", "err")
            return render_template("admin/login.html"), 429
        u = get_db().execute("SELECT * FROM admins WHERE lower(username)=lower(?)",
                             (request.form.get("username", "").strip(),)).fetchone()
        if u and check_password_hash(u["password_hash"], request.form.get("password", "")):
            session.clear()
            session["admin"] = u["username"]
            csrf_token()
            return redirect(url_for("admin_dashboard"))
        ATTEMPTS.setdefault(ip, []).append(time.time())
        flash("Identifiants incorrects.", "err")
    return render_template("admin/login.html")


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


# ---------------------------------------------------------------- admin : demandes
def filtered_submissions():
    q = request.args.get("q", "").strip()
    etat = request.args.get("etat", "").strip()
    statut = request.args.get("statut", "").strip()
    sql, args = "SELECT * FROM submissions WHERE 1=1", []
    if q:
        sql += " AND (prenom LIKE ? OR nom LIKE ? OR email LIKE ? OR telephone LIKE ? OR ville LIKE ?)"
        args += [f"%{q}%"] * 5
    if etat:
        sql += " AND etat=?"
        args.append(etat)
    if statut in ("0", "1"):
        sql += " AND traite=?"
        args.append(int(statut))
    sql += " ORDER BY id DESC"
    return get_db().execute(sql, args).fetchall()


@app.route("/admin")
@login_required
def admin_dashboard():
    rows = filtered_submissions()
    db = get_db()
    stats = {
        "total": db.execute("SELECT COUNT(*) FROM submissions").fetchone()[0],
        "nouveaux": db.execute("SELECT COUNT(*) FROM submissions WHERE traite=0").fetchone()[0],
        "posts": db.execute("SELECT COUNT(*) FROM posts").fetchone()[0],
    }
    return render_template("admin/dashboard.html", rows=rows, stats=stats,
                           q=request.args.get("q", ""), etat=request.args.get("etat", ""),
                           statut=request.args.get("statut", ""))


@app.route("/admin/demande/<int:sid>/traite", methods=["POST"])
@login_required
def toggle_traite(sid):
    db = get_db()
    db.execute("UPDATE submissions SET traite = 1 - traite WHERE id=?", (sid,))
    db.commit()
    return redirect(request.referrer or url_for("admin_dashboard"))


@app.route("/admin/demande/<int:sid>/supprimer", methods=["POST"])
@login_required
def delete_submission(sid):
    db = get_db()
    db.execute("DELETE FROM submissions WHERE id=?", (sid,))
    db.commit()
    flash("Demande supprimée.", "ok")
    return redirect(request.referrer or url_for("admin_dashboard"))


def safe_cell(v):
    v = "" if v is None else str(v)
    return "'" + v if v[:1] in ("=", "+", "-", "@") else v


@app.route("/admin/export.csv")
@login_required
def export_csv():
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["ID", "Date (UTC)", "Prénom", "Nom", "Téléphone", "E-mail", "État", "Ville",
                "Demande", "Message", "Traité"])
    for r in filtered_submissions():
        w.writerow([r["id"], r["created_at"], safe_cell(r["prenom"]), safe_cell(r["nom"]),
                    safe_cell(r["telephone"]), safe_cell(r["email"]), r["etat"],
                    safe_cell(r["ville"]), r["demande"], safe_cell(r["message"]),
                    "oui" if r["traite"] else "non"])
    data = "\ufeff" + out.getvalue()
    return Response(data, mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=demandes_kiiraay.csv"})


# ---------------------------------------------------------------- admin : publications
def save_image(file):
    """Enregistre l'image si elle est valide. Retourne le nom du fichier ou None."""
    if not file or not file.filename:
        return None
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_IMG:
        raise ValueError("Image refusée : formats autorisés JPG, PNG, WEBP.")
    head = file.stream.read(12)
    file.stream.seek(0)
    if not head.startswith(ALLOWED_IMG[ext]) or (ext == "webp" and head[8:12] != b"WEBP"):
        raise ValueError("Le fichier n'est pas une vraie image.")
    name = f"{secrets.token_hex(8)}.{ext}"
    file.save(os.path.join(UPLOADS, name))
    return name


def remove_image(name):
    if name:
        path = os.path.join(UPLOADS, os.path.basename(name))
        if os.path.exists(path):
            os.remove(path)


@app.route("/admin/publications")
@login_required
def admin_posts():
    posts = get_db().execute("SELECT * FROM posts ORDER BY id DESC").fetchall()
    return render_template("admin/posts.html", posts=posts)


@app.route("/admin/publications/nouvelle", methods=["GET", "POST"])
@app.route("/admin/publications/<int:pid>/modifier", methods=["GET", "POST"])
@login_required
def admin_post_form(pid=None):
    db = get_db()
    post, extras = None, []
    if pid:
        post = db.execute("SELECT * FROM posts WHERE id=?", (pid,)).fetchone()
        if not post:
            abort(404)
        extras = db.execute("SELECT * FROM post_images WHERE post_id=? ORDER BY position, id", (pid,)).fetchall()

    def render_err(msg):
        flash(msg, "err")
        return render_template("admin/post_form.html", post=request.form, pid=pid,
                               old_image=post["image"] if post else None, extras=extras), 400

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        published = 1 if request.form.get("published") else 0
        if not title or not content:
            return render_err("Le titre et le texte sont obligatoires.")
        saved = []
        try:
            cover = save_image(request.files.get("image"))
            if cover:
                saved.append(cover)
            more = []
            for f in request.files.getlist("images"):
                n = save_image(f)
                if n:
                    more.append(n)
                    saved.append(n)
        except ValueError as e:
            for n in saved:
                remove_image(n)
            return render_err(str(e))
        if post:
            image = post["image"]
            if cover or request.form.get("remove_image"):
                remove_image(image)
                image = cover
            db.execute("UPDATE posts SET title=?, content=?, image=?, published=? WHERE id=?",
                       (title, content, image, published, pid))
            for rid in request.form.getlist("remove_extra"):
                row = db.execute("SELECT * FROM post_images WHERE id=? AND post_id=?",
                                 (rid, pid)).fetchone()
                if row:
                    remove_image(row["image"])
                    db.execute("DELETE FROM post_images WHERE id=?", (row["id"],))
            post_id = pid
            flash("Publication modifiée.", "ok")
        else:
            cur = db.execute("INSERT INTO posts(title,content,image,published,created_at) VALUES(?,?,?,?,?)",
                             (title, content, cover, published, now()))
            post_id = cur.lastrowid
            flash("Publication créée.", "ok")
        start = db.execute("SELECT COALESCE(MAX(position),-1)+1 FROM post_images WHERE post_id=?",
                           (post_id,)).fetchone()[0]
        for i, n in enumerate(more):
            db.execute("INSERT INTO post_images(post_id,image,position) VALUES(?,?,?)", (post_id, n, start + i))
        db.commit()
        return redirect(url_for("admin_posts"))
    return render_template("admin/post_form.html", post=post, pid=pid,
                           old_image=post["image"] if post else None, extras=extras)


@app.route("/admin/publications/<int:pid>/supprimer", methods=["POST"])
@login_required
def delete_post(pid):
    db = get_db()
    p = db.execute("SELECT image FROM posts WHERE id=?", (pid,)).fetchone()
    if p:
        remove_image(p["image"])
        for r in db.execute("SELECT image FROM post_images WHERE post_id=?", (pid,)).fetchall():
            remove_image(r["image"])
        db.execute("DELETE FROM post_images WHERE post_id=?", (pid,))
        db.execute("DELETE FROM posts WHERE id=?", (pid,))
        db.commit()
        flash("Publication supprimée.", "ok")
    return redirect(url_for("admin_posts"))


# ---------------------------------------------------------------- admin : galerie
def remove_site_image(path):
    if path and path.startswith("uploads/"):
        remove_image(path[len("uploads/"):])


@app.route("/admin/galerie")
@login_required
def admin_gallery():
    items = get_db().execute("SELECT * FROM gallery ORDER BY id DESC").fetchall()
    return render_template("admin/gallery.html", items=items)


@app.route("/admin/galerie/ajouter", methods=["POST"])
@login_required
def gallery_add():
    try:
        name = save_image(request.files.get("image"))
    except ValueError as e:
        flash(str(e), "err")
        return redirect(url_for("admin_gallery"))
    if not name:
        flash("Choisissez une image.", "err")
        return redirect(url_for("admin_gallery"))
    db = get_db()
    db.execute("INSERT INTO gallery(image,caption,created_at) VALUES(?,?,?)",
               ("uploads/" + name, request.form.get("caption", "").strip()[:200], now()))
    db.commit()
    flash("Image ajoutée à la galerie.", "ok")
    return redirect(url_for("admin_gallery"))


@app.route("/admin/galerie/<int:gid>/supprimer", methods=["POST"])
@login_required
def gallery_delete(gid):
    db = get_db()
    g_ = db.execute("SELECT image FROM gallery WHERE id=?", (gid,)).fetchone()
    if g_:
        remove_site_image(g_["image"])
        db.execute("DELETE FROM gallery WHERE id=?", (gid,))
        db.commit()
        flash("Image supprimée.", "ok")
    return redirect(url_for("admin_gallery"))


# ---------------------------------------------------------------- admin : réglages du site
def set_setting(db, key, value):
    db.execute("INSERT INTO settings(key,value) VALUES(?,?) "
               "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))


@app.route("/admin/reglages", methods=["GET", "POST"])
@login_required
def admin_settings():
    db = get_db()
    if request.method == "POST":
        for k in TEXT_KEYS:
            v = request.form.get(k, "").strip()[:3000]
            if v:
                set_setting(db, k, v)
        current = get_settings()["hero_image"]
        try:
            new_img = save_image(request.files.get("hero_image"))
        except ValueError as e:
            flash(str(e), "err")
            return redirect(url_for("admin_settings"))
        if new_img:
            remove_site_image(current)
            set_setting(db, "hero_image", "uploads/" + new_img)
        elif request.form.get("reset_hero_image"):
            remove_site_image(current)
            set_setting(db, "hero_image", SETTINGS_DEFAULTS["hero_image"])
        db.commit()
        flash("Le site a été mis à jour.", "ok")
        return redirect(url_for("admin_settings"))
    return render_template("admin/settings.html")


@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404


@app.errorhandler(413)
def too_big(_):
    flash("Fichier trop gros (6 Mo maximum).", "err")
    return redirect(request.referrer or url_for("admin_posts"))


@app.template_filter("linkify")
def linkify(text):
    from markupsafe import Markup, escape
    safe = str(escape(text or ""))
    safe = re.sub(r'(https?://[^\s<]+)', r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>', safe)
    return Markup(safe)


@app.template_filter("dt")
def fmt_dt(v):
    return v or ""


init_db()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "set-password":
        user = input("Nom d'utilisateur admin [admin] : ").strip() or "admin"
        pwd = getpass.getpass("Nouveau mot de passe (10 caractères minimum) : ")
        if len(pwd) < 10:
            sys.exit("Mot de passe trop court.")
        db = sqlite3.connect(DB_PATH)
        cur = db.execute("UPDATE admins SET password_hash=? WHERE username=?",
                         (generate_password_hash(pwd), user))
        if cur.rowcount == 0:
            db.execute("INSERT INTO admins(username,password_hash) VALUES(?,?)",
                       (user, generate_password_hash(pwd)))
        db.commit()
        print("Mot de passe enregistré.")
    else:
        app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False)
