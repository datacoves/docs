export type Plan = {
  name: string;
  slug: string;
  billing_period: string;
  trial_period_days: number;
  kind: string;
};

export type Account = {
  name: string;
  slug: string;
  owned_by: string;
  subscription_id?: string;
  plan?: Plan;
  remaining_trial_days: number;
  trial_ends_at?: string;
  has_environments: boolean;
  is_suspended: boolean;
};

export interface IAccountContext {
  currentAccount: Account | undefined;
  setCurrentAccount: (account: Account | undefined) => void;
  accounts: Account[] | undefined;
  setAccounts: (accounts: Account[]) => void;
}
