"""MapReduce educational simulation (NOT a Hadoop cluster).
Input: order line items.  Map -> (product, (units, sales)).  Shuffle -> group by key.  Reduce -> sum.
"""
from collections import defaultdict

# Matches the example in the syllabus demo: Laptop 10, Phone 25, Headphones 15, Watch 8
SAMPLE = [
    {"order_id": 1, "product": "Laptop", "qty": 6, "unit_price": 55999},
    {"order_id": 2, "product": "Phone", "qty": 15, "unit_price": 19999},
    {"order_id": 3, "product": "Headphones", "qty": 9, "unit_price": 3499},
    {"order_id": 4, "product": "Laptop", "qty": 4, "unit_price": 55999},
    {"order_id": 5, "product": "Watch", "qty": 8, "unit_price": 2999},
    {"order_id": 6, "product": "Phone", "qty": 10, "unit_price": 19999},
    {"order_id": 7, "product": "Headphones", "qty": 6, "unit_price": 3499},
]


def map_phase(records):
    """Each record becomes a (key, value) pair: key = product, value = (units, sales)."""
    return [(r["product"], (int(r["qty"]), float(r["unit_price"]) * int(r["qty"]))) for r in records]


def shuffle_phase(pairs):
    """Group all values that share the same key (this is what the framework does between map and reduce)."""
    groups = defaultdict(list)
    for key, value in pairs:
        groups[key].append(value)
    return dict(groups)


def reduce_phase(groups):
    """Combine every group into one result per key."""
    result = [{"product": k, "units": sum(v[0] for v in vals), "sales": sum(v[1] for v in vals)}
              for k, vals in groups.items()]
    return sorted(result, key=lambda r: r["sales"], reverse=True)


def run(records):
    mapped = map_phase(records)
    shuffled = shuffle_phase(mapped)
    return {"input": records, "mapped": mapped, "shuffled": shuffled, "reduced": reduce_phase(shuffled)}
