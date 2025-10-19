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

