from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Jogador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(100), nullable=False)
    apelido = db.Column(db.String(50))
    idade = db.Column(db.Integer)
    posicao = db.Column(db.String(50))
    data_entrada = db.Column(db.Date, nullable=False)
    numero = db.Column(db.Integer)

    estatisticas = db.relationship("Estatistica", backref="jogador", lazy=True)


class Partida(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time_adversario = db.Column(db.String(100), nullable=False)
    data = db.Column(db.Date, nullable=False)

    estatisticas = db.relationship("Estatistica", backref="partida", lazy=True)


class Estatistica(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jogador_id = db.Column(db.Integer, db.ForeignKey("jogador.id"), nullable=False)
    partida_id = db.Column(db.Integer, db.ForeignKey("partida.id"), nullable=False)

    gol_marcado = db.Column(db.Integer, default=0)
    gol_sofrido = db.Column(db.Integer, default=0)
    gol_contra = db.Column(db.Integer, default=0)
    assistencia = db.Column(db.Integer, default=0)
    falta_feita = db.Column(db.Integer, default=0)
    falta_sofrida = db.Column(db.Integer, default=0)
    cartao_amarelo = db.Column(db.Integer, default=0)
    cartao_vermelho = db.Column(db.Integer, default=0)
