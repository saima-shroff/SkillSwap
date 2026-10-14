from datetime import datetime, timezone
from uuid import uuid4

from flask_security import RoleMixin, UserMixin

from app import db

user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Integer(), db.ForeignKey("user.id"), primary_key=True),
    db.Column("role_id", db.Integer(), db.ForeignKey("role.id"), primary_key=True),
)


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False, default="")
    bio = db.Column(db.String(500), nullable=False, default="")
    location = db.Column(db.String(120), nullable=False, default="")
    active = db.Column(db.Boolean, nullable=False, default=True)
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False, default=lambda: uuid4().hex)
    roles = db.relationship("Role", secondary=user_roles, backref=db.backref("users", lazy="dynamic"))
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    category = db.Column(db.String(80), nullable=False, default="Other")


class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    skill_id = db.Column(db.Integer, db.ForeignKey("skill.id"), nullable=False)
    listing_type = db.Column(db.String(10), nullable=False)
    is_approved = db.Column(db.Boolean, nullable=False, default=False)
    moderation_status = db.Column(db.String(12), nullable=False, default="pending")
    description = db.Column(db.String(1200), nullable=False, default="")
    proficiency_level = db.Column(db.String(30), nullable=False, default="Intermediate")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    owner = db.relationship("User", backref=db.backref("listings", lazy=True))
    skill = db.relationship("Skill")
    sent_requests = db.relationship(
        "ExchangeRequest", foreign_keys="ExchangeRequest.offered_listing_id", back_populates="offered_listing"
    )
    received_requests = db.relationship(
        "ExchangeRequest", foreign_keys="ExchangeRequest.requested_listing_id", back_populates="requested_listing"
    )


class ExchangeRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    offered_listing_id = db.Column(db.Integer, db.ForeignKey("listing.id"), nullable=False)
    requested_listing_id = db.Column(db.Integer, db.ForeignKey("listing.id"), nullable=False)
    status = db.Column(db.String(12), nullable=False, default="Pending")
    sender_completed = db.Column(db.Boolean, nullable=False, default=False)
    receiver_completed = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    sender = db.relationship("User", foreign_keys=[sender_id])
    receiver = db.relationship("User", foreign_keys=[receiver_id])
    offered_listing = db.relationship(
        "Listing", foreign_keys=[offered_listing_id], back_populates="sent_requests"
    )
    requested_listing = db.relationship(
        "Listing", foreign_keys=[requested_listing_id], back_populates="received_requests"
    )


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exchange_id = db.Column(db.Integer, db.ForeignKey("exchange_request.id"), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(800), nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (
        db.UniqueConstraint("exchange_id", "reviewer_id", name="uq_review_exchange_reviewer"),
    )
    reviewer = db.relationship("User", foreign_keys=[reviewer_id])
    reviewee = db.relationship("User", foreign_keys=[reviewee_id])
