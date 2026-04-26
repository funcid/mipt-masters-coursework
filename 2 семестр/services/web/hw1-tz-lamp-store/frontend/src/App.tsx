import { FormEvent, ReactNode, useEffect, useMemo, useState } from 'react';
import { Link, NavLink, Navigate, Route, Routes, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { categories, getCategory, Product, products } from './data/products';

type CartState = Record<string, number>;

type CartLine = {
  product: Product;
  quantity: number;
  lineTotal: number;
};

type CheckoutForm = {
  name: string;
  email: string;
  phone: string;
  address: string;
  comment: string;
};

type OrderSummary = CheckoutForm & {
  orderNumber: string;
  total: number;
  itemsCount: number;
};

const CART_STORAGE_KEY = 'lamp-store-cart';
const ORDER_STORAGE_KEY = 'lamp-store-last-order';

const formatPrice = (cents: number) =>
  new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0,
  }).format(cents / 100);

const loadCart = (): CartState => {
  try {
    const rawCart = localStorage.getItem(CART_STORAGE_KEY);
    return rawCart ? JSON.parse(rawCart) : {};
  } catch {
    return {};
  }
};

function App() {
  const [cart, setCart] = useState<CartState>(() => loadCart());

  useEffect(() => {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));
  }, [cart]);

  const cartLines = useMemo<CartLine[]>(
    () =>
      Object.entries(cart)
        .map(([productId, quantity]) => {
          const product = products.find((item) => item.id === productId);
          return product ? { product, quantity, lineTotal: product.priceCents * quantity } : null;
        })
        .filter((line): line is CartLine => Boolean(line)),
    [cart],
  );

  const cartTotal = cartLines.reduce((sum, line) => sum + line.lineTotal, 0);
  const itemsCount = cartLines.reduce((sum, line) => sum + line.quantity, 0);

  const addToCart = (productId: string, quantity = 1) => {
    setCart((current) => ({
      ...current,
      [productId]: (current[productId] ?? 0) + quantity,
    }));
  };

  const updateQuantity = (productId: string, quantity: number) => {
    setCart((current) => {
      const nextCart = { ...current };
      if (quantity <= 0) {
        delete nextCart[productId];
      } else {
        nextCart[productId] = quantity;
      }
      return nextCart;
    });
  };

  const clearCart = () => setCart({});

  return (
    <div className="app-shell">
      <Header itemsCount={itemsCount} />
      <main>
        <Routes>
          <Route path="/" element={<HomePage onAddToCart={addToCart} />} />
          <Route path="/catalog" element={<CatalogPage onAddToCart={addToCart} />} />
          <Route path="/catalog/:productId" element={<ProductPage onAddToCart={addToCart} />} />
          <Route
            path="/cart"
            element={<CartPage cartLines={cartLines} total={cartTotal} onUpdateQuantity={updateQuantity} />}
          />
          <Route
            path="/checkout"
            element={
              <CheckoutPage cartLines={cartLines} total={cartTotal} itemsCount={itemsCount} onCheckout={clearCart} />
            }
          />
          <Route path="/confirmation/:orderNumber" element={<ConfirmationPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}

function Header({ itemsCount }: { itemsCount: number }) {
  return (
    <header className="site-header">
      <Link to="/" className="brand" aria-label="На главную">
        <span className="brand-mark">LS</span>
        <span>
          <strong>Lamp Store</strong>
          <small>заводские лампы онлайн</small>
        </span>
      </Link>

      <nav className="main-nav" aria-label="Основная навигация">
        <NavItem to="/">Главная</NavItem>
        <NavItem to="/catalog">Каталог</NavItem>
        <NavLink to="/cart" className={({ isActive }) => `cart-link ${isActive ? 'active' : ''}`}>
          Корзина
          <span>{itemsCount}</span>
        </NavLink>
      </nav>
    </header>
  );
}

function NavItem({ to, children }: { to: string; children: ReactNode }) {
  return (
    <NavLink to={to} className={({ isActive }) => (isActive ? 'active' : undefined)} end={to === '/'}>
      {children}
    </NavLink>
  );
}

function HomePage({ onAddToCart }: { onAddToCart: (productId: string) => void }) {
  const featuredProducts = products.filter((product) => product.badge).slice(0, 4);

  return (
    <>
      <section className="hero">
        <div className="hero-content">
          <p className="eyebrow">Интернет-магазин завода лампочек</p>
          <h1>Подберите освещение для дома, офиса и производства</h1>
          <p>
            Каталог с фильтрами, карточки товаров, корзина и оформление заказа реализованы на React Router DOM и
            работают на mock-данных.
          </p>
          <div className="hero-actions">
            <Link to="/catalog" className="button button-primary">
              Смотреть каталог
            </Link>
            <Link to="/cart" className="button button-ghost">
              Перейти в корзину
            </Link>
          </div>
        </div>
        <div className="hero-card" aria-label="Преимущества магазина">
          <span className="bulb-icon">●</span>
          <strong>20 товаров</strong>
          <p>5 категорий, понятные характеристики, быстрый заказ без регистрации.</p>
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <p className="eyebrow">Категории</p>
          <h2>Все основные типы ламп</h2>
        </div>
        <div className="category-grid">
          {categories.map((category) => (
            <Link key={category.slug} to={`/catalog?category=${category.slug}`} className="category-card">
              <strong>{category.name}</strong>
              <span>{category.description}</span>
            </Link>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-heading inline-heading">
          <div>
            <p className="eyebrow">Популярное</p>
            <h2>Рекомендуемые товары</h2>
          </div>
          <Link to="/catalog">Все товары</Link>
        </div>
        <ProductGrid productsList={featuredProducts} onAddToCart={onAddToCart} />
      </section>
    </>
  );
}

function CatalogPage({ onAddToCart }: { onAddToCart: (productId: string) => void }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const activeCategory = searchParams.get('category') ?? 'all';
  const query = searchParams.get('q') ?? '';

  const filteredProducts = products.filter((product) => {
    const matchesCategory = activeCategory === 'all' || product.category === activeCategory;
    const matchesQuery = `${product.name} ${product.sku}`.toLowerCase().includes(query.toLowerCase());
    return matchesCategory && matchesQuery;
  });

  const setCategory = (category: string) => {
    const nextParams = new URLSearchParams(searchParams);
    if (category === 'all') {
      nextParams.delete('category');
    } else {
      nextParams.set('category', category);
    }
    setSearchParams(nextParams);
  };

  return (
    <section className="page-section">
      <div className="page-title">
        <p className="eyebrow">Каталог</p>
        <h1>Лампы в наличии</h1>
        <p>Фильтруйте товары по категории или найдите нужную модель по названию и артикулу.</p>
      </div>

      <div className="catalog-layout">
        <aside className="filters" aria-label="Фильтры каталога">
          <h2>Категории</h2>
          <button className={activeCategory === 'all' ? 'selected' : ''} onClick={() => setCategory('all')}>
            Все товары
          </button>
          {categories.map((category) => (
            <button
              key={category.slug}
              className={activeCategory === category.slug ? 'selected' : ''}
              onClick={() => setCategory(category.slug)}
            >
              {category.name}
            </button>
          ))}
        </aside>

        <div className="catalog-content">
          <label className="search-field">
            <span>Поиск</span>
            <input
              value={query}
              onChange={(event) => {
                const nextParams = new URLSearchParams(searchParams);
                if (event.target.value) {
                  nextParams.set('q', event.target.value);
                } else {
                  nextParams.delete('q');
                }
                setSearchParams(nextParams);
              }}
              placeholder="Например, E27 или LED"
            />
          </label>

          <div className="result-line">
            Найдено товаров: <strong>{filteredProducts.length}</strong>
          </div>

          {filteredProducts.length > 0 ? (
            <ProductGrid productsList={filteredProducts} onAddToCart={onAddToCart} />
          ) : (
            <EmptyState title="Ничего не найдено" text="Попробуйте изменить категорию или поисковый запрос." />
          )}
        </div>
      </div>
    </section>
  );
}

function ProductPage({ onAddToCart }: { onAddToCart: (productId: string, quantity?: number) => void }) {
  const { productId } = useParams();
  const [quantity, setQuantity] = useState(1);
  const product = products.find((item) => item.id === productId);

  if (!product) {
    return <Navigate to="/catalog" replace />;
  }

  const category = getCategory(product.category);

  return (
    <section className="page-section product-page">
      <div className="product-visual large">
        <span>{product.baseType ?? 'LED'}</span>
      </div>

      <div className="product-details">
        <Link to="/catalog" className="back-link">
          ← Вернуться в каталог
        </Link>
        <p className="eyebrow">{category?.name}</p>
        <h1>{product.name}</h1>
        <p className="lead">{product.description}</p>

        <div className="price-row">
          <strong>{formatPrice(product.priceCents)}</strong>
          <span>В наличии: {product.stockQty} шт.</span>
        </div>

        <dl className="spec-list">
          <div>
            <dt>Артикул</dt>
            <dd>{product.sku}</dd>
          </div>
          <div>
            <dt>Мощность</dt>
            <dd>{product.watt} Вт</dd>
          </div>
          <div>
            <dt>Цоколь</dt>
            <dd>{product.baseType ?? 'не требуется'}</dd>
          </div>
          <div>
            <dt>Температура</dt>
            <dd>{product.colorTempK ? `${product.colorTempK} K` : 'теплый свет'}</dd>
          </div>
          <div>
            <dt>Срок службы</dt>
            <dd>{product.lifetimeHours.toLocaleString('ru-RU')} ч</dd>
          </div>
        </dl>

        <div className="buy-panel">
          <label>
            Количество
            <input
              type="number"
              min="1"
              max={product.stockQty}
              value={quantity}
              onChange={(event) => setQuantity(Math.max(1, Number(event.target.value)))}
            />
          </label>
          <button className="button button-primary" onClick={() => onAddToCart(product.id, quantity)}>
            Добавить в корзину
          </button>
        </div>
      </div>
    </section>
  );
}

function CartPage({
  cartLines,
  total,
  onUpdateQuantity,
}: {
  cartLines: CartLine[];
  total: number;
  onUpdateQuantity: (productId: string, quantity: number) => void;
}) {
  if (cartLines.length === 0) {
    return (
      <section className="page-section">
        <EmptyState
          title="Корзина пуста"
          text="Добавьте товары из каталога, чтобы перейти к оформлению заказа."
          action={<Link to="/catalog" className="button button-primary">В каталог</Link>}
        />
      </section>
    );
  }

  return (
    <section className="page-section">
      <div className="page-title compact">
        <p className="eyebrow">Корзина</p>
        <h1>Ваш заказ</h1>
      </div>

      <div className="cart-layout">
        <div className="cart-list">
          {cartLines.map(({ product, quantity, lineTotal }) => (
            <article key={product.id} className="cart-item">
              <div className="product-visual small">
                <span>{product.baseType ?? 'LED'}</span>
              </div>
              <div>
                <Link to={`/catalog/${product.id}`}>{product.name}</Link>
                <span>{product.sku}</span>
              </div>
              <input
                aria-label={`Количество: ${product.name}`}
                type="number"
                min="1"
                max={product.stockQty}
                value={quantity}
                onChange={(event) => onUpdateQuantity(product.id, Number(event.target.value))}
              />
              <strong>{formatPrice(lineTotal)}</strong>
              <button className="text-button" onClick={() => onUpdateQuantity(product.id, 0)}>
                Удалить
              </button>
            </article>
          ))}
        </div>

        <OrderSummaryCard total={total}>
          <Link to="/checkout" className="button button-primary full-width">
            Оформить заказ
          </Link>
          <Link to="/catalog" className="button button-ghost full-width">
            Продолжить покупки
          </Link>
        </OrderSummaryCard>
      </div>
    </section>
  );
}

function CheckoutPage({
  cartLines,
  total,
  itemsCount,
  onCheckout,
}: {
  cartLines: CartLine[];
  total: number;
  itemsCount: number;
  onCheckout: () => void;
}) {
  const navigate = useNavigate();
  const [form, setForm] = useState<CheckoutForm>({
    name: '',
    email: '',
    phone: '',
    address: '',
    comment: '',
  });

  if (cartLines.length === 0) {
    return <Navigate to="/cart" replace />;
  }

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const orderNumber = `LS-${new Date().getFullYear()}-${Math.floor(10000 + Math.random() * 90000)}`;
    const order: OrderSummary = { ...form, orderNumber, total, itemsCount };
    sessionStorage.setItem(ORDER_STORAGE_KEY, JSON.stringify(order));
    onCheckout();
    navigate(`/confirmation/${orderNumber}`);
  };

  return (
    <section className="page-section">
      <div className="page-title compact">
        <p className="eyebrow">Оформление</p>
        <h1>Контактные данные и доставка</h1>
      </div>

      <div className="checkout-layout">
        <form className="checkout-form" onSubmit={handleSubmit}>
          <Field label="Имя и фамилия">
            <input
              required
              minLength={2}
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
              placeholder="Иван Иванов"
            />
          </Field>
          <Field label="Email">
            <input
              required
              type="email"
              value={form.email}
              onChange={(event) => setForm({ ...form, email: event.target.value })}
              placeholder="mail@example.com"
            />
          </Field>
          <Field label="Телефон">
            <input
              required
              minLength={5}
              value={form.phone}
              onChange={(event) => setForm({ ...form, phone: event.target.value })}
              placeholder="+7 999 000-00-00"
            />
          </Field>
          <Field label="Адрес доставки">
            <textarea
              required
              minLength={5}
              value={form.address}
              onChange={(event) => setForm({ ...form, address: event.target.value })}
              placeholder="Город, улица, дом, квартира"
            />
          </Field>
          <Field label="Комментарий к заказу">
            <textarea
              value={form.comment}
              onChange={(event) => setForm({ ...form, comment: event.target.value })}
              placeholder="Удобное время доставки или дополнительные пожелания"
            />
          </Field>
          <button className="button button-primary full-width" type="submit">
            Подтвердить заказ
          </button>
        </form>

        <OrderSummaryCard total={total}>
          <div className="summary-line">
            <span>Товаров</span>
            <strong>{itemsCount}</strong>
          </div>
          <div className="summary-products">
            {cartLines.map(({ product, quantity }) => (
              <span key={product.id}>
                {product.name} × {quantity}
              </span>
            ))}
          </div>
        </OrderSummaryCard>
      </div>
    </section>
  );
}

function ConfirmationPage() {
  const { orderNumber } = useParams();
  const rawOrder = sessionStorage.getItem(ORDER_STORAGE_KEY);
  const order: OrderSummary | null = rawOrder ? JSON.parse(rawOrder) : null;

  return (
    <section className="page-section">
      <div className="success-card">
        <span className="success-icon">✓</span>
        <p className="eyebrow">Заказ оформлен</p>
        <h1>Спасибо за покупку!</h1>
        <p>
          Заказ <strong>{order?.orderNumber ?? orderNumber}</strong> принят в обработку. Менеджер свяжется с вами для
          подтверждения доставки.
        </p>
        {order && (
          <div className="confirmation-details">
            <span>Получатель: {order.name}</span>
            <span>Email: {order.email}</span>
            <span>Телефон: {order.phone}</span>
            <span>Сумма: {formatPrice(order.total)}</span>
          </div>
        )}
        <Link to="/catalog" className="button button-primary">
          Вернуться в каталог
        </Link>
      </div>
    </section>
  );
}

function NotFoundPage() {
  return (
    <section className="page-section">
      <EmptyState title="Страница не найдена" text="Проверьте адрес или вернитесь в каталог." action={<Link to="/catalog" className="button button-primary">В каталог</Link>} />
    </section>
  );
}

function ProductGrid({
  productsList,
  onAddToCart,
}: {
  productsList: Product[];
  onAddToCart: (productId: string) => void;
}) {
  return (
    <div className="product-grid">
      {productsList.map((product) => (
        <article key={product.id} className="product-card">
          {product.badge && <span className="badge">{product.badge}</span>}
          <Link to={`/catalog/${product.id}`} className="product-visual">
            <span>{product.baseType ?? 'LED'}</span>
          </Link>
          <div className="product-card-body">
            <Link to={`/catalog/${product.id}`} className="product-title">
              {product.name}
            </Link>
            <p>
              {product.watt} Вт · {product.baseType ?? 'без цоколя'} ·{' '}
              {product.colorTempK ? `${product.colorTempK} K` : 'теплый свет'}
            </p>
            <div className="product-card-footer">
              <strong>{formatPrice(product.priceCents)}</strong>
              <button className="button button-small" onClick={() => onAddToCart(product.id)}>
                В корзину
              </button>
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="form-field">
      <span>{label}</span>
      {children}
    </label>
  );
}

function OrderSummaryCard({ total, children }: { total: number; children: ReactNode }) {
  return (
    <aside className="order-summary">
      <h2>Итого</h2>
      <div className="summary-line">
        <span>Стоимость товаров</span>
        <strong>{formatPrice(total)}</strong>
      </div>
      <div className="summary-line">
        <span>Доставка</span>
        <strong>по согласованию</strong>
      </div>
      <div className="summary-total">
        <span>К оплате</span>
        <strong>{formatPrice(total)}</strong>
      </div>
      {children}
    </aside>
  );
}

function EmptyState({ title, text, action }: { title: string; text: string; action?: ReactNode }) {
  return (
    <div className="empty-state">
      <h1>{title}</h1>
      <p>{text}</p>
      {action}
    </div>
  );
}

function Footer() {
  return (
    <footer className="site-footer">
      <span>Lamp Store, учебный проект</span>
      <span>React + React Router DOM · mock-данные</span>
    </footer>
  );
}

export default App;
