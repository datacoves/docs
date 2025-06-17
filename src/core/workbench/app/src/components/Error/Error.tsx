import './error.css';

import { ChakraProvider } from '@chakra-ui/react';

import { UIProvider } from '../../context/UIProvider';
import { main } from '../../themes';

import { Error500Page } from './500';
import NotAuthorized from './NotAuthorized';

export function ErrorFallback({ error }: any) {
  if (
    error.message.toString().lastIndexOf('code 403') !== -1 ||
    error.message.toString().lastIndexOf('code 401') !== -1
  ) {
    return (
      <UIProvider>
        <NotAuthorized error={error} />
      </UIProvider>
    );
  } else
    return (
      <ChakraProvider resetCSS theme={main}>
        <Error500Page />
      </ChakraProvider>
    );
}
