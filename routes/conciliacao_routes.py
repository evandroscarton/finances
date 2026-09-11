"""
Rotas de conciliação de extrato PDF.
Camada HTTP: valida entrada, chama service, renderiza template.
Nenhum SQL nem conexão de banco aqui — isso é responsabilidade dos services.
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user

from services import contas_service, conciliacao_service

conciliacao_bp = Blueprint("conciliacao", __name__, url_prefix="/conciliacao")

EXTENSOES_PERMITIDAS = {"pdf"}


def _extensao_valida(nome_arquivo: str) -> bool:
    return "." in nome_arquivo and nome_arquivo.rsplit(".", 1)[1].lower() in EXTENSOES_PERMITIDAS


@conciliacao_bp.route("/", methods=["GET"])
@login_required
def tela_conciliacao():
    # aplicar_permissao=False: usuário administra as próprias contas, igual à tela de Contas
    contas = contas_service.listar_contas_com_saldos(current_user.id, aplicar_permissao=False)
    return render_template("conciliacao.html", contas=contas, resultado=None)


@conciliacao_bp.route("/importar", methods=["POST"])
@login_required
def importar_extrato():
    conta_id = request.form.get("conta_id", type=int)
    arquivo = request.files.get("arquivo_pdf")

    if not conta_id:
        flash("Selecione uma conta antes de importar o extrato.", "erro")
        return redirect(url_for("conciliacao.tela_conciliacao"))

    if not arquivo or arquivo.filename == "":
        flash("Selecione um arquivo PDF para importar.", "erro")
        return redirect(url_for("conciliacao.tela_conciliacao"))

    if not _extensao_valida(arquivo.filename):
        flash("Apenas arquivos PDF são aceitos.", "erro")
        return redirect(url_for("conciliacao.tela_conciliacao"))

    # Confirma que a conta pertence ao usuário logado (evita acesso cruzado)
    conta = contas_service.buscar_conta(conta_id, current_user.id)
    if not conta:
        flash("Conta inválida.", "erro")
        return redirect(url_for("conciliacao.tela_conciliacao"))

    try:
        resultado = conciliacao_service.conciliar_extrato(current_user.id, conta_id, arquivo.stream)
    except ValueError as e:
        flash(str(e), "erro")
        return redirect(url_for("conciliacao.tela_conciliacao"))

    contas = contas_service.listar_contas_com_saldos(current_user.id, aplicar_permissao=False)
    return render_template("conciliacao.html", contas=contas, resultado=resultado, conta_selecionada=conta_id)
