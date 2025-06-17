import { useEffect, useState } from 'react';

export function usePersistedState(
  key: string,
  defaultValue: any,
  transformer?: (val: string) => string
) {
  const [state, setState] = useState(() => {
    const storedValue = localStorage.getItem(key) as string;
    const parsedValue =
      storedValue === 'undefined' || !storedValue ? defaultValue : JSON.parse(storedValue);
    return transformer ? transformer(parsedValue) : parsedValue;
  });
  useEffect(() => {
    localStorage.setItem(key, JSON.stringify(state));
  }, [key, state]);
  return [state, setState];
}
