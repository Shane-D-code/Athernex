"""
Order Management System.

Handles order lifecycle: place, modify, cancel, check status.
Manages order storage, validation, and confirmation generation.
"""

import logging
import uuid
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

from llm.base import OrderItem

logger = logging.getLogger(__name__)


class OrderStatus(str, Enum):
    """Order lifecycle statuses."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    MODIFIED = "modified"


@dataclass
class Order:
    """Represents a customer order."""
    order_id: str
    session_id: str
    status: OrderStatus = OrderStatus.PENDING
    items: List[OrderItem] = field(default_factory=list)
    delivery_time: Optional[str] = None
    special_instructions: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    modification_history: List[Dict[str, Any]] = field(default_factory=list)
    total_items: int = 0
    language: str = "en"

    def __post_init__(self):
        self.total_items = sum(item.quantity for item in self.items)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize order to dictionary."""
        return {
            "order_id": self.order_id,
            "session_id": self.session_id,
            "status": self.status.value,
            "items": [
                {
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "special_instructions": item.special_instructions,
                }
                for item in self.items
            ],
            "delivery_time": self.delivery_time,
            "special_instructions": self.special_instructions,
            "total_items": self.total_items,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "language": self.language,
        }

    def add_item(self, item: OrderItem):
        """Add or update an item in the order."""
        # Check if item already exists
        for existing in self.items:
            if existing.name.lower() == item.name.lower():
                existing.quantity += item.quantity
                self.updated_at = time.time()
                self.total_items = sum(i.quantity for i in self.items)
                logger.debug("Updated item %s quantity to %d", item.name, existing.quantity)
                return
        
        self.items.append(item)
        self.total_items = sum(i.quantity for i in self.items)
        self.updated_at = time.time()
        logger.debug("Added item %s (qty=%d)", item.name, item.quantity)

    def remove_item(self, item_name: str, quantity: Optional[int] = None):
        """Remove or reduce an item quantity."""
        for i, existing in enumerate(self.items):
            if existing.name.lower() == item_name.lower():
                if quantity is None or quantity >= existing.quantity:
                    self.items.pop(i)
                else:
                    existing.quantity -= quantity
                self.total_items = sum(it.quantity for it in self.items)
                self.updated_at = time.time()
                logger.debug("Removed/reduced item %s", item_name)
                return True
        return False

    def update_status(self, new_status: OrderStatus):
        """Update order status and record history."""
        old_status = self.status
        self.status = new_status
        self.updated_at = time.time()
        self.modification_history.append({
            "action": "status_change",
            "from": old_status.value,
            "to": new_status.value,
            "timestamp": time.time(),
        })
        logger.info("Order %s status: %s -> %s", self.order_id, old_status.value, new_status.value)

    def get_confirmation_message(self) -> str:
        """Generate a confirmation message in the order's language."""
        items_str = ", ".join([f"{item.quantity}x {item.name}" for item in self.items])
        
        messages = {
            "hi": f"आपका ऑर्डर {self.order_id} कन्फर्म हो गया है। {items_str}।",
            "en": f"Your order {self.order_id} is confirmed. Items: {items_str}.",
            "kn": f"ನಿಮ್ಮ ಆರ್ಡರ್ {self.order_id} ದೃಢೀಕರಿಸಲಾಗಿದೆ. {items_str}.",
            "mr": f"तुमची ऑर्डर {self.order_id} कन्फर्म झाली आहे. {items_str}.",
        }
        return messages.get(self.language, messages["en"])

    def get_status_message(self) -> str:
        """Generate a status check message."""
        status_messages = {
            "hi": {
                OrderStatus.PENDING: f"ऑर्डर {self.order_id} प्रोसेस हो रहा है।",
                OrderStatus.CONFIRMED: f"ऑर्डर {self.order_id} कन्फर्म हो गया है।",
                OrderStatus.PREPARING: f"ऑर्डर {self.order_id} तैयार हो रहा है।",
                OrderStatus.READY: f"ऑर्डर {self.order_id} तैयार है।",
                OrderStatus.OUT_FOR_DELIVERY: f"ऑर्डर {self.order_id} डिलीवरी पर है।",
                OrderStatus.DELIVERED: f"ऑर्डर {self.order_id} डिलीवर हो गया।",
                OrderStatus.CANCELLED: f"ऑर्डर {self.order_id} कैंसिल हो गया।",
            },
            "en": {
                OrderStatus.PENDING: f"Order {self.order_id} is being processed.",
                OrderStatus.CONFIRMED: f"Order {self.order_id} is confirmed.",
                OrderStatus.PREPARING: f"Order {self.order_id} is being prepared.",
                OrderStatus.READY: f"Order {self.order_id} is ready.",
                OrderStatus.OUT_FOR_DELIVERY: f"Order {self.order_id} is out for delivery.",
                OrderStatus.DELIVERED: f"Order {self.order_id} has been delivered.",
                OrderStatus.CANCELLED: f"Order {self.order_id} has been cancelled.",
            },
        }
        lang_map = status_messages.get(self.language, status_messages["en"])
        return lang_map.get(self.status, f"Order {self.order_id} status: {self.status.value}")


class OrderManager:
    """
    Manages all orders in the system.
    
    Provides CRUD operations for orders with in-memory storage.
    Can be extended to use Redis/database for persistence.
    """

    def __init__(self):
        self.orders: Dict[str, Order] = {}
        self.session_orders: Dict[str, List[str]] = {}
        logger.info("OrderManager initialized")

    def _generate_order_id(self) -> str:
        """Generate a short, human-readable order ID."""
        # Format: ORD-XXXXXX (6 alphanumeric chars)
        return f"ORD-{uuid.uuid4().hex[:6].upper()}"

    def create_order(
        self,
        session_id: str,
        items: List[OrderItem],
        delivery_time: Optional[str] = None,
        special_instructions: Optional[str] = None,
        language: str = "en",
    ) -> Order:
        """Create a new order."""
        order_id = self._generate_order_id()
        
        order = Order(
            order_id=order_id,
            session_id=session_id,
            items=list(items),
            delivery_time=delivery_time,
            special_instructions=special_instructions,
            language=language,
        )
        
        self.orders[order_id] = order
        
        if session_id not in self.session_orders:
            self.session_orders[session_id] = []
        self.session_orders[session_id].append(order_id)
        
        logger.info("Created order %s for session %s (%d items)", order_id, session_id, len(items))
        return order

    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        return self.orders.get(order_id)

    def get_orders_by_session(self, session_id: str) -> List[Order]:
        """Get all orders for a session."""
        order_ids = self.session_orders.get(session_id, [])
        return [self.orders[oid] for oid in order_ids if oid in self.orders]

    def get_last_order_for_session(self, session_id: str) -> Optional[Order]:
        """Get the most recent order for a session."""
        orders = self.get_orders_by_session(session_id)
        if not orders:
            return None
        return max(orders, key=lambda o: o.created_at)

    def modify_order(
        self,
        order_id: str,
        new_items: Optional[List[OrderItem]] = None,
        add_items: Optional[List[OrderItem]] = None,
        remove_items: Optional[List[str]] = None,
        new_delivery_time: Optional[str] = None,
        new_instructions: Optional[str] = None,
    ) -> Optional[Order]:
        """Modify an existing order."""
        order = self.orders.get(order_id)
        if not order:
            logger.warning("Order %s not found for modification", order_id)
            return None
        
        # Record modification
        order.modification_history.append({
            "action": "modify",
            "timestamp": time.time(),
            "old_items": [i.to_dict() if hasattr(i, 'to_dict') else str(i) for i in order.items],
        })
        
        # Apply changes
        if new_items is not None:
            order.items = list(new_items)
        
        if add_items:
            for item in add_items:
                order.add_item(item)
        
        if remove_items:
            for item_name in remove_items:
                order.remove_item(item_name)
        
        if new_delivery_time:
            order.delivery_time = new_delivery_time
        
        if new_instructions:
            order.special_instructions = new_instructions
        
        order.update_status(OrderStatus.MODIFIED)
        logger.info("Modified order %s", order_id)
        return order

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        order = self.orders.get(order_id)
        if not order:
            logger.warning("Order %s not found for cancellation", order_id)
            return False
        
        if order.status in (OrderStatus.DELIVERED, OrderStatus.CANCELLED):
            logger.warning("Cannot cancel order %s (status=%s)", order_id, order.status.value)
            return False
        
        order.update_status(OrderStatus.CANCELLED)
        logger.info("Cancelled order %s", order_id)
        return True

    def confirm_order(self, order_id: str) -> Optional[Order]:
        """Confirm a pending order."""
        order = self.orders.get(order_id)
        if not order:
            return None
        
        order.update_status(OrderStatus.CONFIRMED)
        logger.info("Confirmed order %s", order_id)
        return order

    def get_all_active_orders(self) -> List[Order]:
        """Get all non-completed orders."""
        active_statuses = {
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.PREPARING,
            OrderStatus.READY,
            OrderStatus.OUT_FOR_DELIVERY,
            OrderStatus.MODIFIED,
        }
        return [o for o in self.orders.values() if o.status in active_statuses]

    def get_order_statistics(self) -> Dict[str, Any]:
        """Get system-wide order statistics."""
        total = len(self.orders)
        status_counts = {}
        for order in self.orders.values():
            status_counts[order.status.value] = status_counts.get(order.status.value, 0) + 1
        
        return {
            "total_orders": total,
            "active_orders": len(self.get_all_active_orders()),
            "status_breakdown": status_counts,
            "total_sessions": len(self.session_orders),
        }

