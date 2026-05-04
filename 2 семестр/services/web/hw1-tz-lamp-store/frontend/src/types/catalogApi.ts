export type CategoryApi = {
  id: string;
  slug: string;
  name: string;
  created_at: string;
};

export type ProductImageApi = {
  id: string;
  url: string;
  sort_order: number;
};

export type ProductApi = {
  id: string;
  sku: string;
  name: string;
  description: string | null;
  category_id: string;
  price_cents: number;
  currency: string;
  watt: number | null;
  base_type: string | null;
  color_temp_k: number | null;
  lifetime_hours: number | null;
  stock_qty: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  category: CategoryApi;
  images: ProductImageApi[];
};
