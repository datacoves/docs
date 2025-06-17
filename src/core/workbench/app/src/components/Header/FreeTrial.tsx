import { InfoIcon } from '@chakra-ui/icons';
import { Button, Tooltip } from '@chakra-ui/react';
import React, { useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { AccountContext } from '../../context/AccountContext';
import { Account } from '../../context/AccountContext/types';
import { UserContext } from '../../context/UserContext';

export const FreeTrialButton = ({ isWorkbench = false }: { isWorkbench?: boolean }) => {
  const { currentUser } = useContext(UserContext);
  const { accounts, currentAccount, setCurrentAccount } = useContext(AccountContext);
  const navigate = useNavigate();

  useEffect(() => {
    if (isWorkbench) {
      const account = accounts?.find(
        (account: Account) => account.slug === currentUser?.env_account
      );
      if (account && account.slug !== currentAccount?.slug) {
        setCurrentAccount(account);
      }
    }
  }, [accounts, currentAccount, currentUser?.env_account, isWorkbench, setCurrentAccount]);

  return (
    <>
      {currentUser &&
        currentUser?.features.accounts_signup &&
        currentAccount &&
        currentAccount.remaining_trial_days >= 0 && (
          <Tooltip
            label={
              'Free Trial is expiring in ' +
              (currentAccount?.remaining_trial_days > 0
                ? `${currentAccount?.remaining_trial_days} days.`
                : 'less than a day.') +
              ' Click here to subscribe to a paid plan.'
            }
            hasArrow
            bg="white"
            color="black"
          >
            <Button
              fontSize="sm"
              size="xs"
              aria-label="Trial"
              colorScheme={currentAccount?.remaining_trial_days < 3 ? 'red' : 'blue'}
              onClick={() => navigate('/admin/account')}
            >
              <InfoIcon mr="1" /> FREE TRIAL -{' '}
              {`${
                currentAccount?.remaining_trial_days > 0
                  ? currentAccount?.remaining_trial_days
                  : 'no'
              } days left`}
            </Button>
          </Tooltip>
        )}
    </>
  );
};
