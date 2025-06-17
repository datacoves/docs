import { Flex } from '@chakra-ui/layout';
import { ReactNode } from 'react';

import Sidebar from './Sidebar';

interface Props {
  children: ReactNode;
}

const PageSidebarContainer = ({ children }: Props) => (
  <Flex h="100vh">
    <Sidebar />
    <Flex direction="column" w="full" h="full" overflow="auto">
      {children}
    </Flex>
  </Flex>
);

export default PageSidebarContainer;
