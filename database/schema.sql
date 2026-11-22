-- =====================================================================
-- MediMatch IA — esquema relacional (PostgreSQL)
-- Todo el catálogo es SIMULADO. No se almacenan datos personales ni médicos.
-- Docker ejecuta este archivo automáticamente la primera vez que crea la BD.
-- =====================================================================

-- Aseguradoras ficticias. es_simulada solo admite TRUE: la BD no puede
-- contener una aseguradora marcada como real.
CREATE TABLE aseguradoras (
    id           SERIAL PRIMARY KEY,
    external_id  VARCHAR(50)  NOT NULL UNIQUE,
    nombre       VARCHAR(120) NOT NULL,
    es_simulada  BOOLEAN      NOT NULL DEFAULT TRUE CHECK (es_simulada)
);

-- Planes. (aseguradora_id, external_id) evita duplicados al sincronizar.
-- activo = FALSE cuando el plan deja de aparecer en la API mock.
CREATE TABLE planes (
    id              SERIAL PRIMARY KEY,
    aseguradora_id  INT NOT NULL REFERENCES aseguradoras(id) ON DELETE CASCADE,
    external_id     VARCHAR(50)   NOT NULL,
    nombre          VARCHAR(120)  NOT NULL,
    nivel           VARCHAR(20)   NOT NULL CHECK (nivel IN ('Básico', 'Intermedio', 'Premium')),
    suma_asegurada  NUMERIC(14,2) NOT NULL CHECK (suma_asegurada > 0),
    moneda          CHAR(3)       NOT NULL DEFAULT 'MXN',
    activo          BOOLEAN       NOT NULL DEFAULT TRUE,
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT now(),
    UNIQUE (aseguradora_id, external_id)
);

-- Variantes de deducible: dominio de la variable D del CSP.
-- La prima vive aquí porque depende del deducible elegido.
CREATE TABLE variantes_deducible (
    id                    SERIAL PRIMARY KEY,
    plan_id               INT NOT NULL REFERENCES planes(id) ON DELETE CASCADE,
    deducible             NUMERIC(12,2) NOT NULL CHECK (deducible >= 0),
    coaseguro_porcentaje  NUMERIC(5,2)  NOT NULL CHECK (coaseguro_porcentaje BETWEEN 0 AND 100),
    prima_mensual         NUMERIC(12,2) NOT NULL CHECK (prima_mensual > 0),
    UNIQUE (plan_id, deducible)
);

-- Catálogo general de coberturas.
CREATE TABLE coberturas (
    id           SERIAL PRIMARY KEY,
    codigo       VARCHAR(40)  NOT NULL UNIQUE,
    nombre       VARCHAR(120) NOT NULL,
    descripcion  TEXT
);

-- Qué ofrece cada plan: incluida (costo 0) u opcional (costo extra mensual).
-- Si no hay fila, el plan no ofrece esa cobertura.
CREATE TABLE plan_coberturas (
    plan_id       INT NOT NULL REFERENCES planes(id) ON DELETE CASCADE,
    cobertura_id  INT NOT NULL REFERENCES coberturas(id),
    tipo          VARCHAR(10)   NOT NULL CHECK (tipo IN ('incluida', 'opcional')),
    costo_extra   NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (costo_extra >= 0),
    PRIMARY KEY (plan_id, cobertura_id),
    CHECK ((tipo = 'incluida' AND costo_extra = 0) OR (tipo = 'opcional' AND costo_extra > 0))
);

-- Reglas de compatibilidad: restricciones binarias del CSP.
--   requiere      : cobertura → cobertura_objetivo debe incluirse también.
--   excluye       : cobertura y cobertura_objetivo no pueden ir juntas.
--   deducible_max : cobertura solo disponible si deducible <= valor.
CREATE TABLE reglas_compatibilidad (
    id                     SERIAL PRIMARY KEY,
    plan_id                INT NOT NULL REFERENCES planes(id) ON DELETE CASCADE,
    tipo                   VARCHAR(15) NOT NULL CHECK (tipo IN ('requiere', 'excluye', 'deducible_max')),
    cobertura_id           INT NOT NULL REFERENCES coberturas(id),
    cobertura_objetivo_id  INT REFERENCES coberturas(id),
    valor                  NUMERIC(12,2),
    CHECK (
        (tipo IN ('requiere', 'excluye') AND cobertura_objetivo_id IS NOT NULL AND valor IS NULL)
        OR (tipo = 'deducible_max' AND cobertura_objetivo_id IS NULL AND valor IS NOT NULL)
    )
);

-- Consultas de recomendación: solo preferencias (presupuesto, pesos, coberturas)
-- y un resumen del resultado. Sin nombre, edad, correo ni datos de salud.
CREATE TABLE consultas (
    id                 SERIAL PRIMARY KEY,
    preferencias_json  JSONB NOT NULL,
    resultado_json     JSONB,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Bitácora de sincronizaciones con la API mock.
CREATE TABLE sincronizaciones (
    id            SERIAL PRIMARY KEY,
    fecha         TIMESTAMPTZ  NOT NULL DEFAULT now(),
    origen        VARCHAR(200) NOT NULL,
    creados       INT NOT NULL DEFAULT 0,
    actualizados  INT NOT NULL DEFAULT 0,
    desactivados  INT NOT NULL DEFAULT 0,
    sin_cambios   INT NOT NULL DEFAULT 0,
    resultado     VARCHAR(10) NOT NULL CHECK (resultado IN ('ok', 'error')),
    mensaje       TEXT
);

CREATE INDEX idx_planes_activo       ON planes(activo);
CREATE INDEX idx_variantes_plan      ON variantes_deducible(plan_id);
CREATE INDEX idx_reglas_plan         ON reglas_compatibilidad(plan_id);
CREATE INDEX idx_sincronizaciones_f  ON sincronizaciones(fecha DESC);
