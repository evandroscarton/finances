"""
Filtros Jinja customizados para formatação de valores no padrão brasileiro.
Registrado em create_app() via app.jinja_env.filters.
"""
from decimal import Decimal


def moeda_br(valor):
    """
    Formata um valor Decimal/float/int no padrão monetário brasileiro:
    milhar separado por ponto, decimal separado por vírgula.
    Ex.: Decimal('1234.5') -> '1.234,50'
    """
    if valor is None:
        valor = Decimal("0")
    valor = Decimal(str(valor))
    negativo = valor < 0
    valor = abs(valor)

    # Formata com separador de milhar padrão (en-US) e depois converte para pt-BR
    texto = f"{valor:,.2f}"  # ex.: '1,234.50'
    texto = texto.replace(",", "_TEMP_").replace(".", ",").replace("_TEMP_", ".")

    return f"-{texto}" if negativo else texto
