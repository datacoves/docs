import { Box, Button, FormLabel, HStack, Textarea, VStack } from '@chakra-ui/react';

interface ProjectKeyBoxProps {
  label: string;
  value: string | undefined;
  onCopy: () => void;
}

export const ProjectKeyBox: React.FC<ProjectKeyBoxProps> = ({ label, value, onCopy }) => {
  return (
    <Box w="100%">
      <VStack>
        <HStack justifyContent="flex-end" alignItems="center" w="full" mb={-6} zIndex={2}>
          <Button colorScheme="green" size="xs" alignSelf="baseline" onClick={onCopy}>
            COPY
          </Button>
        </HStack>
      </VStack>
      <FormLabel htmlFor={label.toLowerCase().replace(' ', '-')}>{label}</FormLabel>
      <Textarea
        name={label.toLowerCase().replace(' ', '-')}
        isReadOnly={true}
        value={value}
        zIndex={1}
        h="1"
      />
    </Box>
  );
};
