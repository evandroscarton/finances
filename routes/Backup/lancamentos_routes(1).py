"""Rotas de lançamentos."""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from services import lancamentos_service
from repositories import lancamentos_repository as lancamentos_repo

lancamentos_bp = Blueprint("lancamentos", __name__, url_prefix="/lancamentos")


@lancamentos_bp.route("", methods=["POST"])
@login_required
def criar():
    body = request.get_json(silent=True) or {}
    try:
        lanc = lancamentos_service.criar_lancamento(
            current_user.id,
            body.get("conta_id"),
            body.get("cartao_id"),
            body.get("categoria_id"),
            body.get("descricao"),
            body.get("valor"),
            body.get("data_lancamento"),
            body.get("data_compensacao"),
        )
        return jsonify(lanc), 201
    except lancamentos_service.ErroValidacao as e:
        return jsonify({"erro": str(e)}), 400


@lancamentos_bp.route("/conta/<int:conta_id>", methods=["GET"])
@login_required
def listar_por_conta(conta_id):
    return jsonify(lancamentos_repo.listar_lancamentos_por_conta(current_user.id, conta_id)), 200


@lancamentos_bp.route("/cartao/<int:cartao_id>", methods=["GET"])
@login_required
def listar_por_cartao(cartao_id):
    return jsonify(lancamentos_repo.listar_lancamentos_por_cartao(current_user.id, cartao_id)), 200


@lancamentos_bp.route("/<int:lancamento_id>", methods=["DELETE"])
@login_required
def excluir(lancamento_id):
    try:
        lancamentos_service.excluir_lancamento(lancamento_id, current_user.id)
        return jsonify({"mensagem": "Lançamento excluído."}), 200
    except lancamentos_service.ErroValidacao as e:
        return jsonify({"erro": str(e)}), 400


@lancamentos_bp.route("/pagar-fatura", methods=["POST"])
@login_required
def pagar_fatura():
    body = request.get_json(silent=True) or {}
    try:
        lanc = lancamentos_service.pagar_fatura_cartao(
            current_user.id, body.get("cartao_id"), body.get("conta_pagamento_id"),
            body.get("valor"), body.get("data_pagamento"),
        )
        return jsonify(lanc), 201
    except lancamentos_service.ErroValidacao as e:
        return jsonify({"erro": str(e)}), 400
