from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Update


class NullMessageMiddleware(BaseMiddleware):
    """Drop callback queries where callback.message is None (messages > 48h old)."""

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Update) and event.callback_query:
            cq = event.callback_query
            if cq.message is None:
                try:
                    await cq.answer("Сообщение устарело. Откройте заново.", show_alert=True)
                except Exception:
                    pass
                return
        return await handler(event, data)
