"""
Migration: Add crisis mode fields to User model.

Adds:
- current_mode: User's current mode (normal, crisis, burnout, uncertainty)
- mode_updated_at: Timestamp when mode was last changed
"""

from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "users" ADD "current_mode" VARCHAR(20) DEFAULT 'normal' NOT NULL;
        ALTER TABLE "users" ADD "mode_updated_at" TIMESTAMP;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "users" DROP COLUMN "current_mode";
        ALTER TABLE "users" DROP COLUMN "mode_updated_at";
    """

