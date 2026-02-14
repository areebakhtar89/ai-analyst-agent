SCHEMA_METADATA = [
    {
        "table": "customers",
        "description": "Customer master data with region and segment information.",
        "columns": {
            "customer_id": "Unique customer identifier",
            "customer_name": "Customer name",
            "region": "Customer geographic region",
            "segment": "Customer segment (SMB or Enterprise)"
        }
    },
    {
        "table": "products",
        "description": "Product catalog with category and price.",
        "columns": {
            "product_id": "Unique product identifier",
            "product_name": "Product name",
            "category": "Product category",
            "price": "Unit price"
        }
    },
    {
        "table": "orders",
        "description": "Customer orders over time.",
        "columns": {
            "order_id": "Unique order identifier",
            "customer_id": "Customer placing the order",
            "order_date": "Date of the order",
            "total_amount": "Total order value"
        }
    },
    {
        "table": "order_items",
        "description": "Line items within each order.",
        "columns": {
            "order_item_id": "Unique line item identifier",
            "order_id": "Associated order",
            "product_id": "Product purchased",
            "quantity": "Number of units",
            "revenue": "Revenue for the line item"
        }
    }
]
