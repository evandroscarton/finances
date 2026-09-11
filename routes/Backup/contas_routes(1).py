"""Rotas de contas. Toda operação usa current_user.id — nunca aceita usuario_id do body/query."""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from services import contas_service

contas_bp = Blueprint("contas", __name__, url_prefix="/contas")


@contas_bp.route("", methods=["POST"])
@login_required
def criar():
    body = request.get_json(silent=True) or {}
    try:
        conta = contas_service.criar_conta(
            current_user.id, body.get("nome"), body.get("banco"), body.get("tipo")
        )
        return jsonify(conta), 201
    except contas_service.ErroValidacao as e:
        return jsonify({"erro": str(e)}), 400


@contas_bp.route("", methods=["GET"])
@login_required
def listar():
    return jsonify(contas_service.listar_contas_com_saldo(current_user.id)), 200


@contas_bp.route("/<int:conta_id>", methods=["GET"])
@login_required
def obter(conta_id):
    conta = contas_service.obter_conta_com_saldo(conta_id, current_user.id)
    if not conta:
        return jsonify({"erro": "Conta não encontrada."}), 404
    return jsonify(conta), 200


@contas_bp.route("/<int:conta_id>", methods=["DELETE"])
@login_required
def excluir(conta_id):
    try:
        contas_service.excluir_conta(conta_id, current_user.id)
        return jsonify({"mensagem": "Conta excluída."}), 200
    except contas_service.ErroValidacao as e:
        return jsonify({"erro": str(e)}), 404
