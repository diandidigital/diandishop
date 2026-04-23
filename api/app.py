from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_cors import CORS
import sqlite3
import os
import sys
import random
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from werkzeug.exceptions import HTTPException
from werkzeug.security import generate_password_hash, check_password_hash


def _resolve_paths():
    if getattr(sys, "frozen", False):
        runtime_dir = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        data_dir = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "DiandiShop"
        data_dir.mkdir(parents=True, exist_ok=True)
    else:
        default_runtime = Path(__file__).resolve().parent.parent
        runtime_dir = Path(os.environ.get("APP_RUNTIME_DIR", str(default_runtime))).resolve()
        data_dir = runtime_dir

    return runtime_dir, data_dir


RUNTIME_DIR, DATA_DIR = _resolve_paths()
DEFAULT_DB_PATH = str(DATA_DIR / "diandishop.db")
DATABASE_URL = os.environ.get("DATABASE_URL")
DB_PATH = os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH)
if DATABASE_URL and DATABASE_URL.startswith("sqlite:///"):
    DB_PATH = DATABASE_URL.replace("sqlite:///", "", 1)
DB_PATH = str(Path(DB_PATH))
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

app = Flask(
    __name__,
    template_folder=str(RUNTIME_DIR / "templates"),
    static_folder=str(RUNTIME_DIR / "static"),
)
app.secret_key = os.environ.get("SECRET_KEY", "diandishop-dev-secret")
CORS(
    app,
    supports_credentials=True,
    origins=os.environ.get("FRONTEND_ORIGIN", "*"),
)

# Code d'activation requis pour creer le tout premier compte admin.
# Definir la variable d'environnement SETUP_CODE pour personnaliser.
SETUP_CODE = os.environ.get("SETUP_CODE", "diandi2024")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _run_sql_migrations(conn):
    migrations_dir = Path(__file__).resolve().parent / "migrations"
    if not migrations_dir.exists():
        return

    applied = {
        row["name"]
        for row in conn.execute("SELECT name FROM migrations").fetchall()
    }

    for migration_file in sorted(migrations_dir.glob("*.sql")):
        if migration_file.name in applied:
            continue
        conn.executescript(migration_file.read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO migrations (name) VALUES (?)",
            (migration_file.name,),
        )


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("PRAGMA user_version")
    current_version = cursor.fetchone()[0]

    if current_version < 1:
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("PRAGMA user_version = 1")

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            couleur TEXT DEFAULT '#22c55e'
        );

        CREATE TABLE IF NOT EXISTS produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prix REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            stock_alerte INTEGER DEFAULT 5,
            categorie_id INTEGER,
            actif INTEGER DEFAULT 1,
            FOREIGN KEY (categorie_id) REFERENCES categories(id)
        );

        CREATE TABLE IF NOT EXISTS ventes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total REAL NOT NULL,
            paiement TEXT DEFAULT 'especes',
            monnaie REAL DEFAULT 0,
            date_vente TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS vente_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vente_id INTEGER,
            produit_id INTEGER,
            nom_produit TEXT,
            prix_unitaire REAL,
            quantite INTEGER,
            sous_total REAL,
            FOREIGN KEY (vente_id) REFERENCES ventes(id),
            FOREIGN KEY (produit_id) REFERENCES produits(id)
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'caissiere')),
            actif INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute(
        "INSERT OR IGNORE INTO migrations (name) VALUES (?)",
        ("baseline_schema_v1",),
    )
    _run_sql_migrations(conn)
    conn.commit()
    conn.close()


def _is_api_request():
    return request.path.startswith("/api/")


def _auth_error(message, status):
    if _is_api_request():
        return jsonify({"success": False, "message": message}), status
    return redirect(url_for("login"))


def _request_payload():
    if request.is_json:
        return request.get_json(silent=True) or {}
    return request.form


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return _auth_error("Authentification requise.", 401)
        return fn(*args, **kwargs)

    return wrapper


def role_required(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return _auth_error("Authentification requise.", 401)
            if session.get("user_role") not in allowed_roles:
                return _auth_error("Acces refuse.", 403)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def _redirect_after_login():
    if session.get("user_role") == "admin":
        return redirect(url_for("dashboard"))
    return redirect(url_for("pos"))


def _set_user_session(user):
    session.clear()
    session["user_id"] = user["id"]
    session["user_nom"] = user["nom"]
    session["username"] = user["username"]
    session["user_role"] = user["role"]


@app.context_processor
def inject_auth_context():
    return {
        "auth_user": session.get("user_nom"),
        "auth_role": session.get("user_role"),
        "is_admin": session.get("user_role") == "admin",
    }


@app.errorhandler(ValueError)
def handle_value_error(exc):
    if _is_api_request():
        return jsonify({"success": False, "message": str(exc)}), 400
    return render_template("login.html", message="", error=str(exc)), 400


@app.errorhandler(Exception)
def handle_unexpected_error(exc):
    if isinstance(exc, HTTPException):
        return exc
    app.logger.exception("Unexpected error", exc_info=exc)
    if _is_api_request():
        return jsonify({"success": False, "message": "Erreur interne du serveur."}), 500
    return render_template("login.html", message="", error="Erreur interne du serveur."), 500


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        if _is_api_request():
            return jsonify({"success": True, "role": session.get("user_role")})
        return _redirect_after_login()

    message = ""
    error = ""

    if request.method == "POST":
        payload = _request_payload()
        username = (payload.get("username") or "").strip().lower()
        password = payload.get("password") or ""

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND actif = 1", (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            _set_user_session(user)
            if _is_api_request():
                return jsonify({"success": True, "role": user["role"]})
            return _redirect_after_login()

        error = "Identifiants invalides."
        if _is_api_request():
            return jsonify({"success": False, "message": error}), 401

    return render_template("login.html", message=message, error=error)


@app.route("/api/auth/me", methods=["GET"])
def auth_me():
    if "user_id" not in session:
        return jsonify({"authenticated": False, "success": False}), 401
    return jsonify(
        {
            "authenticated": True,
            "success": True,
            "user": {
                "id": session.get("user_id"),
                "nom": session.get("user_nom"),
                "username": session.get("username"),
                "role": session.get("user_role"),
            },
        }
    )


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    return login()


@app.route("/api/auth/register", methods=["POST"])
def api_register():
    return register()


@app.route("/api/auth/logout", methods=["POST"])
@login_required
def api_logout():
    session.clear()
    return jsonify({"success": True})


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if "user_id" in session:
        return _redirect_after_login()

    step = request.args.get("step", "1")
    error = ""
    message = ""

    if request.method == "POST":
        if step == "1":
            username = (request.form.get("username") or "").strip().lower()
            nom = (request.form.get("nom") or "").strip()

            conn = get_db()
            user = conn.execute(
                "SELECT * FROM users WHERE username = ? AND actif = 1", (username,)
            ).fetchone()
            conn.close()

            if user and user["nom"].strip().lower() == nom.lower():
                return render_template(
                    "forgot_password.html",
                    step="2",
                    username=username,
                    error="",
                    message="",
                )
            error = "Nom d'utilisateur ou nom complet incorrect."
            return render_template("forgot_password.html", step="1", error=error, message="")

        elif step == "2":
            username = (request.form.get("username") or "").strip().lower()
            new_password = request.form.get("new_password") or ""
            confirm_password = request.form.get("confirm_password") or ""

            if len(new_password) < 6:
                return render_template(
                    "forgot_password.html",
                    step="2",
                    username=username,
                    error="Le mot de passe doit contenir au moins 6 caracteres.",
                    message="",
                )
            if new_password != confirm_password:
                return render_template(
                    "forgot_password.html",
                    step="2",
                    username=username,
                    error="Les mots de passe ne correspondent pas.",
                    message="",
                )

            conn = get_db()
            user = conn.execute(
                "SELECT id FROM users WHERE username = ? AND actif = 1", (username,)
            ).fetchone()
            if user:
                conn.execute(
                    "UPDATE users SET password_hash = ? WHERE id = ?",
                    (generate_password_hash(new_password), user["id"]),
                )
                conn.commit()
            conn.close()

            return render_template(
                "login.html",
                message="Mot de passe reinitialise avec succes. Vous pouvez vous connecter.",
                error="",
            )

    return render_template("forgot_password.html", step="1", error="", message="")


@app.route("/register", methods=["GET", "POST"])
def register():
    conn = get_db()
    user_count = conn.execute("SELECT COUNT(*) as nb FROM users WHERE actif = 1").fetchone()["nb"]
    has_users = user_count > 0

    if has_users and session.get("user_role") != "admin":
        conn.close()
        if _is_api_request():
            return jsonify({"success": False, "message": "Acces refuse."}), 403
        return redirect(url_for("login"))

    error = ""
    message = ""

    if request.method == "POST":
        payload = _request_payload()
        nom = (payload.get("nom") or "").strip()
        username = (payload.get("username") or "").strip().lower()
        password = payload.get("password") or ""

        if has_users:
            role = payload.get("role") if payload.get("role") in ("admin", "caissiere") else "caissiere"
        else:
            role = "admin"
            setup_code = (payload.get("setup_code") or "").strip()
            if setup_code != SETUP_CODE:
                error = "Code d'activation incorrect. Contacte l'administrateur."
                conn.close()
                if _is_api_request():
                    return jsonify({"success": False, "message": error}), 400
                return render_template("register.html", error=error, message="", has_users=False)

        if not nom or not username or len(password) < 4:
            error = "Remplis tous les champs (mot de passe minimum 4 caracteres)."
        else:
            existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            if existing:
                error = "Ce nom d'utilisateur existe deja."
            else:
                conn.execute(
                    """
                    INSERT INTO users (nom, username, password_hash, role)
                    VALUES (?, ?, ?, ?)
                    """,
                    (nom, username, generate_password_hash(password), role),
                )
                conn.commit()

                if not has_users:
                    user = conn.execute(
                        "SELECT * FROM users WHERE username = ?", (username,)
                    ).fetchone()
                    _set_user_session(user)
                    conn.close()
                    if _is_api_request():
                        return jsonify({"success": True, "role": user["role"]})
                    return redirect(url_for("dashboard"))

                message = "Compte cree avec succes."

    conn.close()
    if _is_api_request():
        status = 200 if not error else 400
        return jsonify({"success": not bool(error), "message": message or error}), status
    return render_template(
        "register.html",
        error=error,
        message=message,
        has_users=has_users,
    )


@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))

# ─── ROUTES PAGES ───────────────────────────────────────────
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return _redirect_after_login()


@app.route("/dashboard")
@role_required("admin")
def dashboard():
    return render_template("dashboard.html")

@app.route("/pos")
@role_required("admin", "caissiere")
def pos():
    return render_template("pos.html")

@app.route("/produits")
@role_required("admin")
def produits():
    return render_template("produits.html")

@app.route("/stock")
@role_required("admin")
def stock():
    return render_template("stock.html")

# ─── API CATEGORIES ─────────────────────────────────────────
@app.route("/api/categories", methods=["GET"])
@role_required("admin", "caissiere")
def get_categories():
    conn = get_db()
    categories = conn.execute("SELECT * FROM categories").fetchall()
    conn.close()
    return jsonify([dict(c) for c in categories])

@app.route("/api/categories", methods=["POST"])
@role_required("admin")
def add_categorie():
    data = _request_payload()
    if not data.get("nom"):
        raise ValueError("Le nom de la categorie est requis.")
    conn = get_db()
    conn.execute("INSERT INTO categories (nom, couleur) VALUES (?, ?)",
                 (data["nom"], data.get("couleur", "#22c55e")))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/categories/<int:id>", methods=["DELETE"])
@role_required("admin")
def delete_categorie(id):
    conn = get_db()
    conn.execute("DELETE FROM categories WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

# ─── API PRODUITS ────────────────────────────────────────────
@app.route("/api/produits", methods=["GET"])
@role_required("admin", "caissiere")
def get_produits():
    conn = get_db()
    produits = conn.execute("""
        SELECT p.*, c.nom as categorie_nom 
        FROM produits p
        LEFT JOIN categories c ON p.categorie_id = c.id
        WHERE p.actif = 1
    """).fetchall()
    conn.close()
    return jsonify([dict(p) for p in produits])

@app.route("/api/produits", methods=["POST"])
@role_required("admin")
def add_produit():
    data = _request_payload()
    if not data.get("nom"):
        raise ValueError("Le nom du produit est requis.")
    conn = get_db()
    conn.execute("""
        INSERT INTO produits (nom, prix, stock, stock_alerte, categorie_id) 
        VALUES (?, ?, ?, ?, ?)
    """, (data["nom"], data["prix"], data.get("stock", 0),
          data.get("stock_alerte", 5), data.get("categorie_id")))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/produits/<int:id>", methods=["PUT"])
@role_required("admin")
def update_produit(id):
    data = _request_payload()
    if not data.get("nom"):
        raise ValueError("Le nom du produit est requis.")
    conn = get_db()
    conn.execute("""
        UPDATE produits SET nom=?, prix=?, stock=?, stock_alerte=?, categorie_id=?
        WHERE id=?
    """, (data["nom"], data["prix"], data.get("stock", 0),
          data.get("stock_alerte", 5), data.get("categorie_id"), id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/produits/<int:id>", methods=["DELETE"])
@role_required("admin")
def delete_produit(id):
    conn = get_db()
    conn.execute("UPDATE produits SET actif = 0 WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

# ─── API VENTES ──────────────────────────────────────────────
@app.route("/api/ventes", methods=["GET"])
@role_required("admin")
def get_ventes():
    conn = get_db()
    ventes = conn.execute("""
        SELECT * FROM ventes ORDER BY date_vente DESC LIMIT 50
    """).fetchall()
    conn.close()
    return jsonify([dict(v) for v in ventes])

@app.route("/api/ventes", methods=["POST"])
@role_required("admin", "caissiere")
def add_vente():
    data = _request_payload()
    items = data.get("items") or []
    if not items:
        raise ValueError("Aucun article dans la vente.")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ventes (total, paiement, monnaie) VALUES (?, ?, ?)
    """, (data["total"], data.get("paiement", "especes"), data.get("monnaie", 0)))
    vente_id = cursor.lastrowid
    for item in items:
        cursor.execute("""
            INSERT INTO vente_items (vente_id, produit_id, nom_produit, prix_unitaire, quantite, sous_total)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (vente_id, item["produit_id"], item["nom_produit"],
              item["prix_unitaire"], item["quantite"], item["sous_total"]))
        cursor.execute("""
            UPDATE produits SET stock = stock - ? WHERE id = ?
        """, (item["quantite"], item["produit_id"]))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "vente_id": vente_id})

# ─── API DASHBOARD ───────────────────────────────────────────
@app.route("/api/dashboard", methods=["GET"])
@role_required("admin")
def get_dashboard():
    conn = get_db()
    stats = conn.execute("""
        SELECT 
            COUNT(*) as nb_ventes,
            COALESCE(SUM(total), 0) as total_jour
        FROM ventes 
        WHERE date(date_vente) = date('now')
    """).fetchone()
    nb_produits = conn.execute("SELECT COUNT(*) as nb FROM produits WHERE actif=1").fetchone()
    alertes = conn.execute("""
        SELECT COUNT(*) as nb FROM produits 
        WHERE actif=1 AND stock <= stock_alerte
    """).fetchone()
    ventes_semaine = conn.execute("""
        SELECT date(date_vente) as jour, SUM(total) as total
        FROM ventes
        WHERE date_vente >= date('now', '-7 days')
        GROUP BY date(date_vente)
        ORDER BY jour
    """).fetchall()
    conn.close()
    return jsonify({
        "nb_ventes": stats["nb_ventes"],
        "total_jour": stats["total_jour"],
        "nb_produits": nb_produits["nb"],
        "alertes_stock": alertes["nb"],
        "ventes_semaine": [dict(v) for v in ventes_semaine]
    })


def _seed_catalog(conn):
    categories = [
        ("Alimentation", "#22c55e"),
        ("Boissons", "#3b82f6"),
        ("Entretien", "#f59e0b"),
        ("Cosmetiques", "#ec4899"),
        ("Divers", "#8b5cf6"),
    ]

    for nom, couleur in categories:
        conn.execute(
            """
            INSERT INTO categories (nom, couleur)
            SELECT ?, ?
            WHERE NOT EXISTS (SELECT 1 FROM categories WHERE nom = ?)
            """,
            (nom, couleur, nom),
        )

    cat_map = {
        row["nom"]: row["id"]
        for row in conn.execute("SELECT id, nom FROM categories").fetchall()
    }

    produits = [
        ("Riz 1kg", 700, 50, 10, "Alimentation"),
        ("Huile 1L", 1500, 30, 5, "Alimentation"),
        ("Sucre 1kg", 600, 40, 10, "Alimentation"),
        ("Lait en poudre 400g", 2200, 18, 4, "Alimentation"),
        ("Coca-Cola 50cl", 500, 60, 10, "Boissons"),
        ("Eau minerale 1.5L", 400, 80, 15, "Boissons"),
        ("Jus Tampico 1L", 800, 25, 5, "Boissons"),
        ("Cafe soluble 100g", 1800, 22, 6, "Boissons"),
        ("Savon OMO 500g", 1200, 20, 5, "Entretien"),
        ("Javel 1L", 600, 15, 3, "Entretien"),
        ("Eponge cuisine", 300, 45, 8, "Entretien"),
        ("Papier toilette x4", 1500, 28, 6, "Entretien"),
        ("Creme Nivea", 2500, 10, 3, "Cosmetiques"),
        ("Savon de toilette", 400, 35, 5, "Cosmetiques"),
        ("Shampoing 250ml", 2300, 14, 4, "Cosmetiques"),
        ("Dentifrice 120ml", 1200, 26, 6, "Cosmetiques"),
        ("Piles AA x2", 900, 16, 4, "Divers"),
        ("Bougie", 250, 70, 15, "Divers"),
        ("Allumettes", 100, 90, 20, "Divers"),
        ("Sacs plastiques x50", 1000, 24, 6, "Divers"),
    ]

    for nom, prix, stock, stock_alerte, cat_name in produits:
        conn.execute(
            """
            INSERT INTO produits (nom, prix, stock, stock_alerte, categorie_id, actif)
            SELECT ?, ?, ?, ?, ?, 1
            WHERE NOT EXISTS (SELECT 1 FROM produits WHERE nom = ?)
            """,
            (nom, prix, stock, stock_alerte, cat_map[cat_name], nom),
        )


def _seed_demo_sales(conn, nb_ventes=35, jours=14):
    produits = conn.execute(
        "SELECT id, nom, prix, stock FROM produits WHERE actif = 1"
    ).fetchall()

    stock_map = {p["id"]: p["stock"] for p in produits}
    product_by_id = {p["id"]: p for p in produits}
    product_ids = [p["id"] for p in produits]

    if not product_ids:
        return 0

    ventes_creees = 0
    for _ in range(nb_ventes):
        if not any(stock > 0 for stock in stock_map.values()):
            break

        random.shuffle(product_ids)
        nb_lignes = random.randint(1, 4)
        lines = []

        for pid in product_ids:
            if len(lines) >= nb_lignes:
                break

            available = stock_map[pid]
            if available <= 0:
                continue

            qte = random.randint(1, min(3, available))
            prod = product_by_id[pid]
            lines.append(
                {
                    "produit_id": pid,
                    "nom_produit": prod["nom"],
                    "prix_unitaire": prod["prix"],
                    "quantite": qte,
                    "sous_total": prod["prix"] * qte,
                }
            )

        if not lines:
            continue

        total = sum(l["sous_total"] for l in lines)
        paiement = random.choice(["especes", "mobile"])
        monnaie = 0
        if paiement == "especes":
            montant_recu = total + random.choice([0, 100, 200, 500, 1000])
            monnaie = montant_recu - total

        date_vente = datetime.now() - timedelta(
            days=random.randint(0, jours - 1),
            hours=random.randint(0, 10),
            minutes=random.randint(0, 59),
        )

        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO ventes (total, paiement, monnaie, date_vente)
            VALUES (?, ?, ?, ?)
            """,
            (total, paiement, monnaie, date_vente.strftime("%Y-%m-%d %H:%M:%S")),
        )
        vente_id = cur.lastrowid

        for line in lines:
            cur.execute(
                """
                INSERT INTO vente_items (vente_id, produit_id, nom_produit, prix_unitaire, quantite, sous_total)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    vente_id,
                    line["produit_id"],
                    line["nom_produit"],
                    line["prix_unitaire"],
                    line["quantite"],
                    line["sous_total"],
                ),
            )
            cur.execute(
                "UPDATE produits SET stock = stock - ? WHERE id = ?",
                (line["quantite"], line["produit_id"]),
            )
            stock_map[line["produit_id"]] -= line["quantite"]

        ventes_creees += 1

    return ventes_creees


def _reset_data(conn):
    conn.execute("DELETE FROM vente_items")
    conn.execute("DELETE FROM ventes")
    conn.execute("DELETE FROM produits")
    conn.execute("DELETE FROM categories")

    # Reset auto-increment counters for a clean training dataset.
    conn.execute(
        "DELETE FROM sqlite_sequence WHERE name IN ('categories', 'produits', 'ventes', 'vente_items')"
    )

# ─── API SEED ────────────────────────────────────────────────
@app.route("/api/seed", methods=["GET"])
@role_required("admin")
def seed():
    reset = request.args.get("reset") == "1"
    with_sales = request.args.get("with_sales") == "1"

    conn = get_db()
    if reset:
        _reset_data(conn)

    _seed_catalog(conn)
    ventes_creees = _seed_demo_sales(conn) if with_sales else 0

    conn.commit()

    stats = {
        "categories": conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0],
        "produits": conn.execute("SELECT COUNT(*) FROM produits WHERE actif = 1").fetchone()[0],
        "ventes": conn.execute("SELECT COUNT(*) FROM ventes").fetchone()[0],
    }
    conn.close()
    return jsonify(
        {
            "success": True,
            "message": "Pre-remplissage effectue.",
            "options": {"reset": reset, "with_sales": with_sales},
            "ventes_creees": ventes_creees,
            "stats": stats,
        }
    )


@app.route("/api/seed/demo", methods=["GET", "POST"])
@role_required("admin")
def seed_demo():
    if request.method == "GET":
        reset = request.args.get("reset", "1") == "1"
        with_sales = request.args.get("with_sales", "1") == "1"
        nb_ventes = int(request.args.get("nb_ventes", 35))
        jours = int(request.args.get("jours", 14))
    else:
        data = _request_payload() or {}
        reset = bool(data.get("reset", True))
        with_sales = bool(data.get("with_sales", True))
        nb_ventes = int(data.get("nb_ventes", 35))
        jours = int(data.get("jours", 14))

    nb_ventes = max(1, min(nb_ventes, 300))
    jours = max(1, min(jours, 60))

    conn = get_db()
    if reset:
        _reset_data(conn)

    _seed_catalog(conn)
    ventes_creees = _seed_demo_sales(conn, nb_ventes=nb_ventes, jours=jours) if with_sales else 0

    conn.commit()

    stats = {
        "categories": conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0],
        "produits": conn.execute("SELECT COUNT(*) FROM produits WHERE actif = 1").fetchone()[0],
        "ventes": conn.execute("SELECT COUNT(*) FROM ventes").fetchone()[0],
    }
    conn.close()

    return jsonify(
        {
            "success": True,
            "message": "Donnees fictives pre-remplies pour entrainement.",
            "options": {
                "reset": reset,
                "with_sales": with_sales,
                "nb_ventes": nb_ventes,
                "jours": jours,
            },
            "ventes_creees": ventes_creees,
            "stats": stats,
        }
    )

# ─── SERVERLESS/LOCAL ENTRYPOINT ─────────────────────────────
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"success": True, "status": "ok"})


init_db()
application = app


if __name__ == "__main__":
    app.run(debug=False, port=int(os.environ.get("PORT", "5000")))
