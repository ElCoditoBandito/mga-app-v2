import { Badge, Button, Container, Heading, Stack, Text, VStack } from '@chakra-ui/react'
import React from 'react'
import { useAuth0 } from '@auth0/auth0-react'

const CTA = () => {
    const { loginWithRedirect } = useAuth0()
    return (
        <Container py="16" maxW="5xl">
        <Stack align="center" gap="8">
            <VStack gap="3" textAlign="center">
            <Badge size="lg" variant="surface" rounded="full" alignSelf="center">
                Get Started
            </Badge>
            <Heading as="h2" size="5xl">
                Ready to grow your business?
            </Heading>
            <Text color="fg.muted" textStyle={{ base: 'md', md: 'lg' }} maxW="3xl">
                Streamline your workflow and boost team productivity with our all-in-one platform.
            </Text>
            </VStack>
            <Button size="lg" onClick={() => loginWithRedirect()}>Login</Button>
        </Stack>
        </Container>
    )
}

export default CTA
