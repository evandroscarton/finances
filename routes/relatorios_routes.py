"""
Rotas de Relatórios: consultas agregadas de lançamentos.
Apenas leitura — nenhuma rota aqui grava dados.
"""
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from services import relatorios_service, contas_service, cartoes_service

relatorios_bp = Blueprint("relatorios", __name__, url_prefix="/relatorios")


@relatorios_bp.route("/categorias")
@login_required
def por_categoria():
    filtros = {
        "conta_id": request.args.get("conta_id", type=int) or None,
        "cartao_id": request.args.get("cartao_id", type=int) or None,
        "tipo": request.args.get("tipo") or None,
        "data_inicio": request.args.get("data_inicio") or None,
        "data_fim": request.args.get("data_fim") or None,
    }

    resultado = relatorios_service.relatorio_por_categoria(current_user.id, filtros)
    contas = contas_service.listar_contas_com_saldos(current_user.id)
    cartoes = cartoes_service.listar_cartoes(current_user.id)

    return render_template(
        "relatorios/por_categoria.html",
        categorias=resultado["categorias"],
        total_geral=resultado["total_geral"],
        contas=contas,
        cartoes=cartoes,
        filtros=filtros,
    )
