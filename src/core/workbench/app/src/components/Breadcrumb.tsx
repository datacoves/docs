import { ChevronRightIcon } from '@chakra-ui/icons';
import {
  Breadcrumb as Breadcrumbs,
  BreadcrumbItem,
  BreadcrumbLink,
  Container,
} from '@chakra-ui/react';
import { Link, useLocation } from 'react-router-dom';

import { getSiteContext } from '../utils/siteContext';

type TRoute = {
  name: string;
  link: string;
};

function getRoutes(pathname: string): TRoute[] {
  const routes: TRoute[] = [];
  const parts = pathname.split('/').slice(1);
  parts.forEach((item, index) => {
    if (item !== 'admin' && item !== 'edit') {
      routes.push({
        name: item,
        link: '/' + parts.slice(0, index + 1).join('/'),
      });
    }
  });
  return routes;
}

export const Breadcrumb = (props: any) => {
  const { pathname } = useLocation();
  const routes = getRoutes(pathname);
  const siteContext = getSiteContext();
  const root = siteContext.isWorkbench ? 'workbench' : 'launchpad';

  return (
    <Container maxW="7xl" py="4" {...props}>
      <Breadcrumbs separator={<ChevronRightIcon color="gray.500" />}>
        <BreadcrumbItem>
          <BreadcrumbLink as={Link} to={`/${root}`}>
            {root}
          </BreadcrumbLink>
        </BreadcrumbItem>
        {routes.map((route) => (
          <BreadcrumbItem key={route.name}>
            <BreadcrumbLink as={Link} to={route.link}>
              {route.name}
            </BreadcrumbLink>
          </BreadcrumbItem>
        ))}
      </Breadcrumbs>
    </Container>
  );
};
