"""
app/core/schema_metadata.py

Schema definitions for the Olist Brazilian E-Commerce dataset.
Column names match EXACTLY what is in the CSVs — verified against actual headers.

Notable quirks in the Olist dataset:
- customer_zip_code_prefix  (not customer_zip_code)
- seller_zip_code_prefix    (not seller_zip_code)
- geolocation_zip_code_prefix (not geolocation_zip_code)
- product_name_lenght       (typo in original CSV — missing 'n')
- product_description_lenght (same typo)
"""

JOIN_RELATIONSHIPS = """
KEY JOIN RELATIONSHIPS:
- orders.customer_id                    → customers.customer_id
- order_items.order_id                  → orders.order_id
- order_items.product_id                → products.product_id
- order_items.seller_id                 → sellers.seller_id
- order_payments.order_id               → orders.order_id
- order_reviews.order_id                → orders.order_id
- customers.customer_zip_code_prefix    → geolocation.geolocation_zip_code_prefix
- sellers.seller_zip_code_prefix        → geolocation.geolocation_zip_code_prefix
- products.product_category_name        → product_category_translation.product_category_name

COMMON JOIN PATTERNS:
- Revenue queries        : orders JOIN order_payments ON orders.order_id = order_payments.order_id
- Customer location      : orders JOIN customers ON orders.customer_id = customers.customer_id
- Product performance    : order_items JOIN products ON order_items.product_id = products.product_id
- Seller analysis        : order_items JOIN sellers ON order_items.seller_id = sellers.seller_id
- Category in English    : products JOIN product_category_translation ON products.product_category_name = product_category_translation.product_category_name
- Full order detail      : orders JOIN order_items JOIN products JOIN customers JOIN order_payments
"""

SCHEMA_METADATA = [
    {
        "table": "orders",
        "description": (
            "Core transaction table. One row per order. "
            "Links customers to their purchases. "
            "Contains order lifecycle timestamps from purchase to delivery."
        ),
        "columns": {
            "order_id":                       "Unique order identifier (PK). JOIN to order_items, order_payments, order_reviews using this column.",
            "customer_id":                    "Links to customers.customer_id. Use to get customer city, state, location.",
            "order_status":                   "Order lifecycle status: delivered, shipped, canceled, processing, invoiced, unavailable, created, approved.",
            "order_purchase_timestamp":       "When the customer placed the order. Primary column for time-based analysis: monthly trends, YoY growth. Use DATE_FORMAT for grouping.",
            "order_approved_at":              "When payment was approved.",
            "order_delivered_carrier_date":   "When order was handed to the carrier.",
            "order_delivered_customer_date":  "When the customer actually received the order.",
            "order_estimated_delivery_date":  "Estimated delivery date. Compare with order_delivered_customer_date to find late deliveries.",
        },
        "joins": [
            "JOIN customers c ON orders.customer_id = c.customer_id",
            "JOIN order_items oi ON orders.order_id = oi.order_id",
            "JOIN order_payments op ON orders.order_id = op.order_id",
            "JOIN order_reviews r ON orders.order_id = r.order_id",
        ]
    },

    {
        "table": "order_items",
        "description": (
            "Line items within each order. One row per item per order. "
            "An order can have multiple items from different sellers. "
            "Contains price and freight per item — use SUM() for order-level totals."
        ),
        "columns": {
            "order_id":            "Links to orders.order_id.",
            "order_item_id":       "Sequential item number within the order (1, 2, 3...).",
            "product_id":          "Links to products.product_id.",
            "seller_id":           "Links to sellers.seller_id — the seller who fulfilled this specific item.",
            "shipping_limit_date": "Deadline by which the seller must ship this item.",
            "price":               "Unit price of the product in BRL. Use SUM(price) for product revenue.",
            "freight_value":       "Freight/shipping cost for this item in BRL. Use SUM(freight_value) for shipping revenue.",
        },
        "joins": [
            "JOIN orders o ON order_items.order_id = o.order_id",
            "JOIN products p ON order_items.product_id = p.product_id",
            "JOIN sellers s ON order_items.seller_id = s.seller_id",
        ]
    },

    {
        "table": "customers",
        "description": (
            "Customer demographic and location data. One row per customer per order. "
            "IMPORTANT: One physical customer can have multiple customer_ids — "
            "use customer_unique_id with COUNT(DISTINCT) for true unique customer counts."
        ),
        "columns": {
            "customer_id":              "Order-level customer ID (PK). Links to orders.customer_id.",
            "customer_unique_id":       "True unique customer identifier across all orders. Use COUNT(DISTINCT customer_unique_id) for unique customer counts.",
            "customer_zip_code_prefix": "5-digit Brazilian zip code prefix. Links to geolocation.geolocation_zip_code_prefix.",
            "customer_city":            "City where the customer is located.",
            "customer_state":           "Brazilian state abbreviation (SP, RJ, MG, etc.). Primary column for geographic/regional analysis.",
        },
        "joins": [
            "JOIN orders o ON customers.customer_id = o.customer_id",
            "JOIN geolocation g ON customers.customer_zip_code_prefix = g.geolocation_zip_code_prefix",
        ]
    },

    {
        "table": "products",
        "description": (
            "Product catalog. One row per product. "
            "IMPORTANT: There is NO product_name column. The only way to group products is by product_category_name. "
            "JOIN product_category_translation to get English category names."
        ),
        "columns": {
            "product_id":                  "Unique product identifier (PK). Links to order_items.product_id.",
            "product_category_name":       "ONLY product grouping column available. Use this when user asks to split/group by products. JOIN product_category_translation for English names. CRITICAL: there is NO product_name column in this table — never use p.product_name.",
            "product_name_lenght":         "Character length of product name text (intentional typo in source). NOT a product name — never use for grouping.",
            "product_description_lenght":  "Character length of product description (note: intentional typo in source data).",
            "product_photos_qty":          "Number of product photos in the listing.",
            "product_weight_g":            "Product weight in grams.",
            "product_length_cm":           "Product length in centimeters.",
            "product_height_cm":           "Product height in centimeters.",
            "product_width_cm":            "Product width in centimeters.",
        },
        "joins": [
            "JOIN order_items oi ON products.product_id = oi.product_id",
            "JOIN product_category_translation t ON products.product_category_name = t.product_category_name",
        ]
    },

    {
        "table": "sellers",
        "description": (
            "Seller/merchant information. One row per seller. "
            "Use for seller performance, geographic distribution, and revenue attribution."
        ),
        "columns": {
            "seller_id":               "Unique seller identifier (PK). Links to order_items.seller_id.",
            "seller_zip_code_prefix":  "5-digit zip code prefix of seller location. Links to geolocation.",
            "seller_city":             "City where seller is located.",
            "seller_state":            "Brazilian state abbreviation. Use for seller geographic analysis.",
        },
        "joins": [
            "JOIN order_items oi ON sellers.seller_id = oi.seller_id",
            "JOIN geolocation g ON sellers.seller_zip_code_prefix = g.geolocation_zip_code_prefix",
        ]
    },

    {
        "table": "order_payments",
        "description": (
            "Payment transactions per order. One row per payment method per order. "
            "An order can have multiple rows if customer split payment across methods. "
            "SUM(payment_value) is the PRIMARY revenue metric in this dataset."
        ),
        "columns": {
            "order_id":             "Links to orders.order_id.",
            "payment_sequential":   "Payment sequence number (1 = primary payment method).",
            "payment_type":         "Payment method used: credit_card, boleto, voucher, debit_card.",
            "payment_installments": "Number of installments (1 = paid in full, >1 = installment plan).",
            "payment_value":        "Amount paid in BRL. SUM(payment_value) is the main revenue metric. Always use this for revenue analysis.",
        },
        "joins": [
            "JOIN orders o ON order_payments.order_id = o.order_id",
        ]
    },

    {
        "table": "order_reviews",
        "description": (
            "Customer satisfaction reviews. One row per review. "
            "Not every order has a review. "
            "Use review_score for satisfaction analysis."
        ),
        "columns": {
            "review_id":               "Unique review identifier (PK).",
            "order_id":                "Links to orders.order_id.",
            "review_score":            "Customer satisfaction score: 1 (worst) to 5 (best). Use AVG(review_score) for average satisfaction.",
            "review_comment_title":    "Short title of the review written by customer. Often NULL.",
            "review_comment_message":  "Full review text written by customer. Often NULL.",
            "review_creation_date":    "Date when the review survey was sent to the customer.",
            "review_answer_timestamp": "Date when the customer submitted their review.",
        },
        "joins": [
            "JOIN orders o ON order_reviews.order_id = o.order_id",
        ]
    },

    {
        "table": "geolocation",
        "description": (
            "Geographic coordinates for Brazilian zip codes. "
            "Multiple lat/lng rows per zip code — use AVG() for centroid coordinates. "
            "Join via customer or seller zip code prefix for map-based analysis."
        ),
        "columns": {
            "geolocation_zip_code_prefix": "5-digit Brazilian zip code prefix. Links to customers.customer_zip_code_prefix and sellers.seller_zip_code_prefix.",
            "geolocation_lat":             "Latitude coordinate of the zip code area.",
            "geolocation_lng":             "Longitude coordinate of the zip code area.",
            "geolocation_city":            "City name for this zip code.",
            "geolocation_state":           "Brazilian state abbreviation.",
        },
        "joins": [
            "JOIN customers c ON geolocation.geolocation_zip_code_prefix = c.customer_zip_code_prefix",
            "JOIN sellers s ON geolocation.geolocation_zip_code_prefix = s.seller_zip_code_prefix",
        ]
    },

    {
        "table": "product_category_translation",
        "description": (
            "Lookup table mapping Portuguese product category names to English. "
            "JOIN to products table when user asks about categories in English."
        ),
        "columns": {
            "product_category_name":         "Portuguese category name (PK). Links to products.product_category_name.",
            "product_category_name_english": "English translation of the category name. Use this for displaying category names to users.",
        },
        "joins": [
            "JOIN products p ON product_category_translation.product_category_name = p.product_category_name",
        ]
    },
]