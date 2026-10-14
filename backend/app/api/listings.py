from flask import Blueprint, jsonify, request
from flask_security import current_user
from sqlalchemy import or_

from app import db
from app.api import error, json_object, protected
from app.models import Listing, Skill

listings_bp = Blueprint("listings", __name__)
LISTING_TYPES = {"Offer", "Want"}
PROFICIENCY_LEVELS = {"Beginner", "Intermediate", "Advanced", "Expert"}


def listing_json(listing):
    return {
        "id": listing.id,
        "user_id": listing.user_id,
        "owner": {
            "id": listing.owner.id,
            "name": listing.owner.name,
            "location": listing.owner.location,
        },
        "skill": {"id": listing.skill.id, "name": listing.skill.name, "category": listing.skill.category},
        "listing_type": listing.listing_type,
        "is_approved": listing.is_approved,
        "moderation_status": listing.moderation_status,
        "description": listing.description,
        "proficiency_level": listing.proficiency_level,
        "created_at": listing.created_at.isoformat(),
    }


def visible_query():
    query = Listing.query.join(Skill).join(Listing.owner)
    if getattr(current_user, "is_authenticated", False):
        return query.filter(
            Listing.owner.has(active=True),
            or_(
                (Listing.listing_type == "Want") & (Listing.is_approved.is_(True)),
                (Listing.listing_type == "Offer") & (Listing.is_approved.is_(True)),
                Listing.user_id == current_user.id,
            )
        )
    return query.filter(Listing.is_approved.is_(True), Listing.owner.has(active=True))


def set_skill(data):
    skill_id = data.get("skill_id")
    skill_name_value = data.get("skill_name", "")
    category_value = data.get("category", "Other")
    if not isinstance(category_value, str) or not isinstance(skill_name_value, str):
        raise ValueError("Skill name and category must be text.")
    skill_name = skill_name_value.strip()
    category = category_value.strip() or "Other"
    if skill_id is not None:
        if isinstance(skill_id, bool) or not isinstance(skill_id, int):
            raise ValueError("Select a valid skill.")
        skill = db.session.get(Skill, skill_id)
        if skill is None:
            raise ValueError("Select a valid skill.")
        return skill
    if not skill_name or len(skill_name) > 120 or len(category) > 80:
        raise ValueError("Provide a skill name (max 120 characters) and category (max 80 characters).")
    skill = Skill.query.filter(db.func.lower(Skill.name) == skill_name.lower()).first()
    if skill is None:
        skill = Skill(name=skill_name, category=category)
        db.session.add(skill)
        db.session.flush()
    return skill


def validate_listing_data(data, listing=None):
    listing_type = data.get("listing_type", listing.listing_type if listing else None)
    if not isinstance(listing_type, str) or listing_type not in LISTING_TYPES:
        raise ValueError("listing_type must be Offer or Want.")
    description = data.get("description", listing.description if listing else "")
    proficiency = data.get("proficiency_level", listing.proficiency_level if listing else "Intermediate")
    if not isinstance(description, str) or len(description.strip()) > 1200:
        raise ValueError("Description must be text no longer than 1200 characters.")
    if not isinstance(proficiency, str) or proficiency not in PROFICIENCY_LEVELS:
        raise ValueError("Choose a valid proficiency level.")
    return listing_type, description.strip(), proficiency


@listings_bp.get("")
def list_listings():
    query = visible_query()
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    listing_type = request.args.get("type", "").strip()
    if search:
        query = query.filter(or_(Skill.name.ilike(f"%{search}%"), Listing.description.ilike(f"%{search}%")))
    if category:
        query = query.filter(Skill.category.ilike(category))
    if listing_type in LISTING_TYPES:
        query = query.filter(Listing.listing_type == listing_type)
    items = query.order_by(Listing.created_at.desc()).limit(200).all()
    return jsonify({"listings": [listing_json(item) for item in items]})


@listings_bp.post("")
@protected
def create_listing():
    data = json_object()
    if data is None:
        return error("Request body must be a JSON object.", 400)
    try:
        listing_type, description, proficiency = validate_listing_data(data)
        skill = set_skill(data)
    except ValueError as exc:
        return error(str(exc), 400)
    listing = Listing(
        owner=current_user,
        skill=skill,
        listing_type=listing_type,
        is_approved=(listing_type == "Want"),
        moderation_status=("approved" if listing_type == "Want" else "pending"),
        description=description,
        proficiency_level=proficiency,
    )
    db.session.add(listing)
    db.session.commit()
    return jsonify({"listing": listing_json(listing)}), 201


@listings_bp.get("/<int:listing_id>")
def get_listing(listing_id):
    listing = db.session.get(Listing, listing_id)
    if listing is None:
        return error("Listing not found.", 404)
    owner = getattr(current_user, "is_authenticated", False) and current_user.id == listing.user_id
    if (not listing.is_approved or not listing.owner.active) and not owner:
        return error("Listing not found.", 404)
    return jsonify({"listing": listing_json(listing)})


@listings_bp.put("/<int:listing_id>")
@protected
def update_listing(listing_id):
    listing = db.session.get(Listing, listing_id)
    if listing is None:
        return error("Listing not found.", 404)
    if listing.user_id != current_user.id:
        return error("You can only edit your own listings.", 403)
    data = json_object()
    if data is None:
        return error("Request body must be a JSON object.", 400)
    try:
        listing_type, description, proficiency = validate_listing_data(data, listing)
        skill = set_skill(data) if "skill_id" in data or "skill_name" in data else listing.skill
    except ValueError as exc:
        return error(str(exc), 400)
    has_exchange_history = bool(listing.sent_requests or listing.received_requests)
    if has_exchange_history and (listing_type != listing.listing_type or skill.id != listing.skill_id):
        return error("The skill and listing type cannot change after an exchange has referenced this listing.", 409)
    listing.listing_type = listing_type
    listing.description = description
    listing.proficiency_level = proficiency
    listing.skill = skill
    if listing_type == "Want":
        listing.is_approved = True
        listing.moderation_status = "approved"
    elif data.get("resubmit") is True or listing_type != "Offer":
        listing.is_approved = False
        listing.moderation_status = "pending"
    elif listing.moderation_status == "approved":
        listing.is_approved = False
        listing.moderation_status = "pending"
    db.session.commit()
    return jsonify({"listing": listing_json(listing)})


@listings_bp.delete("/<int:listing_id>")
@protected
def delete_listing(listing_id):
    listing = db.session.get(Listing, listing_id)
    if listing is None:
        return error("Listing not found.", 404)
    if listing.user_id != current_user.id:
        return error("You can only delete your own listings.", 403)
    if listing.sent_requests or listing.received_requests:
        return error("A listing referenced by an exchange cannot be deleted.", 409)
    db.session.delete(listing)
    db.session.commit()
    return jsonify({"message": "Listing deleted."})
