import { Box, Flex, NumberInput, NumberInputField, Select, Text } from '@chakra-ui/react';
import { InputControl } from 'formik-chakra-ui';
import React, { useState } from 'react';

interface Props {
  name: string;
  label: string;
  value: string | undefined;
  setFieldValue: (field: string, value: any, shouldValidate?: boolean | undefined) => void;
  type: 'CPU' | 'memory';
}

const QUANTITY_SUFIXES = ['Ti', 'Gi', 'Mi'];
const CPU_SUFIXES = ['', 'm'];

export const MemoryInput = ({ name, label, value, setFieldValue, type }: Props) => {
  const [digits, setDigits] = useState((value?.match(/\D+|\d+/g) || [])[0]);
  const [quantity, setQuantity] = useState((value?.match(/\D+|\d+/g) || [])[1] || '');

  const handleNumericChange = (valueAsString: string) => {
    setDigits(valueAsString);
    setFieldValue(name, `${valueAsString}${quantity}`);
  };

  const handleQuantityChange = (e: React.ChangeEvent<any>) => {
    setQuantity(e.target.value);
    setFieldValue(name, `${digits}${e.target.value}`);
  };

  return (
    <Box w="full" minW="160px" maxW="170px">
      <InputControl
        labelProps={{ fontSize: 'sm' }}
        name={name}
        label={label}
        defaultValue={digits}
        display="none"
      />
      <Text fontSize="sm">{label}</Text>
      <Flex w="full">
        <NumberInput defaultValue={digits} onChange={handleNumericChange}>
          <NumberInputField borderRightRadius="0" pl={2} pr={2} />
        </NumberInput>
        <Select
          borderLeftRadius="0"
          defaultValue={quantity}
          width="160%"
          onChange={handleQuantityChange}
        >
          {(type === 'memory' ? QUANTITY_SUFIXES : CPU_SUFIXES).map((sufix) => (
            <option value={sufix} key={sufix}>
              {sufix}
            </option>
          ))}
        </Select>
      </Flex>
    </Box>
  );
};
