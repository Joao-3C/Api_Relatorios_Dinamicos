# models.py
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, CHAR, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db import Base

class Cliente(Base):
    __tablename__ = "CLIENTES"
    id: Mapped[int]             = mapped_column("ID", primary_key=True)
    cnpj: Mapped[str]           = mapped_column("CNPJ", CHAR(14), unique=True, nullable=False)
    nome: Mapped[str]           = mapped_column("NOME", String(120), nullable=False)
    telefone: Mapped[str | None]= mapped_column("TELEFONE", String(20))
    email: Mapped[str]          = mapped_column("EMAIL", String(255), nullable=False)
    inscricao_estadual: Mapped[str | None] = mapped_column("INSCRICAO_ESTADUAL", String(30))
    uf: Mapped[str | None]      = mapped_column("UF", CHAR(2))
    cidade: Mapped[str | None]  = mapped_column("CIDADE", String(100))
    endereco: Mapped[str | None]= mapped_column("ENDERECO", String(200))
    criado_em: Mapped[datetime | None] = mapped_column("CRIADO_EM", DateTime)

    passagens: Mapped[list["Passagem"]] = relationship(back_populates="cliente")

class Motorista(Base):
    __tablename__ = "MOTORISTAS"
    id: Mapped[int]             = mapped_column("ID", primary_key=True)
    nome: Mapped[str]           = mapped_column("NOME", String(120), nullable=False)
    cpf: Mapped[str]            = mapped_column("CPF", CHAR(11), unique=True, nullable=False)
    telefone: Mapped[str | None]= mapped_column("TELEFONE", String(20))
    criado_em: Mapped[datetime | None] = mapped_column("CRIADO_EM", DateTime)

    veiculos: Mapped[list["Veiculo"]] = relationship(back_populates="motorista")

class Veiculo(Base):
    __tablename__ = "VEICULOS"
    id: Mapped[int]             = mapped_column("ID", primary_key=True)
    placa: Mapped[str]          = mapped_column("PLACA", String(10), unique=True, nullable=False)
    marca: Mapped[str]          = mapped_column("MARCA", String(60), nullable=False)
    modelo: Mapped[str]         = mapped_column("MODELO", String(60), nullable=False)
    motorista_id: Mapped[int | None] = mapped_column("MOTORISTA_ID", ForeignKey("MOTORISTAS.ID"))
    criado_em: Mapped[datetime | None] = mapped_column("CRIADO_EM", DateTime)

    motorista: Mapped["Motorista | None"] = relationship(back_populates="veiculos")
    passagens: Mapped[list["Passagem"]] = relationship(back_populates="veiculo")

class Passagem(Base):
    __tablename__ = "PASSAGENS"
    id: Mapped[int]                 = mapped_column("ID", primary_key=True)
    veiculo_id: Mapped[int | None]  = mapped_column("VEICULO_ID", ForeignKey("VEICULOS.ID"))
    placa_livre: Mapped[str | None] = mapped_column("PLACA_LIVRE", String(10))
    cliente_id: Mapped[int]         = mapped_column("CLIENTE_ID", ForeignKey("CLIENTES.ID"), nullable=False)
    peso_chegada: Mapped[Decimal]   = mapped_column("PESO_CHEGADA", Numeric(12, 3), nullable=False)
    peso_saida:   Mapped[Decimal]   = mapped_column("PESO_SAIDA",   Numeric(12, 3), nullable=False)
    # coluna virtual no banco: PESO_LIQUIDO (acessar via Passagem.__table__.c.PESO_LIQUIDO)
    entrada_ts:   Mapped[datetime]  = mapped_column("ENTRADA_TS", DateTime, nullable=False)
    saida_ts:     Mapped[datetime | None] = mapped_column("SAIDA_TS", DateTime)
    observacao:   Mapped[str | None]= mapped_column("OBSERVACAO", String(400))
    criado_em:    Mapped[datetime | None] = mapped_column("CRIADO_EM", DateTime)

    cliente:  Mapped["Cliente"]           = relationship(back_populates="passagens")
    veiculo:  Mapped["Veiculo | None"]    = relationship(back_populates="passagens")

