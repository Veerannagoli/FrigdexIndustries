-- Frigdex Industries starter database for MySQL Workbench 8+
-- Workbench: open this file, connect to your local MySQL instance, then click the lightning bolt.
CREATE DATABASE IF NOT EXISTS frigdex CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE frigdex;

CREATE TABLE IF NOT EXISTS admin_users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(80) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  last_login DATETIME NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS products (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(180) NOT NULL,
  brand VARCHAR(100) NOT NULL DEFAULT '',
  model VARCHAR(120) NOT NULL DEFAULT '',
  category VARCHAR(80) NOT NULL DEFAULT 'Freezer',
  description TEXT NULL,
  price DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  stock INT NOT NULL DEFAULT 0,
  capacity VARCHAR(80) NOT NULL DEFAULT '',
  refrigerant VARCHAR(80) NOT NULL DEFAULT '',
  temperature_range VARCHAR(100) NOT NULL DEFAULT '',
  power_consumption VARCHAR(80) NOT NULL DEFAULT '',
  door_type VARCHAR(100) NOT NULL DEFAULT '',
  color VARCHAR(80) NOT NULL DEFAULT '',
  image_url VARCHAR(500) NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_products_active (is_active),
  INDEX idx_products_category (category),
  INDEX idx_products_brand (brand),
  INDEX idx_products_name (name)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS product_images (
  id INT AUTO_INCREMENT PRIMARY KEY,
  product_id INT NOT NULL,
  image_url VARCHAR(500) NOT NULL,
  alt_text VARCHAR(180) NOT NULL DEFAULT '',
  sort_order INT NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_product_images_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS customers (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(150) NOT NULL,
  phone VARCHAR(40) NULL,
  email VARCHAR(180) NULL,
  address TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_customers_phone (phone)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS enquiries (
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer_name VARCHAR(150) NOT NULL,
  phone VARCHAR(40) NULL,
  email VARCHAR(180) NULL,
  product_interest VARCHAR(180) NULL,
  message TEXT NOT NULL,
  status ENUM('New','Contacted','Quoted','Converted','Closed') NOT NULL DEFAULT 'New',
  admin_notes TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_enquiries_status (status),
  INDEX idx_enquiries_created (created_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS orders (
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NULL,
  status ENUM('Pending','Confirmed','Dispatched','Completed','Cancelled') NOT NULL DEFAULT 'Pending',
  total_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  notes TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
  INDEX idx_orders_status (status),
  INDEX idx_orders_created (created_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS order_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  product_id INT NULL,
  product_name VARCHAR(180) NOT NULL,
  quantity INT NOT NULL DEFAULT 1,
  unit_price DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  line_total DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  CONSTRAINT fk_order_items_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
  CONSTRAINT fk_order_items_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
  INDEX idx_order_items_product (product_id)
) ENGINE=InnoDB;

-- Optional sample product based on the product screenshot provided by the user.
-- This is a demo record. Verify price and specs with Frigdex before publishing.
INSERT INTO products
(name,brand,model,category,description,price,stock,capacity,refrigerant,temperature_range,power_consumption,door_type,color,image_url,is_active)
SELECT 'SS TVS XL 65 Eutectic Deep Freezer','Frigdex','TVS XL 65','Deep Freezer',
'Demo reference product. Verify all details with Frigdex Industries before publishing.',
25500,0,'200 L','R 290','-35 Degrees Centigrade','180 W','Top Open Door','Silver','',1
WHERE NOT EXISTS (SELECT 1 FROM products WHERE model='TVS XL 65');
