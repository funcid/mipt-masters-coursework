import { FormEvent, ReactNode, useEffect, useMemo, useState } from 'react';
import { Link, NavLink, Navigate, Route, Routes, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { categoryDescriptions, type Product } from './data/products';
import { useAppDispatch, useAppSelector } from './store/hooks';
import {
  addItemToCart,
  checkoutCart,
  clearMutationError,
  ensureCart,
  removeCartItem,
  updateCartItemQuantity,
} from './store/slices/cartSlice';
import { fetchOrders, prependOrder } from './store/slices/ordersSlice';
import { fetchCategories, fetchProductById, fetchProducts } from './store/slices/productsSlice';
import type { CartLineApi, OrderApi } from './types/orderApi';

type CheckoutForm = {
  name: string;
  email: string;
  phone: string;
  address: string;
  comment: string;
};

const ORDER_STORAGE_PREFIX = 'lamp-store-order-';

let appInitPromise: Promise<void> | null = null;

const formatPrice = (cents: number) =>
  new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0,
  }).format(cents / 100);

function AppBootstrap() {
  const dispatch = useAppDispatch();

  useEffect(() => {
    if (!appInitPromise) {
      appInitPromise = Promise.all([
        dispatch(fetchCategories()).unwrap(),
        dispatch(fetchProducts()).unwrap(),
        dispatch(ensureCart()).unwrap(),
      ])
        .then(() => undefined)
        .catch(() => {
          appInitPromise = null;
        });
    }
    void appInitPromise;
  }, [dispatch]);

  return null;
}

function App() {
  return (
    <div className="app-shell">
      <AppBootstrap />
      <Header />
      <GlobalStatusBar />
      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/catalog" element={<CatalogPage />} />
          <Route path="/catalog/:productId" element={<ProductPage />} />
          <Route path="/cart" element={<CartPage />} />
          <Route path="/checkout" element={<CheckoutPage />} />
          <Route path="/orders" element={<OrdersPage />} />
          <Route path="/confirmation/:orderId" element={<ConfirmationPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}

function GlobalStatusBar() {
  const dispatch = useAppDispatch();
  const productsError = useAppSelector((s) => s.products.error);
  const listStatus = useAppSelector((s) => s.products.listStatus);
  const bootstrapStatus = useAppSelector((s) => s.cart.bootstrapStatus);
  const mutationError = useAppSelector((s) => s.cart.mutationError);

  const fatal: string[] = [];
  if (listStatus === 'failed') {
    fatal.push(productsError ?? 'Не удалось загрузить каталог');
  }
  if (bootstrapStatus === 'failed') {
    fatal.push(mutationError ?? 'Не удалось подключить корзину');
  }

  const transient = mutationError && bootstrapStatus !== 'failed' ? mutationError : null;

  if (!fatal.length && !transient) {
    return null;
  }

  return (
    <div className="global-banner" role="status">
      {fatal.map((message) => (
        <p key={message}>{message}</p>
      ))}
      {transient && (
        <p>
          {transient}{' '}
          <button type="button" className="text-button" onClick={() => dispatch(clearMutationError())}>
            Закрыть
          </button>
        </p>
      )}
    </div>
  );
}

function Header() {
  const itemsCount = useAppSelector((s) => s.cart.cart?.lines.reduce((sum, line) => sum + line.quantity, 0) ?? 0);

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
        <NavItem to="/orders">Заказы</NavItem>
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

function HomePage() {
  const dispatch = useAppDispatch();
  const categories = useAppSelector((s) => s.products.categories);
  const productsList = useAppSelector((s) => s.products.items);
  const listStatus = useAppSelector((s) => s.products.listStatus);

  const featuredProducts = useMemo(() => {
    const withBadges = productsList.filter((product) => product.badge);
    return (withBadges.length > 0 ? withBadges : productsList).slice(0, 4);
  }, [productsList]);

  const handleAdd = (productId: string) => {
    void dispatch(addItemToCart({ productId, quantity: 1 }));
  };

  if (listStatus === 'loading' || listStatus === 'idle') {
    return <PageLoading text="Загружаем каталог…" />;
  }

  return (
    <>
      <section className="hero">
        <div className="hero-content">
          <p className="eyebrow">Интернет-магазин завода лампочек</p>
          <h1>Подберите освещение для дома, офиса и производства</h1>
          <p>
            Каталог, корзина и оформление заказа работают через микросервисы каталога и заказов: данные приходят с
            backend, состояние хранится в Redux, запросы выполняются через fetch.
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
          <strong>Живой каталог</strong>
          <p>Категории и товары с catalog-service, корзина и заказы с order-service.</p>
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
              <span>{categoryDescriptions[category.slug] ?? 'Категория каталога.'}</span>
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
        <ProductGrid productsList={featuredProducts} onAddToCart={handleAdd} />
      </section>
    </>
  );
}

function CatalogPage() {
  const dispatch = useAppDispatch();
  const productsList = useAppSelector((s) => s.products.items);
  const categories = useAppSelector((s) => s.products.categories);
  const listStatus = useAppSelector((s) => s.products.listStatus);
  const [searchParams, setSearchParams] = useSearchParams();
  const activeCategory = searchParams.get('category') ?? 'all';
  const query = searchParams.get('q') ?? '';

  const filteredProducts = productsList.filter((product) => {
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

  const handleAdd = (productId: string) => {
    void dispatch(addItemToCart({ productId, quantity: 1 }));
  };

  if (listStatus === 'loading' || listStatus === 'idle') {
    return <PageLoading text="Загружаем товары…" />;
  }

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
          <button type="button" className={activeCategory === 'all' ? 'selected' : ''} onClick={() => setCategory('all')}>
            Все товары
          </button>
          {categories.map((category) => (
            <button
              key={category.slug}
              type="button"
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
            <ProductGrid productsList={filteredProducts} onAddToCart={handleAdd} />
          ) : (
            <EmptyState title="Ничего не найдено" text="Попробуйте изменить категорию или поисковый запрос." />
          )}
        </div>
      </div>
    </section>
  );
}

function ProductPage() {
  const dispatch = useAppDispatch();
  const { productId } = useParams();
  const [quantity, setQuantity] = useState(1);
  const categories = useAppSelector((s) => s.products.categories);
  const product = useAppSelector((s) => (productId ? s.products.byId[productId] : undefined));
  const detailStatus = useAppSelector((s) => s.products.detailStatus);

  useEffect(() => {
    if (productId) {
      void dispatch(fetchProductById(productId));
    }
  }, [dispatch, productId]);

  if (!productId) {
    return <Navigate to="/catalog" replace />;
  }

  if (detailStatus === 'loading' || (detailStatus === 'idle' && !product)) {
    return <PageLoading text="Загружаем карточку товара…" />;
  }

  if (!product) {
    return <Navigate to="/catalog" replace />;
  }

  const category = categories.find((item) => item.slug === product.category);

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
              min={1}
              max={product.stockQty}
              value={quantity}
              onChange={(event) => setQuantity(Math.max(1, Number(event.target.value)))}
            />
          </label>
          <button
            type="button"
            className="button button-primary"
            onClick={() => void dispatch(addItemToCart({ productId: product.id, quantity }))}
          >
            Добавить в корзину
          </button>
        </div>
      </div>
    </section>
  );
}

function resolveLineProduct(line: CartLineApi, catalogProduct?: Product): Product {
  if (catalogProduct) {
    return catalogProduct;
  }
  return {
    id: line.product_id,
    sku: line.product_snapshot.sku,
    name: line.product_snapshot.name,
    description: line.product_snapshot.name,
    category: 'led',
    priceCents: line.product_snapshot.price_cents,
    watt: 0,
    lifetimeHours: 0,
    stockQty: 999,
  };
}

function CartPage() {
  const dispatch = useAppDispatch();
  const cart = useAppSelector((s) => s.cart.cart);
  const byId = useAppSelector((s) => s.products.byId);
  const bootstrapStatus = useAppSelector((s) => s.cart.bootstrapStatus);

  const cartLines = useMemo(() => {
    const lines = cart?.lines ?? [];
    return lines.map((line) => {
      const product = resolveLineProduct(line, byId[line.product_id]);
      const lineTotal = line.line_total_cents;
      return { product, quantity: line.quantity, lineTotal, productId: line.product_id };
    });
  }, [cart, byId]);

  const total = cart?.total_cents ?? 0;

  if (bootstrapStatus === 'loading' || bootstrapStatus === 'idle') {
    return <PageLoading text="Синхронизируем корзину…" />;
  }

  if (!cartLines.length) {
    return (
      <section className="page-section">
        <EmptyState
          title="Корзина пуста"
          text="Добавьте товары из каталога, чтобы перейти к оформлению заказа."
          action={
            <Link to="/catalog" className="button button-primary">
              В каталог
            </Link>
          }
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
          {cartLines.map(({ product, quantity, lineTotal, productId }) => (
            <article key={productId} className="cart-item">
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
                min={1}
                max={product.stockQty}
                value={quantity}
                onChange={(event) =>
                  void dispatch(updateCartItemQuantity({ productId, quantity: Number(event.target.value) }))
                }
              />
              <strong>{formatPrice(lineTotal)}</strong>
              <button type="button" className="text-button" onClick={() => void dispatch(removeCartItem(productId))}>
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

function CheckoutPage() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const cart = useAppSelector((s) => s.cart.cart);
  const byId = useAppSelector((s) => s.products.byId);
  const [form, setForm] = useState<CheckoutForm>({
    name: '',
    email: '',
    phone: '',
    address: '',
    comment: '',
  });

  const cartLines = useMemo(() => {
    const lines = cart?.lines ?? [];
    return lines.map((line) => {
      const product = resolveLineProduct(line, byId[line.product_id]);
      return { product, quantity: line.quantity };
    });
  }, [cart, byId]);

  const total = cart?.total_cents ?? 0;
  const itemsCount = cart?.lines.reduce((sum, line) => sum + line.quantity, 0) ?? 0;

  if (!cartLines.length) {
    return <Navigate to="/cart" replace />;
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    try {
      const order = await dispatch(
        checkoutCart({
          customer_name: form.name,
          customer_email: form.email,
          customer_phone: form.phone,
          delivery_address: form.address,
          comment: form.comment.trim() ? form.comment : undefined,
        }),
      ).unwrap();
      dispatch(prependOrder(order));
      sessionStorage.setItem(`${ORDER_STORAGE_PREFIX}${order.id}`, JSON.stringify(order));
      navigate(`/confirmation/${order.id}`);
    } catch {
      /* ошибка уже в mutationError */
    }
  };

  return (
    <section className="page-section">
      <div className="page-title compact">
        <p className="eyebrow">Оформление</p>
        <h1>Контактные данные и доставка</h1>
      </div>

      <div className="checkout-layout">
        <form className="checkout-form" onSubmit={(e) => void handleSubmit(e)}>
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
  const { orderId } = useParams();
  const rawOrder = orderId ? sessionStorage.getItem(`${ORDER_STORAGE_PREFIX}${orderId}`) : null;
  const order: OrderApi | null = rawOrder ? (JSON.parse(rawOrder) as OrderApi) : null;

  return (
    <section className="page-section">
      <div className="success-card">
        <span className="success-icon">✓</span>
        <p className="eyebrow">Заказ оформлен</p>
        <h1>Спасибо за покупку!</h1>
        <p>
          Заказ <strong>{order?.order_number ?? orderId}</strong> принят в обработку. Менеджер свяжется с вами для
          подтверждения доставки.
        </p>
        {order && (
          <div className="confirmation-details">
            <span>Получатель: {order.customer_name}</span>
            <span>Email: {order.customer_email}</span>
            <span>Телефон: {order.customer_phone}</span>
            <span>Сумма: {formatPrice(order.total_cents)}</span>
            <span>Статус: {order.status}</span>
          </div>
        )}
        <Link to="/catalog" className="button button-primary">
          Вернуться в каталог
        </Link>
      </div>
    </section>
  );
}

function OrdersPage() {
  const dispatch = useAppDispatch();
  const orders = useAppSelector((s) => s.orders.items);
  const listStatus = useAppSelector((s) => s.orders.listStatus);
  const listError = useAppSelector((s) => s.orders.error);

  useEffect(() => {
    void dispatch(fetchOrders());
  }, [dispatch]);

  if (listStatus === 'loading' || listStatus === 'idle') {
    return <PageLoading text="Загружаем заказы…" />;
  }

  if (listStatus === 'failed') {
    return (
      <section className="page-section">
        <EmptyState title="Не удалось загрузить заказы" text={listError ?? 'Проверьте, что order-service запущен.'} />
      </section>
    );
  }

  if (!orders.length) {
    return (
      <section className="page-section">
        <EmptyState
          title="Заказов пока нет"
          text="Оформите первый заказ из корзины — он появится в этом списке."
          action={
            <Link to="/catalog" className="button button-primary">
              В каталог
            </Link>
          }
        />
      </section>
    );
  }

  return (
    <section className="page-section">
      <div className="page-title compact">
        <p className="eyebrow">История</p>
        <h1>Заказы</h1>
      </div>
      <div className="cart-list">
        {orders.map((order) => (
          <article key={order.id} className="cart-item">
            <div>
              <strong>{order.order_number}</strong>
              <span>
                {order.status} · {new Date(order.created_at).toLocaleString('ru-RU')}
              </span>
            </div>
            <div>
              <span>{order.customer_name}</span>
              <span>{order.customer_email}</span>
            </div>
            <strong>{formatPrice(order.total_cents)}</strong>
          </article>
        ))}
      </div>
    </section>
  );
}

function NotFoundPage() {
  return (
    <section className="page-section">
      <EmptyState
        title="Страница не найдена"
        text="Проверьте адрес или вернитесь в каталог."
        action={
          <Link to="/catalog" className="button button-primary">
            В каталог
          </Link>
        }
      />
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
              <button type="button" className="button button-small" onClick={() => onAddToCart(product.id)}>
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

function PageLoading({ text }: { text: string }) {
  return (
    <section className="page-section">
      <div className="empty-state">
        <h1>{text}</h1>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="site-footer">
      <span>Lamp Store, учебный проект</span>
      <span>React + Redux Toolkit + fetch · catalog-service + order-service</span>
    </footer>
  );
}

export default App;
