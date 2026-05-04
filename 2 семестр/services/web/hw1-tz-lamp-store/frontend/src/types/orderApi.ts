export type CartLineApi = {
  id: string;
  product_id: string;
  product_snapshot: {
    id: string;
    sku: string;
    name: string;
    price_cents: number;
    currency: string;
  };
  quantity: number;
  line_total_cents: number;
};

export type CartApi = {
  id: string;
  cart_token: string;
  status: string;
  lines: CartLineApi[];
  total_cents: number;
  currency: string;
  created_at: string;
  updated_at: string;
};

export type CartCreateResponse = {
  cart_token: string;
};

export type OrderLineApi = {
  id: string;
  product_id: string;
  product_name: string;
  sku: string;
  unit_price_cents: number;
  quantity: number;
  line_total_cents: number;
};

export type OrderApi = {
  id: string;
  order_number: string;
  cart_id: string | null;
  status: string;
  customer_name: string;
  customer_email: string;
  customer_phone: string;
  delivery_address: string;
  comment: string | null;
  total_cents: number;
  currency: string;
  created_at: string;
  updated_at: string;
  lines: OrderLineApi[];
};
