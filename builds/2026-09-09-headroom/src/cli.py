"""Headroom CLI — RRSP/TFSA contribution room and deadline tracker."""

from __future__ import annotations

import argparse
import os
from datetime import date
from pathlib import Path

from . import ai_briefing, csv_import, dashboard, deadlines, rrsp, storage, tfsa

DEFAULT_DATA_PATH = Path("data/headroom.json")


def _compute(data: dict, as_of: date) -> tuple[tfsa.TFSAResult, rrsp.RRSPResult]:
    birth_year = data["profile"]["birth_year"]
    resident_since = data["profile"].get("resident_since_year")

    tfsa_contribs, tfsa_withdrawals = storage.tfsa_transactions(data)
    tfsa_result = tfsa.compute_tfsa(
        birth_year, tfsa_contribs, tfsa_withdrawals, as_of, resident_since
    )

    rrsp_contribs, rrsp_income, opening = storage.rrsp_records(data)
    rrsp_result = rrsp.compute_rrsp(birth_year, rrsp_contribs, rrsp_income, as_of, opening)

    return tfsa_result, rrsp_result


def cmd_init(args: argparse.Namespace) -> None:
    path = Path(args.data)
    if path.exists() and not args.force:
        print(f"{path} already exists. Use --force to overwrite.")
        return
    data = storage.default_profile()
    data["profile"]["birth_year"] = args.birth_year
    data["profile"]["resident_since_year"] = args.resident_since_year
    storage.save(path, data)
    print(f"Created {path}")


def cmd_add_contribution(args: argparse.Namespace) -> None:
    path = Path(args.data)
    data = storage.load(path)
    entry_date = date.fromisoformat(args.date)
    if args.account == "tfsa":
        data.setdefault("tfsa_contributions", []).append(
            {"date": entry_date.isoformat(), "amount": args.amount}
        )
    else:
        tax_year = args.tax_year or entry_date.year
        data.setdefault("rrsp_contributions", []).append(
            {"date": entry_date.isoformat(), "amount": args.amount, "tax_year": tax_year}
        )
    storage.save(path, data)
    print(f"Recorded {args.account.upper()} contribution of ${args.amount:,.2f} on {entry_date}")


def cmd_add_withdrawal(args: argparse.Namespace) -> None:
    path = Path(args.data)
    data = storage.load(path)
    entry_date = date.fromisoformat(args.date)
    data.setdefault("tfsa_withdrawals", []).append(
        {"date": entry_date.isoformat(), "amount": args.amount}
    )
    storage.save(path, data)
    print(f"Recorded TFSA withdrawal of ${args.amount:,.2f} on {entry_date}")


def cmd_add_income(args: argparse.Namespace) -> None:
    path = Path(args.data)
    data = storage.load(path)
    data.setdefault("rrsp_income", []).append(
        {
            "year": args.year,
            "earned_income": args.amount,
            "pension_adjustment": args.pension_adjustment,
        }
    )
    storage.save(path, data)
    print(f"Recorded {args.year} earned income of ${args.amount:,.2f}")


def cmd_import_csv(args: argparse.Namespace) -> None:
    path = Path(args.data)
    data = storage.load(path)
    csv_path = Path(args.file)

    if args.type in ("contributions-tfsa", "contributions-rrsp"):
        rows = csv_import.import_contributions(csv_path)
        key = "tfsa_contributions" if args.type == "contributions-tfsa" else "rrsp_contributions"
        for row in rows:
            entry = {"date": row["date"].isoformat(), "amount": row["amount"]}
            if key == "rrsp_contributions":
                entry["tax_year"] = row["date"].year
            data.setdefault(key, []).append(entry)
        print(f"Imported {len(rows)} rows into {key}")
    elif args.type == "income":
        rows = csv_import.import_income(csv_path)
        data.setdefault("rrsp_income", []).extend(rows)
        print(f"Imported {len(rows)} rows into rrsp_income")
    else:
        raise ValueError(f"Unknown import type: {args.type}")

    storage.save(path, data)


def cmd_status(args: argparse.Namespace) -> None:
    path = Path(args.data)
    data = storage.load(path)
    as_of = date.today()
    tfsa_result, rrsp_result = _compute(data, as_of)

    print(f"Headroom status as of {as_of}")
    print("-" * 40)
    if tfsa_result.is_overcontributed:
        print(f"TFSA: OVER-CONTRIBUTED by ${tfsa_result.overcontribution_amount:,.2f}")
    else:
        print(f"TFSA: ${tfsa_result.available_room:,.2f} available")

    if rrsp_result.is_overcontributed:
        print(f"RRSP: OVER-CONTRIBUTED by ${rrsp_result.overcontribution_amount:,.2f}")
    else:
        print(f"RRSP: ${rrsp_result.available_room:,.2f} available")

    next_deadline, tax_year = deadlines.next_rrsp_deadline(as_of)
    print(f"Next RRSP deadline: {next_deadline} (tax year {tax_year})")
    print(f"Next TFSA room opens: {deadlines.next_tfsa_room_date(as_of)}")


def cmd_report(args: argparse.Namespace) -> None:
    path = Path(args.data)
    data = storage.load(path)
    as_of = date.today()
    tfsa_result, rrsp_result = _compute(data, as_of)

    next_deadline, tax_year = deadlines.next_rrsp_deadline(as_of)
    tfsa_next_room = deadlines.next_tfsa_room_date(as_of)

    payload = ai_briefing.build_summary_payload(
        tfsa_result.available_room,
        tfsa_result.is_overcontributed,
        tfsa_result.overcontribution_amount,
        rrsp_result.available_room,
        rrsp_result.is_overcontributed,
        rrsp_result.overcontribution_amount,
        next_deadline,
        tax_year,
        tfsa_next_room,
    )
    api_key = os.environ.get("ANTHROPIC_API_KEY") if args.use_ai else None
    briefing = ai_briefing.generate_briefing(payload, api_key)

    history = []
    for row in data.get("tfsa_contributions", []):
        history.append({"account": "TFSA contribution", "date": row["date"], "amount": row["amount"]})
    for row in data.get("tfsa_withdrawals", []):
        history.append({"account": "TFSA withdrawal", "date": row["date"], "amount": -row["amount"]})
    for row in data.get("rrsp_contributions", []):
        history.append({"account": "RRSP contribution", "date": row["date"], "amount": row["amount"]})
    history.sort(key=lambda r: r["date"])

    context = {
        "as_of": as_of.isoformat(),
        "tfsa": {
            "available_room": tfsa_result.available_room,
            "is_overcontributed": tfsa_result.is_overcontributed,
            "overcontribution_amount": tfsa_result.overcontribution_amount,
            "estimated_monthly_penalty": tfsa_result.estimated_monthly_penalty,
            "year_snapshots": [
                {"year": s.year, "ending_balance": s.ending_balance} for s in tfsa_result.year_snapshots
            ],
        },
        "rrsp": {
            "available_room": rrsp_result.available_room,
            "is_overcontributed": rrsp_result.is_overcontributed,
            "overcontribution_amount": rrsp_result.overcontribution_amount,
            "estimated_monthly_penalty": rrsp_result.estimated_monthly_penalty,
            "year_snapshots": [
                {"year": s.year, "ending_balance": s.ending_balance} for s in rrsp_result.year_snapshots
            ],
        },
        "deadlines": [
            {
                "label": f"RRSP contribution deadline (tax year {tax_year})",
                "date": next_deadline.isoformat(),
                "days_until": deadlines.days_until(next_deadline, as_of),
            },
            {
                "label": "Next TFSA room opens",
                "date": tfsa_next_room.isoformat(),
                "days_until": deadlines.days_until(tfsa_next_room, as_of),
            },
        ],
        "briefing": briefing,
        "history": history,
    }

    html = dashboard.render_dashboard(context)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)
    print(f"Wrote dashboard to {out_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="headroom", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_init = subparsers.add_parser("init", help="Create a new local data file")
    p_init.add_argument("--data", default=str(DEFAULT_DATA_PATH))
    p_init.add_argument("--birth-year", type=int, required=True)
    p_init.add_argument("--resident-since-year", type=int, default=None)
    p_init.add_argument("--force", action="store_true")
    p_init.set_defaults(func=cmd_init)

    p_contrib = subparsers.add_parser("add-contribution", help="Record a TFSA or RRSP contribution")
    p_contrib.add_argument("--data", default=str(DEFAULT_DATA_PATH))
    p_contrib.add_argument("--account", choices=["tfsa", "rrsp"], required=True)
    p_contrib.add_argument("--date", required=True)
    p_contrib.add_argument("--amount", type=float, required=True)
    p_contrib.add_argument("--tax-year", type=int, default=None, help="RRSP only")
    p_contrib.set_defaults(func=cmd_add_contribution)

    p_withdraw = subparsers.add_parser("add-withdrawal", help="Record a TFSA withdrawal")
    p_withdraw.add_argument("--data", default=str(DEFAULT_DATA_PATH))
    p_withdraw.add_argument("--date", required=True)
    p_withdraw.add_argument("--amount", type=float, required=True)
    p_withdraw.set_defaults(func=cmd_add_withdrawal)

    p_income = subparsers.add_parser("add-income", help="Record a year of RRSP-eligible earned income")
    p_income.add_argument("--data", default=str(DEFAULT_DATA_PATH))
    p_income.add_argument("--year", type=int, required=True)
    p_income.add_argument("--amount", type=float, required=True)
    p_income.add_argument("--pension-adjustment", type=float, default=0.0)
    p_income.set_defaults(func=cmd_add_income)

    p_csv = subparsers.add_parser("import-csv", help="Bulk-import a contributions or income CSV")
    p_csv.add_argument("--data", default=str(DEFAULT_DATA_PATH))
    p_csv.add_argument("--file", required=True)
    p_csv.add_argument(
        "--type", choices=["contributions-tfsa", "contributions-rrsp", "income"], required=True
    )
    p_csv.set_defaults(func=cmd_import_csv)

    p_status = subparsers.add_parser("status", help="Print a quick terminal summary")
    p_status.add_argument("--data", default=str(DEFAULT_DATA_PATH))
    p_status.set_defaults(func=cmd_status)

    p_report = subparsers.add_parser("report", help="Generate the HTML dashboard")
    p_report.add_argument("--data", default=str(DEFAULT_DATA_PATH))
    p_report.add_argument("--out", default="headroom_report.html")
    p_report.add_argument("--use-ai", action="store_true")
    p_report.set_defaults(func=cmd_report)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
