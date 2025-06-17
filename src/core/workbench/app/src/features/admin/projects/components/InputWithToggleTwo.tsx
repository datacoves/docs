import { Input } from '@chakra-ui/input';
import { Box, Flex, FormLabel, Switch, Tooltip, VStack } from '@chakra-ui/react';
import { InputControl } from 'formik-chakra-ui';
import React, { FC, useEffect, useRef, useState } from 'react';

type NewType = JSX.IntrinsicElements['input'];

interface InputWithToggleProps extends NewType {
  label: string;
  name: string;
  wasChanged?: boolean;
  setOverrideValue: React.Dispatch<React.SetStateAction<boolean>>;
}

export const InputWithToggleTwo: FC<InputWithToggleProps> = ({
  label,
  name,
  defaultValue,
  wasChanged,
  setOverrideValue,
}) => {
  const [isOverriden, setIsOverridden] = useState(false);
  const inputDiv = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setIsOverridden(wasChanged === true);
  }, [setOverrideValue, wasChanged]);

  useEffect(() => {
    setOverrideValue(isOverriden);
  }, [setOverrideValue, isOverriden, name]);

  const onSwitchChange = () => {
    setIsOverridden(!isOverriden);
    if (!isOverriden) {
      // FIXME: Find a better way to wait until div is rendered
      setTimeout(() => {
        if (inputDiv.current) {
          const input: HTMLInputElement | null = inputDiv.current.querySelector(`#${name}`);
          input?.focus();
        }
      }, 100);
    }
  };

  return (
    <Flex justify="space-between" alignItems="flex-start" display="flex" w="full">
      <VStack ref={inputDiv} w="full" mr={5} alignItems="flex-start">
        {isOverriden ? (
          <InputControl name={name} label={label} id={`${name}-input`} mr={5} />
        ) : (
          <>
            <FormLabel htmlFor={name} mb="0">
              {label}
            </FormLabel>
            <Input value={defaultValue} isReadOnly textColor="GrayText" />
          </>
        )}
      </VStack>
      <Tooltip label="Override default value" hasArrow bg="gray.300" color="black">
        <Box
          alignItems="center"
          display="flex"
          justifyContent="center"
          verticalAlign="baseline"
          mt="10"
        >
          <Switch
            id={`${name}-switch`}
            mr={1}
            display="flex"
            isChecked={isOverriden}
            onChange={onSwitchChange}
          />
        </Box>
      </Tooltip>
    </Flex>
  );
};
