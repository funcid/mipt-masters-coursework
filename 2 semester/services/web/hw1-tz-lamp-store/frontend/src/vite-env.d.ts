/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_CATALOG_BASE_URL?: string;
  readonly VITE_ORDER_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}