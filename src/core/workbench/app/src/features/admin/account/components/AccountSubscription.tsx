import { CheckIcon } from '@chakra-ui/icons';
import {
  Box,
  Button,
  Flex,
  Radio,
  Stack,
  StackDivider,
  Tag,
  TagLabel,
  TagLeftIcon,
  VStack,
  Text,
  HStack,
} from '@chakra-ui/react';
import { Formik, Form } from 'formik';
import { RadioGroupControl, SelectControl } from 'formik-chakra-ui';
import React, { useContext, useState } from 'react';

import { Card } from '../../../../components/Card';
import { HeadingGroup } from '../../../../components/ProfileForm/HeadingGroup';
import { AccountContext } from '../../../../context/AccountContext';
import { UserContext } from '../../../../context/UserContext';
import { useAccountSubscribe } from '../../../global/api/accountSubscribe';

export const AccountSubscription = () => {
  const { currentUser } = useContext(UserContext);
  const { currentAccount } = useContext(AccountContext);
  const initialValues = {
    plan: currentAccount && currentAccount.plan ? currentAccount.plan.kind : 'starter',
    billing_period:
      currentAccount && currentAccount.plan ? currentAccount.plan.billing_period : 'monthly',
  };
  const [currentPlan, setCurrentPlan] = useState<string>(initialValues.plan);

  const subscribeAccountMutation = useAccountSubscribe();

  const isOnTrial =
    currentAccount && currentAccount.plan && currentAccount.remaining_trial_days >= 0;

  const hasStripeSubscription =
    currentAccount &&
    currentAccount.subscription_id !== null &&
    currentAccount.subscription_id !== undefined;

  const handleSubmit = (body: any) => {
    if (hasStripeSubscription) {
      alert('Changing an active subscription is not implemented yet');
    } else {
      body.account_slug = currentAccount?.slug;
      subscribeAccountMutation.mutateAsync({ body: body }).then((data: any) => {
        window.location.href = data.checkout_session_url;
      });
    }
  };

  const onPlanChange = (event: any) => {
    setCurrentPlan(event.target.value);
  };

  const handleManageSubscription = () => {
    if (currentUser?.customer_portal) {
      window.location.href = currentUser.customer_portal;
    }
  };

  return (
    <Stack as="section" spacing="6">
      <HeadingGroup title="Account Subscription" description="Change your subscription details." />
      <Card>
        <Stack divider={<StackDivider />} spacing="6">
          <Formik initialValues={initialValues} onSubmit={handleSubmit}>
            <Form>
              {isOnTrial && (
                <Flex w="full" justifyContent="flex-end">
                  <Tag variant="subtle" colorScheme="green">
                    <TagLeftIcon boxSize="12px" as={CheckIcon} />
                    <TagLabel>
                      on Free Trial - {`${currentAccount.remaining_trial_days} days left`}
                    </TagLabel>
                  </Tag>
                </Flex>
              )}
              <VStack width="full" spacing="6" alignItems="flex-start">
                <Box w="full">
                  <RadioGroupControl
                    name="plan"
                    label="Plan"
                    stackProps={{ alignItems: 'flex-start', direction: 'column' }}
                    onChange={onPlanChange}
                    isDisabled={hasStripeSubscription}
                  >
                    <Radio value="starter">Starter Plan</Radio>
                    <Radio value="growth">Growth Plan</Radio>
                  </RadioGroupControl>
                </Box>
                <Box w="full">
                  <SelectControl
                    label="Billing Period"
                    name="billing_period"
                    isDisabled={hasStripeSubscription}
                  >
                    <option value="monthly">Monthly</option>
                    <option value="yearly">Yearly</option>
                  </SelectControl>
                </Box>
                {!hasStripeSubscription && (
                  <HStack mt="5">
                    <Button
                      type="submit"
                      size="sm"
                      colorScheme="blue"
                      isLoading={subscribeAccountMutation.isLoading}
                      isDisabled={!currentUser?.features.admin_billing}
                    >
                      Subscribe to {currentPlan}
                    </Button>
                    {!currentUser?.features.admin_billing && (
                      <Text color="gray">Subscribe feature is temporarily disabled.</Text>
                    )}
                  </HStack>
                )}
                {hasStripeSubscription && currentUser?.customer_portal && (
                  <Box>
                    <Button mt="5" size="sm" colorScheme="blue" onClick={handleManageSubscription}>
                      Manage subscription
                    </Button>
                    <Text color="gray.500" fontSize="xs" mt={1}>
                      Manage your current subscription, invoices, and payments.
                    </Text>
                  </Box>
                )}
              </VStack>
            </Form>
          </Formik>
        </Stack>
      </Card>
    </Stack>
  );
};
