import { InfoIcon, WarningTwoIcon } from '@chakra-ui/icons';
import { VStack, HStack, Stack, Text, Link } from '@chakra-ui/layout';
import { Box, Button, Tooltip, useToast } from '@chakra-ui/react';
import { Form, Formik } from 'formik';
import { InputControl, TextareaControl, SelectControl } from 'formik-chakra-ui';
import { useState, createElement } from 'react';
import * as Yup from 'yup';

import ExpandibleToast from '../../../components/ExpandibleToast/ExpandibleToast';
import { getSSHKey } from '../api/getSshKey';
import { useTestGitConnection } from '../api/testGitConnection';
import { TestConnectionProgress } from '../components';
import { SSHKey } from '../types';

export const GitRepositorySignUp = (props: any) => {
  const [devKeyToCopy, setDevKeyToCopy] = useState('');
  const [deployKeyToCopy, setDeployKeyToCopy] = useState('');
  const [currentSSHKeyType, setCurrentSSHKeyType] = useState<string>();
  const [currentSSHKeyDeploy, setCurrentSSHKeyDeploy] = useState<SSHKey>();
  const [currentSSHKeyDevelopment, setCurrentSSHKeyDevelopment] = useState<SSHKey>();
  const toast = useToast();
  const initialValues = {
    gitRepoUrl: '',
    releaseBranch: '',
    developmentKeyId: '',
    deployKeyId: '',
  };
  const copyDevKeyToClipboard = () => {
    navigator.clipboard.writeText(devKeyToCopy);
    toast({
      render: () => {
        return createElement(ExpandibleToast, {
          message: 'SSH developer key copied to clipboard',
          status: 'success',
        });
      },
      isClosable: true,
      duration: 3000,
    });
  };
  const copyDeployKeyToClipboard = () => {
    navigator.clipboard.writeText(deployKeyToCopy);
    toast({
      render: () => {
        return createElement(ExpandibleToast, {
          message: 'SSH deploy key copied to clipboard',
          status: 'success',
        });
      },
      isClosable: true,
      duration: 3000,
    });
  };
  const onGenSSHKey = async (keyType: string) => {
    if (keyType) {
      const sshKeyDeploy = await getSSHKey({ usage: 'project', ssh_key_type: keyType });
      const sshKeyDeployment = await getSSHKey({ usage: 'user', ssh_key_type: keyType });
      setCurrentSSHKeyDeploy(sshKeyDeploy);
      setCurrentSSHKeyDevelopment(sshKeyDeployment);
      setDeployKeyToCopy(sshKeyDeploy['ssh_key']);
      setDevKeyToCopy(sshKeyDeployment['ssh_key']);
    }
    setCurrentSSHKeyType(keyType);
  };
  const devGitMutation = useTestGitConnection(false);
  const deployGitMutation = useTestGitConnection(true);
  const handleSubmit = (val: any, { setSubmitting }: any) => {
    props.payload.release_branch = val.releaseBranch;
    props.payload.repository.git_url = val.gitRepoUrl;
    props.payload.development_key_id = currentSSHKeyDevelopment?.id;
    props.payload.deploy_key_id = currentSSHKeyDeploy?.id;
    devGitMutation
      .mutateAsync({
        url: val.gitRepoUrl,
        key_id:
          currentSSHKeyDevelopment !== undefined
            ? parseInt(currentSSHKeyDevelopment.id)
            : undefined,
        branch: val.releaseBranch,
      })
      .then(() =>
        deployGitMutation
          .mutateAsync({
            url: val.gitRepoUrl,
            key_id:
              currentSSHKeyDeploy !== undefined ? parseInt(currentSSHKeyDeploy.id) : undefined,
            branch: val.releaseBranch,
            get_dbt_projects: true,
          })
          .then((res: any) => {
            props.payload.dbt_project_paths = res.dbt_project_paths;
            props.setPayload(props.payload);
            setSubmitting(false);
            props.nextStep();
          })
          .catch(() => setSubmitting(false))
      )
      .catch(() => setSubmitting(false));
  };

  return (
    <Formik
      initialValues={initialValues}
      validationSchema={Yup.object({
        gitRepoUrl: Yup.string()
          .matches(/^.*:(.*)\/(.*)/, 'Enter a valid SSH git repository url')
          .required('Required'),
        releaseBranch: Yup.string().required('Required'),
      })}
      onSubmit={handleSubmit}
    >
      {function Render() {
        return (
          <Form>
            <VStack width="full" spacing="6">
              <Box w="full">
                <InputControl
                  name="gitRepoUrl"
                  label="Git Repo SSH URL"
                  inputProps={{ placeholder: 'git@github.com:organization/repo.git' }}
                  isRequired
                />
                <Text color="gray.500" mt={1} fontSize="xs">
                  <WarningTwoIcon boxSize={4} color="yellow.500" /> If this is a newly created
                  repository, please ensure that it contains at least one commit.
                </Text>
              </Box>
              <InputControl
                name="releaseBranch"
                label="Release Branch"
                inputProps={{ placeholder: 'typically "main" or "master"' }}
                isRequired
              />
              <SelectControl
                mb={5}
                label="SSH key type"
                name="ssh_key_type"
                selectProps={{ placeholder: 'Select SSH key type', value: currentSSHKeyType }}
                onChange={(event: any) => onGenSSHKey(event.target.value)}
                isRequired
              >
                <option value="ed25519">ED25519</option>
                <option value="rsa">RSA (Azure Compatibility)</option>
              </SelectControl>
              <VStack w="full">
                <Stack direction="row" justifyContent="flex-end" w="full" mb={-8} zIndex={2}>
                  <Button
                    colorScheme="gray"
                    size="xs"
                    alignSelf="baseline"
                    onClick={copyDeployKeyToClipboard}
                  >
                    COPY
                  </Button>
                  <Tooltip
                    hasArrow
                    label="Copy and add this SSH key to your git repository as a deploy key."
                    bg="gray.300"
                    color="black"
                  >
                    <InfoIcon boxSize={6} color="blue.500" />
                  </Tooltip>
                </Stack>
                <Box w="full">
                  <TextareaControl
                    name="deployKey"
                    label="SSH Deploy Key"
                    textareaProps={{
                      placeholder: 'SSH Key',
                      isReadOnly: true,
                      value: currentSSHKeyDeploy?.ssh_key || '',
                    }}
                  />
                  <Text color="gray.500" mt={1} fontSize="xs">
                    Learn more about configuring SSH deploy keys for your repository{' '}
                    <Link
                      href="https://docs.datacoves.com/how-tos/git/ssh-keys"
                      isExternal
                      color="blue.500"
                      textDecoration="underline"
                    >
                      here
                    </Link>
                    .
                  </Text>
                </Box>
              </VStack>
              <VStack w="full">
                <Stack direction="row" justifyContent="flex-end" w="full" mb={-8} zIndex={2}>
                  <Button
                    colorScheme="gray"
                    size="xs"
                    alignSelf="baseline"
                    onClick={copyDevKeyToClipboard}
                  >
                    COPY
                  </Button>
                  <Tooltip
                    hasArrow
                    label="Copy and add this SSH key to your user account in your git tool (Github, Gitlab, Bitbucket)."
                    bg="gray.300"
                    color="black"
                  >
                    <InfoIcon boxSize={6} color="blue.500" />
                  </Tooltip>
                </Stack>
                <Box w="full">
                  <TextareaControl
                    name="developmentKey"
                    label="SSH Developer Key"
                    textareaProps={{
                      placeholder: 'SSH Key',
                      isReadOnly: true,
                      value: currentSSHKeyDevelopment?.ssh_key || '',
                    }}
                  />
                  <Text color="gray.500" mt={1} fontSize="xs">
                    Learn more about configuring this SSH key in your user account{' '}
                    <Link
                      href="https://docs.datacoves.com/how-tos/git/ssh-keys"
                      isExternal
                      color="blue.500"
                      textDecoration="underline"
                    >
                      here
                    </Link>
                    .
                  </Text>
                </Box>
              </VStack>
            </VStack>
            <HStack mt={6}>
              <Button size="sm" onClick={props.prevStep} variant="ghost">
                Back
              </Button>
              <Button
                type="submit"
                colorScheme="green"
                size="sm"
                isLoading={devGitMutation.isLoading || deployGitMutation.isLoading}
              >
                Next
              </Button>
            </HStack>
            {(devGitMutation.isLoading || deployGitMutation.isLoading) && (
              <TestConnectionProgress infoText="NOTE: CI automation scripts only available for GitHub Actions and Gitlab CI, you may configure your own scripts." />
            )}
          </Form>
        );
      }}
    </Formik>
  );
};
