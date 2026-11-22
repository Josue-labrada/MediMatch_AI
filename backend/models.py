"""
Modelos ORM: reflejan database/schema.sql (la fuente de verdad del esquema es el SQL;
estas clases solo lo mapean para consultarlo desde Python).
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import JSON, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

JsonType = JSON().with_variant(JSONB(), "postgresql")


class Aseguradora(Base):
    __tablename__ = "aseguradoras"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(50), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    es_simulada: Mapped[bool] = mapped_column(default=True)

    planes: Mapped[List["PlanDB"]] = relationship(back_populates="aseguradora")


class Cobertura(Base):
    __tablename__ = "coberturas"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(40), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[Optional[str]] = mapped_column(Text)


class PlanDB(Base):
    __tablename__ = "planes"

    id: Mapped[int] = mapped_column(primary_key=True)
    aseguradora_id: Mapped[int] = mapped_column(ForeignKey("aseguradoras.id", ondelete="CASCADE"))
    external_id: Mapped[str] = mapped_column(String(50))
    nombre: Mapped[str] = mapped_column(String(120))
    nivel: Mapped[str] = mapped_column(String(20))
    suma_asegurada: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    moneda: Mapped[str] = mapped_column(String(3), default="MXN")
    activo: Mapped[bool] = mapped_column(default=True)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())

    aseguradora: Mapped[Aseguradora] = relationship(back_populates="planes")
    variantes: Mapped[List["VarianteDB"]] = relationship(
        cascade="all, delete-orphan", order_by="VarianteDB.deducible"
    )
    coberturas: Mapped[List["PlanCobertura"]] = relationship(cascade="all, delete-orphan")
    reglas: Mapped[List["ReglaDB"]] = relationship(cascade="all, delete-orphan", order_by="ReglaDB.id")


class VarianteDB(Base):
    __tablename__ = "variantes_deducible"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("planes.id", ondelete="CASCADE"))
    deducible: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    coaseguro_porcentaje: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    prima_mensual: Mapped[Decimal] = mapped_column(Numeric(12, 2))


class PlanCobertura(Base):
    __tablename__ = "plan_coberturas"

    plan_id: Mapped[int] = mapped_column(ForeignKey("planes.id", ondelete="CASCADE"), primary_key=True)
    cobertura_id: Mapped[int] = mapped_column(ForeignKey("coberturas.id"), primary_key=True)
    tipo: Mapped[str] = mapped_column(String(10))
    costo_extra: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    cobertura: Mapped[Cobertura] = relationship()


class ReglaDB(Base):
    __tablename__ = "reglas_compatibilidad"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("planes.id", ondelete="CASCADE"))
    tipo: Mapped[str] = mapped_column(String(15))
    cobertura_id: Mapped[int] = mapped_column(ForeignKey("coberturas.id"))
    cobertura_objetivo_id: Mapped[Optional[int]] = mapped_column(ForeignKey("coberturas.id"))
    valor: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))

    cobertura: Mapped[Cobertura] = relationship(foreign_keys=[cobertura_id])
    objetivo: Mapped[Optional[Cobertura]] = relationship(foreign_keys=[cobertura_objetivo_id])


class Consulta(Base):
    __tablename__ = "consultas"

    id: Mapped[int] = mapped_column(primary_key=True)
    preferencias_json: Mapped[dict] = mapped_column(JsonType)
    resultado_json: Mapped[Optional[dict]] = mapped_column(JsonType)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Sincronizacion(Base):
    __tablename__ = "sincronizaciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[datetime] = mapped_column(server_default=func.now())
    origen: Mapped[str] = mapped_column(String(200))
    creados: Mapped[int] = mapped_column(default=0)
    actualizados: Mapped[int] = mapped_column(default=0)
    desactivados: Mapped[int] = mapped_column(default=0)
    sin_cambios: Mapped[int] = mapped_column(default=0)
    resultado: Mapped[str] = mapped_column(String(10))
    mensaje: Mapped[Optional[str]] = mapped_column(Text)
