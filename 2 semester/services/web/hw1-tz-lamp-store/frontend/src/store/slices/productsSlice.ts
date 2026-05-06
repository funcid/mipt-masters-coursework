import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import { catalogBaseUrl } from '../../api/endpoints';
import { jsonFetch } from '../../api/jsonFetch';
import { mapProductApiToUi } from '../../domain/mapCatalogProduct';
import type { Product } from '../../data/products';
import type { CategoryApi, ProductApi } from '../../types/catalogApi';

export type CategoryRow = {
  id: string;
  slug: string;
  name: string;
};

type ProductsState = {
  categories: CategoryRow[];
  items: Product[];
  byId: Record<string, Product>;
  listStatus: 'idle' | 'loading' | 'succeeded' | 'failed';
  detailStatus: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
};

const initialState: ProductsState = {
  categories: [],
  items: [],
  byId: {},
  listStatus: 'idle',
  detailStatus: 'idle',
  error: null,
};

export const fetchCategories = createAsyncThunk('products/fetchCategories', async () => {
  const rows = await jsonFetch<CategoryApi[]>(`${catalogBaseUrl}/api/v1/categories`);
  return rows.map((row) => ({ id: row.id, slug: row.slug, name: row.name }));
});

export const fetchProducts = createAsyncThunk('products/fetchAll', async () => {
  const rows = await jsonFetch<ProductApi[]>(`${catalogBaseUrl}/api/v1/products?active_only=true`);
  return rows.map(mapProductApiToUi);
});

export const fetchProductById = createAsyncThunk('products/fetchOne', async (productId: string) => {
  const row = await jsonFetch<ProductApi>(`${catalogBaseUrl}/api/v1/products/${productId}`);
  return mapProductApiToUi(row);
});

const productsSlice = createSlice({
  name: 'products',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchCategories.pending, (state) => {
        state.error = null;
      })
      .addCase(fetchCategories.fulfilled, (state, action) => {
        state.categories = action.payload;
      })
      .addCase(fetchCategories.rejected, (state, action) => {
        state.error = action.error.message ?? 'Не удалось загрузить категории';
      })
      .addCase(fetchProducts.pending, (state) => {
        state.listStatus = 'loading';
        state.error = null;
      })
      .addCase(fetchProducts.fulfilled, (state, action) => {
        state.listStatus = 'succeeded';
        state.items = action.payload;
        state.byId = Object.fromEntries(action.payload.map((product) => [product.id, product]));
      })
      .addCase(fetchProducts.rejected, (state, action) => {
        state.listStatus = 'failed';
        state.error = action.error.message ?? 'Не удалось загрузить товары';
      })
      .addCase(fetchProductById.pending, (state) => {
        state.detailStatus = 'loading';
        state.error = null;
      })
      .addCase(fetchProductById.fulfilled, (state, action) => {
        state.detailStatus = 'succeeded';
        const product = action.payload;
        state.byId[product.id] = product;
        const index = state.items.findIndex((item) => item.id === product.id);
        if (index >= 0) {
          state.items[index] = product;
        }
      })
      .addCase(fetchProductById.rejected, (state, action) => {
        state.detailStatus = 'failed';
        state.error = action.error.message ?? 'Не удалось загрузить товар';
      });
  },
});

export const productsReducer = productsSlice.reducer;
