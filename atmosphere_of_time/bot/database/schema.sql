-- =====================================================
-- Atmosphere of Time — схема БД с демо-данными
-- =====================================================

CREATE TABLE IF NOT EXISTS users (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id      INTEGER UNIQUE NOT NULL,
    username   TEXT,
    full_name  TEXT,
    phone      TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id   INTEGER REFERENCES categories(id),
    name          TEXT NOT NULL,
    brand         TEXT NOT NULL,
    description   TEXT,
    top_notes     TEXT,
    heart_notes   TEXT,
    base_notes    TEXT,
    price         REAL NOT NULL,
    photo_id      TEXT,
    stock         INTEGER DEFAULT 0,
    is_new        INTEGER DEFAULT 0,
    is_bestseller INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS product_volumes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    volume_ml  INTEGER NOT NULL,
    price      REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS cart (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    volume_ml  INTEGER NOT NULL,
    qty        INTEGER NOT NULL DEFAULT 1,
    UNIQUE(user_id, product_id, volume_ml)
);

CREATE TABLE IF NOT EXISTS favorites (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE(user_id, product_id)
);

CREATE TABLE IF NOT EXISTS orders (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER REFERENCES users(id),
    total          REAL NOT NULL,
    status         TEXT DEFAULT 'новый',
    name           TEXT,
    phone          TEXT,
    address        TEXT,
    payment_method TEXT,
    comment        TEXT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id   INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER,
    volume_ml  INTEGER,
    qty        INTEGER,
    price      REAL
);

-- =====================================================
-- Категории
-- =====================================================
INSERT OR IGNORE INTO categories (id, name, slug) VALUES
    (1, 'Унисекс',     'unisex'),
    (2, 'Женские',     'female'),
    (3, 'Мужские',     'male');

-- =====================================================
-- Демо-товары (8 ароматов)
-- =====================================================
INSERT OR IGNORE INTO products
    (id, category_id, name, brand, description, top_notes, heart_notes, base_notes, price, photo_id, stock, is_new, is_bestseller)
VALUES
(1, 1, 'Time Sand', 'AoT Atelier',
 'Тёплый янтарный аромат о пустыне на закате — когда время замедляется, а песок хранит тепло дня.',
 'Бергамот, розовый перец', 'Ирис, ладан', 'Амбра, сандал, ваниль',
 3200, 'https://images.unsplash.com/photo-1541643600914-78b084683601?w=800', 15, 1, 1),

(2, 3, 'Midnight Hour', 'Noir Éditions',
 'Строгий и дымный — для тех, кто ценит тишину после полуночи и кожу старых библиотек.',
 'Чёрный перец, кардамон', 'Кожа, ветивер', 'Уд, пачули, табак',
 4500, 'https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?w=800', 10, 0, 1),

(3, 2, 'Velvet Dawn', 'AoT Atelier',
 'Нежный, как утренний свет на шёлке. Розовый ирис и мягкая пудра — аромат-объятие.',
 'Пион, личи', 'Роза, ирис', 'Мускус, белый кедр, ваниль',
 3800, 'https://images.unsplash.com/photo-1587017539504-67cfbddac569?w=800', 20, 1, 0),

(4, 1, 'Amber Clock', 'Chronos Lab',
 'Механизм из амбры и специй — тёплый, тягучий, механический. Слышен за метр.',
 'Апельсин, гвоздика', 'Корица, бензоин', 'Амбра, лабданум, мускус',
 2900, 'https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800', 25, 0, 1),

(5, 3, 'Noir Chronos', 'Chronos Lab',
 'Глубокий и тёмный. Смолы, кожа, специи — аромат для зимних вечеров и сильных решений.',
 'Бергамот, шафран', 'Кедр, кипарис', 'Уд, кожа, амбра',
 5200, 'https://images.unsplash.com/photo-1615634260167-c8cdede054de?w=800', 8, 1, 1),

(6, 2, 'Silk Moment', 'Maison AoT',
 'Воздушный и минеральный. Как прохладный шёлк — идеален в жару и в городе.',
 'Морская соль, грейпфрут', 'Жасмин, фиалка', 'Белый мускус, кедр',
 3400, 'https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800', 18, 0, 0),

(7, 1, 'Frozen Memory', 'Noir Éditions',
 'Холодный, металлический, ностальгический — запах фотоальбома из 90-х, открытого в декабре.',
 'Мята, эвкалипт', 'Ладан, кедр', 'Ветивер, амбра, мускус',
 3600, 'https://images.unsplash.com/photo-1610461888750-10bfc601b874?w=800', 12, 1, 0),

(8, 2, 'Eternal Bloom', 'Maison AoT',
 'Тёплый цветочный с уклоном в восток. Роза, иланг и мягкая ваниль — для вечеров.',
 'Иланг, мандарин', 'Роза, тубероза', 'Ваниль, бензоин, сандал',
 4100, 'https://images.unsplash.com/photo-1563170351-be82bc888aa4?w=800', 14, 0, 1);

-- =====================================================
-- Объёмы и цены
-- =====================================================
INSERT OR IGNORE INTO product_volumes (product_id, volume_ml, price) VALUES
    (1, 30, 3200), (1, 50, 4500), (1, 100, 7200),
    (2, 30, 4500), (2, 50, 6300), (2, 100, 9800),
    (3, 30, 3800), (3, 50, 5300), (3, 100, 8500),
    (4, 30, 2900), (4, 50, 4100), (4, 100, 6600),
    (5, 30, 5200), (5, 50, 7300), (5, 100, 11500),
    (6, 30, 3400), (6, 50, 4800), (6, 100, 7600),
    (7, 30, 3600), (7, 50, 5000), (7, 100, 8000),
    (8, 30, 4100), (8, 50, 5700), (8, 100, 9000);