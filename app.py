from flask import Flask, render_template, jsonify, request, redirect, url_for, session, Response
import sqlite3
import os
import sys
import webbrowser
import threading
import random
import csv
import io
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash


def _resolve_paths():
    if getattr(sys, "frozen", False):
        runtime_dir = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        data_dir = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "DiandiShop"
        data_dir.mkdir(parents=True, exist_ok=True)
    else:
        runtime_dir = Path(__file__).resolve().parent
        # Sur Render, utiliser /tmp/ pour les données persistantes
        if os.environ.get("RENDER"):
            data_dir = Path("/tmp/diandishop_data")
            data_dir.mkdir(parents=True, exist_ok=True)
        else:
            data_dir = runtime_dir

    return runtime_dir, data_dir


RUNTIME_DIR, DATA_DIR = _resolve_paths()

app = Flask(
    __name__,
    template_folder=str(RUNTIME_DIR / "templates"),
    static_folder=str(RUNTIME_DIR / "static"),
)
DB_PATH = str(DATA_DIR / "diandishop.db")
app.secret_key = os.environ.get("SECRET_KEY", "diandishop-dev-secret")

# Code d'activation requis pour creer le tout premier compte admin.
# Definir la variable d'environnement SETUP_CODE pour personnaliser.
SETUP_CODE = os.environ.get("SETUP_CODE", "diandi2024")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                couleur TEXT DEFAULT '#22c55e'
            );

            CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                code_barres TEXT,
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
                mobile_operateur TEXT,
                mobile_reference TEXT,
                statut TEXT DEFAULT 'validee',
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

            CREATE TABLE IF NOT EXISTS fournisseurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                contact TEXT,
                telephone TEXT,
                email TEXT,
                adresse TEXT,
                actif INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS achats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fournisseur_id INTEGER,
                total REAL NOT NULL,
                reference TEXT,
                notes TEXT,
                user_id INTEGER,
                date_achat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (fournisseur_id) REFERENCES fournisseurs(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS achat_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                achat_id INTEGER NOT NULL,
                produit_id INTEGER,
                nom_produit TEXT NOT NULL,
                prix_achat REAL NOT NULL,
                quantite INTEGER NOT NULL,
                sous_total REAL NOT NULL,
                FOREIGN KEY (achat_id) REFERENCES achats(id),
                FOREIGN KEY (produit_id) REFERENCES produits(id)
            );

            CREATE TABLE IF NOT EXISTS depenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                libelle TEXT NOT NULL,
                montant REAL NOT NULL,
                categorie TEXT,
                notes TEXT,
                user_id INTEGER,
                date_depense TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS caisse_evenements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                evenement TEXT NOT NULL,
                vente_id INTEGER,
                montant REAL NOT NULL,
                paiement TEXT,
                operateur TEXT,
                reference TEXT,
                details TEXT,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vente_id) REFERENCES ventes(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS annulations_vente (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vente_id INTEGER NOT NULL,
                motif TEXT,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vente_id) REFERENCES ventes(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)

        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_produits_code_barres ON produits(code_barres) WHERE code_barres IS NOT NULL AND code_barres <> ''")

        existing_columns = {
            row["name"]
            for row in cursor.execute("PRAGMA table_info(produits)").fetchall()
        }
        if "code_barres" not in existing_columns:
            cursor.execute("ALTER TABLE produits ADD COLUMN code_barres TEXT")

        existing_sales_columns = {
            row["name"]
            for row in cursor.execute("PRAGMA table_info(ventes)").fetchall()
        }
        if "mobile_operateur" not in existing_sales_columns:
            cursor.execute("ALTER TABLE ventes ADD COLUMN mobile_operateur TEXT")
        if "mobile_reference" not in existing_sales_columns:
            cursor.execute("ALTER TABLE ventes ADD COLUMN mobile_reference TEXT")
        if "statut" not in existing_sales_columns:
            cursor.execute("ALTER TABLE ventes ADD COLUMN statut TEXT DEFAULT 'validee'")

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ventes_date_statut ON ventes(date_vente, statut)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_caisse_evenements_created_at ON caisse_evenements(created_at)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_achat_items_produit_id ON achat_items(produit_id)"
        )

        conn.commit()
        conn.close()
        print("✅ Base de données initialisée avec succès")
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données: {e}")
        raise


def _is_api_request():
    return request.path.startswith("/api/")


def _auth_error(message, status):
    if _is_api_request():
        return jsonify({"success": False, "message": message}), status
    return redirect(url_for("login"))


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


@app.context_processor
def inject_auth_context():
    return {
        "auth_user": session.get("user_nom"),
        "auth_role": session.get("user_role"),
        "is_admin": session.get("user_role") == "admin",
    }


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return _redirect_after_login()

    message = ""
    error = ""

    if request.method == "POST":
        username = (request.form.get("username") or "").strip().lower()
        password = request.form.get("password") or ""

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND actif = 1", (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["user_nom"] = user["nom"]
            session["username"] = user["username"]
            session["user_role"] = user["role"]
            return _redirect_after_login()

        error = "Identifiants invalides."

    return render_template("login.html", message=message, error=error)


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
        return redirect(url_for("login"))

    error = ""
    message = ""

    if request.method == "POST":
        nom = (request.form.get("nom") or "").strip()
        username = (request.form.get("username") or "").strip().lower()
        password = request.form.get("password") or ""

        if has_users:
            role = request.form.get("role") if request.form.get("role") in ("admin", "caissiere") else "caissiere"
        else:
            role = "admin"
            setup_code = (request.form.get("setup_code") or "").strip()
            if setup_code != SETUP_CODE:
                error = "Code d'activation incorrect. Contacte l'administrateur."
                conn.close()
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
                    session.clear()
                    session["user_id"] = user["id"]
                    session["user_nom"] = user["nom"]
                    session["username"] = user["username"]
                    session["user_role"] = user["role"]
                    conn.close()
                    return redirect(url_for("dashboard"))

                message = "Compte cree avec succes."

    conn.close()
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


@app.route("/rapport-journalier")
@role_required("admin")
def rapport_journalier():
    return render_template("rapport_journalier.html")


@app.route("/fournisseurs-achats")
@role_required("admin")
def fournisseurs_achats():
    return render_template("fournisseurs_achats.html")


@app.route("/caisse-historique")
@role_required("admin")
def caisse_historique():
    return render_template("caisse_historique.html")


@app.route("/dashboard-patron")
@role_required("admin")
def dashboard_patron():
    return render_template("dashboard_patron.html")

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
    data = request.json
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
    data = request.json
    code_barres = (data.get("code_barres") or "").strip()
    if code_barres == "":
        code_barres = None

    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO produits (nom, code_barres, prix, stock, stock_alerte, categorie_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (data["nom"], code_barres, data["prix"], data.get("stock", 0),
              data.get("stock_alerte", 5), data.get("categorie_id")))
        conn.commit()
        return jsonify({"success": True})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Ce code-barres existe deja."}), 400
    finally:
        conn.close()

@app.route("/api/produits/<int:id>", methods=["PUT"])
@role_required("admin")
def update_produit(id):
    data = request.json
    conn = get_db()
    existing = conn.execute("SELECT code_barres FROM produits WHERE id = ?", (id,)).fetchone()
    if not existing:
        conn.close()
        return jsonify({"success": False, "message": "Produit introuvable."}), 404

    if "code_barres" in data:
        code_barres = (data.get("code_barres") or "").strip() or None
    else:
        code_barres = existing["code_barres"]

    try:
        conn.execute("""
            UPDATE produits SET nom=?, code_barres=?, prix=?, stock=?, stock_alerte=?, categorie_id=?
            WHERE id=?
        """, (data["nom"], code_barres, data["prix"], data.get("stock", 0),
              data.get("stock_alerte", 5), data.get("categorie_id"), id))
        conn.commit()
        return jsonify({"success": True})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Ce code-barres existe deja."}), 400
    finally:
        conn.close()

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
        SELECT * FROM ventes ORDER BY date_vente DESC LIMIT 100
    """).fetchall()
    conn.close()
    return jsonify([dict(v) for v in ventes])


@app.route("/api/caisse/historique", methods=["GET"])
@role_required("admin")
def get_caisse_historique():
    date_debut = (request.args.get("date_debut") or "").strip()
    date_fin = (request.args.get("date_fin") or "").strip()
    if not date_debut:
        date_debut = datetime.now().strftime("%Y-%m-%d")
    if not date_fin:
        date_fin = date_debut

    conn = get_db()
    events = conn.execute(
        """
        SELECT
            ce.id,
            ce.type,
            ce.evenement,
            ce.vente_id,
            ce.montant,
            ce.paiement,
            ce.operateur,
            ce.reference,
            ce.details,
            ce.created_at,
            u.nom as utilisateur
        FROM caisse_evenements ce
        LEFT JOIN users u ON u.id = ce.user_id
        WHERE date(ce.created_at) BETWEEN ? AND ?
        ORDER BY ce.created_at DESC
        """,
        (date_debut, date_fin),
    ).fetchall()
    conn.close()

    return jsonify({"success": True, "events": [dict(e) for e in events]})


@app.route("/api/ventes/<int:vente_id>/ticket", methods=["GET"])
@role_required("admin", "caissiere")
def get_vente_ticket(vente_id):
    conn = get_db()
    vente = conn.execute(
        """
        SELECT id, total, paiement, mobile_operateur, mobile_reference, monnaie, date_vente
        FROM ventes
        WHERE id = ?
        """,
        (vente_id,),
    ).fetchone()

    if not vente:
        conn.close()
        return jsonify({"success": False, "message": "Vente introuvable."}), 404

    items = conn.execute(
        """
        SELECT nom_produit, prix_unitaire, quantite, sous_total
        FROM vente_items
        WHERE vente_id = ?
        ORDER BY id ASC
        """,
        (vente_id,),
    ).fetchall()
    conn.close()

    return jsonify(
        {
            "success": True,
            "vente": dict(vente),
            "items": [dict(i) for i in items],
        }
    )

@app.route("/api/ventes", methods=["POST"])
@role_required("admin", "caissiere")
def add_vente():
    data = request.json
    mobile_operateur = None
    mobile_reference = None

    if data.get("paiement") == "mobile":
        operateurs_valides = {"orange", "mtn", "moov"}
        mobile_operateur = (data.get("mobile_operateur") or "").strip().lower()
        mobile_reference = (data.get("mobile_reference") or "").strip()
        if mobile_operateur not in operateurs_valides:
            return jsonify({"success": False, "message": "Operateur Mobile Money invalide."}), 400
        if mobile_reference == "":
            mobile_reference = None

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ventes (total, paiement, mobile_operateur, mobile_reference, statut, monnaie) VALUES (?, ?, ?, ?, 'validee', ?)
    """, (data["total"], data.get("paiement", "especes"), mobile_operateur, mobile_reference, data.get("monnaie", 0)))
    vente_id = cursor.lastrowid
    for item in data["items"]:
        cursor.execute("""
            INSERT INTO vente_items (vente_id, produit_id, nom_produit, prix_unitaire, quantite, sous_total)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (vente_id, item["produit_id"], item["nom_produit"],
              item["prix_unitaire"], item["quantite"], item["sous_total"]))
        cursor.execute("""
            UPDATE produits SET stock = stock - ? WHERE id = ?
        """, (item["quantite"], item["produit_id"]))

    cursor.execute(
        """
        INSERT INTO caisse_evenements (type, evenement, vente_id, montant, paiement, operateur, reference, details, user_id)
        VALUES ('entree', 'vente', ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            vente_id,
            data["total"],
            data.get("paiement", "especes"),
            mobile_operateur,
            mobile_reference,
            f"Vente de {len(data['items'])} ligne(s)",
            session.get("user_id"),
        ),
    )

    conn.commit()

    created = conn.execute(
        "SELECT id, date_vente FROM ventes WHERE id = ?",
        (vente_id,),
    ).fetchone()

    conn.close()
    return jsonify(
        {
            "success": True,
            "vente_id": vente_id,
            "date_vente": created["date_vente"] if created else None,
        }
    )


@app.route("/api/ventes/<int:vente_id>/annuler", methods=["POST"])
@role_required("admin")
def annuler_vente(vente_id):
    data = request.json or {}
    motif = (data.get("motif") or "").strip() or "Annulation manuelle"

    conn = get_db()
    vente = conn.execute(
        "SELECT * FROM ventes WHERE id = ?",
        (vente_id,),
    ).fetchone()

    if not vente:
        conn.close()
        return jsonify({"success": False, "message": "Vente introuvable."}), 404

    if vente["statut"] == "annulee":
        conn.close()
        return jsonify({"success": False, "message": "Cette vente est deja annulee."}), 400

    items = conn.execute(
        "SELECT produit_id, quantite FROM vente_items WHERE vente_id = ?",
        (vente_id,),
    ).fetchall()

    for item in items:
        conn.execute(
            "UPDATE produits SET stock = stock + ? WHERE id = ?",
            (item["quantite"], item["produit_id"]),
        )

    conn.execute(
        "UPDATE ventes SET statut = 'annulee' WHERE id = ?",
        (vente_id,),
    )
    conn.execute(
        "INSERT INTO annulations_vente (vente_id, motif, user_id) VALUES (?, ?, ?)",
        (vente_id, motif, session.get("user_id")),
    )
    conn.execute(
        """
        INSERT INTO caisse_evenements (type, evenement, vente_id, montant, paiement, operateur, reference, details, user_id)
        VALUES ('sortie', 'annulation', ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            vente_id,
            vente["total"],
            vente["paiement"],
            vente["mobile_operateur"],
            vente["mobile_reference"],
            motif,
            session.get("user_id"),
        ),
    )

    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Vente annulee."})

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
          AND statut = 'validee'
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
          AND statut = 'validee'
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


@app.route("/api/rapport/journalier", methods=["GET"])
@role_required("admin")
def get_rapport_journalier():
    date_param = (request.args.get("date") or "").strip()
    if not date_param:
        date_param = datetime.now().strftime("%Y-%m-%d")

    conn = get_db()

    stats = conn.execute(
        """
        SELECT
            COUNT(*) as nb_ventes,
            COALESCE(SUM(total), 0) as total_jour,
            COALESCE(SUM(CASE WHEN paiement = 'mobile' THEN total ELSE 0 END), 0) as total_mobile,
            COALESCE(SUM(CASE WHEN paiement = 'especes' THEN total ELSE 0 END), 0) as total_especes
        FROM ventes
        WHERE date(date_vente) = ?
                    AND statut = 'validee'
        """,
        (date_param,),
    ).fetchone()

    repartition_mobile = conn.execute(
        """
        SELECT
            COALESCE(mobile_operateur, 'inconnu') as operateur,
            COUNT(*) as nb,
            COALESCE(SUM(total), 0) as total
        FROM ventes
        WHERE date(date_vente) = ?
          AND paiement = 'mobile'
                    AND statut = 'validee'
        GROUP BY COALESCE(mobile_operateur, 'inconnu')
        """,
        (date_param,),
    ).fetchall()

    ventes = conn.execute(
        """
        SELECT
            v.id,
            v.total,
            v.paiement,
            v.mobile_operateur,
            v.mobile_reference,
            v.monnaie,
            v.date_vente,
            COALESCE(SUM(vi.quantite), 0) as total_articles
        FROM ventes v
        LEFT JOIN vente_items vi ON vi.vente_id = v.id
        WHERE date(v.date_vente) = ?
                    AND v.statut = 'validee'
        GROUP BY v.id
        ORDER BY v.date_vente DESC
        """,
        (date_param,),
    ).fetchall()

    top_produits = conn.execute(
        """
        SELECT
            vi.nom_produit,
            SUM(vi.quantite) as quantite,
            SUM(vi.sous_total) as montant
        FROM vente_items vi
        JOIN ventes v ON v.id = vi.vente_id
        WHERE date(v.date_vente) = ?
                    AND v.statut = 'validee'
        GROUP BY vi.nom_produit
        ORDER BY quantite DESC
        LIMIT 5
        """,
        (date_param,),
    ).fetchall()

    conn.close()

    return jsonify(
        {
            "success": True,
            "date": date_param,
            "stats": dict(stats),
            "repartition_mobile": [dict(r) for r in repartition_mobile],
            "ventes": [dict(v) for v in ventes],
            "top_produits": [dict(t) for t in top_produits],
        }
    )


# ─── API FOURNISSEURS & ACHATS ────────────────────────────
@app.route("/api/fournisseurs", methods=["GET"])
@role_required("admin")
def get_fournisseurs():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM fournisseurs WHERE actif = 1 ORDER BY nom ASC"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/fournisseurs", methods=["POST"])
@role_required("admin")
def add_fournisseur():
    data = request.json or {}
    nom = (data.get("nom") or "").strip()
    if not nom:
        return jsonify({"success": False, "message": "Nom fournisseur requis."}), 400

    conn = get_db()
    conn.execute(
        """
        INSERT INTO fournisseurs (nom, contact, telephone, email, adresse)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            nom,
            (data.get("contact") or "").strip() or None,
            (data.get("telephone") or "").strip() or None,
            (data.get("email") or "").strip() or None,
            (data.get("adresse") or "").strip() or None,
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/fournisseurs/<int:fournisseur_id>", methods=["PUT"])
@role_required("admin")
def update_fournisseur(fournisseur_id):
    data = request.json or {}
    nom = (data.get("nom") or "").strip()
    if not nom:
        return jsonify({"success": False, "message": "Nom fournisseur requis."}), 400

    conn = get_db()
    conn.execute(
        """
        UPDATE fournisseurs
        SET nom = ?, contact = ?, telephone = ?, email = ?, adresse = ?
        WHERE id = ?
        """,
        (
            nom,
            (data.get("contact") or "").strip() or None,
            (data.get("telephone") or "").strip() or None,
            (data.get("email") or "").strip() or None,
            (data.get("adresse") or "").strip() or None,
            fournisseur_id,
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/fournisseurs/<int:fournisseur_id>", methods=["DELETE"])
@role_required("admin")
def delete_fournisseur(fournisseur_id):
    conn = get_db()
    conn.execute("UPDATE fournisseurs SET actif = 0 WHERE id = ?", (fournisseur_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/achats", methods=["GET"])
@role_required("admin")
def get_achats():
    date_debut = (request.args.get("date_debut") or "").strip()
    date_fin = (request.args.get("date_fin") or "").strip()
    query = """
        SELECT a.*, f.nom as fournisseur_nom, u.nom as utilisateur_nom,
               COALESCE(SUM(ai.quantite), 0) as total_articles
        FROM achats a
        LEFT JOIN fournisseurs f ON f.id = a.fournisseur_id
        LEFT JOIN users u ON u.id = a.user_id
        LEFT JOIN achat_items ai ON ai.achat_id = a.id
    """
    params = []
    if date_debut and date_fin:
        query += " WHERE date(a.date_achat) BETWEEN ? AND ? "
        params.extend([date_debut, date_fin])
    query += " GROUP BY a.id ORDER BY a.date_achat DESC LIMIT 200"

    conn = get_db()
    rows = conn.execute(query, tuple(params)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/achats", methods=["POST"])
@role_required("admin")
def add_achat():
    data = request.json or {}
    items = data.get("items") or []
    if not items:
        return jsonify({"success": False, "message": "Ajout d'au moins une ligne requis."}), 400

    conn = get_db()
    cur = conn.cursor()
    total = 0
    normalized = []

    for item in items:
        produit_id = item.get("produit_id")
        quantite = int(item.get("quantite") or 0)
        prix_achat = float(item.get("prix_achat") or 0)
        if not produit_id or quantite <= 0 or prix_achat <= 0:
            conn.close()
            return jsonify({"success": False, "message": "Lignes d'achat invalides."}), 400

        produit = conn.execute(
            "SELECT id, nom FROM produits WHERE id = ? AND actif = 1",
            (produit_id,),
        ).fetchone()
        if not produit:
            conn.close()
            return jsonify({"success": False, "message": "Produit introuvable dans un achat."}), 404

        sous_total = quantite * prix_achat
        total += sous_total
        normalized.append(
            {
                "produit_id": produit_id,
                "nom_produit": produit["nom"],
                "quantite": quantite,
                "prix_achat": prix_achat,
                "sous_total": sous_total,
            }
        )

    cur.execute(
        """
        INSERT INTO achats (fournisseur_id, total, reference, notes, user_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            data.get("fournisseur_id"),
            total,
            (data.get("reference") or "").strip() or None,
            (data.get("notes") or "").strip() or None,
            session.get("user_id"),
        ),
    )
    achat_id = cur.lastrowid

    for line in normalized:
        cur.execute(
            """
            INSERT INTO achat_items (achat_id, produit_id, nom_produit, prix_achat, quantite, sous_total)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                achat_id,
                line["produit_id"],
                line["nom_produit"],
                line["prix_achat"],
                line["quantite"],
                line["sous_total"],
            ),
        )
        cur.execute(
            "UPDATE produits SET stock = stock + ? WHERE id = ?",
            (line["quantite"], line["produit_id"]),
        )

    cur.execute(
        """
        INSERT INTO caisse_evenements (type, evenement, montant, details, user_id)
        VALUES ('sortie', 'achat', ?, ?, ?)
        """,
        (
            total,
            f"Achat fournisseur ref {(data.get('reference') or '').strip() or '-'}",
            session.get("user_id"),
        ),
    )

    conn.commit()
    conn.close()
    return jsonify({"success": True, "achat_id": achat_id})


@app.route("/api/depenses", methods=["GET"])
@role_required("admin")
def get_depenses():
    date_debut = (request.args.get("date_debut") or "").strip()
    date_fin = (request.args.get("date_fin") or "").strip()
    query = """
        SELECT d.*, u.nom as utilisateur_nom
        FROM depenses d
        LEFT JOIN users u ON u.id = d.user_id
    """
    params = []
    if date_debut and date_fin:
        query += " WHERE date(d.date_depense) BETWEEN ? AND ? "
        params.extend([date_debut, date_fin])
    query += " ORDER BY d.date_depense DESC LIMIT 200"

    conn = get_db()
    rows = conn.execute(query, tuple(params)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/depenses", methods=["POST"])
@role_required("admin")
def add_depense():
    data = request.json or {}
    libelle = (data.get("libelle") or "").strip()
    montant = float(data.get("montant") or 0)
    if not libelle or montant <= 0:
        return jsonify({"success": False, "message": "Depense invalide."}), 400

    conn = get_db()
    conn.execute(
        """
        INSERT INTO depenses (libelle, montant, categorie, notes, user_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            libelle,
            montant,
            (data.get("categorie") or "").strip() or None,
            (data.get("notes") or "").strip() or None,
            session.get("user_id"),
        ),
    )
    conn.execute(
        """
        INSERT INTO caisse_evenements (type, evenement, montant, details, user_id)
        VALUES ('sortie', 'depense', ?, ?, ?)
        """,
        (montant, libelle, session.get("user_id")),
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/stock/alertes", methods=["GET"])
@role_required("admin")
def get_stock_alertes_intelligentes():
    conn = get_db()

    ruptures = conn.execute(
        """
        SELECT id, nom, stock, stock_alerte FROM produits
        WHERE actif = 1 AND stock <= 0
        ORDER BY nom
        """
    ).fetchall()

    stock_bas = conn.execute(
        """
        SELECT id, nom, stock, stock_alerte FROM produits
        WHERE actif = 1 AND stock > 0 AND stock <= stock_alerte
        ORDER BY stock ASC
        """
    ).fetchall()

    fast_movers = conn.execute(
        """
        SELECT
            p.id,
            p.nom,
            p.stock,
            p.stock_alerte,
            COALESCE(SUM(vi.quantite), 0) as qte_7j,
            ROUND(COALESCE(SUM(vi.quantite), 0) / 7.0, 2) as moyenne_jour
        FROM produits p
        LEFT JOIN vente_items vi ON vi.produit_id = p.id
        LEFT JOIN ventes v ON v.id = vi.vente_id
            AND v.statut = 'validee'
            AND v.date_vente >= date('now', '-7 days')
        WHERE p.actif = 1
        GROUP BY p.id
        HAVING qte_7j > 0
        ORDER BY qte_7j DESC
        LIMIT 12
        """
    ).fetchall()

    suggestions = []
    for row in fast_movers:
        stock_cible = int(round(row["moyenne_jour"] * 10))
        a_commander = max(0, stock_cible - row["stock"])
        if a_commander > 0:
            suggestions.append(
                {
                    "id": row["id"],
                    "nom": row["nom"],
                    "stock": row["stock"],
                    "moyenne_jour": row["moyenne_jour"],
                    "a_commander": a_commander,
                }
            )

    conn.close()
    return jsonify(
        {
            "success": True,
            "ruptures": [dict(r) for r in ruptures],
            "stock_bas": [dict(r) for r in stock_bas],
            "fast_movers": [dict(r) for r in fast_movers],
            "suggestions": suggestions,
        }
    )


@app.route("/api/dashboard/patron", methods=["GET"])
@role_required("admin")
def get_dashboard_patron():
    date_fin = (request.args.get("date_fin") or "").strip() or datetime.now().strftime("%Y-%m-%d")
    date_debut = (request.args.get("date_debut") or "").strip()
    if not date_debut:
        date_debut = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    conn = get_db()

    ca = conn.execute(
        """
        SELECT COALESCE(SUM(total), 0) as total
        FROM ventes
        WHERE date(date_vente) BETWEEN ? AND ?
          AND statut = 'validee'
        """,
        (date_debut, date_fin),
    ).fetchone()["total"]

    depenses = conn.execute(
        """
        SELECT COALESCE(SUM(montant), 0) as total
        FROM depenses
        WHERE date(date_depense) BETWEEN ? AND ?
        """,
        (date_debut, date_fin),
    ).fetchone()["total"]

    achats = conn.execute(
        """
        SELECT COALESCE(SUM(total), 0) as total
        FROM achats
        WHERE date(date_achat) BETWEEN ? AND ?
        """,
        (date_debut, date_fin),
    ).fetchone()["total"]

    paiements = conn.execute(
        """
        SELECT paiement, COUNT(*) as nb, COALESCE(SUM(total), 0) as total
        FROM ventes
        WHERE date(date_vente) BETWEEN ? AND ?
          AND statut = 'validee'
        GROUP BY paiement
        """,
        (date_debut, date_fin),
    ).fetchall()

    ventes_par_caissier = conn.execute(
        """
        SELECT u.nom as caissier, COUNT(*) as nb, COALESCE(SUM(ce.montant), 0) as total
        FROM caisse_evenements ce
        LEFT JOIN users u ON u.id = ce.user_id
        WHERE ce.evenement = 'vente'
          AND date(ce.created_at) BETWEEN ? AND ?
        GROUP BY ce.user_id
        ORDER BY total DESC
        """,
        (date_debut, date_fin),
    ).fetchall()

    heures_pic = conn.execute(
        """
        SELECT strftime('%H', date_vente) as heure, COUNT(*) as nb
        FROM ventes
        WHERE date(date_vente) BETWEEN ? AND ?
          AND statut = 'validee'
        GROUP BY strftime('%H', date_vente)
        ORDER BY nb DESC
        LIMIT 5
        """,
        (date_debut, date_fin),
    ).fetchall()

    top_rentables = conn.execute(
        """
        SELECT
            vi.nom_produit,
            SUM(vi.quantite) as quantite,
            SUM(vi.sous_total) as chiffre,
            ROUND(
                SUM(
                    vi.sous_total - (COALESCE(c.cout_moyen, vi.prix_unitaire * 0.7) * vi.quantite)
                ),
                2
            ) as marge_estimee
        FROM vente_items vi
        JOIN ventes v ON v.id = vi.vente_id
        LEFT JOIN (
            SELECT produit_id, AVG(prix_achat) as cout_moyen
            FROM achat_items
            GROUP BY produit_id
        ) c ON c.produit_id = vi.produit_id
        WHERE date(v.date_vente) BETWEEN ? AND ?
          AND v.statut = 'validee'
        GROUP BY vi.nom_produit
        ORDER BY marge_estimee DESC
        LIMIT 8
        """,
        (date_debut, date_fin),
    ).fetchall()

    conn.close()

    benefice_net = ca - depenses - achats
    return jsonify(
        {
            "success": True,
            "periode": {"date_debut": date_debut, "date_fin": date_fin},
            "kpis": {
                "ca": ca,
                "depenses": depenses,
                "achats": achats,
                "benefice_net": benefice_net,
            },
            "paiements": [dict(r) for r in paiements],
            "ventes_par_caissier": [dict(r) for r in ventes_par_caissier],
            "heures_pic": [dict(r) for r in heures_pic],
            "top_rentables": [dict(r) for r in top_rentables],
        }
    )


def _csv_response(filename, headers, rows):
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    content = stream.getvalue()
    stream.close()
    return Response(
        content,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.route("/api/export/ventes.csv", methods=["GET"])
@role_required("admin")
def export_ventes_csv():
    conn = get_db()
    rows = conn.execute(
        """
        SELECT id, date_vente, statut, paiement, mobile_operateur, mobile_reference, total, monnaie
        FROM ventes
        ORDER BY date_vente DESC
        LIMIT 2000
        """
    ).fetchall()
    conn.close()
    data = [
        [
            r["id"],
            r["date_vente"],
            r["statut"],
            r["paiement"],
            r["mobile_operateur"] or "",
            r["mobile_reference"] or "",
            r["total"],
            r["monnaie"],
        ]
        for r in rows
    ]
    return _csv_response(
        "ventes_diandishop.csv",
        ["id", "date_vente", "statut", "paiement", "operateur", "reference", "total", "monnaie"],
        data,
    )


@app.route("/api/export/achats.csv", methods=["GET"])
@role_required("admin")
def export_achats_csv():
    conn = get_db()
    rows = conn.execute(
        """
        SELECT a.id, a.date_achat, COALESCE(f.nom, '-') as fournisseur, a.reference, a.total
        FROM achats a
        LEFT JOIN fournisseurs f ON f.id = a.fournisseur_id
        ORDER BY a.date_achat DESC
        LIMIT 2000
        """
    ).fetchall()
    conn.close()
    data = [[r["id"], r["date_achat"], r["fournisseur"], r["reference"] or "", r["total"]] for r in rows]
    return _csv_response(
        "achats_diandishop.csv",
        ["id", "date_achat", "fournisseur", "reference", "total"],
        data,
    )


def _seed_catalog(conn):
    categories = [
        ("Alimentation", "#22c55e"),
        ("Boissons", "#3b82f6"),
        ("Entretien", "#f59e0b"),
        ("Cosmetiques", "#ec4899"),
        ("Electronique", "#8b5cf6"),
        ("Vetements", "#f97316"),
        ("Accessoires", "#06b6d4"),
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

    # 80 produits fictifs adaptés à Abidjan Yopougon
    produits = [
        # Alimentation (20 produits)
        ("Riz Wita 1kg", 800, 100, 10, "Alimentation"),
        ("Riz Wita 5kg", 3500, 50, 5, "Alimentation"),
        ("Huile Fryna 1L", 1200, 80, 10, "Alimentation"),
        ("Huile Fryna 5L", 5500, 30, 5, "Alimentation"),
        ("Sucre roux 1kg", 700, 100, 10, "Alimentation"),
        ("Sucre blanc 1kg", 750, 90, 10, "Alimentation"),
        ("Lait Nido 400g", 2200, 60, 8, "Alimentation"),
        ("Lait Nido 900g", 4500, 30, 5, "Alimentation"),
        ("Farine de blé 1kg", 600, 80, 10, "Alimentation"),
        ("Farine de maïs 1kg", 550, 85, 10, "Alimentation"),
        ("Poudre de tomate 200g", 800, 70, 8, "Alimentation"),
        ("Sel iodé 1kg", 400, 120, 15, "Alimentation"),
        ("Poisson sec 1kg", 2500, 20, 3, "Alimentation"),
        ("Œuf frais (12)", 3500, 40, 5, "Alimentation"),
        ("Beurre de karité 500g", 2000, 25, 4, "Alimentation"),
        ("Arachides grillées 1kg", 1500, 60, 8, "Alimentation"),
        ("Pâtes italiennes 500g", 700, 100, 10, "Alimentation"),
        ("Piment rouge poudre 100g", 900, 50, 6, "Alimentation"),
        ("Miel naturel 500ml", 3500, 20, 3, "Alimentation"),
        ("Noix de coco râpée 500g", 1800, 30, 5, "Alimentation"),

        # Boissons (15 produits)
        ("Coca-Cola 50cl", 600, 200, 20, "Boissons"),
        ("Fanta Orange 50cl", 550, 180, 20, "Boissons"),
        ("Sprite 50cl", 550, 180, 20, "Boissons"),
        ("Eau minérale 1.5L", 500, 300, 30, "Boissons"),
        ("Eau minérale 0.5L", 200, 400, 40, "Boissons"),
        ("Jus Tampico 1L", 1000, 100, 10, "Boissons"),
        ("Jus Frais Orange 1L", 1200, 80, 10, "Boissons"),
        ("Café soluble Nescafé 100g", 2200, 40, 5, "Boissons"),
        ("Café moulu 500g", 3500, 30, 4, "Boissons"),
        ("Thé en sachets 25", 1200, 60, 8, "Boissons"),
        ("Lait concentré Carnation 397g", 1200, 50, 6, "Boissons"),
        ("Boisson Gatorade 500ml", 800, 60, 8, "Boissons"),
        ("Vin rouge 750ml", 2500, 20, 3, "Boissons"),
        ("Bière 33cl", 600, 100, 10, "Boissons"),
        ("Whisky 500ml", 5000, 15, 2, "Boissons"),

        # Entretien (15 produits)
        ("Savon OMO 500g", 1200, 100, 10, "Entretien"),
        ("Lessive OMO 500ml", 1800, 80, 10, "Entretien"),
        ("Javel 1L", 700, 120, 15, "Entretien"),
        ("Désinfectant 1L", 1500, 60, 8, "Entretien"),
        ("Éponge cuisine", 400, 150, 20, "Entretien"),
        ("Balai plastique", 1200, 40, 5, "Entretien"),
        ("Pelle poussière", 900, 35, 5, "Entretien"),
        ("Papier toilette x4", 1800, 200, 25, "Entretien"),
        ("Papier essuie-tout", 1500, 180, 20, "Entretien"),
        ("Mouchoirs 50", 800, 100, 10, "Entretien"),
        ("Savon liquide main 500ml", 1200, 60, 8, "Entretien"),
        ("Shampoing cheveux 500ml", 2200, 40, 5, "Entretien"),
        ("Dentifrice 120ml", 1300, 80, 10, "Entretien"),
        ("Déodorant spray 200ml", 1500, 50, 6, "Entretien"),
        ("Brosserie nylon", 600, 100, 12, "Entretien"),

        # Cosmétiques (12 produits)
        ("Crème visage Nivea 50ml", 2800, 35, 4, "Cosmetiques"),
        ("Crème mains Nivea 75ml", 2000, 45, 5, "Cosmetiques"),
        ("Savon beauté 100g", 800, 100, 12, "Cosmetiques"),
        ("Gel douche Duru 500ml", 1800, 50, 6, "Cosmetiques"),
        ("Lotion corporelle 500ml", 2200, 40, 5, "Cosmetiques"),
        ("Rouge à lèvres Maybelline", 3500, 20, 3, "Cosmetiques"),
        ("Mascara Black 7ml", 3000, 25, 3, "Cosmetiques"),
        ("Eyeliner liquide 5ml", 2500, 30, 4, "Cosmetiques"),
        ("Fond de teint 30ml", 4000, 20, 2, "Cosmetiques"),
        ("Poudre compacte 12g", 3500, 25, 3, "Cosmetiques"),
        ("Huile de coco 500ml", 2500, 35, 4, "Cosmetiques"),
        ("Sérum visage 30ml", 5000, 15, 2, "Cosmetiques"),

        # Electronique (10 produits)
        ("Ampoule LED 9W", 2500, 100, 10, "Electronique"),
        ("Piles AA (2)", 1200, 150, 20, "Electronique"),
        ("Piles AAA (2)", 1000, 150, 20, "Electronique"),
        ("Batterie de secours 10000mAh", 8000, 30, 4, "Electronique"),
        ("Chargeur USB 2.1A", 4500, 40, 5, "Electronique"),
        ("Câble USB type C", 2500, 60, 8, "Electronique"),
        ("Adaptateur électrique USB", 3500, 50, 6, "Electronique"),
        ("Lampe torche LED", 5000, 25, 3, "Electronique"),
        ("Radio FM portable", 7500, 15, 2, "Electronique"),
        ("Enceinte Bluetooth", 12000, 10, 1, "Electronique"),

        # Vêtements (6 produits)
        ("T-shirt coton XL", 3500, 80, 10, "Vetements"),
        ("Chemise homme M", 8000, 40, 5, "Vetements"),
        ("Pantalon jeans 34", 12000, 35, 4, "Vetements"),
        ("Short coton L", 5000, 50, 6, "Vetements"),
        ("Chaussettes x3", 2000, 100, 12, "Vetements"),
        ("Ceinture cuir", 4500, 60, 8, "Vetements"),

        # Accessoires (2 produits)
        ("Clé USB 32GB", 8000, 20, 3, "Accessoires"),
        ("Montre digitale", 15000, 15, 2, "Accessoires"),
    ]

    for idx, item in enumerate(produits, start=1):
        if len(item) == 6:
            nom, code_barres, prix, stock, stock_alerte, cat_name = item
        else:
            nom, prix, stock, stock_alerte, cat_name = item
            code_barres = f"618{idx:010d}"

        conn.execute(
            """
            INSERT INTO produits (nom, code_barres, prix, stock, stock_alerte, categorie_id, actif)
            SELECT ?, ?, ?, ?, ?, ?, 1
            WHERE NOT EXISTS (SELECT 1 FROM produits WHERE nom = ?)
            """,
            (nom, code_barres, prix, stock, stock_alerte, cat_map[cat_name], nom),
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
    conn.execute("DELETE FROM annulations_vente")
    conn.execute("DELETE FROM caisse_evenements")
    conn.execute("DELETE FROM achat_items")
    conn.execute("DELETE FROM achats")
    conn.execute("DELETE FROM depenses")
    conn.execute("DELETE FROM fournisseurs")
    conn.execute("DELETE FROM vente_items")
    conn.execute("DELETE FROM ventes")
    conn.execute("DELETE FROM produits")
    conn.execute("DELETE FROM categories")

    # Reset auto-increment counters for a clean training dataset.
    conn.execute(
        "DELETE FROM sqlite_sequence WHERE name IN ('categories', 'produits', 'ventes', 'vente_items', 'fournisseurs', 'achats', 'achat_items', 'depenses', 'caisse_evenements', 'annulations_vente')"
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
        data = request.json or {}
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

# ─── INITIALISATION AUTOMATIQUE ─────────────────────────────
# Initialiser la base de données au démarrage (inclus pour Gunicorn)
init_db()

# ─── LANCEMENT ───────────────────────────────────────────────
def open_browser():
    webbrowser.open("http://localhost:5000")

if __name__ == "__main__":
    threading.Timer(1.5, open_browser).start()
    app.run(debug=False, port=5000)
