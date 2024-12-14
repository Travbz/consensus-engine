"""Database models for the Consensus Engine."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class Discussion(Base):
    __tablename__ = 'discussions'
    
    id = Column(Integer, primary_key=True)
    prompt = Column(Text, nullable=False)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    consensus_reached = Column(Integer, default=0)
    final_consensus = Column(Text, nullable=True)
    
    rounds = relationship("DiscussionRound", back_populates="discussion")

class DiscussionRound(Base):
    __tablename__ = 'discussion_rounds'
    
    id = Column(Integer, primary_key=True)
    discussion_id = Column(Integer, ForeignKey('discussions.id'))
    round_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    discussion = relationship("Discussion", back_populates="rounds")
    responses = relationship("LLMResponse", back_populates="round")

class LLMResponse(Base):
    __tablename__ = 'llm_responses'
    
    id = Column(Integer, primary_key=True)
    round_id = Column(Integer, ForeignKey('discussion_rounds.id'))
    llm_name = Column(String(100), nullable=False)
    response_text = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    round = relationship("DiscussionRound", back_populates="responses")