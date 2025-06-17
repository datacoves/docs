import { Box, Stack, Tooltip } from '@chakra-ui/react';

interface MaxWidthTableCellProps {
  value: string;
  maxW: string;
}
export const MaxWidthTableCell = (props: MaxWidthTableCellProps) => {
  const { value, maxW } = props;
  return (
    <Stack direction="row" spacing="4" align="center" maxW={maxW}>
      <Box overflow="hidden">
        <Tooltip label={value}>
          <Box fontSize="sm" isTruncated={true}>
            {value}
          </Box>
        </Tooltip>
      </Box>
    </Stack>
  );
};
