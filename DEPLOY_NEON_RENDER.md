# Deploy com Neon e Render

## Variaveis no Render

Configure estas variaveis em Environment:

- `DATABASE_URL`: cole a connection string do Neon. Use a URL com `postgresql://...`.
- `SECRET_KEY`: crie uma chave longa e aleatoria para proteger as sessoes.

Ao iniciar, a aplicacao executa `db.create_all()` e cria as tabelas faltantes no banco apontado por `DATABASE_URL`.

## Tabelas criadas

- `times`: conta do time que faz login.
- `jogadores`: plantel vinculado ao time.
- `partidas`: historico de partidas vinculado ao time.
- `estatisticas`: numeros por jogador e partida.

## Fluxo esperado

1. Cadastre o time em `/register`.
2. Entre com usuario e senha em `/login`.
3. Cadastre atletas em `/plantel`.
4. Preencha e salve a partida em `/sumula`.
5. Veja os dados em `/dashboard` e o resumo em `/historico`.

Se o Neon ja tiver tabelas antigas do projeto, crie um banco novo ou remova as tabelas antigas antes do primeiro deploy, porque `create_all()` cria tabelas faltantes mas nao transforma colunas antigas.
