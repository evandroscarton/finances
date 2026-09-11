"""Rotas de categorias."""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from services import categorias_service

categorias_bp = Blueprint("categorias", __name__, url_prefix="/categorias")


@categorias_bp.route("", methods=["POST"])
@login_required
def criar():
    body = request.get_json(silent=True) or {}
    try:
        categoria = categorias_service.criar_categoria(
            current_user.id, body.get("nome"), body.get("tipo"), body.get("cor")
        )
        return jsonify(categoria), 201
    except categorias_service.ErroValidacao as e:
        return jsonify({"erro": str(e)}), 400


@categorias_bp.route("", methods=["GET"])
@login_required
def listar():
    return jsonify(categorias_service.listar_categorias(current_user.id)), 200
