import { Route, Routes } from 'react-router-dom';

import { Cancel } from './Cancel';
import { Checkout } from './Checkout';

export const BillingRoutes = () => {
  return (
    <Routes>
      <Route path="checkout" element={<Checkout />} />
      <Route path="cancel" element={<Cancel />} />
    </Routes>
  );
};
