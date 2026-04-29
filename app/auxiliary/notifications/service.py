import logging
from app.domain.events.events import DrawingCreatedEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NotificationComponent")

class NotificationService:
    """
    Допоміжний компонент. Має власний контракт і нічого не знає про FastAPI чи CQRS хендлери.
    """
    def __init__(self):
        self.processed_events = set() # Для перевірки ідемпотентності

    def send_notification_sync(self, drawing_id: int, owner_id: int, title: str):
        """Синхронний контракт (прямий виклик). Якщо тут помилка - впаде весь запит."""
        logger.info(f"[SYNC CALL] Sending email to followers of User {owner_id} about new drawing '{title}'")

    def handle_drawing_created_event(self, event: DrawingCreatedEvent):
        """Асинхронний контракт (через Event Bus)."""
        # Перевірка на ідемпотентність (якщо подія доставляється двічі)
        if event.event_id in self.processed_events:
            logger.warning(f"[ASYNC] Event {event.event_id} already processed. Skipping.")
            return
            
        logger.info(f"[ASYNC EVENT] Processing '{event.title}' created by User {event.owner_id} at {event.occurred_at}")
        
        # Виконуємо бізнес-логіку побічної дії
        self._mock_send_push_notification(event.owner_id, event.title)
        
        # Відмічаємо подію як оброблену
        self.processed_events.add(event.event_id)

    def _mock_send_push_notification(self, user_id: int, title: str):
        # Імітація довгої або нестабільної операції
        logger.info(f"==> Push notification sent successfully for drawing: {title}")

# Ініціалізуємо сервіс
notification_service = NotificationService()
