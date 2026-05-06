import os
from datetime import datetime

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_migrate import Migrate
from sqlalchemy import func

from models import db, Estatistica, Jogador, Partida, Time


def normalize_database_url(url):
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = normalize_database_url(
    os.environ.get("DATABASE_URL", "sqlite:///matchreport.db")
)
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "troque-esta-chave-no-render")

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Entre com a conta do time para continuar."


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Time, int(user_id))


@app.context_processor
def inject_team():
    return {"team_name": current_user.nome if current_user.is_authenticated else "MRG"}


with app.app_context():
    db.create_all()


def safe_int(value, default=0):
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


@app.route("/")
def index():
    return redirect(url_for("dashboard" if current_user.is_authenticated else "login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip().lower()
        password = request.form.get("password") or ""
        team = Time.query.filter_by(username=username).first()

        if team and team.check_password(password):
            login_user(team)
            return redirect(url_for("dashboard"))

        flash("Usuario ou senha invalidos.")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        nome = (request.form.get("nome_time") or "").strip()
        username = (request.form.get("username") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        if not nome:
            flash("Informe o nome do time.")
            return redirect(url_for("register"))
        if Time.query.filter_by(username=username).first():
            flash("Esse usuario ja existe.")
            return redirect(url_for("register"))
        if password != confirm_password:
            flash("As senhas nao coincidem.")
            return redirect(url_for("register"))
        if len(password) < 6:
            flash("A senha deve ter pelo menos 6 caracteres.")
            return redirect(url_for("register"))

        team = Time(nome=nome, username=username)
        team.set_password(password)
        db.session.add(team)
        db.session.commit()
        login_user(team)
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/plantel")
@login_required
def plantel():
    jogadores = (
        Jogador.query.filter_by(time_id=current_user.id)
        .order_by(Jogador.numero.asc().nullslast(), Jogador.nome_completo.asc())
        .all()
    )
    return render_template("plantel.html", jogadores=jogadores)


@app.route("/add_jogador", methods=["GET", "POST"])
@login_required
def add_jogador():
    if request.method == "POST":
        nome_completo = (request.form.get("nome_completo") or "").strip()
        apelido = (request.form.get("apelido") or "").strip() or None
        posicao = (request.form.get("posicao") or "").strip()
        data_entrada = request.form.get("data_entrada")

        if not nome_completo or not posicao or not data_entrada:
            flash("Preencha nome, posicao e data de entrada.")
            return redirect(url_for("add_jogador"))

        jogador = Jogador(
            time_id=current_user.id,
            nome_completo=nome_completo,
            apelido=apelido,
            idade=safe_int(request.form.get("idade"), None),
            posicao=posicao,
            numero=safe_int(request.form.get("numero"), None),
            data_entrada=datetime.strptime(data_entrada, "%Y-%m-%d").date(),
        )
        db.session.add(jogador)
        db.session.commit()
        return redirect(url_for("plantel"))

    return render_template("add_jogador.html")


@app.route("/delete_jogador/<int:jogador_id>", methods=["POST"])
@login_required
def delete_jogador(jogador_id):
    jogador = Jogador.query.filter_by(id=jogador_id, time_id=current_user.id).first_or_404()
    db.session.delete(jogador)
    db.session.commit()
    return redirect(url_for("plantel"))


@app.route("/sumula", methods=["GET", "POST"])
@login_required
def sumula():
    jogadores = (
        Jogador.query.filter_by(time_id=current_user.id)
        .order_by(Jogador.numero.asc().nullslast(), Jogador.nome_completo.asc())
        .all()
    )

    if request.method == "POST":
        if not jogadores:
            flash("Cadastre jogadores no plantel antes de salvar uma sumula.")
            return redirect(url_for("plantel"))

        data_partida = request.form.get("data_partida")
        partida = Partida(
            time_id=current_user.id,
            time_casa=(request.form.get("time_casa") or current_user.nome).strip(),
            time_adversario=(request.form.get("time_adversario") or "").strip(),
            data=datetime.strptime(data_partida, "%Y-%m-%d").date(),
            score_casa=safe_int(request.form.get("score_casa")),
            score_visitante=safe_int(request.form.get("score_visitante")),
        )
        db.session.add(partida)
        db.session.flush()

        for jogador in jogadores:
            estat = Estatistica(
                jogador_id=jogador.id,
                partida_id=partida.id,
                gol_marcado=safe_int(request.form.get(f"gol_marcado_{jogador.id}")),
                gol_sofrido=safe_int(request.form.get(f"gol_sofrido_{jogador.id}")),
                gol_contra=safe_int(request.form.get(f"gol_contra_{jogador.id}")),
                assistencia=safe_int(request.form.get(f"assistencia_{jogador.id}")),
                falta_feita=safe_int(request.form.get(f"falta_feita_{jogador.id}")),
                falta_sofrida=safe_int(request.form.get(f"falta_sofrida_{jogador.id}")),
                cartao_amarelo=safe_int(request.form.get(f"cartao_amarelo_{jogador.id}")),
                cartao_vermelho=safe_int(request.form.get(f"cartao_vermelho_{jogador.id}")),
            )
            db.session.add(estat)

        db.session.commit()
        return redirect(url_for("historico"))

    return render_template("sumula.html", jogadores=jogadores)


@app.route("/historico")
@login_required
def historico():
    partidas = (
        Partida.query.filter_by(time_id=current_user.id)
        .order_by(Partida.data.desc(), Partida.id.desc())
        .all()
    )
    return render_template("historico.html", partidas=partidas)


@app.route("/historico/<int:partida_id>")
@login_required
def partida_detalhe(partida_id):
    partida = Partida.query.filter_by(id=partida_id, time_id=current_user.id).first_or_404()
    estatisticas = (
        Estatistica.query.join(Jogador)
        .filter(Estatistica.partida_id == partida.id, Jogador.time_id == current_user.id)
        .order_by(Jogador.nome_completo.asc())
        .all()
    )
    return render_template("partida_detalhe.html", partida=partida, estatisticas=estatisticas)


@app.route("/api/dashboard")
@login_required
def api_dashboard():
    team_id = current_user.id
    base_query = db.session.query(Estatistica).join(Jogador).filter(Jogador.time_id == team_id)

    total_gols = base_query.with_entities(func.sum(Estatistica.gol_marcado)).scalar() or 0
    total_assists = base_query.with_entities(func.sum(Estatistica.assistencia)).scalar() or 0
    total_amarelos = base_query.with_entities(func.sum(Estatistica.cartao_amarelo)).scalar() or 0
    total_vermelhos = base_query.with_entities(func.sum(Estatistica.cartao_vermelho)).scalar() or 0
    total_partidas = Partida.query.filter_by(time_id=team_id).count()

    artilheiros_q = (
        db.session.query(
            Jogador.apelido,
            Jogador.nome_completo,
            func.sum(Estatistica.gol_marcado).label("gols"),
        )
        .join(Estatistica)
        .filter(Jogador.time_id == team_id)
        .group_by(Jogador.id)
        .order_by(func.sum(Estatistica.gol_marcado).desc())
        .limit(5)
        .all()
    )

    assists_q = (
        db.session.query(
            Jogador.apelido,
            Jogador.nome_completo,
            func.sum(Estatistica.assistencia).label("assists"),
        )
        .join(Estatistica)
        .filter(Jogador.time_id == team_id)
        .group_by(Jogador.id)
        .order_by(func.sum(Estatistica.assistencia).desc())
        .limit(5)
        .all()
    )

    cartoes_q = (
        db.session.query(
            Jogador.apelido,
            Jogador.nome_completo,
            func.sum(Estatistica.cartao_amarelo).label("amarelos"),
            func.sum(Estatistica.cartao_vermelho).label("vermelhos"),
        )
        .join(Estatistica)
        .filter(Jogador.time_id == team_id)
        .group_by(Jogador.id)
        .order_by(
            (
                func.sum(Estatistica.cartao_amarelo)
                + func.sum(Estatistica.cartao_vermelho)
            ).desc()
        )
        .limit(5)
        .all()
    )

    partidas_q = (
        Partida.query.filter_by(time_id=team_id)
        .order_by(Partida.data.desc(), Partida.id.desc())
        .limit(5)
        .all()
    )

    return jsonify(
        {
            "team_name": current_user.nome,
            "total_gols": int(total_gols),
            "total_assists": int(total_assists),
            "total_amarelos": int(total_amarelos),
            "total_vermelhos": int(total_vermelhos),
            "total_partidas": int(total_partidas),
            "artilheiros": [
                {"nome": r.apelido or r.nome_completo, "gols": int(r.gols or 0)}
                for r in artilheiros_q
            ],
            "assistencias": [
                {"nome": r.apelido or r.nome_completo, "assists": int(r.assists or 0)}
                for r in assists_q
            ],
            "cartoes": [
                {
                    "nome": r.apelido or r.nome_completo,
                    "amarelos": int(r.amarelos or 0),
                    "vermelhos": int(r.vermelhos or 0),
                }
                for r in cartoes_q
            ],
            "partidas": [
                {
                    "id": p.id,
                    "data": p.data.strftime("%d/%m/%Y"),
                    "time_casa": p.time_casa,
                    "time_adv": p.time_adversario,
                    "score_casa": p.score_casa,
                    "score_vis": p.score_visitante,
                }
                for p in partidas_q
            ],
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
