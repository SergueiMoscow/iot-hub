import {
  Container,
  EmptyState,
  Flex,
  Heading,
  Table,
  VStack,
  Text,
  Box,
  SwitchControl,
  Switch,
} from "@chakra-ui/react"

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { FiSearch } from "react-icons/fi"

import { ControllerBoardsService } from "@/client"
import PendingItems from "@/components/Pending/PendingItems"

export const Route = createFileRoute("/_layout/board-state/$id")({
  component: BoardState,
})

function BoardStateTable() {
  const { id } = Route.useParams()
  const navigate = useNavigate({ from: Route.fullPath })

  const { data, isLoading } = useQuery({
    queryFn: () => ControllerBoardsService.getControllerState({ id: parseInt(id) }),
    queryKey: ["board-state", id],
  })

  const handleRelayToggle = (deviceName: string, newValue: boolean) => {
    // Здесь будет логика обновления состояния реле
    console.log(`Toggle ${deviceName} to ${newValue ? "ON" : "OFF"}`)
    // TODO: вызвать API для обновления состояния
  }

  if (isLoading) {
    return <PendingItems />
  }

  if (!data || data.data.length === 0) {
    return (
      <EmptyState.Root>
        <EmptyState.Content>
          <EmptyState.Indicator>
            <FiSearch />
          </EmptyState.Indicator>
          <VStack textAlign="center">
            <EmptyState.Title>No devices found for this board</EmptyState.Title>
            <EmptyState.Description>
              The board might not have any connected devices
            </EmptyState.Description>
          </VStack>
        </EmptyState.Content>
      </EmptyState.Root>
    )
  }

  return (
    <Table.Root size={{ base: "sm", md: "md" }}>
      <Table.Header>
        <Table.Row>
          <Table.ColumnHeader w="20%">Device</Table.ColumnHeader>
          <Table.ColumnHeader w="20%">Type</Table.ColumnHeader>
          <Table.ColumnHeader w="30%">Description</Table.ColumnHeader>
          <Table.ColumnHeader w="15%">Value</Table.ColumnHeader>
          <Table.ColumnHeader w="15%">Last Updated</Table.ColumnHeader>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {data.data.map((device) => (
          <Table.Row key={`${device.device_name}-${device.device_type}`}>
            <Table.Cell>{device.device_name}</Table.Cell>
            <Table.Cell>{device.device_type}</Table.Cell>
            <Table.Cell>{device.device_description || "-"}</Table.Cell>
            <Table.Cell>
              {device.device_type === "Relay" ? (
                <Switch.Root
                  checked={device.value === 1}
                  onCheckedChange={(e) => {
                    console.log(e.checked);
                    handleRelayToggle(device.device_name, e.checked);
                  }}
                  colorScheme="green"
                >
                  <Switch.HiddenInput />
                    <Switch.Control>
                      <Switch.Thumb />
                    </Switch.Control>
                  </Switch.Root>
              ) : (
                <Text>{device.value}</Text>
              )}
            </Table.Cell>
            <Table.Cell>
              {new Date(device.last_updated).toLocaleString()}
            </Table.Cell>
          </Table.Row>
        ))}
      </Table.Body>
    </Table.Root>
  )
}

function BoardState() {
  const { id } = Route.useParams()

  return (
    <Container maxW="full">
      <Heading size="lg" pt={12}>
        Board {id} State
      </Heading>
      <BoardStateTable />
    </Container>
  )
}
