from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import re
import os
from models import db, Jogador, Partida, Estatistica
from flask_migrate import Migrate
from datetime import datetime
from functools import wraps
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from sqlalchemy import func
#def ensure_partida_columns(engine):
#    """Ensure the partida table has the new columns added to the model.
#    Use the provided SQLAlchemy engine to operate on the same DB file the app uses.
#    This is best-effort and will not raise on failure.
#    """
#    try:
#        conn = engine.raw_connection()
#        cur = conn.cursor()
#        cur.execute("PRAGMA table_info(partida)")
#        existing = [r[1] for r in cur.fetchall()]
#        alters = []
#        if 'time_casa' not in existing:
#            alters.append("ALTER TABLE partida ADD COLUMN time_casa VARCHAR(100)")
#        if 'score_casa' not in existing:
#            alters.append("ALTER TABLE partida ADD COLUMN score_casa INTEGER DEFAULT 0")
#        if 'score_visitante' not in existing:
#            alters.append("ALTER TABLE partida ADD COLUMN score_visitante INTEGER DEFAULT 0")
#        for sql in alters:
#            try:
#                cur.execute(sql)
#            except Exception:
#                # best-effort: if one ALTER fails, continue with others
#                pass
#        if alters:
#            conn.commit()
#    except Exception:
#        # don't crash the app here; migrations can be handled via Flask-Migrate
#        pass
#    finally:
#        try:
#            conn.close()
#        except Exception:
#            pass
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///matchreport.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'seu_secret_key_aqui'  # Importante para sessões

db.init_app(app)
migrate = Migrate(app, db)

# Criar o banco de dados e as tabelas se não existirem
with app.app_context():
    # create tables if missing, then ensure new columns exist in existing DB
    db.create_all()
    # pass SQLAlchemy engine so we operate on the same DB used by the ORM
#    ensure_partida_columns(db.engine)
    
# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Modelo temporário de usuário para teste
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Usuário de teste
test_user = User(1)
users = {'admin': {'password': 'admin', 'id': 1}}


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# -------------------- ROTAS DE AUTENTICAÇÃO ---------------------


@app.route("/")
def index():
    return redirect(url_for('login'))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # TODO: Implementar verificação com Firebase
        # Por enquanto, vamos usar um login temporário
        if username in users and users[username]['password'] == password:
            user = User(users[username]['id'])
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha inválidos')
    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Validações básicas
        if username in users:
            flash('Nome de usuário já existe')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('As senhas não coincidem')
            return redirect(url_for('register'))
        
        if len(password) < 4:
            flash('A senha deve ter pelo menos 4 caracteres')
            return redirect(url_for('register'))

        # Criar novo usuário (temporário)
        new_user_id = len(users) + 1
        users[username] = {'password': password, 'id': new_user_id}
        
        flash('Conta criada com sucesso! Faça login para continuar.')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ---- Plantel de Jogadores ----

jogadores = []


@app.route("/plantel")
@login_required
def plantel():
    jogadores = Jogador.query.all()  # pega todos os jogadores
    return render_template('plantel.html', jogadores=jogadores)


@app.route("/add_jogador", methods=["GET", "POST"])
@login_required
def add_jogador():
    if request.method == "POST":
        nome_completo = request.form.get("nome_completo")
        apelido = request.form.get("apelido")
        idade = request.form.get("idade")
        posicao = request.form.get("posicao")
        numero = request.form.get("numero")
        data_entrada = request.form.get("data_entrada")

        if nome_completo and posicao and data_entrada:
            from datetime import datetime
            data_entrada = datetime.strptime(data_entrada, '%Y-%m-%d').date()
            
            novo = Jogador(
                nome_completo=nome_completo,
                apelido=apelido,
                idade=idade,
                posicao=posicao,
                numero=numero,
                data_entrada=data_entrada
            )
            db.session.add(novo)
            db.session.commit()
            return redirect(url_for("plantel"))
    return render_template("add_jogador.html")


@app.route('/delete_jogador/<int:index>', methods=['POST', 'GET'])
@login_required
def delete_jogador(index):
    jogador = Jogador.query.get_or_404(index)  # pega o jogador pelo id
    db.session.delete(jogador)
    db.session.commit()
    return redirect(url_for('plantel'))  # volta para a página do plantel


# ---- Iniciar Partida ----
@app.route("/sumula", methods=["GET", "POST"])
@login_required
def sumula():
    todos_jogadores = Jogador.query.all()  # Lista de todos os jogadores cadastrados para o select

    if request.method == "POST":
        time_casa = request.form.get("time_casa")
        time_adversario = request.form.get("time_adversario")
        data_partida = request.form.get("data_partida")
        
        # placar (valores atualizados pelo JS antes do submit)
        try:
            score_casa = int(request.form.get("score_casa", 0))
        except ValueError:
            score_casa = 0
        try:
            score_visitante = int(request.form.get("score_visitante", 0))
        except ValueError:
            score_visitante = 0
        
        data_obj = datetime.strptime(data_partida, '%Y-%m-%d').date()
        
        partida = Partida(time_casa=time_casa, time_adversario=time_adversario, data=data_obj,
                          score_casa=score_casa, score_visitante=score_visitante)
        db.session.add(partida)
        db.session.commit()
        # Primeiro: detectar jogadores novos adicionados na súmula (campos new_nome_<n>)
        new_players = {}
        for key in request.form:
            m = re.match(r'new_nome_(\d+)', key)
            if m:
                idx = m.group(1)
                nome_novo = request.form.get(key)
                if nome_novo and nome_novo.strip():
                    new_players[idx] = nome_novo.strip()

        # Criar registros de Jogador para os novos jogadores (numero=0, posicao vazia)
        created_new = []
        for idx, nome in new_players.items():
            novo = Jogador(nome=nome, posicao='', numero=0)
            db.session.add(novo)
            created_new.append((idx, novo))
        if created_new:
            db.session.commit()

        # Estatísticas para jogadores existentes (antes de criarmos os novos)
        for jogador in jogadores:
            estat = Estatistica(
                jogador_id=jogador.id,
                partida_id=partida.id,
                gol_marcado=int(request.form.get(f"gol_marcado_{jogador.id}", 0)),
                gol_sofrido=int(request.form.get(f"gol_sofrido_{jogador.id}", 0)),
                gol_contra=int(request.form.get(f"gol_contra_{jogador.id}", 0)),
                assistencia=int(request.form.get(f"assistencia_{jogador.id}", 0)),
                falta_feita=int(request.form.get(f"falta_feita_{jogador.id}", 0)),
                falta_sofrida=int(request.form.get(f"falta_sofrida_{jogador.id}", 0)),
                cartao_amarelo=int(request.form.get(f"cartao_amarelo_{jogador.id}", 0)),
                cartao_vermelho=int(request.form.get(f"cartao_vermelho_{jogador.id}", 0)),
            )
            db.session.add(estat)

        # Estatísticas para os novos jogadores (usam nomes de campo como gol_marcado_new_<n>)
        for idx, novo in created_new:
            estat = Estatistica(
                jogador_id=novo.id,
                partida_id=partida.id,
                gol_marcado=int(request.form.get(f"gol_marcado_new_{idx}", 0)),
                gol_sofrido=int(request.form.get(f"gol_sofrido_new_{idx}", 0)),
                gol_contra=int(request.form.get(f"gol_contra_new_{idx}", 0)),
                assistencia=int(request.form.get(f"assistencia_new_{idx}", 0)),
                falta_feita=int(request.form.get(f"falta_feita_new_{idx}", 0)),
                falta_sofrida=int(request.form.get(f"falta_sofrida_new_{idx}", 0)),
                cartao_amarelo=int(request.form.get(f"cartao_amarelo_new_{idx}", 0)),
                cartao_vermelho=int(request.form.get(f"cartao_vermelho_new_{idx}", 0)),
            )
            db.session.add(estat)

        db.session.commit()
        return redirect(url_for("historico"))

    return render_template("sumula.html", todos_jogadores=todos_jogadores)


# ---- Histórico ----
@app.route("/historico")
def historico():
    partidas = Partida.query.all()
    return render_template("historico.html", partidas=partidas)


# ---- Estatística e Histórico (em branco por enquanto) ----
@app.route("/estatistica")
def estatistica():
    return "<h2>Em construção...</h2>"

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)

# ─── ROTA DA API DO DASHBOARD ────────────────────────────────────────────────
 
@app.route("/api/dashboard")
@login_required
def api_dashboard():
    """Retorna JSON com todas as estatísticas para o dashboard."""
 
    # Total de gols marcados
    total_gols = db.session.query(
        func.sum(Estatistica.gol_marcado)
    ).scalar() or 0
 
    # Total de assistências
    total_assists = db.session.query(
        func.sum(Estatistica.assistencia)
    ).scalar() or 0
 
    # Total de cartões amarelos
    total_amarelos = db.session.query(
        func.sum(Estatistica.cartao_amarelo)
    ).scalar() or 0
 
    # Total de cartões vermelhos
    total_vermelhos = db.session.query(
        func.sum(Estatistica.cartao_vermelho)
    ).scalar() or 0
 
    # Top 5 artilheiros
    artilheiros_q = db.session.query(
        Jogador.apelido.label("nome"),
        func.sum(Estatistica.gol_marcado).label("gols")
    ).join(Estatistica, Estatistica.jogador_id == Jogador.id
    ).group_by(Jogador.id
    ).order_by(func.sum(Estatistica.gol_marcado).desc()
    ).limit(5).all()
 
    artilheiros = [
        {"nome": r.nome or "—", "gols": int(r.gols or 0)}
        for r in artilheiros_q
    ]
 
    # Top 5 assistências
    assists_q = db.session.query(
        Jogador.apelido.label("nome"),
        func.sum(Estatistica.assistencia).label("assists")
    ).join(Estatistica, Estatistica.jogador_id == Jogador.id
    ).group_by(Jogador.id
    ).order_by(func.sum(Estatistica.assistencia).desc()
    ).limit(5).all()
 
    assistencias = [
        {"nome": r.nome or "—", "assists": int(r.assists or 0)}
        for r in assists_q
    ]
 
    # Top 5 cartões
    cartoes_q = db.session.query(
        Jogador.apelido.label("nome"),
        func.sum(Estatistica.cartao_amarelo).label("amarelos"),
        func.sum(Estatistica.cartao_vermelho).label("vermelhos")
    ).join(Estatistica, Estatistica.jogador_id == Jogador.id
    ).group_by(Jogador.id
    ).order_by(
        (func.sum(Estatistica.cartao_amarelo) + func.sum(Estatistica.cartao_vermelho)).desc()
    ).limit(5).all()
 
    cartoes = [
        {
            "nome": r.nome or "—",
            "amarelos": int(r.amarelos or 0),
            "vermelhos": int(r.vermelhos or 0)
        }
        for r in cartoes_q
    ]
 
    # Últimas 5 partidas
    ultimas = Partida.query.order_by(Partida.data.desc()).limit(5).all()
    partidas = [
        {
            "data": p.data.strftime("%d/%m"),
            "time_casa": p.time_casa or "Casa",
            "time_adv": p.time_adversario,
            "score_casa": p.score_casa or 0,
            "score_vis": p.score_visitante or 0
        }
        for p in ultimas
    ]
 
    return jsonify({
        "total_gols": int(total_gols),
        "total_assists": int(total_assists),
        "total_amarelos": int(total_amarelos),
        "total_vermelhos": int(total_vermelhos),
        "artilheiros": artilheiros,
        "assistencias": assistencias,
        "cartoes": cartoes,
        "partidas": partidas
    })
 
