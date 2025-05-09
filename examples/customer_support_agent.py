"""
Customer Support Agent Example with OpenAI Function Calling

This example demonstrates how to build an advanced customer support agent using:
- Contexa SDK as the foundation
- OpenAI Function Calling for structured tool usage
- Knowledge base integration for product documentation
- Ticket management system integration
- Order tracking capabilities
- Personalized response generation

The agent can:
1. Search product documentation and FAQs
2. Create and update support tickets
3. Track customer orders
4. Generate personalized responses based on customer history
5. Escalate complex issues to human agents
"""

import asyncio
import os
import json
import datetime
import random
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

# Import Contexa SDK components
from contexa_sdk.core.tool import ContexaTool, ToolOutput
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.adapters.openai import agent as openai_agent

# Tool input schemas
class KnowledgeBaseSearchInput(BaseModel):
    """Input for searching the knowledge base."""
    query: str = Field(description="Search query for knowledge base")
    product: Optional[str] = Field(None, description="Specific product to search documentation for")
    max_results: int = Field(3, description="Maximum number of results to return")

class TicketManagementInput(BaseModel):
    """Input for creating or updating support tickets."""
    action: str = Field(description="Action to perform: create, update, or check")
    ticket_id: Optional[str] = Field(None, description="Ticket ID for update or check actions")
    customer_id: Optional[str] = Field(None, description="Customer ID for ticket creation")
    issue: Optional[str] = Field(None, description="Description of the customer issue")
    priority: Optional[str] = Field(None, description="Ticket priority: low, medium, high, critical")
    status: Optional[str] = Field(None, description="New status when updating a ticket")
    notes: Optional[str] = Field(None, description="Additional notes for the ticket")

class OrderTrackingInput(BaseModel):
    """Input for order tracking."""
    order_id: str = Field(description="Order ID to track")
    customer_id: Optional[str] = Field(None, description="Customer ID for verification")

class CustomerHistoryInput(BaseModel):
    """Input for retrieving customer history."""
    customer_id: str = Field(description="Customer ID to retrieve history for")
    history_type: Optional[str] = Field("all", description="Type of history to retrieve: purchases, tickets, interactions, all")
    limit: int = Field(5, description="Maximum number of history items to return")

class EscalationInput(BaseModel):
    """Input for escalating issues to human agents."""
    customer_id: str = Field(description="Customer ID for the escalation")
    ticket_id: Optional[str] = Field(None, description="Related ticket ID if available")
    reason: str = Field(description="Reason for escalation")
    urgency: str = Field("medium", description="Urgency of escalation: low, medium, high")

# Simulated database for the example
knowledge_base = {
    "articles": [
        {
            "id": "kb001",
            "title": "How to Reset Your Password",
            "product": "account_management",
            "content": "To reset your password, go to the login page and click 'Forgot Password'. Follow the instructions sent to your email.",
            "tags": ["password", "reset", "account", "login"]
        },
        {
            "id": "kb002",
            "title": "Tracking Your Order",
            "product": "order_management",
            "content": "You can track your order by logging into your account and visiting the 'Orders' section. Click on any order to see detailed status information.",
            "tags": ["order", "tracking", "shipping", "delivery"]
        },
        {
            "id": "kb003",
            "title": "Return Policy",
            "product": "policies",
            "content": "Our return policy allows returns within a 30-day window of purchase. Items must be unused and in original packaging. Contact customer support to initiate a return.",
            "tags": ["return", "refund", "policy"]
        },
        {
            "id": "kb004",
            "title": "Membership Benefits",
            "product": "account_management",
            "content": "Premium members enjoy benefits including free shipping, early access to sales, and exclusive discounts. Upgrade your account in the membership section.",
            "tags": ["membership", "benefits", "premium", "account"]
        },
        {
            "id": "kb005",
            "title": "Setting Up Your Smart Home Device",
            "product": "smart_home",
            "content": "To set up your smart home device, download our app, create an account, and follow the in-app setup wizard. Ensure your device is powered on and near your Wi-Fi router during setup.",
            "tags": ["setup", "smart home", "device", "configuration"]
        }
    ]
}

tickets_database = {
    "tickets": [
        {
            "id": "T1001",
            "customer_id": "C5001",
            "issue": "Unable to reset password",
            "status": "open",
            "priority": "medium",
            "created_at": "2025-04-01T14:30:00Z",
            "updated_at": "2025-04-01T14:30:00Z",
            "notes": "Customer tried password reset but didn't receive email"
        }
    ]
}

orders_database = {
    "orders": [
        {
            "id": "O7001",
            "customer_id": "C5001",
            "date": "2025-03-25T10:15:00Z",
            "items": [
                {"product_id": "P101", "name": "Smart Home Hub", "quantity": 1, "price": 129.99},
                {"product_id": "P203", "name": "Motion Sensor", "quantity": 2, "price": 24.99}
            ],
            "total": 179.97,
            "status": "shipped",
            "tracking_number": "TRK78901234",
            "estimated_delivery": "2025-04-05T00:00:00Z"
        }
    ]
}

customers_database = {
    "customers": [
        {
            "id": "C5001",
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "phone": "555-123-4567",
            "membership": "premium",
            "joined_date": "2023-11-10T00:00:00Z",
            "purchase_count": 12,
            "total_spend": 1245.67,
            "interaction_history": [
                {"type": "chat", "date": "2025-03-10T15:45:00Z", "summary": "Inquired about smart home compatibility"},
                {"type": "email", "date": "2025-02-20T09:30:00Z", "summary": "Received shipping confirmation"},
                {"type": "call", "date": "2025-01-15T13:20:00Z", "summary": "Requested help with device setup"}
            ]
        }
    ]
}

# Tool implementations
@ContexaTool.register(
    name="search_knowledge_base",
    description="Search the product knowledge base for articles and documentation",
)
async def search_knowledge_base(input_data: KnowledgeBaseSearchInput) -> ToolOutput:
    """Search the knowledge base for articles and documentation."""
    query = input_data.query.lower()
    product_filter = input_data.product.lower() if input_data.product else None
    
    # Simple search logic - in a real implementation, this would use vector search
    matching_articles = []
    for article in knowledge_base["articles"]:
        # Check if product filter is applied and matches
        if product_filter and article["product"].lower() != product_filter:
            continue
            
        # Check if query terms are in title, content, or tags
        if (query in article["title"].lower() or 
            query in article["content"].lower() or 
            any(query in tag.lower() for tag in article["tags"])):
            matching_articles.append({
                "id": article["id"],
                "title": article["title"],
                "content": article["content"],
                "product": article["product"]
            })
    
    # Sort by relevance (simple implementation - just using presence in title as proxy)
    matching_articles.sort(key=lambda x: query in x["title"].lower(), reverse=True)
    
    # Limit results
    results = matching_articles[:input_data.max_results]
    
    return ToolOutput(
        content=f"Found {len(results)} articles matching '{input_data.query}'",
        json_data={"articles": results}
    )

@ContexaTool.register(
    name="manage_support_ticket",
    description="Create, update, or check support tickets",
)
async def manage_support_ticket(input_data: TicketManagementInput) -> ToolOutput:
    """Create, update, or check support tickets."""
    action = input_data.action.lower()
    
    if action == "create":
        # Validate required fields for ticket creation
        if not input_data.customer_id or not input_data.issue:
            return ToolOutput(
                content="Error: Customer ID and issue description are required to create a ticket",
                json_data={"error": "missing_required_fields"}
            )
        
        # Generate a ticket ID
        ticket_id = f"T{random.randint(1000, 9999)}"
        
        # Set default priority if not provided
        priority = input_data.priority or "medium"
        
        # Create timestamp
        timestamp = datetime.datetime.now().isoformat()
        
        # Create the ticket
        new_ticket = {
            "id": ticket_id,
            "customer_id": input_data.customer_id,
            "issue": input_data.issue,
            "status": "open",
            "priority": priority,
            "created_at": timestamp,
            "updated_at": timestamp,
            "notes": input_data.notes or ""
        }
        
        # Add to database
        tickets_database["tickets"].append(new_ticket)
        
        return ToolOutput(
            content=f"Successfully created ticket {ticket_id} for customer {input_data.customer_id}",
            json_data={"ticket": new_ticket}
        )
        
    elif action == "update":
        # Validate ticket ID
        if not input_data.ticket_id:
            return ToolOutput(
                content="Error: Ticket ID is required for updates",
                json_data={"error": "missing_ticket_id"}
            )
        
        # Find the ticket
        ticket = next((t for t in tickets_database["tickets"] if t["id"] == input_data.ticket_id), None)
        if not ticket:
            return ToolOutput(
                content=f"Error: Ticket {input_data.ticket_id} not found",
                json_data={"error": "ticket_not_found"}
            )
        
        # Update fields
        if input_data.status:
            ticket["status"] = input_data.status
        if input_data.priority:
            ticket["priority"] = input_data.priority
        if input_data.notes:
            ticket["notes"] += f"\n{input_data.notes}"
        
        # Update timestamp
        ticket["updated_at"] = datetime.datetime.now().isoformat()
        
        return ToolOutput(
            content=f"Successfully updated ticket {input_data.ticket_id}",
            json_data={"ticket": ticket}
        )
        
    elif action == "check":
        # Validate ticket ID
        if not input_data.ticket_id:
            return ToolOutput(
                content="Error: Ticket ID is required to check status",
                json_data={"error": "missing_ticket_id"}
            )
        
        # Find the ticket
        ticket = next((t for t in tickets_database["tickets"] if t["id"] == input_data.ticket_id), None)
        if not ticket:
            return ToolOutput(
                content=f"Error: Ticket {input_data.ticket_id} not found",
                json_data={"error": "ticket_not_found"}
            )
        
        return ToolOutput(
            content=f"Retrieved details for ticket {input_data.ticket_id}",
            json_data={"ticket": ticket}
        )
    
    else:
        return ToolOutput(
            content=f"Error: Invalid action '{action}'. Use 'create', 'update', or 'check'",
            json_data={"error": "invalid_action"}
        )

@ContexaTool.register(
    name="track_order",
    description="Track customer orders and provide shipping status",
)
async def track_order(input_data: OrderTrackingInput) -> ToolOutput:
    """Track customer orders and provide shipping status."""
    # Find the order
    order = next((o for o in orders_database["orders"] if o["id"] == input_data.order_id), None)
    
    if not order:
        return ToolOutput(
            content=f"Error: Order {input_data.order_id} not found",
            json_data={"error": "order_not_found"}
        )
    
    # Verify customer ID if provided
    if input_data.customer_id and order["customer_id"] != input_data.customer_id:
        return ToolOutput(
            content="Error: This order does not belong to the specified customer",
            json_data={"error": "customer_mismatch"}
        )
    
    # Determine shipping status message based on order status
    status_message = ""
    if order["status"] == "processing":
        status_message = "Your order is being processed and will ship soon."
    elif order["status"] == "shipped":
        status_message = f"Your order has been shipped. Tracking number: {order['tracking_number']}. Estimated delivery: {order['estimated_delivery']}."
    elif order["status"] == "delivered":
        status_message = f"Your order was delivered on {order['delivery_date']}."
    elif order["status"] == "cancelled":
        status_message = "This order has been cancelled."
    
    # Prepare the response
    tracking_info = {
        "order_id": order["id"],
        "status": order["status"],
        "items": [{"name": item["name"], "quantity": item["quantity"]} for item in order["items"]],
        "total": order["total"],
        "status_message": status_message
    }
    
    # Add tracking number and delivery estimate if available
    if "tracking_number" in order:
        tracking_info["tracking_number"] = order["tracking_number"]
    if "estimated_delivery" in order:
        tracking_info["estimated_delivery"] = order["estimated_delivery"]
    if "delivery_date" in order:
        tracking_info["delivery_date"] = order["delivery_date"]
    
    return ToolOutput(
        content=status_message,
        json_data={"tracking": tracking_info}
    )

@ContexaTool.register(
    name="get_customer_history",
    description="Retrieve customer history for personalized support",
)
async def get_customer_history(input_data: CustomerHistoryInput) -> ToolOutput:
    """Retrieve customer history for personalized support."""
    # Find the customer
    customer = next((c for c in customers_database["customers"] if c["id"] == input_data.customer_id), None)
    
    if not customer:
        return ToolOutput(
            content=f"Error: Customer {input_data.customer_id} not found",
            json_data={"error": "customer_not_found"}
        )
    
    # Prepare the response based on requested history type
    history_type = input_data.history_type.lower()
    customer_history = {}
    
    # Basic customer info
    customer_history["customer"] = {
        "id": customer["id"],
        "name": customer["name"],
        "email": customer["email"],
        "membership": customer["membership"],
        "joined_date": customer["joined_date"],
        "purchase_count": customer["purchase_count"],
        "total_spend": customer["total_spend"]
    }
    
    # Add purchase history if requested
    if history_type in ["purchases", "all"]:
        customer_history["purchases"] = [
            {
                "id": order["id"],
                "date": order["date"],
                "total": order["total"],
                "status": order["status"],
                "items": [{"name": item["name"], "quantity": item["quantity"]} for item in order["items"]]
            }
            for order in orders_database["orders"] 
            if order["customer_id"] == input_data.customer_id
        ][:input_data.limit]
    
    # Add ticket history if requested
    if history_type in ["tickets", "all"]:
        customer_history["tickets"] = [
            {
                "id": ticket["id"],
                "issue": ticket["issue"],
                "status": ticket["status"],
                "priority": ticket["priority"],
                "created_at": ticket["created_at"]
            }
            for ticket in tickets_database["tickets"] 
            if ticket["customer_id"] == input_data.customer_id
        ][:input_data.limit]
    
    # Add interaction history if requested
    if history_type in ["interactions", "all"]:
        customer_history["interactions"] = customer["interaction_history"][:input_data.limit]
    
    return ToolOutput(
        content=f"Retrieved {history_type} history for customer {customer['name']}",
        json_data={"history": customer_history}
    )

@ContexaTool.register(
    name="escalate_to_human",
    description="Escalate complex issues to human support agents",
)
async def escalate_to_human(input_data: EscalationInput) -> ToolOutput:
    """Escalate complex issues to human support agents."""
    # Find the customer for verification
    customer = next((c for c in customers_database["customers"] if c["id"] == input_data.customer_id), None)
    
    if not customer:
        return ToolOutput(
            content=f"Error: Customer {input_data.customer_id} not found for escalation",
            json_data={"error": "customer_not_found"}
        )
    
    # Generate an escalation ID
    escalation_id = f"ESC{random.randint(10000, 99999)}"
    
    # Determine expected response time based on urgency
    response_times = {
        "low": "within 24 hours",
        "medium": "within 4 hours",
        "high": "within 1 hour"
    }
    expected_response = response_times.get(input_data.urgency, "within 4 hours")
    
    # Prepare escalation record
    escalation = {
        "id": escalation_id,
        "customer_id": input_data.customer_id,
        "customer_name": customer["name"],
        "ticket_id": input_data.ticket_id,
        "reason": input_data.reason,
        "urgency": input_data.urgency,
        "created_at": datetime.datetime.now().isoformat(),
        "status": "pending",
        "expected_response": expected_response
    }
    
    # In a real implementation, this would trigger a notification to human agents
    
    return ToolOutput(
        content=f"Issue escalated to human support. A support agent will contact you {expected_response}. Reference ID: {escalation_id}",
        json_data={"escalation": escalation}
    )

# Create the customer support agent
async def create_customer_support_agent():
    """Create and configure the customer support agent."""
    # Register all the tools
    tools = [
        search_knowledge_base,
        manage_support_ticket,
        track_order,
        get_customer_history,
        escalate_to_human
    ]
    
    # Create the model
    model = ContexaModel(
        provider="openai", 
        model_id="gpt-4",
        temperature=0.3  # Lower temperature for more consistent support responses
    )
    
    # Define the system prompt
    system_prompt = """
    You are a helpful customer support assistant that helps users with their questions and issues.
    
    When helping customers:
    1. Always be courteous and professional
    2. Use the customer's name when you have it
    3. Search the knowledge base before creating tickets
    4. Verify order details when providing tracking information
    5. Personalize responses based on customer history when available
    6. Only escalate to human agents when necessary
    
    If you can't help with a specific issue, create a support ticket and provide the ticket ID to the customer.
    """
    
    # Create the Contexa agent
    support_agent = ContexaAgent(
        name="Customer Support Agent",
        description="Assists customers with support requests and product information",
        tools=tools,
        model=model,
        system_prompt=system_prompt
    )
    
    # Convert to OpenAI agent
    openai_support_agent = openai_agent(support_agent)
    
    return openai_support_agent

# Example usage
async def run_customer_support_example():
    print("🔄 Creating Customer Support Agent with OpenAI Function Calling...")
    agent = await create_customer_support_agent()
    
    print("\n📞 Processing Customer Support Queries...")
    
    # Example 1: Knowledge base search
    query1 = "How do I reset my password?"
    print(f"\n👤 Customer: {query1}")
    response1 = await agent.invoke({"input": query1})
    print(f"🤖 Agent: {response1}")
    
    # Example 2: Order tracking
    query2 = "I'm customer Jane Smith (ID: C5001) and I want to check on my order O7001"
    print(f"\n👤 Customer: {query2}")
    response2 = await agent.invoke({"input": query2})
    print(f"🤖 Agent: {response2}")
    
    # Example 3: Problem requiring ticket creation
    query3 = "My smart home device won't connect to WiFi. I've tried resetting it multiple times."
    print(f"\n👤 Customer: {query3}")
    response3 = await agent.invoke({"input": query3})
    print(f"🤖 Agent: {response3}")
    
    # Example 4: Complex issue requiring escalation
    query4 = "I've been charged twice for my last order and need this resolved immediately."
    print(f"\n👤 Customer: {query4}")
    response4 = await agent.invoke({"input": query4})
    print(f"🤖 Agent: {response4}")
    
    print("\n✅ Customer Support Agent Demo Complete")

if __name__ == "__main__":
    asyncio.run(run_customer_support_example()) 