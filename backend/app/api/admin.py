from flask import Blueprint, jsonify, request
from app import db
from app.api import admin_required, error, json_object
from app.models import ExchangeRequest, Listing, Review, User

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/stats")
@admin_required
def stats():
    return jsonify(
        {
            "total_users": User.query.count(),
            "active_users": User.query.filter_by(active=True).count(),
            "active_offers": Listing.query.join(User).filter(
                Listing.listing_type == "Offer", Listing.is_approved.is_(True), User.active.is_(True)
            ).count(),
            "pending_offers": Listing.query.filter_by(listing_type="Offer", moderation_status="pending").count(),
            "completed_exchanges": ExchangeRequest.query.filter_by(status="Completed").count(),
            "reviews": Review.query.count(),
        }
    )


@admin_bp.get("/users")
@admin_required
def users():
    records = User.query.order_by(User.created_at.desc()).limit(500).all()
    return jsonify(
        {
            "users": [
                {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "active": user.active,
                    "roles": [role.name for role in user.roles],
                    "created_at": user.created_at.isoformat(),
                }
                for user in records
            ]
        }
    )


@admin_bp.put("/users/<int:user_id>/status")
@admin_required
def update_user_status(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return error("User not found.", 404)
    data = json_object()
    if data is None:
        return error("Request body must be a JSON object.", 400)
    active = data.get("active")
    if not isinstance(active, bool):
        return error("active must be a boolean.", 400)
    user.active = active
    db.session.commit()
    return jsonify({"user": {"id": user.id, "email": user.email, "active": user.active}})


@admin_bp.get("/listings/pending")
@admin_required
def pending_listings():
    from app.api.listings import listing_json

    records = Listing.query.filter_by(listing_type="Offer", moderation_status="pending").order_by(Listing.created_at.asc()).all()
    return jsonify({"listings": [listing_json(item) for item in records]})


@admin_bp.put("/listings/<int:listing_id>/approve")
@admin_required
def moderate_listing(listing_id):
    listing = db.session.get(Listing, listing_id)
    if listing is None:
        return error("Listing not found.", 404)
    if listing.listing_type != "Offer":
        return error("Only Offer listings can be moderated.", 400)
    if listing.moderation_status != "pending":
        return error("This listing is not awaiting moderation.", 409)
    data = json_object()
    if data is None:
        return error("Request body must be a JSON object.", 400)
    approved = data.get("approved")
    if not isinstance(approved, bool):
        return error("approved must be a boolean.", 400)
    listing.is_approved = approved
    listing.moderation_status = "approved" if approved else "rejected"
    db.session.commit()
    from app.api.listings import listing_json

    return jsonify({"listing": listing_json(listing)})
