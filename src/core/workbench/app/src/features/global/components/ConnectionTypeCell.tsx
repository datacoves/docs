import { HStack, Icon, Text } from '@chakra-ui/react';

import { BigqueryIcon } from '../../../components/Icons/Bigquery';
import { DatabricksIcon } from '../../../components/Icons/Databricks';
import { RedshiftIcon } from '../../../components/Icons/Redshift';
import { SnowflakeIcon } from '../../../components/Icons/Snowflake';
import { ConnectionTemplate } from '../types';

interface ConnectionTypeCellProps {
  connectionTemplate: ConnectionTemplate;
}

export const ConnectionTypeCell = (props: ConnectionTypeCellProps) => {
  const { connectionTemplate: connectionTemplate } = props;

  return (
    <HStack>
      {connectionTemplate.type_slug === 'snowflake' && (
        <Icon boxSize={4} as={SnowflakeIcon} color="blue.500" />
      )}
      {connectionTemplate.type_slug === 'redshift' && (
        <Icon boxSize={4} as={RedshiftIcon} color="blue.500" />
      )}
      {connectionTemplate.type_slug === 'databricks' && (
        <Icon boxSize={4} as={DatabricksIcon} color="red.500" />
      )}
      {connectionTemplate.type_slug === 'bigquery' && (
        <Icon boxSize={4} as={BigqueryIcon} color="blue.500" />
      )}
      <Text fontSize="sm" textTransform="capitalize">
        {connectionTemplate.type_slug}
      </Text>
    </HStack>
  );
};
