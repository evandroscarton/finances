"""
Rotas de gestão de permissões. Chave principal é o e-mail do usuário
(usuario_id resolvido a partir dele); a mudança de usuário no combo recarrega
a tela via GET, exibindo as permissões atuais daquele usuário selecionado.
Qualquer usuário logado pode alterar permissões de qualquer outro (regra
confirmada pelo cliente — sem hierarquia de admin neste sistema).
"""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from services import usuarios_service, permissoes_service, contas_service, cartoes_service
from services.permissoes_service import ErroValidacao

permissoes_bp = Blueprint("permissoes", __name__, url_prefix="/permissoes")


@permissoes_bp.route("/", methods=["GET"])
@login_required
def index():
    usuarios = usuarios_service.listar_usuarios()

    usuario_selecionado_id = request.args.get("usuario_id", type=int)
    contas_marcadas, cartoes_marcados = [], []
    todas_contas, todos_cartoes = [], []

    if usuario_selecionado_id:
        contas_marcadas, cartoes_marcados = permissoes_service.obter_permissoes(
            usuario_selecionado_id
        )
        # aplicar_permissao=False: a tela de Permissões precisa listar TODAS
        # as contas/cartões do usuário parametrizado, senão seria impossível
        # conceder permissão sobre algo que já está fora de uma parametrização
        # anterior (ciclo vicioso).
        todas_contas = contas_service.listar_contas(usuario_selecionado_id, aplicar_permissao=False)
        todos_cartoes = cartoes_service.listar_cartoes(usuario_selecionado_id, aplicar_permissao=False)

    return render_template(
        "permissoes/form.html",
        usuarios=usuarios,
        usuario_selecionado_id=usuario_selecionado_id,
        todas_contas=todas_contas,
        todos_cartoes=todos_cartoes,
        contas_marcadas=set(contas_marcadas),
        cartoes_marcados=set(cartoes_marcados),
    )


@permissoes_bp.route("/salvar", methods=["POST"])
@login_required
def salvar():
    usuario_id = request.form.get("usuario_id", type=int)
    if not usuario_id:
        flash("Selecione um usuário (e-mail) válido.", "erro")
        return redirect(url_for("permissoes.index"))

    contas_ids = request.form.getlist("contas_ids")
    cartoes_ids = request.form.getlist("cartoes_ids")

    try:
        permissoes_service.salvar_permissoes(usuario_id, contas_ids, cartoes_ids)
        flash("Permissões atualizadas com sucesso!", "sucesso")
    except ErroValidacao as e:
        flash(str(e), "erro")

    return redirect(url_for("permissoes.index", usuario_id=usuario_id))
