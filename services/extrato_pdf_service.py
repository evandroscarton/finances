"""
Parser do extrato bancário em PDF (layout Viacredi, conforme exemplo fornecido).

Layout da linha de movimento (colunas nesta ordem):
  DATA | DESCRICAO | DOCUMENTO | CREDITO (R$) | DEBITO (R$) | SALDO (R$)

Exemplo real:
  01/09/2026 CREDITO PIX - Evandro Miguel Scarton 893815.146 17.056,00 18.340,52

Como o texto extraído via pdfplumber vem "corrido" (sem tabulação confiável),
usamos regex para capturar: data (dd/mm/aaaa), o número do documento
(token numérico com ponto/traço, sem vírgula decimal) e os valores monetários
no padrão brasileiro (1.234,56). A descrição é tudo que sobra entre a data
e o número do documento.

Linhas de cabeçalho/rodapé (SALDO ANTERIOR, TOTAL, SAC, OUVIDORIA etc.)
são ignoradas via lista de exclusão.
"""
import re
import pdfplumber
from datetime import datetime
from decimal import Decimal, InvalidOperation

# Linhas que nunca são lançamentos (cabeçalho, rodapé, avisos)
LINHAS_IGNORADAS = (
    "EXTRATO", "Período", "Emitido em", "Nome:", "Cooperativa:",
    "SALDO (R$)", "SALDO ANTERIOR", "Os dados acima", "TOTAL",
    "SAC", "OUVIDORIA", "Atendimento", "-- ", "DÉBITO (R$)", "DATA DESCRI",
)

# Data no formato dd/mm/aaaa
REGEX_DATA = re.compile(r"(\d{2}/\d{2}/\d{4})")
# Valor monetário brasileiro, com sinal opcional: -12.345,67 ou 12.345,67
REGEX_VALOR = re.compile(r"(-?\d{1,3}(?:\.\d{3})*,\d{2})")
# Número de documento: token numérico (com ponto/traço opcional) SEM vírgula decimal
# — aparece entre a descrição e o primeiro valor monetário. Ex.: "893815.146"
REGEX_DOCUMENTO = re.compile(r"\b[\d.\-/]{4,}\b")


def _parse_valor_br(valor_str: str) -> Decimal:
    """Converte '17.056,00' ou '-15.000,00' para Decimal."""
    limpo = valor_str.replace(".", "").replace(",", ".")
    try:
        return Decimal(limpo)
    except InvalidOperation:
        raise ValueError(f"Valor monetário inválido no PDF: {valor_str}")


def extrair_texto_pdf(arquivo_stream) -> str:
    """Extrai todo o texto do PDF usando pdfplumber."""
    texto_completo = []
    with pdfplumber.open(arquivo_stream) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text() or ""
            texto_completo.append(texto)
    return "\n".join(texto_completo)


def _extrair_descricao(trecho: str) -> str:
    """
    Recebe o trecho da linha ENTRE o fim da data e o início do primeiro
    valor monetário (ex.: "CREDITO PIX - Evandro Miguel Scarton 893815.146 ").
    Remove o número de documento (último token puramente numérico/pontuado)
    e retorna só a descrição.
    """
    trecho = trecho.strip()
    if not trecho:
        return ""

    # Procura o número de documento como o ÚLTIMO token do trecho
    tokens = trecho.split()
    if tokens and REGEX_DOCUMENTO.fullmatch(tokens[-1]):
        tokens = tokens[:-1]

    return " ".join(tokens).strip()


def parsear_linhas_extrato(texto_pdf: str) -> list[dict]:
    """
    Retorna lista de dicts:
    { "data": date, "valor": Decimal, "tipo": "credito"/"debito",
      "descricao": str, "linha_original": str }

    O sinal do valor já vem correto do PDF (débito com '-', crédito sem sinal).
    Classificamos tipo pelo sinal do PRIMEIRO valor monetário encontrado na linha
    após a data (que corresponde à coluna Crédito/Débito, não ao saldo acumulado).
    A descrição é extraída do trecho entre a data e esse primeiro valor,
    descontando o número de documento.
    """
    linhas_resultado = []

    for linha_bruta in texto_pdf.splitlines():
        linha = linha_bruta.strip()
        if not linha:
            continue
        if any(linha.startswith(prefixo) or prefixo in linha for prefixo in LINHAS_IGNORADAS):
            continue

        match_data = REGEX_DATA.search(linha)
        if not match_data:
            continue  # linha sem data não é lançamento

        data_str = match_data.group(1)
        try:
            data_lancamento = datetime.strptime(data_str, "%d/%m/%Y").date()
        except ValueError:
            continue

        # Todos os valores monetários da linha, na ordem em que aparecem.
        valores_encontrados = list(REGEX_VALOR.finditer(linha))
        if not valores_encontrados:
            continue

        primeiro_valor_match = valores_encontrados[0]

        # O primeiro valor após a data é o valor do lançamento (débito ou crédito).
        # Os demais (se houver) são saldo acumulado — descartados aqui.
        valor_lancamento = _parse_valor_br(primeiro_valor_match.group(1))
        tipo = "debito" if valor_lancamento < 0 else "credito"

        # Descrição = trecho entre o fim da data e o início do primeiro valor,
        # descontando o número de documento (ex.: "893815.146").
        trecho_meio = linha[match_data.end():primeiro_valor_match.start()]
        descricao = _extrair_descricao(trecho_meio)

        linhas_resultado.append({
            "data": data_lancamento,
            "valor": valor_lancamento,
            "tipo": tipo,
            "descricao": descricao,
            "linha_original": linha,
        })

    return linhas_resultado
