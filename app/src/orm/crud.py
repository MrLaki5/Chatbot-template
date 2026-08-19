import os
import secrets
import sys
from typing import List, Optional

from sqlalchemy.orm import Session

from .models import Permanent, Videos

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logging_config import get_logger

logger = get_logger(__name__)


def create_video(
    db: Session, video_id: str, summary: str, highlight_questions: List[str], override: bool
) -> Videos:
    """
    Create a new video record in the database.

    Args:
        db: SQLAlchemy database session
        video_id: Unique identifier for the video
        summary: Video summary text
        highlight_questions: List of highlight questions
        override: If True, delete existing video with same ID; if False, skip if exists

    Returns:
        Created Videos object
    """
    # Check if video already exists
    existing_video = get_video(db, video_id)

    if existing_video:
        if not override:
            # Skip creation if override is False
            logger.info(f"Video {video_id} already exists. Skipping creation (override=False)")
            return existing_video
        else:
            # Delete existing video if override is True
            logger.info(
                f"Video {video_id} already exists. Deleting existing video (override=True)"
            )
            delete_video(db, video_id)
            logger.info(f"Existing video {video_id} deleted successfully")

    # Create new video
    logger.info(f"Creating new video record for {video_id}")
    db_video = Videos(video_id=video_id, summary=summary, highlight_questions=highlight_questions)
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    logger.info(f"Video {video_id} created successfully with ID: {db_video.id}")
    return db_video


def get_video(db: Session, video_id: str) -> Optional[Videos]:
    """
    Get a video by ID.

    Args:
        db: SQLAlchemy database session
        video_id: ID of the video to retrieve

    Returns:
        Videos object or None if not found
    """
    return db.query(Videos).filter(Videos.video_id == video_id).first()


def get_video_count(db: Session) -> int:
    """
    Get the total count of videos in the database.

    Args:
        db: SQLAlchemy database session

    Returns:
        Total count of videos
    """
    return db.query(Videos).count()


def delete_video(db: Session, video_id: str) -> bool:
    """
    Delete a video record.

    Args:
        db: SQLAlchemy database session
        video_id: ID of the video to delete

    Returns:
        True if deleted, False if not found
    """
    db_video = db.query(Videos).filter(Videos.video_id == video_id).first()
    if db_video:
        db.delete(db_video)
        db.commit()
        return True
    return False


def create_bearer(db: Session) -> Permanent:
    """
    Create a new bearer token record in the database with a generated token.

    Args:
        db: SQLAlchemy database session

    Returns:
        Created Permanent object with generated bearer token
    """
    # Generate a secure random bearer token
    bearer_token = secrets.token_urlsafe(32)

    logger.info("Creating new bearer token record")
    db_permanent = Permanent(bearer_token=bearer_token)
    db.add(db_permanent)
    db.commit()
    db.refresh(db_permanent)
    logger.info(f"Bearer token created successfully with ID: {db_permanent.id}")
    return db_permanent


def delete_bearer(db: Session, bearer_token: str) -> bool:
    """
    Delete a bearer token record.

    Args:
        db: SQLAlchemy database session
        bearer_token: Bearer token string to delete

    Returns:
        True if deleted, False if not found
    """
    db_permanent = db.query(Permanent).filter(Permanent.bearer_token == bearer_token).first()
    if db_permanent:
        logger.info(f"Deleting bearer token with ID: {db_permanent.id}")
        db.delete(db_permanent)
        db.commit()
        logger.info(f"Bearer token {db_permanent.id} deleted successfully")
        return True
    logger.warning("Bearer token not found")
    return False


def regenerate_bearer(db: Session) -> Permanent:
    """
    Regenerate a bearer token by deleting any existing one and creating a new one.

    Args:
        db: SQLAlchemy database session

    Returns:
        Created Permanent object with new bearer token
    """
    # Delete any existing bearer token
    existing_bearer = db.query(Permanent).first()
    if existing_bearer:
        logger.info(f"Deleting existing bearer token with ID: {existing_bearer.id}")
        db.delete(existing_bearer)
        db.commit()
        logger.info("Existing bearer token deleted successfully")
    else:
        logger.info("No existing bearer token found")

    # Create new bearer token
    logger.info("Generating new bearer token")
    new_bearer = create_bearer(db)
    logger.info("Bearer token regenerated successfully")
    return new_bearer
