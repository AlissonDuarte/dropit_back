import models
from singleton.log import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, func
from sqlalchemy.future import select
from services import notification_service

TAG = "Reaction Repository -> "


async def create_post_reaction(db: AsyncSession, post: models.Post, user:models.User, raw_reaction:str):
    enum_map = {
        "love": models.ReactionType.LOVE.name,
        "like": models.ReactionType.LIKE.name,
        "support": models.ReactionType.SUPPORT.name,
        "sad": models.ReactionType.SAD.name
    }
    
    reaction = enum_map[raw_reaction]
    logger.info("{} User: {} reacted post: {} with: {}".format(
        TAG, 
        user.username, 
        post.title, 
        reaction
        )
    )
    try:
        existing_reaction = await db.execute(
            select(models.PostReaction)
            .where(
                and_(
                    models.PostReaction.user_id == user.uuid,
                    models.PostReaction.post_id == post.uuid
                )
            )
        )
        existing_reaction = existing_reaction.scalar_one_or_none()
        reaction_counts = await db.execute(
            select(models.PostReactionCount)
            .where(models.PostReactionCount.post_id == post.uuid)
        )
        reaction_counts = reaction_counts.scalar_one_or_none()
    except Exception as e:
        await db.rollback()
        logger.error("%s Error while restoring react information: %s", TAG, str(e))
        return {
            "status":"error",
            "message": str(e),
            "reaction": reaction,
            "counts": {
                "love": 0,
                "like": 0,
                "support": 0,
                "sad": 0
            }
        }
    
    try:
        if not reaction_counts:
            reaction_counts = models.PostReactionCount(
                post_id=post.uuid,
                love=0,
                like=0,
                support=0,
                sad=0
            )
            db.add(reaction_counts) 
        if existing_reaction:
            if existing_reaction.reaction_type == models.ReactionType.LOVE and reaction_counts.love > 0:
                reaction_counts.love -= 1
            elif existing_reaction.reaction_type == models.ReactionType.LIKE and reaction_counts.like > 0:
                reaction_counts.like -= 1
            elif existing_reaction.reaction_type == models.ReactionType.SUPPORT and reaction_counts.support > 0:
                reaction_counts.support -= 1
            elif existing_reaction.reaction_type == models.ReactionType.SAD and reaction_counts.sad > 0:
                reaction_counts.sad -= 1
            
            existing_reaction.reaction_type = reaction
        else:
            new_reaction = models.PostReaction(
                user_id=user.uuid,
                post_id=post.uuid,
                reaction_type=reaction
            )
            db.add(new_reaction)
        
        if reaction == models.ReactionType.LOVE.name:
            reaction_counts.love += 1
        elif reaction == models.ReactionType.LIKE.name:
            reaction_counts.like += 1
        elif reaction == models.ReactionType.SUPPORT.name:
            reaction_counts.support += 1
        elif reaction == models.ReactionType.SAD.name:
            reaction_counts.sad += 1
        
        await db.commit()
        
        await db.refresh(reaction_counts)
        if existing_reaction:
            await db.refresh(existing_reaction)
        
        return {
            "status": "success",
            "message": "Reaction created successfully",
            "reaction": reaction,
            "counts": {
                "love": reaction_counts.love,
                "like": reaction_counts.like,
                "support": reaction_counts.support,
                "sad": reaction_counts.sad
            }
        }
    
    except Exception as e:
        await db.rollback()
        logger.error("%s Error creating reaction: %s", TAG, str(e))
        return {
            "status":"error",
            "message": str(e),
            "reaction": reaction,
            "counts": {
                "love": 0,
                "like": 0,
                "support": 0,
                "sad": 0
            }
        }


async def get_user_reactions_count_by_type(db: AsyncSession, user: models.User) -> dict:
    stmt = select(
        models.PostReaction.reaction_type,
        func.count().label('count')
    ).where(
        models.PostReaction.user_id == user.uuid
    ).group_by(
        models.PostReaction.reaction_type
    )
    
    result = await db.execute(stmt)
    return {row.reaction_type: row.count for row in result.all()}