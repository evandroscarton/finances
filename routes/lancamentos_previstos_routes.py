"""
Rotas de Lançamentos Previstos: criação, listagem, edição, exclusão e o
botão "Lançar" (gera o lançamento real correspondente na tela de Lançamentos).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from services import lancamentos_previstos_service, contas_service, cartoes_service, categorias_service
from services.lancamentos_previstos_service import ErroValidacao

lancamentos_previstos_bp = Blueprint(
    "lancamentos_previstos", __name__, url_prefix="/lancamentos-previstos"
)


def _filtros_da_querystring():
    """
    Lê os filtros ativos repassados via querystring — usados pelos botões de
    ação rápida da listagem (Lançar/Excluir), que fazem POST direto sem
    formulário próprio, apenas com a action da URL levando os filtros. Evita
    que essas ações resetem a busca do usuário ao redirecionar de volta.
    """
    return {
        "conta_id": request.args.get("conta_id") or None,
        "cartao_id": request.args.get("cartao_id") or None,
        "categoria_id": request.args.get("categoria_id") or None,
        "ultimo_lancamento_inicio": request.args.get("ultimo_lancamento_inicio") or None,
        "ultimo_lancamento_fim": request.args.get("ultimo_lancamento_fim") or None,
    }


@lancamentos_previstos_bp.route("/")
@login_required
def listar():
    filtros = {
        "conta_id": request.args.get("conta_id", type=int) or None,
        "cartao_id": request.args.get("cartao_id", type=int) or None,
        "categoria_id": request.args.get("categoria_id", type=int) or None,
        "ultimo_lancamento_inicio": request.args.get("ultimo_lancamento_inicio") or None,
        "ultimo_lancamento_fim": request.args.get("ultimo_lancamento_fim") or None,
    }
    previstos = lancamentos_previstos_service.listar_previstos(current_user.id, filtros)
    contas = contas_service.listar_contas_com_saldos(current_user.id)
    cartoes = cartoes_service.listar_cartoes(current_user.id)
    categorias = categorias_service.listar_categorias(current_user.id)

    return render_template(
        "lancamentos_previstos/list.html",
        previstos=previstos, contas=contas, cartoes=cartoes,
        categorias=categorias, filtros=filtros,
    )


def _extrair_dados_form(form):
    origem = form.get("origem")
    conta_id = form.get("conta_id", type=int) if origem == "conta" else None
    cartao_id = form.get("cartao_id", type=int) if origem == "cartao" else None
    return {
        "conta_id": conta_id,
        "cartao_id": cartao_id,
        "categoria_id": form.get("categoria_id", type=int) or None,
        "descricao": form.get("descricao", "").strip(),
        "valor_str": form.get("valor", "0"),
        "tipo_valor": form.get("tipo_valor"),
        "dia_mes_str": form.get("dia_mes", ""),
        "mes_ano_str": form.get("mes_ano", ""),
        "acao": form.get("acao", "salvar"),  # 'salvar' ou 'lancar'
    }


@lancamentos_previstos_bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    contas = contas_service.listar_contas_com_saldos(current_user.id)
    cartoes = cartoes_service.listar_cartoes(current_user.id)
    categorias = categorias_service.listar_categorias(current_user.id)

    if request.method == "GET":
        return render_template(
            "lancamentos_previstos/form.html", previsto=None,
            contas=contas, cartoes=cartoes, categorias=categorias,
        )

    dados = _extrair_dados_form(request.form)
    try:
        previsto = lancamentos_previstos_service.criar_previsto(
            current_user.id, dados["conta_id"], dados["cartao_id"],
            dados["categoria_id"], dados["descricao"], dados["valor_str"],
            dados["tipo_valor"], dados["dia_mes_str"], dados["mes_ano_str"],
        )
        if dados["acao"] == "lancar":
            lancamentos_previstos_service.lancar_previsto(previsto["id"], current_user.id)
            flash("Lançamento previsto salvo e lançado com sucesso!", "sucesso")
        else:
            flash("Lançamento previsto criado com sucesso!", "sucesso")
        return redirect(url_for("lancamentos_previstos.listar"))
    except ErroValidacao as e:
        flash(str(e), "erro")
        return redirect(url_for("lancamentos_previstos.novo"))


@lancamentos_previstos_bp.route("/<int:previsto_id>/editar", methods=["GET", "POST"])
@login_required
def editar(previsto_id):
    previsto = lancamentos_previstos_service.buscar_previsto(previsto_id, current_user.id)
    if not previsto:
        flash("Lançamento previsto não encontrado.", "erro")
        return redirect(url_for("lancamentos_previstos.listar"))

    contas = contas_service.listar_contas_com_saldos(current_user.id)
    cartoes = cartoes_service.listar_cartoes(current_user.id)
    categorias = categorias_service.listar_categorias(current_user.id)

    if request.method == "GET":
        return render_template(
            "lancamentos_previstos/form.html", previsto=previsto,
            contas=contas, cartoes=cartoes, categorias=categorias,
        )

    dados = _extrair_dados_form(request.form)
    try:
        lancamentos_previstos_service.atualizar_previsto(
            previsto_id, current_user.id, dados["conta_id"], dados["cartao_id"],
            dados["categoria_id"], dados["descricao"], dados["valor_str"],
            dados["tipo_valor"], dados["dia_mes_str"], dados["mes_ano_str"],
        )
        if dados["acao"] == "lancar":
            lancamentos_previstos_service.lancar_previsto(previsto_id, current_user.id)
            flash("Lançamento previsto salvo e lançado com sucesso!", "sucesso")
        else:
            flash("Lançamento previsto atualizado com sucesso!", "sucesso")
        return redirect(url_for("lancamentos_previstos.listar"))
    except ErroValidacao as e:
        flash(str(e), "erro")
        return redirect(url_for("lancamentos_previstos.editar", previsto_id=previsto_id))


@lancamentos_previstos_bp.route("/<int:previsto_id>/excluir", methods=["POST"])
@login_required
def excluir(previsto_id):
    """
    Filtros ativos são recebidos via querystring (repassados pela action do
    form no list.html) e devolvidos no redirect, preservando a busca.
    """
    filtros = _filtros_da_querystring()
    try:
        lancamentos_previstos_service.excluir_previsto(previsto_id, current_user.id)
        flash("Lançamento previsto excluído com sucesso!", "sucesso")
    except ErroValidacao as e:
        flash(str(e), "erro")
    return redirect(url_for("lancamentos_previstos.listar", **filtros))

@lancamentos_previstos_bp.route("/<int:previsto_id>/lancar", methods=["POST"])
@login_required
def lancar(previsto_id):
    """
    Gera o lançamento real correspondente a este previsto (dia_mes + mes_ano
    -> data_lancamento), chamado direto da tela de listagem. Não altera nem
    remove o registro previsto, permitindo reutilizá-lo em meses futuros.

    Filtros ativos são recebidos via querystring e devolvidos no redirect,
    preservando a busca (mesmo tratamento de excluir/compensar).
    """
    filtros = _filtros_da_querystring()
    try:
        lancamentos_previstos_service.lancar_previsto(previsto_id, current_user.id)
        flash("Lançamento gerado com sucesso na tela de Lançamentos!", "sucesso")
    except ErroValidacao as e:
        flash(str(e), "erro")
    return redirect(url_for("lancamentos_previstos.listar", **filtros))

@lancamentos_previstos_bp.route("/atualizar-mes-ano-em-massa", methods=["POST"])
@login_required
def atualizar_mes_ano_em_massa():
    mes_ano_str = request.form.get("mes_ano_massa", "")
    try:
        linhas = lancamentos_previstos_service.atualizar_mes_ano_em_massa(
            current_user.id, mes_ano_str
        )
        flash(f"{linhas} lançamento(s) previsto(s) atualizado(s) para o novo mês/ano!", "sucesso")
    except ErroValidacao as e:
        flash(str(e), "erro")
    return redirect(url_for("lancamentos_previstos.listar"))
