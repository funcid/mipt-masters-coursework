import type { Product } from '../data/products';
import type { ProductApi } from '../types/catalogApi';
import { badgeBySku } from '../data/products';

export function mapProductApiToUi(model: ProductApi): Product {
  return {
    id: model.id,
    sku: model.sku,
    name: model.name,
    description: model.description?.trim() ? model.description : `${model.name}. Заводская гарантия и стабильное качество.`,
    category: model.category.slug,
    priceCents: model.price_cents,
    watt: model.watt ?? 0,
    baseType: model.base_type ?? undefined,
    colorTempK: model.color_temp_k ?? undefined,
    lifetimeHours: model.lifetime_hours ?? 0,
    stockQty: model.stock_qty,
    badge: badgeBySku[model.sku],
  };
}
