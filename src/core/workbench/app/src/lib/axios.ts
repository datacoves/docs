import * as Axios from 'axios';

import { API_URL } from '../config';
import { useNotificationStore } from '../hooks/useNotificationStore';

export const axios = Axios.default.create({
  baseURL: API_URL,
  withCredentials: true,
});

axios.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    const message = error.response?.data?.message || error.message;
    useNotificationStore.getState().addNotification({
      type: 'error',
      title: 'Error',
      message,
    });

    return Promise.reject(error);
  }
);
