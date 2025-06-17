import { Avatar, Box, Img, Stack } from '@chakra-ui/react';

interface UserProps {
  data: {
    image?: string;
    name: string;
    email: string;
  };
}

export const UsersRow = (props: UserProps) => {
  const { name, email, image } = props.data;
  return (
    <Stack direction="row" spacing="4" align="center">
      <Box flexShrink={0} h="10" w="10">
        {!image ? (
          <Avatar name={name} />
        ) : (
          <Img
            objectFit="cover"
            htmlWidth="160px"
            htmlHeight="160px"
            w="10"
            h="10"
            rounded="full"
            src={image}
            alt=""
          />
        )}
      </Box>
      <Box>
        <Box fontSize="sm" fontWeight="medium">
          {name}
        </Box>
        <Box fontSize="sm" color="gray.500">
          {email}
        </Box>
      </Box>
    </Stack>
  );
};
