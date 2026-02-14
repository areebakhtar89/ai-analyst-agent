import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(42)

os.makedirs("data", exist_ok=True)

# Customers
customers = []
regions = ["North", "South", "East", "West"]
segments = ["SMB", "Enterprise"]

for i in range(1, 101):
    customers.append([
        i,
        f"Customer_{i}",
        np.random.choice(regions),
        np.random.choice(segments)
    ])

customers_df = pd.DataFrame(
    customers,
    columns=["customer_id", "customer_name", "region", "segment"]
)

# Products
products = [
    [1, "Laptop", "Electronics", 60000],
    [2, "Phone", "Electronics", 25000],
    [3, "Tablet", "Electronics", 20000],
    [4, "Headphones", "Accessories", 5000],
]

products_df = pd.DataFrame(
    products,
    columns=["product_id", "product_name", "category", "price"]
)

# Orders (2 years of data)
orders = []
order_items = []

start_date = datetime(2023, 1, 1)
order_id = 1
order_item_id = 1

for day in range(730):  # 2 years
    date = start_date + timedelta(days=day)

    # random number of orders per day
    for _ in range(np.random.randint(2, 6)):
        customer_id = np.random.randint(1, 101)

        orders.append([
            order_id,
            customer_id,
            date.strftime("%Y-%m-%d"),
            0  # will compute later
        ])

        # each order has 1–3 items
        num_items = np.random.randint(1, 4)
        total_amount = 0

        for _ in range(num_items):
            product = products_df.sample(1).iloc[0]
            quantity = np.random.randint(1, 3)
            revenue = product["price"] * quantity
            total_amount += revenue

            order_items.append([
                order_item_id,
                order_id,
                product["product_id"],
                quantity,
                revenue
            ])
            order_item_id += 1

        orders[-1][3] = total_amount
        order_id += 1

orders_df = pd.DataFrame(
    orders,
    columns=["order_id", "customer_id", "order_date", "total_amount"]
)

order_items_df = pd.DataFrame(
    order_items,
    columns=["order_item_id", "order_id", "product_id", "quantity", "revenue"]
)

# Save to CSV
customers_df.to_csv("data/customers.csv", index=False)
products_df.to_csv("data/products.csv", index=False)
orders_df.to_csv("data/orders.csv", index=False)
order_items_df.to_csv("data/order_items.csv", index=False)

print("Data generation complete.")