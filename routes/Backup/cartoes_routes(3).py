"""
Rotas de Cartões de Crédito: CRUD + tela de fatura atual.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from services import cartoes_service, contas_service
from services.cartoes_service import ErroValidacao

cartoes_bp = Blueprint("cartoes", __name__, url_prefix="/cartoes")


@cartoes_bp.route("/")
@login_required
def listar():
    # aplicar_permissao=False: tela de gestão dos PRÓPRIOS cartões — o
    # usuário deve ver e administrar 100% do que é dele.
    cartoes = cartoes_service.listar_cartoes(current_user.id, aplicar_permissao=False)
    for c in cartoes:
        c["fatura_atual"] = cartoes_service.calcular_fatura_atual(c["id"], current_user.id)
    return render_template("cartoes/list.html", cartoes=cartoes)


@cartoes_bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    # aplicar_permissao=False: combo de conta de pagamento deve listar TODAS
    # as contas próprias, não só as parametrizadas para consulta.
    contas = contas_service.listar_contas_com_saldos(current_user.id, aplicar_permissao=False)

    if request.method == "GET":
        return render_template("cartoes/form.html", cartao=None, contas=contas)

    nome = request.form.get("nome", "").strip()
    limite = request.form.get("limite", "0")
    dia_fechamento = request.form.get("dia_fechamento", type=int)
    dia_vencimento = request.form.get("dia_vencimento", type=int)
    conta_pagamento_id = request.form.get("conta_pagamento_id", type=int)

    try:
        cartoes_service.criar_cartao(
            current_user.id, nome, limite, dia_fechamento, dia_vencimento, conta_pagamento_id
        )
        flash("Cartão criado com sucesso!", "sucesso")
        return redirect(url_for("cartoes.listar"))
    except ErroValidacao as e:
        flash(str(e), "erro")
        return redirect(url_for("cartoes.novo"))


@cartoes_bp.route("/<int:cartao_id>/fatura")
@login_required
def fatura(cartao_id):
    cartao = cartoes_service.buscar_cartao(cartao_id, current_user.id)
    if not cartao:
        flash("Cartão não encontrado.", "erro")
        return redirect(url_for("cartoes.listar"))

    lancamentos_pendentes = cartoes_service.listar_lancamentos_pendentes(cartao_id, current_user.id)
    total_fatura = cartoes_service.calcular_fatura_atual(cartao_id, current_user.id)
    contas = contas_service.listar_contas_com_saldos(current_user.id, aplicar_permissao=False)

    return render_template(
        "cartoes/fatura.html",
        cartao=cartao,
        lancamentos=lancamentos_pendentes,
        total_fatura=total_fatura,
        contas=contas,
    )


@cartoes_bp.route("/<int:cartao_id>/pagar-fatura", methods=["POST"])
@login_required
def pagar_fatura(cartao_id):
    from services import lancamentos_service

    conta_pagamento_id = request.form.get("conta_pagamento_id", type=int)
    valor = request.form.get("valor", "0")
    data_pagamento = request.form.get("data_pagamento", "")

    try:
        lancamentos_service.pagar_fatura_cartao(
            current_user.id, cartao_id, conta_pagamento_id, valor, data_pagamento
        )
        flash("Fatura paga com sucesso!", "sucesso")
    except Exception as e:
        flash(str(e), "erro")
    return redirect(url_for("cartoes.fatura", cartao_id=cartao_id))
