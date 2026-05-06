from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class Time(UserMixin, db.Model):
    __tablename__ = "times"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    criado_em = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    jogadores = db.relationship("Jogador", backref="time", lazy=True, cascade="all, delete-orphan")
    partidas = db.relationship("Partida", backref="time", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Jogador(db.Model):
    __tablename__ = "jogadores"

    id = db.Column(db.Integer, primary_key=True)
    time_id = db.Column(db.Integer, db.ForeignKey("times.id"), nullable=False, index=True)
    nome_completo = db.Column(db.String(100), nullable=False)
    apelido = db.Column(db.String(50))
    idade = db.Column(db.Integer)
    posicao = db.Column(db.String(50), nullable=False)
    data_entrada = db.Column(db.Date, nullable=False)
    numero = db.Column(db.Integer)

    estatisticas = db.relationship("Estatistica", backref="jogador", lazy=True, cascade="all, delete-orphan")

    @property
    def nome_exibicao(self):
        return self.apelido or self.nome_completo


class Partida(db.Model):
    __tablename__ = "partidas"

    id = db.Column(db.Integer, primary_key=True)
    time_id = db.Column(db.Integer, db.ForeignKey("times.id"), nullable=False, index=True)
    time_casa = db.Column(db.String(100), nullable=False)
    time_adversario = db.Column(db.String(100), nullable=False)
    data = db.Column(db.Date, nullable=False)
    score_casa = db.Column(db.Integer, default=0, nullable=False)
    score_visitante = db.Column(db.Integer, default=0, nullable=False)

    estatisticas = db.relationship("Estatistica", backref="partida", lazy=True, cascade="all, delete-orphan")


class Estatistica(db.Model):
    __tablename__ = "estatisticas"

    id = db.Column(db.Integer, primary_key=True)
    jogador_id = db.Column(db.Integer, db.ForeignKey("jogadores.id"), nullable=False, index=True)
    partida_id = db.Column(db.Integer, db.ForeignKey("partidas.id"), nullable=False, index=True)
    gol_marcado = db.Column(db.Integer, default=0, nullable=False)
    gol_sofrido = db.Column(db.Integer, default=0, nullable=False)
    gol_contra = db.Column(db.Integer, default=0, nullable=False)
    assistencia = db.Column(db.Integer, default=0, nullable=False)
    falta_feita = db.Column(db.Integer, default=0, nullable=False)
    falta_sofrida = db.Column(db.Integer, default=0, nullable=False)
    cartao_amarelo = db.Column(db.Integer, default=0, nullable=False)
    cartao_vermelho = db.Column(db.Integer, default=0, nullable=False)
