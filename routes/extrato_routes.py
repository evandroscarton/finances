"""
Rotas de Extrato: consulta de lançamentos (compensados, e opcionalmente
pendentes) com saldo acumulado.
Apenas leitura — nenhuma rota aqui grava dados.
"""
from datetime import date
from calendar import monthrange
from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user
from services import extrato_service, contas_service, cartoes_service
from services.extrato_service import ErroValidacao

extrato_bp = Blueprint("extrato", __name__, url_prefix="/extrato")


def _primeiro_e_ultimo_dia_mes_atual():
    """Sugestão default de período: do dia 1 até o último dia do mês corrente."""
    hoje = date.today()
    primeiro_dia = hoje.replace(day=1)
    ultimo_dia = hoje.replace(day=monthrange(hoje.year, hoje.month)[1])
    return primeiro_dia.isoformat(), ultimo_dia.isoformat()


@extrato_bp.route("/")
@login_required
def index():
    contas = contas_service.listar_contas_com_saldos(current_user.id)
    cartoes = cartoes_service.listar_cartoes(current_user.id)

    default_inicio, default_fim = _primeiro_e_ultimo_dia_mes_atual()

    filtros = {
        "conta_id": request.args.get("conta_id", type=int) or None,
        "cartao_id": request.args.get("cartao_id", type=int) or None,
        # Se o usuário não informou data, sugere o mês atual (início e fim)
        "data_inicio": request.args.get("data_inicio") or default_inicio,
        "data_fim": request.args.get("data_fim") or default_fim,
        # Padrão: NÃO incluir pendentes. Só entra True se o checkbox foi
        # explicitamente marcado (valor "1" enviado pelo form).
        "incluir_pendentes": request.args.get("incluir_pendentes") == "1",
    }

    resultado = None
    # Só gera o extrato se o usuário já selecionou conta ou cartão
    if filtros["conta_id"] or filtros["cartao_id"]:
        try:
            resultado = extrato_service.gerar_extrato(
                current_user.id, filtros["conta_id"], filtros["cartao_id"],
                filtros["data_inicio"], filtros["data_fim"],
                filtros["incluir_pendentes"],
            )
        except ErroValidacao as e:
            flash(str(e), "erro")

    return render_template(
        "extrato/index.html",
        contas=contas, cartoes=cartoes, filtros=filtros, resultado=resultado,
    )
