"""
Repository de permissões de acesso. A regra "sem parametrização = vê tudo" é
resolvida no service (aqui só existem CRUDs simples). Toda escrita é feita
dentro de uma transação atômica no service (apaga tudo e reinsere).
"""


def listar_contas_permitidas_ids(cur, usuario_id):
    cur.execute(
        "SELECT conta_id FROM permissoes_conta WHERE usuario_id = %s",
        (usuario_id,),
    )
    return [row["conta_id"] for row in cur.fetchall()]


def listar_cartoes_permitidos_ids(cur, usuario_id):
    cur.execute(
        "SELECT cartao_id FROM permissoes_cartao WHERE usuario_id = %s",
        (usuario_id,),
    )
    return [row["cartao_id"] for row in cur.fetchall()]


def substituir_permissoes(cur, usuario_id, contas_ids, cartoes_ids):
    """
    Estratégia "delete + insert": mais simples e segura para refletir
    exatamente o que veio marcado no formulário (checkboxes desmarcados
    significam remoção da permissão).
    """
    cur.execute("DELETE FROM permissoes_conta WHERE usuario_id = %s", (usuario_id,))
    cur.execute("DELETE FROM permissoes_cartao WHERE usuario_id = %s", (usuario_id,))

    for conta_id in contas_ids:
        cur.execute(
            "INSERT INTO permissoes_conta (usuario_id, conta_id) VALUES (%s, %s)",
            (usuario_id, conta_id),
        )
    for cartao_id in cartoes_ids:
        cur.execute(
            "INSERT INTO permissoes_cartao (usuario_id, cartao_id) VALUES (%s, %s)",
            (usuario_id, cartao_id),
        )
