CREATE TABLE categories (
    category_id BIGSERIAL PRIMARY KEY,

    category_name VARCHAR(100) NOT NULL,
    description TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE products (
    product_id BIGSERIAL PRIMARY KEY,

    category_id BIGINT,

    product_name VARCHAR(255) NOT NULL,
    sku VARCHAR(100) NOT NULL,
    description TEXT,

    unit_price NUMERIC(12,2) NOT NULL,
    cost_price NUMERIC(12,2),

    product_status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_products_category
        FOREIGN KEY (category_id)
        REFERENCES categories(category_id)
);

CREATE TABLE customers (
    customer_id BIGSERIAL PRIMARY KEY,

    first_name VARCHAR(100),
    last_name VARCHAR(100),

    email VARCHAR(255),
    phone VARCHAR(50),

    date_of_birth DATE,
    gender VARCHAR(30),

    city VARCHAR(100),
    country VARCHAR(100),

    customer_status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE orders (
    order_id BIGSERIAL PRIMARY KEY,

    customer_id BIGINT,

    order_date TIMESTAMP NOT NULL,

    order_status VARCHAR(30) NOT NULL,

    currency VARCHAR(3) NOT NULL DEFAULT 'USD',

    shipping_address TEXT,
    shipping_city VARCHAR(100),
    shipping_country VARCHAR(100),

    total_amount NUMERIC(14,2) NOT NULL DEFAULT 0,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
);


CREATE TABLE order_items (
    order_item_id BIGSERIAL PRIMARY KEY,

    order_id BIGINT,
    product_id BIGINT,

    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12,2) NOT NULL,

    discount_amount NUMERIC(12,2) DEFAULT 0,

    line_total NUMERIC(14,2) NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_order_items_order
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id),

    CONSTRAINT fk_order_items_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
);


CREATE TABLE payments (
    payment_id BIGSERIAL PRIMARY KEY,

    order_id BIGINT,

    payment_date TIMESTAMP,

    payment_method VARCHAR(50),
    payment_status VARCHAR(30),

    amount NUMERIC(14,2),

    transaction_reference VARCHAR(255),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_payments_order
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id)
);

CREATE TABLE returns (
    return_id BIGSERIAL PRIMARY KEY,

    order_id BIGINT,
    order_item_id BIGINT,

    return_date TIMESTAMP,

    return_reason VARCHAR(255),

    quantity INTEGER,

    refund_amount NUMERIC(14,2),

    return_status VARCHAR(30),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_returns_order
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id),

    CONSTRAINT fk_returns_order_item
        FOREIGN KEY (order_item_id)
        REFERENCES order_items(order_item_id)
);


CREATE INDEX idx_products_category_id
    ON products(category_id);

CREATE INDEX idx_orders_customer_id
    ON orders(customer_id);

CREATE INDEX idx_orders_order_date
    ON orders(order_date);

CREATE INDEX idx_order_items_order_id
    ON order_items(order_id);

CREATE INDEX idx_order_items_product_id
    ON order_items(product_id);

CREATE INDEX idx_payments_order_id
    ON payments(order_id);

CREATE INDEX idx_returns_order_id
    ON returns(order_id);