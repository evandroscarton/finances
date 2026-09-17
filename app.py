"""
Cadastro de Contas - CRUD com Flask + PostgreSQL
--------------------------------------------------
Requisitos:
    pip install flask psycopg2-binary gunicorn python-dotenv

Para rodar localmente:
    python app.py
Depois acesse: http://localhost:5000
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
from dotenv import load_dotenv

load_dotenv()  # Carrega variáveis do arquivo .env (apenas em ambiente local)

app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
app.secret_key = os.environ.get("SECRET_KEY", "chave-padrao-dev")

# =========================
# CONFIGURAÇÃO DO BANCO
# =========================
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Produção (Render) - usa a URL completa fornecida pela plataforma
    def conectar():
        return psycopg2.connect(DATABASE_URL)
else:
    # Desenvolvimento local
    DB_CONFIG = {
        "host": "localhost",
        "port": "5432",
        "dbname": "finances",
        "user": "postgres",
        "password": os.environ.get("DB_PASSWORD", ""),
    }

    def conectar():
        return psycopg2.connect(**DB_CONFIG)


# =========================
# OPERAÇÕES NO BANCO
# =========================
def listar_contas():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT codigo, descricao, ativo FROM contas ORDER BY codigo;")
    dados = cur.fetchall()
    cur.close()
    conn.close()
    return dados


def buscar_conta(codigo):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT codigo, descricao, ativo FROM contas WHERE codigo = %s;", (codigo,))
    dado = cur.fetchone()
    cur.close()
    conn.close()
    return dado


def inserir_conta(descricao, ativo):
    conn = conectar()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO contas (descricao, ativo) VALUES (%s, %s);",
        (descricao, ativo),
    )
    conn.commit()
    cur.close()
    conn.close()


def atualizar_conta(codigo, descricao, ativo):
    conn = conectar()
    cur = conn.cursor()
    cur.execute(
        "UPDATE contas SET descricao = %s, ativo = %s WHERE codigo = %s;",
        (descricao, ativo, codigo),
    )
    conn.commit()
    cur.close()
    conn.close()


def excluir_conta(codigo):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("DELETE FROM contas WHERE codigo = %s;", (codigo,))
    conn.commit()
    cur.close()
    conn.close()


def listar_categorias():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT codigo, descricao FROM categoria ORDER BY codigo;")
    dados = cur.fetchall()
    cur.close()
    conn.close()
    return dados


def buscar_categoria(codigo):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT codigo, descricao FROM categoria WHERE codigo = %s;", (codigo,))
    dado = cur.fetchone()
    cur.close()
    conn.close()
    return dado


def inserir_categoria(descricao):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("INSERT INTO categoria (descricao) VALUES (%s);", (descricao,))
    conn.commit()
    cur.close()
    conn.close()


def atualizar_categoria(codigo, descricao):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("UPDATE categoria SET descricao = %s WHERE codigo = %s;", (descricao, codigo))
    conn.commit()
    cur.close()
    conn.close()


def excluir_categoria(codigo):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("DELETE FROM categoria WHERE codigo = %s;", (codigo,))
    conn.commit()
    cur.close()
    conn.close()


# =========================
# ROTAS
# =========================
@app.route("/")
def index():
    try:
        contas = listar_contas()
        erro = None
    except Exception as e:
        contas = []
        erro = str(e)
    return render_template("index.html", contas=contas, erro=erro)


@app.route("/nova", methods=["GET", "POST"])
def nova():
    if request.method == "POST":
        descricao = request.form.get("descricao", "").strip()
        ativo = "ativo" in request.form

        if not descricao:
            flash("A descrição é obrigatória.", "erro")
            return render_template("form.html", conta=None, descricao=descricao, ativo=ativo)

        try:
            inserir_conta(descricao, ativo)
            flash("Conta cadastrada com sucesso.", "sucesso")
            return redirect(url_for("index"))
        except Exception as e:
            flash(f"Erro ao salvar: {e}", "erro")
            return render_template("form.html", conta=None, descricao=descricao, ativo=ativo)

    return render_template("form.html", conta=None, descricao="", ativo=True)


@app.route("/editar/<int:codigo>", methods=["GET", "POST"])
def editar(codigo):
    if request.method == "POST":
        descricao = request.form.get("descricao", "").strip()
        ativo = "ativo" in request.form

        if not descricao:
            flash("A descrição é obrigatória.", "erro")
            return render_template("form.html", conta=(codigo, descricao, ativo), descricao=descricao, ativo=ativo)

        try:
            atualizar_conta(codigo, descricao, ativo)
            flash("Conta atualizada com sucesso.", "sucesso")
            return redirect(url_for("index"))
        except Exception as e:
            flash(f"Erro ao atualizar: {e}", "erro")
            return render_template("form.html", conta=(codigo, descricao, ativo), descricao=descricao, ativo=ativo)

    conta = buscar_conta(codigo)
    if conta is None:
        flash("Conta não encontrada.", "erro")
        return redirect(url_for("index"))

    return render_template("form.html", conta=conta, descricao=conta[1], ativo=conta[2])


@app.route("/excluir/<int:codigo>", methods=["POST"])
def excluir(codigo):
    try:
        excluir_conta(codigo)
        flash("Conta excluída com sucesso.", "sucesso")
    except Exception as e:
        flash(f"Erro ao excluir: {e}", "erro")
    return redirect(url_for("index"))


@app.route("/categorias")
def categorias_index():
    try:
        categorias = listar_categorias()
        erro = None
    except Exception as e:
        categorias = []
        erro = str(e)
    return render_template("categoria_index.html", categorias=categorias, erro=erro)


@app.route("/categorias/nova", methods=["GET", "POST"])
def categorias_nova():
    if request.method == "POST":
        descricao = request.form.get("descricao", "").strip()

        if not descricao:
            flash("A descrição é obrigatória.", "erro")
            return render_template("categoria_form.html", categoria=None, descricao=descricao)

        try:
            inserir_categoria(descricao)
            flash("Categoria cadastrada com sucesso.", "sucesso")
            return redirect(url_for("categorias_index"))
        except Exception as e:
            flash(f"Erro ao salvar: {e}", "erro")
            return render_template("categoria_form.html", categoria=None, descricao=descricao)

    return render_template("categoria_form.html", categoria=None, descricao="")


@app.route("/categorias/editar/<int:codigo>", methods=["GET", "POST"])
def categorias_editar(codigo):
    if request.method == "POST":
        descricao = request.form.get("descricao", "").strip()

        if not descricao:
            flash("A descrição é obrigatória.", "erro")
            return render_template("categoria_form.html", categoria=(codigo, descricao), descricao=descricao)

        try:
            atualizar_categoria(codigo, descricao)
            flash("Categoria atualizada com sucesso.", "sucesso")
            return redirect(url_for("categorias_index"))
        except Exception as e:
            flash(f"Erro ao atualizar: {e}", "erro")
            return render_template("categoria_form.html", categoria=(codigo, descricao), descricao=descricao)

    categoria = buscar_categoria(codigo)
    if categoria is None:
        flash("Categoria não encontrada.", "erro")
        return redirect(url_for("categorias_index"))

    return render_template("categoria_form.html", categoria=categoria, descricao=categoria[1])


@app.route("/categorias/excluir/<int:codigo>", methods=["POST"])
def categorias_excluir(codigo):
    try:
        excluir_categoria(codigo)
        flash("Categoria excluída com sucesso.", "sucesso")
    except Exception as e:
        flash(f"Erro ao excluir: {e}", "erro")
    return redirect(url_for("categorias_index"))


if __name__ == "__main__":
    app.run(debug=True)
