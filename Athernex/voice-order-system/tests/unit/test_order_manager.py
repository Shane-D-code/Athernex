"""
Unit tests for OrderManager component.

Tests validate requirements 6.1-6.5 for order processing and execution.
"""

import pytest
from datetime import datetime
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from order_manager import OrderManager, OrderRecord
from llm.base import StructuredOrderData, Intent, OrderItem


class TestOrderManager:
    """Test suite for OrderManager component."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.order_manager = OrderManager()
    
    def test_place_order_creates_new_record(self):
        """Test Requirement 6.2: Create new order records for place_order intent."""
        # Arrange
        order_data = StructuredOrderData(
            intent=Intent.PLACE_ORDER,
            items=[
                OrderItem(name="Pizza", quantity=2, unit="Large"),
                OrderItem(name="Coke", quantity=1)
            ],
            delivery_time="2024-01-15T18:30:00Z",
            special_instructions="Ring doorbell twice"
        )
        
        # Act
        result = self.order_manager.process_order(order_data)
        
        # Assert
        assert result["status"] == "success"
        assert result["action"] == "place_order"
        assert result["order_id"] is not None
        assert "placed successfully" in result["confirmation_message"]
        
        # Verify order is stored
        orders = self.order_manager.get_all_orders()
        assert len(orders) == 1
        
        order_id = result["order_id"]
        stored_order = orders[order_id]
        assert stored_order.intent == Intent.PLACE_ORDER
        assert len(stored_order.items) == 2
        assert stored_order.items[0].name == "Pizza"
        assert stored_order.delivery_time == "2024-01-15T18:30:00Z"
        assert stored_order.special_instructions == "Ring doorbell twice"
        assert stored_order.status == "active"
    
    def test_modify_order_updates_existing_record(self):
        """Test Requirement 6.3: Update existing orders for modify_order intent."""
        # Arrange - Create initial order
        initial_data = StructuredOrderData(
            intent=Intent.PLACE_ORDER,
            items=[OrderItem(name="Pizza", quantity=1)],
            delivery_time="2024-01-15T18:30:00Z"
        )
        initial_result = self.order_manager.process_order(initial_data)
        order_id = initial_result["order_id"]
        
        # Arrange - Modification data
        modify_data = StructuredOrderData(
            intent=Intent.MODIFY_ORDER,
            order_id=order_id,
            items=[OrderItem(name="Pizza", quantity=2), OrderItem(name="Salad", quantity=1)],
            delivery_time="2024-01-15T19:00:00Z"
        )
        
        # Act
        result = self.order_manager.process_order(modify_data)
        
        # Assert
        assert result["status"] == "success"
        assert result["action"] == "modify_order"
        assert result["order_id"] == order_id
        assert "modified successfully" in result["confirmation_message"]
        
        # Verify order is updated
        orders = self.order_manager.get_all_orders()
        updated_order = orders[order_id]
        assert len(updated_order.items) == 2
        assert updated_order.items[0].quantity == 2
        assert updated_order.items[1].name == "Salad"
        assert updated_order.delivery_time == "2024-01-15T19:00:00Z"
    
    def test_cancel_order_marks_as_cancelled(self):
        """Test Requirement 6.4: Mark orders as cancelled for cancel_order intent."""
        # Arrange - Create initial order
        initial_data = StructuredOrderData(
            intent=Intent.PLACE_ORDER,
            items=[OrderItem(name="Pizza", quantity=1)]
        )
        initial_result = self.order_manager.process_order(initial_data)
        order_id = initial_result["order_id"]
        
        # Arrange - Cancellation data
        cancel_data = StructuredOrderData(
            intent=Intent.CANCEL_ORDER,
            order_id=order_id
        )
        
        # Act
        result = self.order_manager.process_order(cancel_data)
        
        # Assert
        assert result["status"] == "success"
        assert result["action"] == "cancel_order"
        assert result["order_id"] == order_id
        assert "cancelled successfully" in result["confirmation_message"]
        
        # Verify order is cancelled
        orders = self.order_manager.get_all_orders()
        cancelled_order = orders[order_id]
        assert cancelled_order.status == "cancelled"
    
    def test_check_order_status(self):
        """Test order status checking functionality."""
        # Arrange - Create initial order
        initial_data = StructuredOrderData(
            intent=Intent.PLACE_ORDER,
            items=[OrderItem(name="Pizza", quantity=1)]
        )
        initial_result = self.order_manager.process_order(initial_data)
        order_id = initial_result["order_id"]
        
        # Arrange - Status check data
        status_data = StructuredOrderData(
            intent=Intent.CHECK_STATUS,
            order_id=order_id
        )
        
        # Act
        result = self.order_manager.process_order(status_data)
        
        # Assert
        assert result["status"] == "success"
        assert result["action"] == "check_status"
        assert result["order_id"] == order_id
        assert "status is active" in result["confirmation_message"]
    
    def test_confirm_order(self):
        """Test order confirmation functionality."""
        # Arrange - Create initial order
        initial_data = StructuredOrderData(
            intent=Intent.PLACE_ORDER,
            items=[OrderItem(name="Pizza", quantity=1)]
        )
        initial_result = self.order_manager.process_order(initial_data)
        order_id = initial_result["order_id"]
        
        # Arrange - Confirmation data
        confirm_data = StructuredOrderData(
            intent=Intent.CONFIRM_ORDER,
            order_id=order_id
        )
        
        # Act
        result = self.order_manager.process_order(confirm_data)
        
        # Assert
        assert result["status"] == "success"
        assert result["action"] == "confirm_order"
        assert result["order_id"] == order_id
        assert "confirmed successfully" in result["confirmation_message"]
        
        # Verify order is confirmed
        orders = self.order_manager.get_all_orders()
        confirmed_order = orders[order_id]
        assert confirmed_order.status == "confirmed"
    
    def test_generate_confirmation_messages(self):
        """Test Requirement 6.5: Generate confirmation messages for TTS output."""
        # Test place_order confirmation
        order_data = {
            "order_id": "12345",
            "items": [OrderItem(name="Pizza", quantity=2), OrderItem(name="Coke", quantity=1)],
            "delivery_time": "6:30 PM"
        }
        
        message = self.order_manager.generate_confirmation("place_order", order_data)
        assert "Order 12345 has been placed successfully" in message
        assert "2 Pizza and 1 Coke" in message
        assert "6:30 PM" in message
        
        # Test modify_order confirmation
        message = self.order_manager.generate_confirmation("modify_order", {"order_id": "12345"})
        assert "Order 12345 has been modified successfully" in message
        
        # Test cancel_order confirmation
        message = self.order_manager.generate_confirmation("cancel_order", {"order_id": "12345"})
        assert "Order 12345 has been cancelled successfully" in message
    
    def test_error_handling_missing_order_id(self):
        """Test error handling when order ID is missing for operations that require it."""
        # Test modify without order ID
        modify_data = StructuredOrderData(
            intent=Intent.MODIFY_ORDER,
            items=[OrderItem(name="Pizza", quantity=2)]
        )
        
        result = self.order_manager.process_order(modify_data)
        assert result["status"] == "error"
        assert "Order ID required" in result["confirmation_message"]
        
        # Test cancel without order ID
        cancel_data = StructuredOrderData(
            intent=Intent.CANCEL_ORDER
        )
        
        result = self.order_manager.process_order(cancel_data)
        assert result["status"] == "error"
        assert "Order ID required" in result["confirmation_message"]
    
    def test_error_handling_nonexistent_order(self):
        """Test error handling when trying to operate on non-existent orders."""
        modify_data = StructuredOrderData(
            intent=Intent.MODIFY_ORDER,
            order_id="nonexistent",
            items=[OrderItem(name="Pizza", quantity=2)]
        )
        
        result = self.order_manager.process_order(modify_data)
        assert result["status"] == "error"
        assert "not found" in result["confirmation_message"]
    
    def test_error_handling_cancelled_order_operations(self):
        """Test error handling when trying to modify or confirm cancelled orders."""
        # Arrange - Create and cancel order
        initial_data = StructuredOrderData(
            intent=Intent.PLACE_ORDER,
            items=[OrderItem(name="Pizza", quantity=1)]
        )
        initial_result = self.order_manager.process_order(initial_data)
        order_id = initial_result["order_id"]
        
        cancel_data = StructuredOrderData(
            intent=Intent.CANCEL_ORDER,
            order_id=order_id
        )
        self.order_manager.process_order(cancel_data)
        
        # Test modify cancelled order
        modify_data = StructuredOrderData(
            intent=Intent.MODIFY_ORDER,
            order_id=order_id,
            items=[OrderItem(name="Pizza", quantity=2)]
        )
        
        result = self.order_manager.process_order(modify_data)
        assert result["status"] == "error"
        assert "Cannot modify cancelled order" in result["confirmation_message"]
    
    def test_items_formatting_for_speech(self):
        """Test formatting of order items for natural speech output."""
        # Single item
        items = [OrderItem(name="Pizza", quantity=1)]
        result = self.order_manager._format_items_for_speech(items)
        assert result == "1 Pizza"
        
        # Two items
        items = [
            OrderItem(name="Pizza", quantity=2),
            OrderItem(name="Coke", quantity=1)
        ]
        result = self.order_manager._format_items_for_speech(items)
        assert result == "2 Pizza and 1 Coke"
        
        # Three items
        items = [
            OrderItem(name="Pizza", quantity=1),
            OrderItem(name="Salad", quantity=1),
            OrderItem(name="Coke", quantity=2)
        ]
        result = self.order_manager._format_items_for_speech(items)
        assert result == "1 Pizza, 1 Salad, and 2 Coke"
        
        # Item with unit
        items = [OrderItem(name="Pizza", quantity=1, unit="Large")]
        result = self.order_manager._format_items_for_speech(items)
        assert result == "1 Pizza Large"
    
    def test_process_order_validates_requirement_6_1(self):
        """Test Requirement 6.1: Process orders when confidence exceeds threshold."""
        # This test verifies that the OrderManager processes validated order data
        # The confidence checking is done by the Confidence_Analyzer before calling OrderManager
        
        order_data = StructuredOrderData(
            intent=Intent.PLACE_ORDER,
            items=[OrderItem(name="Pizza", quantity=1)]
        )
        
        # Act - OrderManager should process the order (assuming it passed confidence check)
        result = self.order_manager.process_order(order_data)
        
        # Assert - Order is processed successfully
        assert result["status"] == "success"
        assert result["order_id"] is not None
        assert len(self.order_manager.get_all_orders()) == 1