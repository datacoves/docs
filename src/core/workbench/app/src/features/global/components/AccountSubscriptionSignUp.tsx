import { CheckIcon } from '@chakra-ui/icons';
import { Box, HStack, VStack, Text } from '@chakra-ui/layout';
import { Button, Link, Radio, Tag, TagLabel, TagLeftIcon } from '@chakra-ui/react';
import { Form, Formik } from 'formik';
import { InputControl, RadioGroupControl, SelectControl } from 'formik-chakra-ui';
import React, { useContext, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import * as Yup from 'yup';

import { AccountContext } from '../../../context/AccountContext';
import { UserContext } from '../../../context/UserContext';
import { useAccountSubscribe } from '../api/accountSubscribe';

export const AccountSubscriptionInfoSignUp = (props: any) => {
  const { plan } = useParams();
  const { currentUser } = useContext(UserContext);
  const navigate = useNavigate();
  const { currentAccount } = useContext(AccountContext);
  const trialAccounts = currentUser ? currentUser.trial_accounts : 0;
  const initialValues = {
    name: currentAccount ? currentAccount.name : '',
    plan: currentAccount?.plan
      ? currentAccount.plan.kind
      : trialAccounts === 0
      ? 'starter'
      : plan
      ? plan
      : 'growth',
    billing_period: currentAccount?.plan ? currentAccount.plan.billing_period : 'monthly',
  };
  const [currentPlan, setCurrentPlan] = useState<string>(initialValues.plan);
  const subscribeAccountMutation = useAccountSubscribe();

  const hasStripeSubscription =
    currentAccount &&
    currentAccount.subscription_id !== null &&
    currentAccount.subscription_id !== undefined;
  const isOnTrial = currentAccount && currentAccount.remaining_trial_days >= 0;
  const nextEnabled = hasStripeSubscription || currentPlan === 'starter';
  const subscribeDisabled = !nextEnabled && !currentUser?.features.admin_billing;

  const handleSubmit = (body: any) => {
    if (hasStripeSubscription || currentPlan === 'starter') {
      props.payload.plan = body.plan;
      props.payload.billing_period = body.billing_period;
      props.payload.account_name = body.name;
      if (hasStripeSubscription) {
        props.payload.account_slug = currentAccount.slug;
      }
      props.setPayload(props.payload);
      props.nextStep();
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

  return (
    <Formik
      initialValues={initialValues}
      validationSchema={Yup.object({
        name: Yup.string().required('Required').max(50),
        plan: Yup.string().required('Required'),
      })}
      onSubmit={handleSubmit}
    >
      <Form>
        <VStack width="full" spacing="6">
          <Box w="full">
            <InputControl
              name="name"
              label="Account name"
              inputProps={{
                placeholder: 'Acme Inc.',
                isDisabled: currentUser?.projects && currentUser?.projects.length > 0,
              }}
              isRequired
            />
            <Text color="gray.500" mt={1} fontSize="xs">
              This will be your account identifier, typically your organization’s name.
            </Text>
          </Box>
          <Box w="full">
            <RadioGroupControl
              name="plan"
              label="Plan"
              stackProps={{ alignItems: 'flex-start', direction: 'column' }}
              onChange={onPlanChange}
            >
              <Radio
                value="starter"
                isDisabled={trialAccounts > 0 || hasStripeSubscription || isOnTrial}
              >
                Starter Plan{' '}
                <Tag variant="subtle" colorScheme="blue">
                  <TagLabel>14-DAYS FREE TRIAL</TagLabel>
                </Tag>
              </Radio>
              {trialAccounts > 0 && (
                <Text color="gray.500" mt={1} fontSize="xs">
                  You have already created a Datacoves trial account in the past.
                </Text>
              )}
              {trialAccounts === 0 && (
                <Text color="gray.500" mt={1} fontSize="xs">
                  Get started right away with a 14 days free-trial starter bundle.{' '}
                  <Link
                    href="https://datacoves.com/pricing"
                    isExternal
                    color="blue.500"
                    textDecoration="underline"
                  >
                    Learn more
                  </Link>
                </Text>
              )}
              <Radio value="growth" isDisabled={hasStripeSubscription || isOnTrial}>
                Growth Plan
              </Radio>
              <Text color="gray.500" mt={1} fontSize="xs">
                Get our most flexible and unlimited pay-as-you-go plan.{' '}
                <Link
                  href="https://datacoves.com/pricing"
                  isExternal
                  color="blue.500"
                  textDecoration="underline"
                >
                  Learn more
                </Link>
              </Text>
            </RadioGroupControl>
          </Box>
          <Box w="full">
            <SelectControl
              label="Billing Period"
              name="billing_period"
              isDisabled={hasStripeSubscription || isOnTrial}
            >
              <option value="monthly">Monthly</option>
              <option value="yearly">Yearly</option>
            </SelectControl>
            <Text color="gray.500" mt={1} fontSize="xs">
              Get a 10% discount on a yearly subscription.
            </Text>
          </Box>
        </VStack>
        <HStack mt={6}>
          {hasStripeSubscription && (
            <Tag variant="subtle" colorScheme="green">
              <TagLeftIcon boxSize="12px" as={CheckIcon} />
              <TagLabel>SUBSCRIBED</TagLabel>
            </Tag>
          )}
          {isOnTrial && (
            <Tag variant="subtle" colorScheme="green">
              <TagLeftIcon boxSize="12px" as={CheckIcon} />
              <TagLabel>already on Free Trial</TagLabel>
            </Tag>
          )}
          {currentUser?.projects && currentUser?.projects.length === 0 && (
            <>
              <Button
                type="submit"
                colorScheme="green"
                size="sm"
                isLoading={subscribeAccountMutation.isLoading}
                isDisabled={subscribeDisabled}
              >
                {nextEnabled ? 'Next' : 'Subscribe'}
              </Button>
              {subscribeDisabled && (
                <Text color="gray">Subscribe feature is temporarily disabled.</Text>
              )}
            </>
          )}
          {currentUser?.projects && currentUser?.projects.length > 0 && (
            <Button size="sm" colorScheme="blue" onClick={() => navigate('/')}>
              Continue to launchpad
            </Button>
          )}
        </HStack>
      </Form>
    </Formik>
  );
};
