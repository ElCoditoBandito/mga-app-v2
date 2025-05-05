// src/pages/Dashboard.tsx
import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { Box, Button, Heading, Text, Container } from '@chakra-ui/react';

const Dashboard = () => {
  const { user, logout } = useAuth0();

  return (
    <Box py={10} px={4}>
      <Container maxW="container.md" textAlign="center">
        <Heading as="h1" mb={6}>
          Dashboard
        </Heading>
        <Text fontSize="lg" mb={8}>
          Welcome, {user?.name || user?.email}!
        </Text>
        <Button
          colorScheme="teal"
          onClick={() =>
            logout({ logoutParams: { returnTo: window.location.origin } })
          }
        >
          Logout
        </Button>
      </Container>
    </Box>
  );
};

export default Dashboard;
