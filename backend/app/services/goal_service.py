"""
Goal service - business logic for fitness goals.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.user import User
from app.models.workout import Goal
from app.schemas.workout import GoalCreate, GoalUpdate
from app.core.logging import get_logger

logger = get_logger(__name__)


class GoalService:
    """Service for goal-related operations."""
    
    @staticmethod
    def create_goal(db: Session, user: User, goal_data: GoalCreate) -> Goal:
        """Create a new goal.
        
        Args:
            db: Database session
            user: User creating the goal
            goal_data: Goal creation data
            
        Returns:
            Created goal
        """
        logger.info(f"Creating goal for user {user.id}: {goal_data.title}")
        
        goal = Goal(
            user_id=user.id,
            **goal_data.model_dump()
        )
        db.add(goal)
        db.commit()
        db.refresh(goal)
        
        logger.info(f"Created goal {goal.id}")
        return goal
    
    @staticmethod
    def get_goal(db: Session, goal_id: int, user_id: int) -> Optional[Goal]:
        """Get a goal by ID for a specific user.
        
        Args:
            db: Database session
            goal_id: Goal ID
            user_id: User ID
            
        Returns:
            Goal if found, None otherwise
        """
        return db.query(Goal).filter(
            Goal.id == goal_id,
            Goal.user_id == user_id
        ).first()
    
    @staticmethod
    def get_goals(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        is_completed: Optional[bool] = None
    ) -> List[Goal]:
        """Get goals for a user with optional filters.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            is_active: Filter by active status
            is_completed: Filter by completion status
            
        Returns:
            List of goals
        """
        query = db.query(Goal).filter(Goal.user_id == user_id)
        
        if is_active is not None:
            query = query.filter(Goal.is_active == is_active)
        if is_completed is not None:
            query = query.filter(Goal.is_completed == is_completed)
        
        return query.order_by(desc(Goal.created_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_goal(
        db: Session,
        goal_id: int,
        user_id: int,
        goal_data: GoalUpdate
    ) -> Optional[Goal]:
        """Update a goal.
        
        Args:
            db: Database session
            goal_id: Goal ID
            user_id: User ID
            goal_data: Update data
            
        Returns:
            Updated goal if found, None otherwise
        """
        goal = GoalService.get_goal(db, goal_id, user_id)
        if not goal:
            return None
        
        # Update fields
        update_data = goal_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(goal, field, value)
        
        # Auto-set completed_date if marking as completed
        if goal_data.is_completed and not goal.completed_date:
            goal.completed_date = datetime.utcnow()
        
        db.commit()
        db.refresh(goal)
        
        logger.info(f"Updated goal {goal_id}")
        return goal
    
    @staticmethod
    def delete_goal(db: Session, goal_id: int, user_id: int) -> bool:
        """Delete a goal.
        
        Args:
            db: Database session
            goal_id: Goal ID
            user_id: User ID
            
        Returns:
            True if deleted, False if not found
        """
        goal = GoalService.get_goal(db, goal_id, user_id)
        if not goal:
            return False
        
        db.delete(goal)
        db.commit()
        
        logger.info(f"Deleted goal {goal_id}")
        return True
    
    @staticmethod
    def update_goal_progress(
        db: Session,
        goal_id: int,
        user_id: int,
        current_value: float
    ) -> Optional[Goal]:
        """Update the current progress value of a goal.
        
        Args:
            db: Database session
            goal_id: Goal ID
            user_id: User ID
            current_value: New current value
            
        Returns:
            Updated goal if found, None otherwise
        """
        goal = GoalService.get_goal(db, goal_id, user_id)
        if not goal:
            return None
        
        goal.current_value = current_value
        
        # Check if goal is completed
        if goal.target_value and current_value >= goal.target_value:
            if not goal.is_completed:
                goal.is_completed = True
                goal.completed_date = datetime.utcnow()
                logger.info(f"Goal {goal_id} marked as completed!")
        
        db.commit()
        db.refresh(goal)
        
        return goal

