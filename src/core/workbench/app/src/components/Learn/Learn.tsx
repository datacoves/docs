import {
  Box,
  Text,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
} from '@chakra-ui/react';
import ChakraUIRenderer from 'chakra-ui-markdown-renderer';
import ReactMarkdown from 'react-markdown';

export function Learn() {
  const firstMd = `
  * [Quickstart](https://docs.airbyte.com/quickstart/getting-started/#set-up-your-preferences)
  * [Sources catalog](https://docs.airbyte.com/category/sources)
  * [Destinations catalog](https://docs.airbyte.com/category/destinations)`;
  const secondMd = `
  * [Snowflake SQL reference](https://docs.snowflake.com/en/sql-reference-commands.html)
  * [Querying Semi-Structured (JSON) data](https://docs.snowflake.com/en/user-guide/querying-semistructured.html)`;
  const thirdMd = `
  * [Version control in VS Code](https://code.visualstudio.com/docs/introvideos/versioncontrol)
  * [dbt commands reference](https://docs.getdbt.com/reference/dbt-commands)`;
  return (
    <Box bg="white" boxShadow={'md'} rounded={'md'} p={6}>
      <Text
        color={'orange.500'}
        textTransform={'uppercase'}
        fontWeight={800}
        fontSize={'sm'}
        letterSpacing={1.1}
      >
        Documentation
      </Text>
      <Accordion mt={5} defaultIndex={[0]}>
        <AccordionItem>
          <h2>
            <AccordionButton _expanded={{ bg: 'gray.100' }}>
              <Box flex="1" textAlign="left">
                Airbyte
              </Box>
              <AccordionIcon />
            </AccordionButton>
          </h2>
          <AccordionPanel pb={4}>
            <ReactMarkdown components={ChakraUIRenderer()}>{firstMd}</ReactMarkdown>
          </AccordionPanel>
        </AccordionItem>

        <AccordionItem>
          <h2>
            <AccordionButton _expanded={{ bg: 'gray.100' }}>
              <Box flex="1" textAlign="left">
                Snowflake reference
              </Box>
              <AccordionIcon />
            </AccordionButton>
          </h2>
          <AccordionPanel pb={4}>
            <ReactMarkdown components={ChakraUIRenderer()}>{secondMd}</ReactMarkdown>
          </AccordionPanel>
        </AccordionItem>

        <AccordionItem>
          <h2>
            <AccordionButton _expanded={{ bg: 'gray.100' }}>
              <Box flex="1" textAlign="left">
                VS Code and dbt
              </Box>
              <AccordionIcon />
            </AccordionButton>
          </h2>
          <AccordionPanel pb={4}>
            <ReactMarkdown components={ChakraUIRenderer()}>{thirdMd}</ReactMarkdown>
          </AccordionPanel>
        </AccordionItem>
      </Accordion>
    </Box>
  );
}
