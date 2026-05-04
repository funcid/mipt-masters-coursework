export type Category = {
  slug: string;
  name: string;
  description: string;
};

export type Product = {
  id: string;
  sku: string;
  name: string;
  description: string;
  category: string;
  priceCents: number;
  watt: number;
  baseType?: string;
  colorTempK?: number;
  lifetimeHours: number;
  stockQty: number;
  badge?: string;
};

/** Короткие описания для карточек на главной (в API категорий нет поля description). */
export const categoryDescriptions: Record<string, string> = {
  incandescent: 'Классический теплый свет для дома и декоративных светильников.',
  led: 'Экономичные лампы с большим сроком службы и разной температурой света.',
  fluorescent: 'Решения для офисов, торговых помещений и рабочих зон.',
  halogen: 'Яркий направленный свет для акцентного и технического освещения.',
  'night-lights': 'Компактная подсветка для спальни, детской и коридора.',
};

/** Бейджи на витрине (как в учебном макете; в каталоге этого поля нет). */
export const badgeBySku: Record<string, string> = {
  'LMP-LED-10-E27-3000': 'Хит',
  'LMP-LED-12-E27-4000': 'Популярно',
  'LMP-LED-IND-50-E40-5000': 'Профи',
  'LMP-NIGHT-LED-1-SENSOR': 'Новинка',
};
