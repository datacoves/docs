import { Flex, useColorModeValue as mode } from '@chakra-ui/react';

import { Breadcrumb } from '../../Breadcrumb';
import { Header } from '../../Header';
import PageSidebarContainer from '../../Sidebar/PageSidebarContainer';

import { PageContent } from './PageContent';
import { PageContentNoBox } from './PageContentNoBox';
import { PageHeader } from './PageHeader';

export const BasePage = (props: any) => {
  return (
    <Flex direction="column" bg={mode('gray.100', 'gray.800')} minH="100vh">
      <Header />
      <PageSidebarContainer>
        {props.header && <PageHeader mt="12" header={props.header}></PageHeader>}

        <Breadcrumb />

        {props.noBox ? (
          <PageContentNoBox>{props.children}</PageContentNoBox>
        ) : (
          <PageContent>{props.children}</PageContent>
        )}
      </PageSidebarContainer>
    </Flex>
  );
};
