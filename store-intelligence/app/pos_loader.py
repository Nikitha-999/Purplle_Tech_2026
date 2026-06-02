"""Load POS CSV into the transactions table on startup."""

from __future__ import annotations

import csv
import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import TransactionRow, _utc_now_iso
from app.stores import resolve_store_id

logger = logging.getLogger("store_intelligence.pos")


def _parse_order_timestamp(order_date: str, order_time: str) -> str:
    """Parse dd-mm-yyyy and HH:MM:SS into UTC ISO-8601 Z."""
    local = datetime.strptime(f"{order_date.strip()} {order_time.strip()}", "%d-%m-%Y %H:%M:%S")
    utc = local.replace(tzinfo=timezone.utc)
    return utc.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_pos_transactions(session: Session, csv_path: Path | None = None) -> int:
    """
    Load brigade POS export: order_id → transaction_id, aggregated NMV per order.
    Returns number of newly inserted transactions.
    """
    settings = get_settings()
    path = csv_path or Path(settings.pos_csv_path)
    if not path.is_file():
        logger.warning("pos_csv_missing path=%s", path)
        return 0

    orders: dict[str, dict] = defaultdict(lambda: {"nmv": 0.0, "salesperson": None, "store_id": None, "ts": None})

    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            order_id = row["order_id"].strip()
            store_id = resolve_store_id(row["store_id"].strip())
            ts = _parse_order_timestamp(row["order_date"], row["order_time"])
            nmv = float(row.get("NMV") or 0)
            orders[order_id]["nmv"] += nmv
            orders[order_id]["store_id"] = store_id
            orders[order_id]["ts"] = ts
            sp = (row.get("salesperson_name") or "").strip()
            if sp:
                orders[order_id]["salesperson"] = sp

    inserted = 0
    for order_id, data in orders.items():
        existing = session.get(TransactionRow, order_id)
        if existing:
            continue
        session.add(
            TransactionRow(
                transaction_id=order_id,
                store_id=data["store_id"],
                timestamp=data["ts"],
                basket_value_inr=round(data["nmv"], 2),
                salesperson=data["salesperson"],
                source="pos_csv",
            )
        )
        inserted += 1

    session.commit()
    logger.info("pos_loaded path=%s orders=%s inserted=%s", path, len(orders), inserted)
    return inserted
