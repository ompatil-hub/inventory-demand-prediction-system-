CREATE DATABASE IF NOT EXISTS inventorydb;
USE inventorydb;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(255) PRIMARY KEY,
    category VARCHAR(255),
    price DECIMAL(10, 2)
);

CREATE TABLE IF NOT EXISTS inventory (
    product_id VARCHAR(255),
    store_id VARCHAR(255),
    record_date DATE,
    store_name VARCHAR(255),
    inventory_level INT,
    units_ordered INT,
    PRIMARY KEY (product_id, store_name)
);

CREATE TABLE IF NOT EXISTS predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id VARCHAR(255),
    prediction_date DATE,
    predicted_demand DECIMAL(10, 2),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255),
    action_type VARCHAR(255),
    product_id VARCHAR(255),
    input_summary TEXT,
    predicted_demand DECIMAL(10, 2),
    recommendation TEXT,
    created_at DATE
);