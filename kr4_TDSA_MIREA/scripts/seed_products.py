import sys
from pathlib import Path

from sqlalchemy.orm import Session

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import engine
from models import Product


def seed_products() -> None:
    products = [
        Product(title="Keyboard", price=4990.00, count=12, description="Mechanical keyboard"),
        Product(title="Mouse", price=2490.00, count=24, description="Wireless mouse"),
    ]

    with Session(engine) as session:
        existing = session.query(Product).count()
        if existing:
            return
        session.add_all(products)
        session.commit()


if __name__ == "__main__":
    seed_products()
