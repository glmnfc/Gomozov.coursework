-- таблица services (службы)
CREATE TABLE services (
    service_id   int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name         text NOT NULL UNIQUE,
    phone        text,
    created_at   timestamptz NOT NULL DEFAULT now()
);

-- таблица departments (отделы служб)
CREATE TABLE departments (
    department_id   int GENERATED ALWAYS AS IDENTITY,
    service_id      int NOT NULL,
    name            text NOT NULL,
    address         text,
    phone           text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (department_id),
    UNIQUE (service_id, name),
    FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE CASCADE
);

-- таблица sections (участки)
CREATE TABLE sections (
    section_id     int GENERATED ALWAYS AS IDENTITY,
    department_id  int NOT NULL,
    name           text NOT NULL,
    manager        text,
    created_at     timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (section_id),
    UNIQUE (department_id, name),
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE CASCADE
);

-- таблица houses (дома)
CREATE TABLE houses (
    house_id         int GENERATED ALWAYS AS IDENTITY,
    service_id       int NOT NULL,
    department_id    int NOT NULL,
    section_id       int NOT NULL,
    street           text NOT NULL,
    house_number     text NOT NULL,
    building         text, -- корпус
    year_built       int CHECK (year_built >= 1800 AND year_built <= extract(year from now())::int),
    total_apartments int NOT NULL DEFAULT 0 CHECK (total_apartments >= 0),
    resident_count   int NOT NULL DEFAULT 0 CHECK (resident_count >= 0), -- число проживающих, будем поддерживать триггером
    created_at       timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (house_id),
    FOREIGN KEY (service_id)    REFERENCES services(service_id) ON DELETE RESTRICT,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE RESTRICT,
    FOREIGN KEY (section_id)    REFERENCES sections(section_id) ON DELETE RESTRICT,
    UNIQUE (street, house_number, building)
);

-- таблица apartments (квартиры)
CREATE TABLE apartments (
    apartment_id     int GENERATED ALWAYS AS IDENTITY,
    house_id         int NOT NULL,
    apt_number       text NOT NULL,
    floor            int CHECK (floor >= -1 AND floor <= 100),
    living_area      numeric(8,2) NOT NULL CHECK (living_area >= 0),
    total_area       numeric(8,2) NOT NULL CHECK (total_area >= living_area),
    privatized       boolean NOT NULL DEFAULT false,
    cold_water       boolean NOT NULL DEFAULT true,
    hot_water        boolean NOT NULL DEFAULT true,
    garbage_chute     boolean NOT NULL DEFAULT false,
    elevator         boolean NOT NULL DEFAULT false,
    current_residents int NOT NULL DEFAULT 0 CHECK (current_residents >= 0), -- число жильцов, будем поддерживать триггером 
    created_at        timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (apartment_id),
    UNIQUE (house_id, apt_number),
    FOREIGN KEY (house_id) REFERENCES houses(house_id) ON DELETE CASCADE
);

-- таблица payer_codes (шифры плательщика)
CREATE TABLE payer_codes (
    payer_code_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code          text NOT NULL UNIQUE,
    name          text NOT NULL,
    percent_share numeric(5,2) NOT NULL CHECK (percent_share >= 0 AND percent_share <= 100),
    created_at    timestamptz NOT NULL DEFAULT now()
);

-- таблица tenants (жильцы)
CREATE TABLE tenants (
    tenant_id    int GENERATED ALWAYS AS IDENTITY,
    apartment_id int NOT NULL,
    full_name    text NOT NULL,
    inn          text,
    passport     text,
    birth_date   date,
    is_responsible boolean NOT NULL DEFAULT false,
    payer_code_id  int,
    moved_in     date NOT NULL DEFAULT current_date,
    moved_out    date, -- NULL = действующий жилец
    created_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id),
    UNIQUE (apartment_id, full_name, moved_in), 
    UNIQUE (inn),
    FOREIGN KEY (apartment_id) REFERENCES apartments(apartment_id) ON DELETE CASCADE,
    FOREIGN KEY (payer_code_id) REFERENCES payer_codes(payer_code_id) ON DELETE SET NULL,
    CHECK (moved_out IS NULL OR moved_out >= moved_in)
);

-- таблица tariffs (тарифы)
CREATE TABLE tariffs (
    tariff_id   int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_type text NOT NULL, -- cold_water, hot_water, elevator
    has_service  boolean NOT NULL DEFAULT true,
    tariff       numeric(10,4) NOT NULL CHECK (tariff >= 0),
    valid_from   date NOT NULL,
    valid_to     date,
    created_at   timestamptz NOT NULL DEFAULT now(),
    UNIQUE (service_type, valid_from)
);

-- ==================== ИНДЕКСЫ ====================

-- индекс для поиска отделов по службе
CREATE INDEX idx_departments_service ON departments(service_id);

-- индекс для поиска участков по отделу
CREATE INDEX idx_sections_department ON sections(department_id);

-- индекс для поиска домов по участку
CREATE INDEX idx_houses_section ON houses(section_id);

-- индекс для поиска домов по улице
CREATE INDEX idx_houses_street ON houses(street);

-- индекс для поиска квартир по дому
CREATE INDEX idx_apartments_house ON apartments(house_id);

-- индекс для поиска жильцов по квартире
CREATE INDEX idx_tenants_apartment ON tenants(apartment_id);

-- индекс для поиска жильцов по ФИО
CREATE INDEX idx_tenants_fullname ON tenants(full_name);

-- индекс для поиска действующих жильцов
CREATE INDEX idx_tenants_active ON tenants(apartment_id) WHERE moved_out IS NULL;

-- индекс для поиска тарифов по типу услуги
CREATE INDEX idx_tariffs_service_type ON tariffs(service_type);

-- ==================== ПРЕДСТАВЛЕНИЯ (VIEW) ====================

-- Представление 1: по одной таблице - список всех квартир с удобствами
CREATE VIEW v_apartments_info AS
SELECT 
    apartment_id,
    house_id,
    apt_number,
    floor,
    living_area,
    total_area,
    CASE WHEN privatized THEN 'Да' ELSE 'Нет' END AS privatized_text,
    CASE WHEN cold_water THEN 'Да' ELSE 'Нет' END AS cold_water_text,
    CASE WHEN hot_water THEN 'Да' ELSE 'Нет' END AS hot_water_text,
    CASE WHEN garbage_chute THEN 'Да' ELSE 'Нет' END AS garbage_chute_text,
    CASE WHEN elevator THEN 'Да' ELSE 'Нет' END AS elevator_text,
    current_residents
FROM apartments;

-- Представление 2: по нескольким таблицам - полная информация о жильцах
CREATE VIEW v_tenants_full AS
SELECT 
    t.tenant_id,
    t.full_name,
    t.inn,
    t.passport,
    t.birth_date,
    CASE WHEN t.is_responsible THEN 'Да' ELSE 'Нет' END AS is_responsible_text,
    pc.name AS payer_code_name,
    pc.percent_share,
    t.moved_in,
    t.moved_out,
    a.apt_number,
    h.street,
    h.house_number,
    h.building,
    s.name AS section_name,
    d.name AS department_name,
    sv.name AS service_name
FROM tenants t
JOIN apartments a ON t.apartment_id = a.apartment_id
JOIN houses h ON a.house_id = h.house_id
JOIN sections s ON h.section_id = s.section_id
JOIN departments d ON h.department_id = d.department_id
JOIN services sv ON h.service_id = sv.service_id
LEFT JOIN payer_codes pc ON t.payer_code_id = pc.payer_code_id;

-- Представление 3: с GROUP BY и HAVING - статистика по домам с более чем 5 квартирами
CREATE VIEW v_houses_stats AS
SELECT 
    h.house_id,
    h.street,
    h.house_number,
    h.building,
    s.name AS section_name,
    d.name AS department_name,
    sv.name AS service_name,
    COUNT(a.apartment_id) AS apartments_count,
    SUM(a.current_residents) AS total_residents,
    SUM(a.total_area) AS total_area_sum,
    AVG(a.total_area) AS avg_apartment_area
FROM houses h
JOIN sections s ON h.section_id = s.section_id
JOIN departments d ON h.department_id = d.department_id
JOIN services sv ON h.service_id = sv.service_id
LEFT JOIN apartments a ON h.house_id = a.house_id
GROUP BY h.house_id, h.street, h.house_number, h.building, 
         s.name, d.name, sv.name
HAVING COUNT(a.apartment_id) > 0;

-- Представление 4: дополнительное - полная информация о домах
CREATE VIEW v_houses_full AS
SELECT 
    h.house_id,
    sv.name AS service_name,
    d.name AS department_name,
    s.name AS section_name,
    h.street,
    h.house_number,
    h.building,
    h.year_built,
    h.total_apartments,
    h.resident_count
FROM houses h
JOIN services sv ON h.service_id = sv.service_id
JOIN departments d ON h.department_id = d.department_id
JOIN sections s ON h.section_id = s.section_id;

-- ==================== ТРИГГЕРЫ ====================

-- Функция для обновления current_residents в apartments
CREATE OR REPLACE FUNCTION update_apartment_residents()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        -- при добавлении жильца увеличиваем счетчик если он активный
        IF NEW.moved_out IS NULL THEN
            UPDATE apartments 
            SET current_residents = current_residents + 1 
            WHERE apartment_id = NEW.apartment_id;
        END IF;
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        -- если жилец переехал (moved_out стал не NULL)
        IF OLD.moved_out IS NULL AND NEW.moved_out IS NOT NULL THEN
            UPDATE apartments 
            SET current_residents = current_residents - 1 
            WHERE apartment_id = NEW.apartment_id;
        -- если жилец вернулся (moved_out стал NULL)
        ELSIF OLD.moved_out IS NOT NULL AND NEW.moved_out IS NULL THEN
            UPDATE apartments 
            SET current_residents = current_residents + 1 
            WHERE apartment_id = NEW.apartment_id;
        END IF;
        -- если сменилась квартира
        IF OLD.apartment_id != NEW.apartment_id THEN
            IF OLD.moved_out IS NULL THEN
                UPDATE apartments 
                SET current_residents = current_residents - 1 
                WHERE apartment_id = OLD.apartment_id;
            END IF;
            IF NEW.moved_out IS NULL THEN
                UPDATE apartments 
                SET current_residents = current_residents + 1 
                WHERE apartment_id = NEW.apartment_id;
            END IF;
        END IF;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        -- при удалении уменьшаем если был активный
        IF OLD.moved_out IS NULL THEN
            UPDATE apartments 
            SET current_residents = current_residents - 1 
            WHERE apartment_id = OLD.apartment_id;
        END IF;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Триггер на таблицу tenants для обновления current_residents
CREATE TRIGGER trg_update_apartment_residents
AFTER INSERT OR UPDATE OR DELETE ON tenants
FOR EACH ROW EXECUTE FUNCTION update_apartment_residents();

-- Функция для обновления resident_count в houses
CREATE OR REPLACE FUNCTION update_house_residents()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        -- обновляем счетчик в доме
        UPDATE houses 
        SET resident_count = resident_count + (NEW.current_residents - OLD.current_residents)
        WHERE house_id = NEW.house_id;
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Триггер на таблицу apartments для обновления resident_count в houses
CREATE TRIGGER trg_update_house_residents
AFTER UPDATE OF current_residents ON apartments
FOR EACH ROW EXECUTE FUNCTION update_house_residents();

-- Функция для обновления total_apartments в houses при добавлении/удалении квартир
CREATE OR REPLACE FUNCTION update_house_apartments_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE houses 
        SET total_apartments = total_apartments + 1 
        WHERE house_id = NEW.house_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE houses 
        SET total_apartments = total_apartments - 1 
        WHERE house_id = OLD.house_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Триггер для подсчета квартир в доме
CREATE TRIGGER trg_update_house_apartments
AFTER INSERT OR DELETE ON apartments
FOR EACH ROW EXECUTE FUNCTION update_house_apartments_count();