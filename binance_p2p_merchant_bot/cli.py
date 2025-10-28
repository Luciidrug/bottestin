from __future__ import annotations
import argparse
from datetime import datetime, timezone
from rich.console import Console
from rich.table import Table
from .binance_p2p import iter_all_ads
from .storage import get_connection, init_db, snapshot_ads
from .metrics import calculate_new_deals, calculate_average_check, calculate_average_commission
from .config import settings


console = Console()


def cmd_sync(args: argparse.Namespace) -> None:
    conn = get_connection(settings.db_path)
    init_db(conn)
    sides = ["BUY", "SELL"] if args.sides == "both" else [args.sides.upper()]
    total = 0
    for side in sides:
        ads = list(iter_all_ads(trade_type=side, asset=args.asset, fiat=args.fiat, include_non_merchants=False))
        inserted = snapshot_ads(conn, ads)
        total += inserted
        console.print(f"Captured {inserted} {side} ads")
    console.print(f"[bold green]Total ads captured:[/bold green] {total}")


def cmd_report(args: argparse.Namespace) -> None:
    conn = get_connection(settings.db_path)
    new_deals, avg_per_merchant = calculate_new_deals(conn, days=args.days)
    avg_check = calculate_average_check(conn, days=args.days)
    avg_commission = calculate_average_commission(conn, days=args.days)

    table = Table(title=f"Binance P2P Merchant Metrics - {args.fiat}/{args.asset} last {args.days} day(s)")
    table.add_column("Metric", style="bold")
    table.add_column("Value")
    table.add_row("New deals (estimated)", str(new_deals))
    table.add_row("Avg new deals per merchant", f"{avg_per_merchant:.2f}")
    table.add_row("Average check (fiat)", f"{avg_check:,.2f} {args.fiat}")
    table.add_row("Average commission (spread %)", f"{avg_commission:.2f}%")

    console.print(table)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="p2p-merchant-bot")
    sub = p.add_subparsers(dest="cmd", required=True)

    s1 = sub.add_parser("sync", help="Fetch and snapshot current merchant ads")
    s1.add_argument("--fiat", default=settings.fiat)
    s1.add_argument("--asset", default=settings.asset)
    s1.add_argument("--sides", default="both", choices=["BUY", "SELL", "both"]) 
    s1.set_defaults(func=cmd_sync)

    s2 = sub.add_parser("report", help="Compute metrics from snapshots")
    s2.add_argument("--days", type=int, default=1)
    s2.add_argument("--fiat", default=settings.fiat)
    s2.add_argument("--asset", default=settings.asset)
    s2.set_defaults(func=cmd_report)

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
