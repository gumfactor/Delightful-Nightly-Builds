"""Client for a locally running Interactive Brokers TWS / IB Gateway instance.

``ib_insync`` is imported lazily, inside ``fetch_snapshot`` only, so this
module has no import-time dependency on it. That keeps ``import
src.ibkr_client`` working in any environment (including one where the
package can't be installed) and lets tests substitute a fake ``ib_insync``
module via ``sys.modules`` instead of requiring the real package.
"""

from __future__ import annotations

from typing import Any


class IBKRConnectionError(Exception):
    """Raised when TWS/IB Gateway can't be reached or account data can't be read."""


_SUMMARY_TAGS = {
    "NetLiquidation": "net_liquidation",
    "TotalCashValue": "total_cash",
    "GrossPositionValue": "gross_position_value",
    "UnrealizedPnL": "unrealized_pnl",
    "RealizedPnL": "realized_pnl",
    "BuyingPower": "buying_power",
}


def fetch_snapshot(
    host: str = "127.0.0.1",
    port: int = 7497,
    client_id: int = 1,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """Connect to TWS/IB Gateway and return a plain-dict account + positions snapshot.

    Raises IBKRConnectionError on any connection or read failure. Always
    disconnects, even when an exception is raised mid-fetch.
    """
    try:
        import ib_insync
    except ImportError as exc:
        raise IBKRConnectionError(
            "ib_insync is not installed. Run `pip install -r requirements.txt` "
            "and make sure TWS or IB Gateway is running with API access enabled."
        ) from exc

    ib = ib_insync.IB()
    try:
        try:
            ib.connect(host, port, clientId=client_id, timeout=timeout)
        except Exception as exc:
            raise IBKRConnectionError(
                f"Could not connect to TWS/IB Gateway at {host}:{port}. "
                f"Is it running with API access enabled for this port? (underlying error: {exc})"
            ) from exc

        try:
            summary_items = ib.accountSummary()
            portfolio_items = ib.portfolio()
        except Exception as exc:
            raise IBKRConnectionError(f"Connected, but failed to read account data: {exc}") from exc

        return _build_snapshot(summary_items, portfolio_items)
    finally:
        try:
            ib.disconnect()
        except Exception:
            pass


def _build_snapshot(summary_items, portfolio_items) -> dict[str, Any]:
    account_id = None
    values = {field_name: 0.0 for field_name in _SUMMARY_TAGS.values()}

    for item in summary_items:
        account_id = account_id or getattr(item, "account", None)
        field_name = _SUMMARY_TAGS.get(getattr(item, "tag", None))
        if field_name is not None:
            try:
                values[field_name] = float(item.value)
            except (TypeError, ValueError):
                pass

    positions = [_position_from_item(item) for item in portfolio_items]

    return {
        "account_id": account_id or "UNKNOWN",
        "positions": positions,
        **values,
    }


def _position_from_item(item) -> dict[str, Any]:
    contract = item.contract
    return {
        "symbol": getattr(contract, "symbol", "") or "",
        "sec_type": getattr(contract, "secType", "") or "",
        "currency": getattr(contract, "currency", "") or "",
        "exchange": getattr(contract, "exchange", "") or getattr(contract, "primaryExchange", "") or "",
        "quantity": float(getattr(item, "position", 0.0) or 0.0),
        "avg_cost": float(getattr(item, "averageCost", 0.0) or 0.0),
        "market_price": float(getattr(item, "marketPrice", 0.0) or 0.0),
        "market_value": float(getattr(item, "marketValue", 0.0) or 0.0),
        "unrealized_pnl": float(getattr(item, "unrealizedPNL", 0.0) or 0.0),
    }
