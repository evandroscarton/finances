"""
Regra de negócio da conciliação de extrato em PDF x lançamentos do sistema.

Casamento (matching): data_lancamento == data da linha do PDF E valor igual
(mesmo sinal, mesma centavos). Cada lançamento do sistema só pode ser usado
em UM casamento — evita que duas linhas do PDF "capturem" o mesmo lançamento
por engano (ex.: dois lançamentos de mesmo valor no mesmo dia).

Resultado devolvido à rota, para renderizar a tela:
- linhas_pdf: cada linha do PDF com status "encontrado" ou "nao_encontrado"
- lancamentos_somente_sistema: lançamentos do período que não bateram com
  nenhuma linha do PDF (para destaque na tela)
"""
from decimal import Decimal

from db.connection import get_cursor
from repositories.lancamentos_repository import listar_lancamentos_por_conta_periodo
from services.extrato_pdf_service import extrair_texto_pdf, parsear_linhas_extrato


def conciliar_extrato(usuario_id: int, conta_id: int, arquivo_pdf_stream) -> dict:
    texto = extrair_texto_pdf(arquivo_pdf_stream)
    linhas_pdf = parsear_linhas_extrato(texto)

    if not linhas_pdf:
        raise ValueError("Não foi possível identificar nenhum lançamento no PDF enviado.")

    data_inicio = min(l["data"] for l in linhas_pdf)
    data_fim = max(l["data"] for l in linhas_pdf)

    # Somente leitura -> commit=False (não precisa gravar nada aqui)
    with get_cursor(commit=False) as cursor:
        lancamentos_sistema = listar_lancamentos_por_conta_periodo(
            cursor, usuario_id, conta_id, data_inicio, data_fim
        )

    ids_usados = set()
    resultado_linhas_pdf = []

    for linha in linhas_pdf:
        casamento = None
        for lanc in lancamentos_sistema:
            if lanc["id"] in ids_usados:
                continue
            if lanc["data_lancamento"] == linha["data"] and Decimal(lanc["valor"]) == linha["valor"]:
                casamento = lanc
                break

        if casamento:
            ids_usados.add(casamento["id"])
            resultado_linhas_pdf.append({
                **linha,
                "status": "encontrado",
                "lancamento_id": casamento["id"],
            })
        else:
            resultado_linhas_pdf.append({
                **linha,
                "status": "nao_encontrado",
                "lancamento_id": None,
            })

    lancamentos_somente_sistema = [
        lanc for lanc in lancamentos_sistema if lanc["id"] not in ids_usados
    ]

    return {
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "linhas_pdf": resultado_linhas_pdf,
        "lancamentos_somente_sistema": lancamentos_somente_sistema,
        "total_linhas_pdf": len(linhas_pdf),
        "total_encontrados": sum(1 for l in resultado_linhas_pdf if l["status"] == "encontrado"),
        "total_nao_encontrados": sum(1 for l in resultado_linhas_pdf if l["status"] == "nao_encontrado"),
    }
