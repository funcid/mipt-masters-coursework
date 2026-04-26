from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, Product, ProductImage


CATEGORIES = [
    ("incandescent", "Лампы накаливания"),
    ("led", "Светодиодные лампы"),
    ("fluorescent", "Люминесцентные лампы"),
    ("halogen", "Галогенные лампы"),
    ("night-lights", "Ночники"),
]

PRODUCTS = [
    ("LMP-INC-40-E27-M", "Лампа накаливания 40 Вт E27 матовая", "incandescent", 6900, 40, "E27", None, 1000, 120),
    ("LMP-INC-60-E27-C", "Лампа накаливания 60 Вт E27 прозрачная", "incandescent", 7900, 60, "E27", None, 1000, 140),
    ("LMP-INC-75-E27", "Лампа накаливания 75 Вт E27", "incandescent", 8900, 75, "E27", None, 1000, 90),
    ("LMP-INC-25-E14-CND", "Лампа накаливания 25 Вт E14 свеча", "incandescent", 6500, 25, "E14", None, 1000, 80),
    ("LMP-INC-40-E14-BALL", "Лампа накаливания 40 Вт E14 шар", "incandescent", 7200, 40, "E14", None, 1000, 75),
    ("LMP-LED-10-E27-3000", "Светодиодная 10 Вт E27 3000K", "led", 18900, 10, "E27", 3000, 25000, 200),
    ("LMP-LED-12-E27-4000", "Светодиодная 12 Вт E27 4000K", "led", 21900, 12, "E27", 4000, 25000, 180),
    ("LMP-LED-15-E27-6500", "Светодиодная 15 Вт E27 6500K", "led", 24900, 15, "E27", 6500, 30000, 160),
    ("LMP-LED-8-E14-3000", "Светодиодная 8 Вт E14 3000K", "led", 17900, 8, "E14", 3000, 25000, 150),
    ("LMP-LED-GU10-5-4000", "Светодиодная GU10 5 Вт 4000K", "led", 16900, 5, "GU10", 4000, 25000, 130),
    ("LMP-LED-GU10-7-3000", "Светодиодная GU10 7 Вт 3000K", "led", 18900, 7, "GU10", 3000, 25000, 125),
    ("LMP-FLU-T8-18-600", "Лампа люминесцентная Т8 18 Вт 600 мм", "fluorescent", 14900, 18, "G13", 4000, 12000, 95),
    ("LMP-FLU-T8-36-1200", "Лампа люминесцентная Т8 36 Вт 1200 мм", "fluorescent", 19900, 36, "G13", 4000, 12000, 85),
    ("LMP-CFL-15-E27", "Компактная люминесцентная 15 Вт E27", "fluorescent", 15900, 15, "E27", 4000, 10000, 110),
    ("LMP-CFL-20-E27", "Компактная люминесцентная 20 Вт E27", "fluorescent", 17900, 20, "E27", 4000, 10000, 105),
    ("LMP-HAL-J78-150-R7S", "Галогенная J78 150 Вт R7s", "halogen", 12900, 150, "R7s", None, 2000, 70),
    ("LMP-HAL-G9-40", "Галогенная G9 40 Вт", "halogen", 9900, 40, "G9", None, 2000, 90),
    ("LMP-LED-LINE-20-6500", "Светодиодная линейная 20 Вт 6500K IP20", "led", 34900, 20, None, 6500, 30000, 60),
    ("LMP-LED-IND-50-E40-5000", "Промышленная LED 50 Вт E40 5000K", "led", 89900, 50, "E40", 5000, 50000, 45),
    ("LMP-NIGHT-LED-1-SENSOR", "Ночник LED 1 Вт с датчиком света", "night-lights", 29900, 1, None, 3000, 30000, 100),
]


async def seed_catalog(session: AsyncSession) -> None:
    category_count = await session.scalar(select(Category).limit(1))
    if category_count:
        return

    categories = {slug: Category(slug=slug, name=name) for slug, name in CATEGORIES}
    session.add_all(categories.values())
    await session.flush()

    for index, (sku, name, slug, price, watt, base_type, temp, lifetime, stock) in enumerate(PRODUCTS, start=1):
        product = Product(
            sku=sku,
            name=name,
            description=f"{name}. Заводская гарантия и стабильное качество для бытового и промышленного освещения.",
            category_id=categories[slug].id,
            price_cents=price,
            watt=watt,
            base_type=base_type,
            color_temp_k=temp,
            lifetime_hours=lifetime,
            stock_qty=stock,
        )
        product.images.append(
            ProductImage(url=f"https://example.com/images/lamp-{index:02d}.jpg", sort_order=0),
        )
        session.add(product)

    await session.commit()
