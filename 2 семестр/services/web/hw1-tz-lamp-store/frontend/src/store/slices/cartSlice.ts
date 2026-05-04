import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import { orderBaseUrl } from '../../api/endpoints';
import { jsonFetch } from '../../api/jsonFetch';
import type { CartApi, CartCreateResponse, OrderApi } from '../../types/orderApi';

type CartTokenSlice = { cart: { cartToken: string | null } };
const selectCartToken = (state: unknown) => (state as CartTokenSlice).cart.cartToken;

const CART_TOKEN_KEY = 'lamp-store-cart-token';

type CartState = {
  cartToken: string | null;
  cart: CartApi | null;
  bootstrapStatus: 'idle' | 'loading' | 'succeeded' | 'failed';
  mutationError: string | null;
};

const initialState: CartState = {
  cartToken: null,
  cart: null,
  bootstrapStatus: 'idle',
  mutationError: null,
};

export const fetchCart = createAsyncThunk('cart/fetch', async (token: string) => {
  return jsonFetch<CartApi>(`${orderBaseUrl}/api/v1/cart`, {
    headers: { 'X-Cart-Token': token },
  });
});

export const ensureCart = createAsyncThunk('cart/ensure', async (_, { dispatch }) => {
  const existing = localStorage.getItem(CART_TOKEN_KEY);
  if (existing) {
    try {
      await dispatch(fetchCart(existing)).unwrap();
      return existing;
    } catch {
      localStorage.removeItem(CART_TOKEN_KEY);
    }
  }

  const created = await jsonFetch<CartCreateResponse>(`${orderBaseUrl}/api/v1/carts`, { method: 'POST' });
  localStorage.setItem(CART_TOKEN_KEY, created.cart_token);
  await dispatch(fetchCart(created.cart_token)).unwrap();
  return created.cart_token;
});

export const addItemToCart = createAsyncThunk(
  'cart/addItem',
  async (
    { productId, quantity = 1 }: { productId: string; quantity?: number },
    { getState, dispatch },
  ) => {
    let token = selectCartToken(getState());
    if (!token) {
      token = await dispatch(ensureCart()).unwrap();
    }

    return jsonFetch<CartApi>(`${orderBaseUrl}/api/v1/cart/items`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Cart-Token': token,
      },
      body: JSON.stringify({ product_id: productId, quantity }),
    });
  },
);

export const updateCartItemQuantity = createAsyncThunk(
  'cart/updateItem',
  async (
    { productId, quantity }: { productId: string; quantity: number },
    { getState },
  ) => {
    const token = selectCartToken(getState());
    if (!token) {
      throw new Error('Корзина не инициализирована');
    }
    return jsonFetch<CartApi>(`${orderBaseUrl}/api/v1/cart/items/${productId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'X-Cart-Token': token,
      },
      body: JSON.stringify({ quantity }),
    });
  },
);

export const removeCartItem = createAsyncThunk(
  'cart/removeItem',
  async (productId: string, { getState }) => {
    const token = selectCartToken(getState());
    if (!token) {
      throw new Error('Корзина не инициализирована');
    }
    await jsonFetch<void>(`${orderBaseUrl}/api/v1/cart/items/${productId}`, {
      method: 'DELETE',
      headers: { 'X-Cart-Token': token },
    });
    return jsonFetch<CartApi>(`${orderBaseUrl}/api/v1/cart`, {
      headers: { 'X-Cart-Token': token },
    });
  },
);

export type CheckoutPayload = {
  customer_name: string;
  customer_email: string;
  customer_phone: string;
  delivery_address: string;
  comment?: string;
};

export const checkoutCart = createAsyncThunk(
  'cart/checkout',
  async (payload: CheckoutPayload, { getState, dispatch }) => {
    const token = selectCartToken(getState());
    if (!token) {
      throw new Error('Корзина не инициализирована');
    }

    const order = await jsonFetch<OrderApi>(`${orderBaseUrl}/api/v1/orders/checkout`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Cart-Token': token,
      },
      body: JSON.stringify(payload),
    });

    const fresh = await jsonFetch<CartCreateResponse>(`${orderBaseUrl}/api/v1/carts`, { method: 'POST' });
    localStorage.setItem(CART_TOKEN_KEY, fresh.cart_token);
    await dispatch(fetchCart(fresh.cart_token)).unwrap();

    return order;
  },
);

const cartSlice = createSlice({
  name: 'cart',
  initialState,
  reducers: {
    clearMutationError(state) {
      state.mutationError = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(ensureCart.pending, (state) => {
        state.bootstrapStatus = 'loading';
        state.mutationError = null;
      })
      .addCase(ensureCart.fulfilled, (state, action) => {
        state.bootstrapStatus = 'succeeded';
        state.cartToken = action.payload;
      })
      .addCase(ensureCart.rejected, (state, action) => {
        state.bootstrapStatus = 'failed';
        state.mutationError = action.error.message ?? 'Не удалось создать корзину';
      })
      .addCase(fetchCart.fulfilled, (state, action) => {
        state.cartToken = action.meta.arg;
        state.cart = action.payload;
      })
      .addCase(fetchCart.rejected, (state, action) => {
        state.mutationError = action.error.message ?? 'Не удалось загрузить корзину';
      })
      .addCase(addItemToCart.fulfilled, (state, action) => {
        state.cart = action.payload;
        state.mutationError = null;
      })
      .addCase(addItemToCart.rejected, (state, action) => {
        state.mutationError = action.error.message ?? 'Не удалось добавить в корзину';
      })
      .addCase(updateCartItemQuantity.fulfilled, (state, action) => {
        state.cart = action.payload;
        state.mutationError = null;
      })
      .addCase(updateCartItemQuantity.rejected, (state, action) => {
        state.mutationError = action.error.message ?? 'Не удалось обновить позицию';
      })
      .addCase(removeCartItem.fulfilled, (state, action) => {
        state.cart = action.payload;
        state.mutationError = null;
      })
      .addCase(removeCartItem.rejected, (state, action) => {
        state.mutationError = action.error.message ?? 'Не удалось удалить позицию';
      })
      .addCase(checkoutCart.fulfilled, (state) => {
        state.mutationError = null;
      })
      .addCase(checkoutCart.rejected, (state, action) => {
        state.mutationError = action.error.message ?? 'Ошибка оформления заказа';
      });
  },
});

export const { clearMutationError } = cartSlice.actions;
export const cartReducer = cartSlice.reducer;
