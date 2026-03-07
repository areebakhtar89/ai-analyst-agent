SCHEMA_METADATA = [
    {
        "table": "customers",
        "description": "Customer master data with region and segment information.",
        "columns": {
            "customer_id": "Unique customer identifier (PRIMARY KEY). Use to JOIN with orders.customer_id",
            "customer_name": "Full name of the customer. NOT in orders table — must JOIN customers to get this.",
            "region": "Geographic region of the customer (e.g. North, South, East, West). NOT in orders table — must JOIN customers.",
            "segment": "Customer segment: SMB or Enterprise. NOT in orders table — must JOIN customers."
        },
        "joins": [
            "JOIN customers ON orders.customer_id = customers.customer_id"
        ]
    },
    {
        "table": "products",
        "description": "Product catalog with category and price.",
        "columns": {
            "product_id": "Unique product identifier (PRIMARY KEY). Use to JOIN with order_items.product_id",
            "product_name": "Name of the product. NOT in order_items — must JOIN products to get this.",
            "category": "Product category (e.g. Electronics, Furniture). NOT in order_items — must JOIN products.",
            "price": "Unit price of the product."
        },
        "joins": [
            "JOIN products ON order_items.product_id = products.product_id"
        ]
    },
    {
        "table": "orders",
        "description": "Customer orders over time. Contains order-level totals. Use customer_id to JOIN customers for name/region/segment.",
        "columns": {
            "order_id": "Unique order identifier (PRIMARY KEY). Use to JOIN with order_items.order_id",
            "customer_id": "Foreign key to customers.customer_id. JOIN customers to get customer_name, region, segment.",
            "order_date": "Date the order was placed. Use STRFTIME(order_date, '%Y-%m') for monthly grouping.",
            "total_amount": "Total monetary value of the order."
        },
        "joins": [
            "JOIN customers ON orders.customer_id = customers.customer_id",
            "JOIN order_items ON orders.order_id = order_items.order_id"
        ]
    },
    {
        "table": "order_items",
        "description": "Individual line items within each order. Contains product-level detail. Use product_id to JOIN products for name/category.",
        "columns": {
            "order_item_id": "Unique line item identifier (PRIMARY KEY).",
            "order_id": "Foreign key to orders.order_id. JOIN orders to get order_date, total_amount, customer_id.",
            "product_id": "Foreign key to products.product_id. JOIN products to get product_name, category, price.",
            "quantity": "Number of units purchased.",
            "revenue": "Total revenue for this line item (quantity x price)."
        },
        "joins": [
            "JOIN orders ON order_items.order_id = orders.order_id",
            "JOIN products ON order_items.product_id = products.product_id"
        ]
    }
]

# Explicit JOIN relationships for the SQL agent prompt
JOIN_RELATIONSHIPS = """
IMPORTANT - Table Relationships (always JOIN when you need columns from another table):
- customers.customer_id = orders.customer_id
- orders.order_id = order_items.order_id  
- products.product_id = order_items.product_id

NEVER assume a column exists in a table without checking the schema above.
ALWAYS JOIN the required table to access its columns.

Examples:
- Need customer_name or region? → JOIN customers ON orders.customer_id = customers.customer_id
- Need product_name or category? → JOIN products ON order_items.product_id = products.product_id
- Need order_date with product info? → JOIN orders ON order_items.order_id = orders.order_id
"""