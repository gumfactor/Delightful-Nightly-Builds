"""Rule-based transaction categorization with optional Claude enrichment for the leftovers."""

from __future__ import annotations

import re

from . import ai_client

CATEGORIES = [
    "Groceries", "Dining", "Transport", "Travel", "Shopping", "Subscriptions",
    "Utilities", "Health", "Housing", "Entertainment", "Fees & Charges",
    "Income", "Transfers", "Other",
]

# Keyword -> category. Matched case-insensitively against the transaction description.
# Order matters: first match wins, so more specific patterns are listed first.
KEYWORD_RULES = [
    ("Income", [r"payroll", r"salary", r"direct deposit", r"employer", r"paycheque", r"paycheck"]),
    ("Transfers", [r"e-?transfer", r"interac", r"transfer to", r"transfer from", r"wire transfer"]),
    ("Subscriptions", [
        r"netflix", r"spotify", r"disney\+?", r"amazon prime", r"apple\.com/bill",
        r"icloud", r"youtube premium", r"hulu", r"crunchyroll", r"patreon",
        r"adobe", r"microsoft 365", r"dropbox", r"github", r"chatgpt", r"openai",
    ]),
    ("Groceries", [
        r"loblaws", r"metro", r"sobeys", r"no frills", r"costco", r"walmart supercentre",
        r"whole foods", r"trader joe", r"safeway", r"food basics", r"farm boy", r"fortinos",
    ]),
    ("Dining", [
        r"starbucks", r"tim hortons", r"mcdonald", r"restaurant", r"cafe", r"coffee",
        r"pizza", r"sushi", r"uber eats", r"doordash", r"skip the dishes", r"grubhub",
        r"pub\b", r"bistro", r"bakery",
    ]),
    ("Transport", [
        r"uber\b", r"lyft", r"presto", r"ttc\b", r"go transit", r"petro-?canada",
        r"shell\b", r"esso", r"chevron", r"parking", r"taxi", r"via rail",
    ]),
    ("Travel", [
        r"air canada", r"westjet", r"delta air", r"united air", r"marriott", r"hilton",
        r"airbnb", r"expedia", r"booking\.com", r"hotel", r"vrbo",
    ]),
    ("Shopping", [
        r"amazon\.ca", r"amazon\.com", r"best buy", r"ikea", r"canadian tire",
        r"home depot", r"indigo", r"the bay\b", r"etsy", r"aritzia",
    ]),
    ("Utilities", [
        r"hydro", r"enbridge", r"bell canada", r"rogers\b", r"telus", r"internet bill",
        r"water bill", r"gas bill", r"electricity", r"utility",
    ]),
    ("Health", [
        r"pharmacy", r"shoppers drug mart", r"rexall", r"dental", r"clinic",
        r"physio", r"optometry", r"medical", r"walk-?in clinic",
    ]),
    ("Housing", [
        r"rent\b", r"mortgage", r"property management", r"condo fee", r"strata",
    ]),
    ("Entertainment", [
        r"cineplex", r"movie theatre", r"ticketmaster", r"steam\b", r"playstation",
        r"xbox", r"concert", r"museum", r"golf club", r"golf course",
    ]),
    ("Fees & Charges", [
        r"nsf fee", r"overdraft", r"interest charge", r"annual fee", r"service charge",
        r"atm fee", r"foreign transaction fee",
    ]),
]

_COMPILED_RULES = [
    (category, [re.compile(pattern, re.IGNORECASE) for pattern in patterns])
    for category, patterns in KEYWORD_RULES
]


def categorize_rule_based(description: str) -> str:
    """Classify a single transaction description using keyword rules only."""
    for category, patterns in _COMPILED_RULES:
        for pattern in patterns:
            if pattern.search(description):
                return category
    return "Other"


def categorize_transactions(transactions: list, use_ai: bool = True) -> dict:
    """Categorize a list of Transaction objects in place.

    Transactions that already carry an existing category (from the input CSV) are
    left untouched. Everything else is rule-matched first; whatever still falls into
    "Other" is optionally sent (redacted, batched) to Claude for a second pass.
    Returns a small stats dict describing how categorization was resolved.
    """
    stats = {"existing": 0, "rule": 0, "ai": 0, "other": 0}
    uncertain = []

    for txn in transactions:
        if txn.category_source == "existing":
            stats["existing"] += 1
            continue
        category = categorize_rule_based(txn.description)
        txn.category = category
        txn.category_source = "rule"
        if category == "Other":
            uncertain.append(txn)
        else:
            stats["rule"] += 1

    if uncertain and use_ai and ai_client.is_configured():
        descriptions = [txn.description for txn in uncertain]
        result = ai_client.classify_batch(descriptions, CATEGORIES)
        if result:
            for txn in uncertain:
                assigned = result.get(txn.description)
                if assigned:
                    txn.category = assigned
                    txn.category_source = "ai"
                    stats["ai"] += 1
                else:
                    stats["other"] += 1
        else:
            stats["other"] += len(uncertain)
    else:
        stats["other"] += len(uncertain)

    return stats
