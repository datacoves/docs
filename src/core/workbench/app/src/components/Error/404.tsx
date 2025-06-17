import { Flex } from '@chakra-ui/react';

import icon from '../../assets/404.svg';
import { Header } from '../Header';

import { ErrorPage } from './ErrorPage';
export const Error404Page = () => {
  return (
    <Flex flexFlow="column" h="100vh">
      <Header />
      <ErrorPage
        svg={icon}
        title="404"
        subtitle="Something's missing"
        body={['This page cannot be found', 'Make sure the URL is correct']}
      />
    </Flex>
  );
};
