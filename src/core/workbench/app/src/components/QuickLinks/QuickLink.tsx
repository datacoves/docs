import { Button, Text } from '@chakra-ui/react';

export function QuickLink(props: any) {
  function open(url: string) {
    const newWindow = window.open(url, '_blank', 'noopener,noreferrer');
    if (newWindow) newWindow.opener = null;
  }

  return (
    <Button
      flexDirection="column"
      color="orange.400"
      role="group"
      _hover={{ bg: 'orange.400', color: 'white' }}
      p={3}
      h="auto"
      whiteSpace="normal"
      justifyContent="end"
      onClick={() => open(props.link)}
    >
      {props.icon}
      <Text fontSize="md" mt={1} color="blackAlpha.800" _groupHover={{ color: 'white' }}>
        {props.title}
      </Text>
    </Button>
  );
}
