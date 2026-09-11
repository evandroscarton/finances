"""Rotas de transferências."""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from services import transferencias_service

transferencias_bp = Blueprint("transferencias", __name__, url_prefix="/transferencias")


@transferencias_bp.route("", methods=["POST"])
@login_required
def criar():
    body = request.get_json(silent=True) or {}
    try:
        resultado = transferencias_service.criar_transferencia(
            current_user.id, body.get("conta_origem_id"), body.get("conta_destino_id"),
            body.get("valor"), body.get("data"), body.get("descricao"),
        )
        return jsonify(resultado), 201
    except transferencias_service.ErroValidacao as e:
        return jsonify({"erro": str(e)}), 400


@transferencias_bp.route("", methods=["GET"])
@login_required
def listar():
    return jsonify(transferencias_service.listar_transferencias(current_user.id)), 200
