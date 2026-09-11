"""
Regras de negócio de Relatórios.
Camada fina — apenas orquestra chamadas ao repository, sem SQL.
"""
from db.connection import get_cursor
from repositories import relatorios_repository as repo


def relatorio_por_categoria(usuario_id, filtros):
    """
    Retorna lista de categorias com totais agregados + total geral do período.
    filtros: dict com conta_id, cartao_id, tipo, data_inicio, data_fim (todos opcionais).
    """
    with get_cursor() as cur:
        categorias = repo.listar_totais_por_categoria(cur, usuario_id, filtros)
        total_geral = repo.somar_total_geral(cur, usuario_id, filtros)
        return {
            "categorias": categorias,
            "total_geral": total_geral,
        }
