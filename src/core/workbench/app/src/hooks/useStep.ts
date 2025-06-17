import { useContext } from 'react';

import { StepContext } from '../features/global/components/StepContext';

export const useStep = () => {
  const context = useContext(StepContext);
  if (!context) {
    throw Error('Wrap your step with `<Steps />`');
  } else {
    return context;
  }
};
