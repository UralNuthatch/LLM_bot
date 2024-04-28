from aiogram import Router
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, MEMBER, KICKED
from aiogram.types import ChatMemberUpdated

from database.database import DB


router = Router()


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def user_blocked_bot(event: ChatMemberUpdated, db: DB):
    await db.set_inactive_user(event.from_user.id)


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def user_start_bot(event: ChatMemberUpdated, db: DB):
    await db.set_active_user(event.from_user.id, event.from_user.username, event.from_user.first_name)