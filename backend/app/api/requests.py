from flask import Blueprint, jsonify, request
from flask_security import current_user

from app import db
from app.api import error, json_object, protected
from app.api.listings import listing_json
from app.models import ExchangeRequest, Listing

requests_bp = Blueprint("requests", __name__)
VALID_STATUSES = {"Pending", "Accepted", "Declined", "Completed", "Cancelled"}


def request_json(item):
    return {
        "id": item.id,
        "sender_id": item.sender_id,
        "receiver_id": item.receiver_id,
        "sender": {"id": item.sender.id, "name": item.sender.name},
        "receiver": {"id": item.receiver.id, "name": item.receiver.name},
        "offered_listing": listing_json(item.offered_listing),
        "requested_listing": listing_json(item.requested_listing),
        "status": item.status,
        "sender_completed": item.sender_completed,
        "receiver_completed": item.receiver_completed,
        "created_at": item.created_at.isoformat(),
    }


@requests_bp.get("")
@protected
def list_requests():
    items = ExchangeRequest.query.filter(
        (ExchangeRequest.sender_id == current_user.id) | (ExchangeRequest.receiver_id == current_user.id)
    ).order_by(ExchangeRequest.created_at.desc()).all()
    return jsonify({"requests": [request_json(item) for item in items]})


@requests_bp.post("")
@protected
def create_request():
    data = json_object()
    if data is None:
        return error("Request body must be a JSON object.", 400)
    for key in ("offered_listing_id", "requested_listing_id"):
        value = data.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            return error(f"{key} must be a positive integer.", 400)
    offered = db.session.get(Listing, data.get("offered_listing_id"))
    requested = db.session.get(Listing, data.get("requested_listing_id"))
    if offered is None or requested is None:
        return error("Both exchange listings must exist.", 404)
    if offered.user_id != current_user.id or offered.listing_type != "Offer":
        return error("Select one of your own Offer listings.", 403)
    if not offered.is_approved:
        return error("Your Offer must be approved before you can use it in an exchange.", 409)
    if requested.user_id == current_user.id or requested.owner.active is False:
        return error("Choose an active member's listing other than your own.", 400)
    if requested.listing_type == "Offer" and not requested.is_approved:
        return error("The requested Offer is not available.", 404)
    if offered.owner.active is False:
        return error("Your account is inactive.", 403)
    item = ExchangeRequest(
        sender_id=current_user.id,
        receiver_id=requested.user_id,
        offered_listing=offered,
        requested_listing=requested,
        status="Pending",
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({"request": request_json(item)}), 201


@requests_bp.put("/<int:request_id>")
@protected
def update_request(request_id):
    item = db.session.get(ExchangeRequest, request_id)
    if item is None:
        return error("Exchange request not found.", 404)
    if current_user.id not in {item.sender_id, item.receiver_id}:
        return error("You are not a participant in this exchange.", 403)
    data = json_object()
    if data is None:
        return error("Request body must be a JSON object.", 400)
    action = data.get("action")
    if not isinstance(action, str):
        return error("action must be accept, decline, cancel, or complete.", 400)
    if action in {"accept", "decline"}:
        if current_user.id != item.receiver_id:
            return error("Only the receiver can accept or decline.", 403)
        if item.status != "Pending":
            return error("Only pending requests can be accepted or declined.", 409)
        item.status = "Accepted" if action == "accept" else "Declined"
    elif action == "cancel":
        if current_user.id != item.sender_id:
            return error("Only the sender can cancel this request.", 403)
        if item.status != "Pending":
            return error("Only pending requests can be cancelled.", 409)
        item.status = "Cancelled"
    elif action == "complete":
        if item.status != "Accepted":
            return error("Only accepted exchanges can be completed.", 409)
        if current_user.id == item.sender_id:
            if item.sender_completed:
                return error("You have already confirmed completion.", 409)
            item.sender_completed = True
        else:
            if item.receiver_completed:
                return error("You have already confirmed completion.", 409)
            item.receiver_completed = True
        if item.sender_completed and item.receiver_completed:
            item.status = "Completed"
    else:
        return error("action must be accept, decline, cancel, or complete.", 400)
    db.session.commit()
    return jsonify({"request": request_json(item)})
