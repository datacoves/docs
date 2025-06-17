import { Input } from '@chakra-ui/input';
import { Box, Flex } from '@chakra-ui/layout';
import { Button, HStack } from '@chakra-ui/react';
import { Tag, TagCloseButton, TagLabel } from '@chakra-ui/tag';
import { useState, FC, useEffect } from 'react';

interface TagInputProps {
  placeholder: string;
  data?: string[];
}

export const TagInput: FC<TagInputProps> = ({ data, placeholder }) => {
  const [input, setInput] = useState<string>('');
  const [tags, setTags] = useState<string[]>([]);
  const [isKeyReleased, setIsKeyReleased] = useState<boolean>(false);

  useEffect(() => {
    if (data !== undefined) setTags(data);
  }, [data]);

  const onChange = (e: any) => {
    const { value } = e.target;
    setInput(value);
  };

  const handlerClick = () => {
    const trimmedInput = input.trim();
    if (trimmedInput.length && !tags.includes(trimmedInput)) {
      setTags((prevState) => [...prevState, trimmedInput]);
      setInput('');
    }
  };

  const onKeyDown = (e: any) => {
    const { key } = e;
    const trimmedInput = input.trim();

    if ((key === ',' || key === 'Enter') && trimmedInput.length && !tags.includes(trimmedInput)) {
      e.preventDefault();
      setTags((prevState) => [...prevState, trimmedInput]);
      setInput('');
    }

    if (key === 'Backspace' && !input.length && tags.length && isKeyReleased) {
      const tagsCopy: string[] = [...tags];
      const poppedTag: string = tagsCopy.pop() || '';
      e.preventDefault();
      setTags(tagsCopy);
      setInput(poppedTag);
    }
    setIsKeyReleased(false);
  };

  const onKeyUp = () => {
    setIsKeyReleased(true);
  };

  const deleteTag = (index: number) => {
    setTags((prevState) => prevState.filter((tag, i) => i !== index));
  };

  return (
    <Flex direction="column" align="center" width="full">
      <HStack spacing={2} width="full" alignItems="baseline">
        <Input
          name="groups"
          value={input}
          placeholder={placeholder}
          onKeyDown={onKeyDown}
          onChange={onChange}
          onKeyUp={onKeyUp}
          mb={3}
        />

        {/* <Input
          value={input}
          placeholder={placeholder}
          onKeyDown={onKeyDown}
          onChange={onChange}
          onKeyUp={onKeyUp}
          mb={3}
        /> */}
        <Button colorScheme="blue" onClick={() => handlerClick()}>
          Add
        </Button>
      </HStack>
      <Box>
        {tags.map((tag, index) => (
          <Tag key={`${index}-tag`} variant="solid" colorScheme="blue" m={1}>
            <TagLabel>{tag}</TagLabel>
            <TagCloseButton onClick={() => deleteTag(index)} />
          </Tag>
        ))}
      </Box>
    </Flex>
  );
};
