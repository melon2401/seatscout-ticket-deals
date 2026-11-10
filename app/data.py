from __future__ import annotations

EVENTS = [
    {"slug": "the-weeknd-toronto", "artist": "The Weeknd", "city": "Toronto", "date": "Mar 21", "venue": "Rogers Centre", "category": "Concerts", "low": 224, "change": -8},
    {"slug": "taylor-swift-toronto", "artist": "Taylor Swift", "city": "Toronto", "date": "Nov 14", "venue": "Rogers Centre", "category": "Concerts", "low": 412, "change": -5},
    {"slug": "raptors-celtics", "artist": "Raptors vs. Celtics", "city": "Toronto", "date": "Dec 04", "venue": "Scotiabank Arena", "category": "Sports", "low": 96, "change": 3},
    {"slug": "oasis-toronto", "artist": "Oasis", "city": "Toronto", "date": "Aug 24", "venue": "Rogers Stadium", "category": "Concerts", "low": 189, "change": -12},
    {"slug": "wicked-toronto", "artist": "Wicked", "city": "Toronto", "date": "Jan 17", "venue": "Princess of Wales Theatre", "category": "Theatre", "low": 88, "change": -2},
]

OFFERS = [
    {"id": "sg-118-h", "seller": "SeatGeek", "section": "118", "row": "H", "quantity": "2 or 4", "base": 254, "fees": 22, "score": 9.8, "label": "BEST DEAL", "kind": "resale", "delivery": "Instant delivery"},
    {"id": "sh-121-k", "seller": "StubHub", "section": "121", "row": "K", "quantity": "2", "base": 263, "fees": 18, "score": 9.2, "label": "PRICE DROP", "kind": "resale", "delivery": "Mobile transfer"},
    {"id": "vs-124-j", "seller": "Vivid Seats", "section": "124", "row": "J", "quantity": "1–4", "base": 265, "fees": 24, "score": 8.9, "label": "LOWEST IN SECTION", "kind": "resale", "delivery": "Mobile transfer"},
    {"id": "tm-121-k", "seller": "Ticketmaster", "section": "121", "row": "K", "quantity": "2", "base": 409, "fees": 40, "score": 7.1, "label": "OFFICIAL", "kind": "official", "delivery": "Official mobile ticket"},
    {"id": "gt-130-m", "seller": "GameTime", "section": "130", "row": "M", "quantity": "2–6", "base": 281, "fees": 29, "score": 8.2, "label": "GOOD VIEW", "kind": "resale", "delivery": "Instant delivery"},
]

PRICE_HISTORY = {
    "labels": ["Oct 12", "Oct 16", "Oct 20", "Oct 24", "Oct 28", "Nov 1", "Nov 5", "Today"],
    "low": [258, 246, 251, 238, 231, 236, 228, 224],
    "median": [338, 329, 318, 311, 305, 301, 296, 298],
    "official": [470, 470, 462, 459, 449, 449, 449, 449],
    "resale": [391, 372, 378, 349, 318, 305, 284, 276],
}

ZONES = [
    {"name": "Floor", "price": 612, "color": "#c99a2d"},
    {"name": "100 Level", "price": 276, "color": "#8f1f25"},
    {"name": "200 Level", "price": 224, "color": "#6f7645"},
    {"name": "Accessible", "price": 289, "color": "#477c76"},
]

