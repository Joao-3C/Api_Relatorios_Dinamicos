from typing import Dict, List, Tuple
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select, inspect
from db import get_session
from models import Cliente, Veiculo, Motorista, Passagem

app = FastAPI()

# Tabelas (pelos models)
TABLES: Dict[str, object] = {
    "CLIENTES":   Cliente.__table__,
    "VEICULOS":   Veiculo.__table__,
    "MOTORISTAS": Motorista.__table__,
    "PASSAGENS":  Passagem.__table__,
}

# Regras de JOIN (whitelist)
JOIN_RULES: Dict[Tuple[str, str], Tuple[str, object]] = {
    ("VEICULOS",  "MOTORISTAS"): ("left",  TABLES["VEICULOS"].c.MOTORISTA_ID == TABLES["MOTORISTAS"].c.ID),

    ("PASSAGENS", "CLIENTES"):   ("inner", TABLES["PASSAGENS"].c.CLIENTE_ID   == TABLES["CLIENTES"].c.ID),
    ("PASSAGENS", "VEICULOS"):   ("left",  TABLES["PASSAGENS"].c.VEICULO_ID   == TABLES["VEICULOS"].c.ID),
    ("VEICULOS",  "MOTORISTAS"): ("left",  TABLES["VEICULOS"].c.MOTORISTA_ID  == TABLES["MOTORISTAS"].c.ID),
}

# Apelidos de relacionamentos (o cliente pode usar nome singular OU nome da tabela)
REL_EDGES: Dict[str, Dict[str, str]] = {
    "PASSAGENS": {"CLIENTE": "CLIENTES", "CLIENTES": "CLIENTES",
                  "VEICULO": "VEICULOS", "VEICULOS": "VEICULOS"},
    "VEICULOS":  {"MOTORISTA": "MOTORISTAS", "MOTORISTAS": "MOTORISTAS"},
    "CLIENTES":  {},
    "MOTORISTAS": {},
}

class RelatorioReq(BaseModel):
    colunas: List[str] = Field(..., description='Cada item pode ser "COLUNA" ou "REL1.REL2.COLUNA".')

@app.post("/relatorio/{tabela}")
def relatorio(payload: RelatorioReq, tabela: str, db: Session = Depends(get_session)):
    base = tabela.upper()
    if base not in TABLES:
        raise HTTPException(400, f"Tabela não permitida: {base}")

    from_clause = TABLES[base]
    joined: set[Tuple[str, str]] = set()  # guarda pares já juntados (FROM, TO)

    def ensure_join_pair(a: str, b: str):
        """Aplica o JOIN (se ainda não aplicado) entre tabelas a -> b usando JOIN_RULES."""
        nonlocal from_clause
        if (a, b) in joined:
            return
        rule = JOIN_RULES.get((a, b))
        if not rule:
            raise HTTPException(400, f"Não há JOIN permitido entre {a} e {b}.")
        how, on_expr = rule
        if how == "inner":
            from_clause = from_clause.join(TABLES[b], on_expr)
        else:
            from_clause = from_clause.outerjoin(TABLES[b], on_expr)
        joined.add((a, b))

    def resolve_chain(base_table: str, chain_raw: str) -> Tuple[str, str, str]:
        """
        Resolve uma cadeia tipo "REL1.REL2.COL" partindo de base_table.
        Para cada RELn, descobre a tabela destino via REL_EDGES e aplica JOIN.
        Retorna (final_table, column_name, label_para_select).
        """
        parts = [p.strip().upper() for p in chain_raw.split(".") if p.strip()]
        if not parts:
            raise HTTPException(400, "Coluna vazia/ inválida.")

        # caso simples: só a coluna
        if len(parts) == 1:
            col = parts[0]
            # valida coluna na base
            if col not in {c.name for c in TABLES[base_table].columns}:
                raise HTTPException(400, f"Coluna inválida: {base_table}.{col}")
            return base_table, col, f"{base_table}.{col}"

        # caso encadeado: REL1 . REL2 ... . COL
        current = base_table
        # percorre todos os segmentos exceto o último (coluna)
        for seg in parts[:-1]:
            # tenta achar a tabela destino pelo apelido/ nome
            next_tbl = REL_EDGES.get(current, {}).get(seg)
            if not next_tbl:
                # se o usuário escreveu já o NOME da tabela destino e houver join direto
                if (current, seg) in JOIN_RULES and seg in TABLES:
                    next_tbl = seg
                else:
                    raise HTTPException(400, f"Caminho inválido: não sei ir de {current} até {seg}.")
            ensure_join_pair(current, next_tbl)
            current = next_tbl

        col = parts[-1]
        # valida coluna na tabela final
        valid_cols = {c.name for c in TABLES[current].columns}
        if col not in valid_cols:
            raise HTTPException(400, f"Coluna inválida: {current}.{col}")

        # label com o caminho completo em maiúsculo (evita colisão de nomes no SELECT)
        return current, col, f"{'.'.join(parts)}"

    # monta SELECT com todas as colunas pedidas (na ordem pedida)
    selected = []
    for item in payload.colunas:
        _, col, label = resolve_chain(base, item)
        # label vira "REL1.REL2.COL" (ou "BASE.COL")
        # para pegar a coluna certa, precisamos da tabela final também:
        # resolvemos de novo, mas guardando current na mesma passada (vamos mudar levemente)
    # Vamos refazer o loop para também coletar a tabela devolvida por resolve_chain
    selected = []
    labels = []
    for item in payload.colunas:
        final_tbl, col, label = resolve_chain(base, item)
        selected.append(TABLES[final_tbl].c[col].label(label))
        labels.append(label)

    stmt = select(*selected).select_from(from_clause).limit(200)
    rows = db.execute(stmt).mappings().all()  # cada row vira {'REL1.REL2.COL': valor, ...}

    return {
        "tabela_base": base,
        "colunas": labels,
        "count": len(rows),
        "items": rows
    }

@app.get("/nomes_colunas/{tabela}")
def nomes_colunastabela(tabela: str, db: Session = Depends(get_session)):
    allowed = {"CLIENTES", "VEICULOS", "MOTORISTAS", "PASSAGENS"}  # whitelist por segurança
    t = tabela.upper()
    if t not in allowed:
        raise HTTPException(400, f"Tabela não permitida: {t}")
    
    insp = inspect(db.bind)  # usa a mesma conexão do Session
    cols = insp.get_columns(t)  # lista metadados das colunas
    return [
        {
            "nome": c["name"],
            "tipo": str(c["type"]),
            "nullable": c["nullable"],
            "default": c.get("default"),
        }
        for c in cols
    ]




@app.get("/clientes")
def listar_clientes(db: Session = Depends(get_session)):
    # 1) montamos um SELECT só com as colunas que queremos
    stmt = select(Cliente.id, Cliente.cnpj, Cliente.nome, Cliente.email)

    # 2) executamos a query usando a sessão injetada pelo FastAPI
    rows = db.execute(stmt).all()  # retorna uma lista de Row

    # 3) transformamos cada Row em dict para serializar em JSON
    data = [{"id": r.id, "cnpj": r.cnpj, "nome": r.nome, "email": r.email} for r in rows]
    return {"total": len(data), "items": data}
