import { createAsyncThunk, createSlice, type PayloadAction } from '@reduxjs/toolkit';
import { orderBaseUrl } from '../../api/endpoints';
import { jsonFetch } from '../../api/jsonFetch';
import type { OrderApi } from '../../types/orderApi';

type OrdersState = {
  items: OrderApi[];
  listStatus: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
};

const initialState: OrdersState = {
  items: [],
  listStatus: 'idle',
  error: null,
};

export const fetchOrders = createAsyncThunk('orders/fetchAll', async () => {
  return jsonFetch<OrderApi[]>(`${orderBaseUrl}/api/v1/orders`);
});

const ordersSlice = createSlice({
  name: 'orders',
  initialState,
  reducers: {
    prependOrder(state, action: PayloadAction<OrderApi>) {
      const exists = state.items.some((order) => order.id === action.payload.id);
      if (!exists) {
        state.items = [action.payload, ...state.items];
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchOrders.pending, (state) => {
        state.listStatus = 'loading';
        state.error = null;
      })
      .addCase(fetchOrders.fulfilled, (state, action) => {
        state.listStatus = 'succeeded';
        state.items = action.payload;
      })
      .addCase(fetchOrders.rejected, (state, action) => {
        state.listStatus = 'failed';
        state.error = action.error.message ?? 'Не удалось загрузить заказы';
      });
  },
});

export const { prependOrder } = ordersSlice.actions;
export const ordersReducer = ordersSlice.reducer;
