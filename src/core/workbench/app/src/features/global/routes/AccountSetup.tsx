import {
  Box,
  Stack,
  Button,
  Text,
  HStack,
  useDisclosure,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
} from '@chakra-ui/react';
import React, { useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import {
  Step,
  Steps,
  StepContent,
  ProjectInfoSignUp,
  ConnectionSignUp,
  GitRepositorySignUp,
} from '..';
import { BasePage } from '../../../components/AdminLayout';
import { UserContext } from '../../../context/UserContext';
import { useSteps } from '../../../hooks/useSteps';
import { AccountSubscriptionInfoSignUp } from '../components/AccountSubscriptionSignUp';
import { ServicesConfigurationSignUp } from '../components/ServicesConfigurationSignUp';
import { AccountSetupPayload } from '../types';

export const AccountSetup = () => {
  const { nextStep, prevStep, reset, activeStep } = useSteps({ initialStep: 0 });
  const { currentUser } = useContext(UserContext);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const navigate = useNavigate();
  const accountSetupPayload: AccountSetupPayload = {
    account_name: '',
    project_name: '',
    release_branch: '',
    development_key_id: '',
    services: { airbyte: false, superset: false, airflow: false },
    connection: { type: '', connection_details: {} },
    repository: { git_url: '' },
    environment_configuration: {},
    project_settings: {},
  };
  const [payload, setPayload] = useState(accountSetupPayload);
  useEffect(() => {
    if (currentUser !== undefined && !currentUser?.features.accounts_signup) {
      onOpen();
    } else if (currentUser !== undefined && !currentUser.setup_enabled) {
      navigate('/');
    }
  }, [currentUser, navigate, onOpen]);

  const closeModal = () => {
    onClose();
    navigate('/');
  };
  const contactSales = () => {
    window.location.href = 'mailto:sales@datacoves.com';
    onClose();
    navigate('/');
  };
  return (
    <BasePage header="Account Setup" noProfile>
      {!currentUser?.features.accounts_signup ? (
        <Modal closeOnOverlayClick={false} isOpen={isOpen} onClose={onClose}>
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>Account creation not supported</ModalHeader>
            <ModalBody pb={6}>
              <Text>
                This Datacoves installation is not configured to support dynamic accounts
                provisioning.
              </Text>
              <Text>Contact our sales team if you need further assistance.</Text>
            </ModalBody>
            <ModalFooter>
              <Button onClick={contactSales} colorScheme="blue">
                Contact
              </Button>
              <Button onClick={closeModal} ml={3}>
                Close
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      ) : (
        <Box mx="auto" maxW="2xl" py="10" px={{ base: '6', md: '8' }} minH="400px">
          <Steps activeStep={activeStep}>
            <Step title="Account Subscription">
              <StepContent>
                <Stack shouldWrapChildren spacing="4">
                  <AccountSubscriptionInfoSignUp
                    nextStep={nextStep}
                    setPayload={setPayload}
                    payload={payload}
                  />
                </Stack>
              </StepContent>
            </Step>
            <Step title="Project and Environment">
              <StepContent>
                <Stack shouldWrapChildren spacing="4">
                  <ProjectInfoSignUp
                    prevStep={prevStep}
                    nextStep={nextStep}
                    setPayload={setPayload}
                    payload={payload}
                  />
                </Stack>
              </StepContent>
            </Step>
            <Step title="Data Warehouse">
              <StepContent>
                <Stack shouldWrapChildren spacing="4">
                  <ConnectionSignUp
                    nextStep={nextStep}
                    prevStep={prevStep}
                    setPayload={setPayload}
                    payload={payload}
                  />
                </Stack>
              </StepContent>
            </Step>
            <Step title="Git Repository">
              <StepContent>
                <Stack shouldWrapChildren spacing="4">
                  <GitRepositorySignUp
                    nextStep={nextStep}
                    prevStep={prevStep}
                    setPayload={setPayload}
                    payload={payload}
                    activeStep={activeStep}
                  />
                </Stack>
              </StepContent>
            </Step>
            <Step title="Services Configuration">
              <StepContent>
                <Stack shouldWrapChildren spacing="4">
                  <ServicesConfigurationSignUp
                    nextStep={nextStep}
                    prevStep={prevStep}
                    setPayload={setPayload}
                    payload={payload}
                    activeStep={activeStep}
                  />
                </Stack>
              </StepContent>
            </Step>
          </Steps>
          <HStack
            display={activeStep === 5 ? 'flex' : 'none'}
            mt="10"
            spacing="4"
            shouldWrapChildren
          >
            <Text>All steps completed - you&apos;re finished</Text>
            <Button size="sm" onClick={reset} variant="outline" verticalAlign="baseline">
              Reset
            </Button>
          </HStack>
        </Box>
      )}
    </BasePage>
  );
};
