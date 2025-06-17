import { CheckCircleIcon, EditIcon } from '@chakra-ui/icons';
import { HStack } from '@chakra-ui/layout';
import { Button, IconButton, Input, Text, Tooltip } from '@chakra-ui/react';
import { InputControl } from 'formik-chakra-ui';
import { useRef, useState } from 'react';
import { BsDashCircle } from 'react-icons/bs';

interface Props {
  initialKey: string;
  keyName: string;
  setFieldValue: (field: string, value: any, shouldValidate?: boolean | undefined) => void;
  initialValue: any;
}

const ENCODED_VALUE = '********';

export const SecretValueInput = ({
  initialKey,
  keyName: key,
  setFieldValue,
  initialValue,
}: Props) => {
  const [isDisabled, setIsDisabled] = useState(true);
  const inputRef = useRef<HTMLInputElement>(null);

  const formatJsonOrString = (text: string | undefined) => {
    try {
      return JSON.parse(text as string);
    } catch (e) {
      return text;
    }
  };

  return (
    <HStack w="full">
      {isDisabled ? (
        <InputControl
          display="flex"
          alignItems="center"
          name={`${initialKey}.${key}`}
          label={`${key}:`}
          isDisabled={isDisabled}
          isReadOnly={isDisabled}
          labelProps={{ mb: 0, whiteSpace: 'nowrap' }}
        />
      ) : (
        <>
          <Text whiteSpace="nowrap" mr={1}>{`${key}:`}</Text>
          <Input
            display="flex"
            alignItems="center"
            name={`edited_${initialKey}.${key}`}
            ml={3}
            ref={inputRef}
            defaultValue={initialValue === ENCODED_VALUE ? '' : initialValue}
          />
        </>
      )}
      <Tooltip label="Delete this item">
        <IconButton
          aria-label="remove secret"
          icon={<BsDashCircle />}
          onClick={() => setFieldValue(`${initialKey}.${key}`, undefined)}
        />
      </Tooltip>
      {isDisabled ? (
        <Tooltip label="Edit this secret value">
          <IconButton
            aria-label="edit secret"
            icon={<EditIcon />}
            onClick={() => setIsDisabled(false)}
          />
        </Tooltip>
      ) : (
        <>
          <Button onClick={() => setIsDisabled(true)}>Cancel</Button>
          <Tooltip label="Confirm changes">
            <IconButton
              aria-label="Confirm changes secret"
              icon={<CheckCircleIcon />}
              onClick={() => {
                setIsDisabled(true);
                setFieldValue(`${initialKey}.${key}`, formatJsonOrString(inputRef.current?.value));
              }}
            />
          </Tooltip>
        </>
      )}
    </HStack>
  );
};
