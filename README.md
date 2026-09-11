# Finance — Controle Financeiro Pessoal Multiusuário

Sistema Flask + PostgreSQL puro (sem ORM) com contas, cartões de crédito,
categorias, lançamentos e transferências. Saldo compensado e projetado
são sempre calculados via SUM(valor) sobre lançamentos — nunca gravados
como coluna fixa.

## Requisitos
- Python 3.11+
- PostgreSQL 15+

## Configuração

1. Crie o banco e rode o schema:
   ```bash
   createdb financeapp
   psql -d financeapp -f schema.sql
