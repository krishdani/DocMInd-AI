"""
Chat API routes with SSE streaming.
POST /api/chat/query      - Ask a question (streams SSE)
GET  /api/chat/history    - Get chat sessions
GET  /api/chat/history/{id} - Get specific session with messages
"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.database import get_db
from app.core.security import get_current_user_id
from app.models.models import Chat, ChatMessage, File, ActivityLog
from app.schemas.chat import (
    ChatQueryRequest, ChatSessionResponse,
    ChatHistoryResponse, ChatMessageResponse
)
from app.services.chat_service import stream_rag_response

router = APIRouter(prefix="/api/chat", tags=["Chat"])
logger = logging.getLogger(__name__)


@router.post("/query")
async def query(
    body: ChatQueryRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Stream a RAG-powered answer via Server-Sent Events.
    Creates or continues a chat session.
    """
    # Validate file ownership
    if body.file_ids:
        result = await db.execute(
            select(File.id).where(
                File.id.in_(body.file_ids),
                File.owner_id == user_id,
            )
        )
        owned_ids = {row[0] for row in result.fetchall()}
        invalid = set(body.file_ids) - owned_ids
        if invalid:
            raise HTTPException(status_code=403, detail=f"Access denied for file IDs: {invalid}")

    # Get or create chat session
    if body.chat_id:
        result = await db.execute(
            select(Chat).where(Chat.id == body.chat_id, Chat.user_id == user_id)
        )
        chat = result.scalar_one_or_none()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat session not found")
    else:
        chat = Chat(
            user_id=user_id,
            title=body.question[:80],
            file_ids=body.file_ids,
        )
        db.add(chat)
        await db.flush()

    # Fetch recent history for context
    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.chat_id == chat.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
    )
    raw_messages = history_result.scalars().all()
    history = [
        {"role": m.role, "content": m.content}
        for m in reversed(raw_messages)
    ]

    # Save user message
    user_msg = ChatMessage(
        chat_id=chat.id,
        role="user",
        content=body.question,
    )
    db.add(user_msg)
    await db.commit()

    async def event_stream():
        """Yield SSE events with streamed tokens."""
        full_response = ""
        sources = []

        async for token in stream_rag_response(
            question=body.question,
            file_ids=body.file_ids,
            chat_history=history,
            db=db,
        ):
            # Check for source marker at end of stream
            if "__SOURCES__" in token:
                parts = token.split("__SOURCES__")
                if parts[0]:
                    full_response += parts[0]
                    yield f"data: {json.dumps({'type': 'token', 'content': parts[0]})}\n\n"
                if len(parts) > 1:
                    src_json = parts[1].replace("__END_SOURCES__", "")
                    try:
                        sources = json.loads(src_json)
                    except Exception:
                        pass
            else:
                full_response += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        # Save assistant message to DB
        from app.db.database import AsyncSessionLocal
        async with AsyncSessionLocal() as save_db:
            ai_msg = ChatMessage(
                chat_id=chat.id,
                role="assistant",
                content=full_response,
                sources=sources,
            )
            save_db.add(ai_msg)
            save_db.add(ActivityLog(
                user_id=user_id,
                action="chat_query",
                resource_type="chat",
                resource_id=str(chat.id),
            ))
            await save_db.commit()

        # Send completion event with chat info
        yield f"data: {json.dumps({'type': 'done', 'chat_id': chat.id, 'sources': sources})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    page: int = 1,
    page_size: int = 20,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all chat sessions for the authenticated user."""
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Chat)
        .where(Chat.user_id == user_id)
        .order_by(Chat.updated_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    sessions = result.scalars().all()

    count_result = await db.execute(select(func.count(Chat.id)).where(Chat.user_id == user_id))
    total = count_result.scalar_one()

    return ChatHistoryResponse(sessions=list(sessions), total=total)


@router.get("/history/{chat_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    chat_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific chat session with all messages."""
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
    )
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat session not found")

    msg_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.chat_id == chat_id)
        .order_by(ChatMessage.created_at.asc())
    )
    chat.messages = msg_result.scalars().all()
    return chat
