from flask import Blueprint, jsonify
from flask_security import current_user

from app import db
from app.api import error, json_object, protected
from app.api.auth import user_json
from app.models import ExchangeRequest, Listing, Review

profile_bp = Blueprint("profile", __name__)


@profile_bp.get("")
@protected
def get_profile():
    listings = Listing.query.filter_by(user_id=current_user.id).all()
    requests = ExchangeRequest.query.filter(
        (ExchangeRequest.sender_id == current_user.id) | (ExchangeRequest.receiver_id == current_user.id)
    ).all()
    reviews = Review.query.filter_by(reviewee_id=current_user.id).all()
    ratings = [review.rating for review in reviews]
    return jsonify(
        {
            "user": user_json(current_user),
            "stats": {
                "listings": len(listings),
                "offers": sum(item.listing_type == "Offer" for item in listings),
                "wants": sum(item.listing_type == "Want" for item in listings),
                "pending_requests": sum(item.status == "Pending" for item in requests),
                "active_exchanges": sum(item.status == "Accepted" for item in requests),
                "completed_exchanges": sum(item.status == "Completed" for item in requests),
                "average_rating": round(sum(ratings) / len(ratings), 1) if ratings else None,
                "review_count": len(ratings),
            },
        }
    )


@profile_bp.put("")
@protected
def update_profile():
    data = json_object()
    if data is None:
        return error("Request body must be a JSON object.", 400)
    for field, limit in (("name", 100), ("bio", 500), ("location", 120)):
        if field in data:
            value = data[field]
            if not isinstance(value, str) or len(value.strip()) > limit:
                return error(f"{field} must be text no longer than {limit} characters.", 400)
            if field == "name" and len(value.strip()) < 2:
                return error("Name must contain at least 2 characters.", 400)
            setattr(current_user, field, value.strip())
    db.session.commit()
    return jsonify({"user": user_json(current_user)})
