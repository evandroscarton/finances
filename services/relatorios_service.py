"""
Regras de negócio de Relatórios.
Camada fina — apenas orquestra chamadas ao repository, sem SQL.
"""
import calendar
from datetime import date
from db.connection import get_cursor
from repositories import relatorios_repository as repo
from services import permissoes_service


def relatorio_por_categoria(usuario_id, filtros):
    """
    Retorna lista de categorias com totais agregados + total geral do período.
    filtros: dict com conta_id, cartao_id, tipo, data_inicio, data_fim (todos opcionais).

    Regra de negócio: quando o usuário não informa data_inicio/data_fim no filtro,
    assumimos o mês corrente (dia 1 até o último dia do mês) como período padrão,
    para que o relatório nunca abra "sem filtro nenhum" somando todo o histórico.
    O dict `filtros` é mutado com os defaults calculados para que a tela exiba
    os inputs de data já preenchidos com o período efetivamente usado.

    contas_visiveis_ids/cartoes_visiveis_ids são obtidos da regra de
    permissoes_service e aplicados no repository — garante que o relatório
    nunca agregue valores de conta/cartão fora da parametrização do usuário.
    """
    if not filtros.get("data_inicio") and not filtros.get("data_fim"):
        hoje = date.today()
        primeiro_dia = hoje.replace(day=1)
        ultimo_dia_num = calendar.monthrange(hoje.year, hoje.month)[1]
        ultimo_dia = hoje.replace(day=ultimo_dia_num)

        filtros["data_inicio"] = primeiro_dia.isoformat()
        filtros["data_fim"] = ultimo_dia.isoformat()

    contas_ids = permissoes_service.obter_contas_visiveis_ids(usuario_id)
    cartoes_ids = permissoes_service.obter_cartoes_visiveis_ids(usuario_id)

    with get_cursor() as cur:
        categorias = repo.listar_totais_por_categoria(cur, usuario_id, filtros, contas_ids, cartoes_ids)
        total_geral = repo.somar_total_geral(cur, usuario_id, filtros, contas_ids, cartoes_ids)
        return {
            "categorias": categorias,
            "total_geral": total_geral,
        }
