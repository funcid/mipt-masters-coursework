const trimSlash = (value: string) => value.replace(/\/+$/, '');

export const catalogBaseUrl = trimSlash(import.meta.env.VITE_CATALOG_BASE_URL ?? '/catalog-api');
export const orderBaseUrl = trimSlash(import.meta.env.VITE_ORDER_BASE_URL ?? '/order-api');
