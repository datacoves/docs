import { DeleteIcon } from '@chakra-ui/icons';
import { Box, Button, Heading, HStack, Select, VStack, Text } from '@chakra-ui/react';

import { EnvironmentIntegration } from '../../../../context/UserContext/types';
import { Integration } from '../../../global/types';

interface Props {
  integrationsSelected: EnvironmentIntegration[];
  setIntegrationsSelected: (value: React.SetStateAction<EnvironmentIntegration[]>) => void;
  integrations: Integration[];
}

const IntegrationsForm = ({
  integrationsSelected,
  integrations,
  setIntegrationsSelected,
}: Props) => {
  const updateIntegration = (itIndex: number, item: EnvironmentIntegration) => {
    setIntegrationsSelected((prevState) => {
      const newState = prevState.map((obj, index) => {
        if (index === itIndex) {
          return item;
        }
        return obj;
      });

      return newState;
    });
  };
  const deleteIntegration = (itIndex: number) => {
    setIntegrationsSelected((prevState) => {
      return prevState.filter((item, index) => index !== itIndex);
    });
  };

  return (
    <VStack w="full" spacing="6">
      <HStack w="full">
        <Box flex="1">
          <Heading size="md">Environment Integrations</Heading>
          <Text fontSize="sm">Connect environment services to external tools/systems.</Text>
        </Box>
        <Button
          onClick={() =>
            setIntegrationsSelected((prevSelected) => [
              ...prevSelected,
              {
                service: 'airflow',
                integration: integrations[0].id,
                type: integrations[0].type,
                is_notification: integrations[0].is_notification ?? false,
              },
            ])
          }
        >
          + Add New Integration
        </Button>
      </HStack>

      {integrationsSelected.length === 0 && <Text>No integrations configured.</Text>}
      {integrationsSelected?.map((envIntegration, index) => {
        return (
          <HStack key={`envIntegration.${index}`} w="full" spacing="6">
            <Select
              name={`integration-${index}`}
              value={envIntegration.integration}
              onChange={(event: any) => {
                envIntegration.integration = event.target.value;
                const selectedIntegration = integrations.find((i) => i.id == event.target.value);
                if (selectedIntegration) {
                  envIntegration.type = selectedIntegration.type;
                }
                updateIntegration(index, envIntegration);
              }}
            >
              {integrations?.map((integration: Integration) => {
                return (
                  <option key={`envIntegration.${index}.${integration.id}`} value={integration.id}>
                    {integration.name} ({integration.type})
                  </option>
                );
              })}
            </Select>
            <Select
              name={`service-${index}`}
              value={envIntegration.service}
              onChange={(event: any) => {
                envIntegration.service = event.target.value;
                updateIntegration(index, envIntegration);
              }}
            >
              <option value="airflow">Airflow</option>
            </Select>
            <Button variant="ghost" colorScheme="red" onClick={() => deleteIntegration(index)}>
              <DeleteIcon />
            </Button>
          </HStack>
        );
      })}
    </VStack>
  );
};

export default IntegrationsForm;
