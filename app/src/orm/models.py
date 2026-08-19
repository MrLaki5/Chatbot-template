from sqlalchemy import JSON, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Videos(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String, unique=True, nullable=False)
    summary = Column(String, nullable=False)
    highlight_questions = Column(JSON, nullable=False)

    def __repr__(self):
        return (
            f"<Videos(id={self.id}, video_id={self.video_id},"
            f" summary='{self.summary}', highlight_questions={self.highlight_questions})>"
        )


class Permanent(Base):
    __tablename__ = "permanent"

    id = Column(Integer, primary_key=True, index=True)
    bearer_token = Column(String, nullable=False)

    def __repr__(self):
        return f"<Permanent(id={self.id}, bearer_token='{self.bearer_token}')>"
