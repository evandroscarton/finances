"""Rotas de cartões de crédito."""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from services import cartoes_service

cartoes_bp = Blueprint("cartoes", __name__, url_prefix="/cartoes")


@cartoes_bp.route("", methods=["POST"])
@login_required
def criar():
    body = request.get_json(silent=True) or {}
    try:
        cartao = cartoes_service.criar_cartao(
            current_user.id, body.get("nome"), body.get("limite"),
            body.get("dia_fechamento"), body.get("dia_vencimento"),
            body.get("conta_pagamento_id"),
        )
        return jsonify(cartao), 201
    except cartoes_service.ErroValidacao as e:
        return jsonify({"erro": str(e)}), 400


@cartoes_bp.route("", methods=["GET"])
@login_required
def listar():
    return jsonify(cartoes_service.listar_cartoes_com_fatura(current_user.id)), 200
