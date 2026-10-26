"""
store_db.py -- M7.6 ke liye chota sa WATCH STORE database (SQLite, in-memory).

Har baar SAME data banta ha (fixed seed) taake har model ko bilkul same database mile
-- like-for-like comparison ki pehli shart.

Tables:
    customers   (customer_id, name, city, joined_date)
    products    (product_id, name, category, brand, price_pkr)
    orders      (order_id, customer_id, order_date, status, payment_method)
    order_items (order_id, product_id, quantity, unit_price_pkr)
"""

import random
import sqlite3

SCHEMA = """
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    city        TEXT NOT NULL,           -- e.g. 'Lahore', 'Karachi', 'Islamabad'
    joined_date TEXT NOT NULL            -- 'YYYY-MM-DD'
);
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    category   TEXT NOT NULL,            -- 'watch' or 'wallet'
    brand      TEXT NOT NULL,
    price_pkr  INTEGER NOT NULL          -- current list price in PKR
);
CREATE TABLE orders (
    order_id       INTEGER PRIMARY KEY,
    customer_id    INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date     TEXT NOT NULL,        -- 'YYYY-MM-DD'
    status         TEXT NOT NULL,        -- 'pending','shipped','delivered','cancelled','returned'
    payment_method TEXT NOT NULL         -- always 'COD'
);
CREATE TABLE order_items (
    order_id       INTEGER NOT NULL REFERENCES orders(order_id),
    product_id     INTEGER NOT NULL REFERENCES products(product_id),
    quantity       INTEGER NOT NULL,
    unit_price_pkr INTEGER NOT NULL      -- price actually charged for one unit
);
""".strip()

CUSTOMERS = [
    (1, "Ali Raza", "Lahore", "2026-01-12"),
    (2, "Sara Khan", "Lahore", "2026-02-03"),
    (3, "Usman Tariq", "Karachi", "2026-02-20"),
    (4, "Hina Ahmed", "Rawalpindi", "2026-03-05"),
    (5, "Bilal Ahmed", "Lahore", "2026-03-18"),
    (6, "Ayesha Noor", "Islamabad", "2026-04-02"),
    (7, "Hamza Iqbal", "Karachi", "2026-05-14"),
    (8, "Zainab Ali", "Faisalabad", "2026-06-01"),
]

PRODUCTS = [
    (1, "Classic Silver Chronograph", "watch", "Tempo", 8500),
    (2, "Gold Dial Analog Watch", "watch", "Aurum", 12000),
    (3, "Steel Mesh Watch", "watch", "Tempo", 9500),
    (4, "Sports Digital Watch", "watch", "Pulse", 4000),
    (5, "Black Leather Wallet", "wallet", "Hide&Co", 2500),
    (6, "Brown Bifold Wallet", "wallet", "Hide&Co", 2200),
    (7, "Slim Card Holder", "wallet", "Carry", 1500),
    (8, "Rose Gold Ladies Watch", "watch", "Aurum", 11000),
    (9, "Smart Fitness Watch", "watch", "Pulse", 7000),
    (10, "Travel Zip Wallet", "wallet", "Carry", 3000),
    (11, "Skeleton Automatic Watch", "watch", "Aurum", 25000),   # naya, abhi tak koi order nahi
    (12, "RFID Leather Wallet", "wallet", "Carry", 3500),        # naya, abhi tak koi order nahi
]
SOLD_PRODUCT_IDS = range(1, 11)          # orders sirf pehle 10 products ke

STATUSES = ["delivered"] * 5 + ["shipped"] * 2 + ["pending"] * 2 + ["cancelled", "returned"]


def _orders_and_items(seed: int = 42):
    rng = random.Random(seed)
    orders, items = [], []
    for order_id in range(1001, 1031):                    # 30 orders, Jun-Oct 2026
        customer_id = rng.randint(1, len(CUSTOMERS))
        month = rng.randint(6, 10)
        day = rng.randint(1, 28)
        orders.append((order_id, customer_id, f"2026-{month:02d}-{day:02d}",
                       rng.choice(STATUSES), "COD"))
        for product_id in rng.sample(SOLD_PRODUCT_IDS, rng.randint(1, 3)):
            list_price = PRODUCTS[product_id - 1][4]
            discount = rng.choice([0, 0, 0, 500])           # kabhi kabhi discount
            items.append((order_id, product_id, rng.randint(1, 2), list_price - discount))
    return orders, items


def build_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.executescript(SCHEMA)
    orders, items = _orders_and_items()
    conn.executemany("INSERT INTO customers VALUES (?,?,?,?)", CUSTOMERS)
    conn.executemany("INSERT INTO products VALUES (?,?,?,?,?)", PRODUCTS)
    conn.executemany("INSERT INTO orders VALUES (?,?,?,?,?)", orders)
    conn.executemany("INSERT INTO order_items VALUES (?,?,?,?)", items)
    conn.commit()
    return conn
