from flask import Blueprint, jsonify, request
from flask_security import current_user

from app import db
from app.api import error, json_object, protected
from app.models import ExchangeRequest, Review

reviews_bp = Blueprint("reviews", __name__)


def review_json(review):
    return {
        "id": review.id,
        "exchange_id": review.exchange_id,
        "reviewer": {"id": review.reviewer.id, "name": review.reviewer.name},
        "reviewee": {"id": review.reviewee.id, "name": review.reviewee.name},
        "rating": review.rating,
        "comment": review.comment,
        "created_at": review.created_at.isoformat(),
    }


@reviews_bp.get("")
def list_reviews():
    query = Review.query
    reviewee_id = request.args.get("reviewee_id", type=int)
    exchange_id = request.args.get("exchange_id", type=int)
    if reviewee_id:
        query = query.filter_by(reviewee_id=reviewee_id)
    if exchange_id:
        query = query.filter_by(exchange_id=exchange_id)
    return jsonify({"reviews": [review_json(item) for item in query.order_by(Review.created_at.desc()).limit(100).all()]})


@reviews_bp.post("")
@protected
def create_review():
    data = json_object()
    if data is None:
        return error("Request body must be a JSON object.", 400)
    exchange_id = data.get("exchange_id")
    if isinstance(exchange_id, bool) or not isinstance(exchange_id, int) or exchange_id < 1:
        return error("exchange_id must be a positive integer.", 400)
    exchange = db.session.get(ExchangeRequest, exchange_id)
    if exchange is None:
        return error("Exchange not found.", 404)
    if exchange.status != "Completed":
        return error("Reviews are available only after both participants complete the exchange.", 409)
    if current_user.id == exchange.sender_id:
        reviewee_id = exchange.receiver_id
    elif current_user.id == exchange.receiver_id:
        reviewee_id = exchange.sender_id
    else:
        return error("You are not a participant in this exchange.", 403)
    if Review.query.filter_by(exchange_id=exchange.id, reviewer_id=current_user.id).first():
        return error("You have already reviewed this exchange.", 409)
    rating = data.get("rating")
    comment = data.get("comment", "")
    if isinstance(rating, bool) or not isinstance(rating, int) or not 1 <= rating <= 5:
        return error("rating must be an integer from 1 to 5.", 400)
    if not isinstance(comment, str) or len(comment.strip()) > 800:
        return error("comment must be text no longer than 800 characters.", 400)
    review = Review(
        exchange_id=exchange.id,
        reviewer_id=current_user.id,
        reviewee_id=reviewee_id,
        rating=rating,
        comment=comment.strip(),
    )
    db.session.add(review)
    db.session.commit()
    return jsonify({"review": review_json(review)}), 201
