from flask import Flask, render_template, request, redirect, url_for, flash
import re
from models import db, Jogador, Partida, Estatistica
from flask_migrate import Migrate
from datetime import datetime
from functools import wraps
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///matchreport.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'seu_secret_key_aqui'  # Importante para sessões

db.init_app(app)
migrate = Migrate(app, db)

# Criar o banco de dados e as tabelas se não existirem
with app.app_context():
    db.create_all()
    
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
    partidas = Partida.query.all()
    return render_template("index.html", partidas=partidas)

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
        time_adversario = request.form.get("time_adversario")
        data_partida = request.form.get("data_partida")
        
        from datetime import datetime
        data_obj = datetime.strptime(data_partida, '%Y-%m-%d').date()
        
        partida = Partida(time_adversario=time_adversario, data=data_obj)
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
