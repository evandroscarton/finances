"""
Rotas de Lançamentos: criação, listagem com filtros, edição, exclusão, compensação rápida.
Um lançamento pertence a UMA conta OU a UM cartão, nunca a ambos.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from services import lancamentos_service, contas_service, cartoes_service, categorias_service
from services.lancamentos_service import ErroValidacao

lancamentos_bp = Blueprint("lancamentos", __name__, url_prefix="/lancamentos")


def _filtros_do_form():
    """
    Lê os filtros preservados nos campos ocultos (f_*) do form de
    novo/editar lançamento e os transforma no dict aceito por
    url_for('lancamentos.listar', **filtros) — usado para redirecionar de
    volta à listagem exatamente com o mesmo filtro que estava ativo antes
    de abrir o formulário.
    """
    return {
        "conta_id": request.form.get("f_conta_id") or None,
        "cartao_id": request.form.get("f_cartao_id") or None,
        "categoria_id": request.form.get("f_categoria_id") or None,
        "status": request.form.get("f_status") or None,
        "data_inicio": request.form.get("f_data_inicio") or None,
        "data_fim": request.form.get("f_data_fim") or None,
    }


def _filtros_da_querystring():
    """
    Lê os filtros repassados via querystring (usados pelos botões de ação
    rápida da listagem — Compensar/Excluir — que fazem POST direto sem
    formulário de edição, então não têm campos hidden f_* disponíveis).
    """
    return {
        "conta_id": request.args.get("conta_id") or None,
        "cartao_id": request.args.get("cartao_id") or None,
        "categoria_id": request.args.get("categoria_id") or None,
        "status": request.args.get("status") or None,
        "data_inicio": request.args.get("data_inicio") or None,
        "data_fim": request.args.get("data_fim") or None,
    }


@lancamentos_bp.route("/")
@login_required
def listar():
    filtros = {
        "conta_id": request.args.get("conta_id", type=int) or None,
        "cartao_id": request.args.get("cartao_id", type=int) or None,
        "categoria_id": request.args.get("categoria_id", type=int) or None,
        "status": request.args.get("status") or None,
        "data_inicio": request.args.get("data_inicio") or None,
        "data_fim": request.args.get("data_fim") or None,
    }
    lancamentos = lancamentos_service.listar_com_filtros(current_user.id, filtros)
    contas = contas_service.listar_contas_com_saldos(current_user.id)
    cartoes = cartoes_service.listar_cartoes(current_user.id)
    categorias = categorias_service.listar_categorias(current_user.id)

    return render_template(
        "lancamentos/list.html",
        lancamentos=lancamentos, contas=contas, cartoes=cartoes,
        categorias=categorias, filtros=filtros,
    )


@lancamentos_bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    contas = contas_service.listar_contas_com_saldos(current_user.id)
    cartoes = cartoes_service.listar_cartoes(current_user.id)
    categorias = categorias_service.listar_categorias(current_user.id)

    if request.method == "GET":
        return render_template(
            "lancamentos/form.html", lancamento=None,
            contas=contas, cartoes=cartoes, categorias=categorias,
        )

    origem = request.form.get("origem")  # 'conta' ou 'cartao'
    conta_id = request.form.get("conta_id", type=int) if origem == "conta" else None
    cartao_id = request.form.get("cartao_id", type=int) if origem == "cartao" else None
    categoria_id = request.form.get("categoria_id", type=int) or None
    descricao = request.form.get("descricao", "").strip()
    valor = request.form.get("valor", "0")
    tipo_valor = request.form.get("tipo_valor")  # 'entrada' ou 'saida'
    data_lancamento = request.form.get("data_lancamento", "")
    data_compensacao = request.form.get("data_compensacao") or None
    status = request.form.get("status", "pendente")

    # Filtros que estavam ativos na listagem antes de abrir este form,
    # recebidos via hidden fields — reenviados no redirect de sucesso/erro.
    filtros = _filtros_do_form()

    try:
        lancamentos_service.criar_lancamento(
            current_user.id, conta_id, cartao_id, categoria_id, descricao,
            valor, tipo_valor, data_lancamento, data_compensacao, status,
        )
        flash("Lançamento criado com sucesso!", "sucesso")
        return redirect(url_for("lancamentos.listar", **filtros))
    except ErroValidacao as e:
        flash(str(e), "erro")
        return redirect(url_for("lancamentos.novo", **filtros))


@lancamentos_bp.route("/<int:lancamento_id>/editar", methods=["GET", "POST"])
@login_required
def editar(lancamento_id):
    lancamento = lancamentos_service.buscar_lancamento(lancamento_id, current_user.id)
    if not lancamento:
        flash("Lançamento não encontrado.", "erro")
        return redirect(url_for("lancamentos.listar"))
    if lancamento["transferencia_id"]:
        flash("Lançamentos de transferência não podem ser editados aqui. Exclua a transferência.", "erro")
        return redirect(url_for("lancamentos.listar"))

    contas = contas_service.listar_contas_com_saldos(current_user.id)
    cartoes = cartoes_service.listar_cartoes(current_user.id)
    categorias = categorias_service.listar_categorias(current_user.id)

    if request.method == "GET":
        return render_template(
            "lancamentos/form.html", lancamento=lancamento,
            contas=contas, cartoes=cartoes, categorias=categorias,
        )

    origem = request.form.get("origem")
    conta_id = request.form.get("conta_id", type=int) if origem == "conta" else None
    cartao_id = request.form.get("cartao_id", type=int) if origem == "cartao" else None
    categoria_id = request.form.get("categoria_id", type=int) or None
    descricao = request.form.get("descricao", "").strip()
    valor = request.form.get("valor", "0")
    tipo_valor = request.form.get("tipo_valor")
    data_lancamento = request.form.get("data_lancamento", "")
    data_compensacao = request.form.get("data_compensacao") or None
    status = request.form.get("status", "pendente")

    filtros = _filtros_do_form()

    try:
        lancamentos_service.atualizar_lancamento(
            lancamento_id, current_user.id, conta_id, cartao_id, categoria_id,
            descricao, valor, tipo_valor, data_lancamento, data_compensacao, status,
        )
        flash("Lançamento atualizado com sucesso!", "sucesso")
        return redirect(url_for("lancamentos.listar", **filtros))
    except ErroValidacao as e:
        flash(str(e), "erro")
        return redirect(url_for("lancamentos.editar", lancamento_id=lancamento_id, **filtros))


@lancamentos_bp.route("/<int:lancamento_id>/compensar", methods=["POST"])
@login_required
def compensar(lancamento_id):
    """
    Ação rápida da listagem: marca um lançamento pendente como compensado,
    reaproveitando a mesma regra usada na edição manual (mesmo caminho de
    código -> mesmo efeito sobre o saldo, pois saldo é sempre derivado via
    SUM sobre status/data_compensacao).

    Os filtros ativos na listagem são recebidos via querystring (repassados
    pela action do form no list.html) e devolvidos no redirect, evitando
    que a ação "Compensar" reset a busca do usuário.
    """
    filtros = _filtros_da_querystring()
    try:
        lancamentos_service.compensar_lancamento(lancamento_id, current_user.id)
        flash("Lançamento compensado com sucesso!", "sucesso")
    except ErroValidacao as e:
        flash(str(e), "erro")
    return redirect(url_for("lancamentos.listar", **filtros))


@lancamentos_bp.route("/<int:lancamento_id>/excluir", methods=["POST"])
@login_required
def excluir(lancamento_id):
    """
    Mesmo tratamento de filtros do endpoint 'compensar' — evita reset da
    busca ao excluir um lançamento direto da listagem.
    """
    filtros = _filtros_da_querystring()
    try:
        lancamentos_service.excluir_lancamento(lancamento_id, current_user.id)
        flash("Lançamento excluído com sucesso!", "sucesso")
    except ErroValidacao as e:
        flash(str(e), "erro")
    return redirect(url_for("lancamentos.listar", **filtros))
