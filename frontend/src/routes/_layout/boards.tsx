import {
    Container,
    EmptyState,
    Flex,
    Heading,
    Table,
    VStack,
    Link as ChakraLink,
  } from "@chakra-ui/react"
  import { useQuery } from "@tanstack/react-query"
  import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
  import { FiSearch } from "react-icons/fi"
  import { z } from "zod"
  
  import { ControllerBoardsService } from "@/client"
  import { ItemActionsMenu } from "@/components/Common/ItemActionsMenu"
  import PendingItems from "@/components/Pending/PendingItems"
  import {
    PaginationItems,
    PaginationNextTrigger,
    PaginationPrevTrigger,
    PaginationRoot,
  } from "@/components/ui/pagination.tsx"
  
  const boardsSearchSchema = z.object({
    page: z.number().catch(1),
  })
  
  const PER_PAGE = 5
  
  function getBoardsQueryOptions({ page }: { page: number }) {
    return {
      queryFn: () =>
        ControllerBoardsService.getBoards({ skip: (page - 1) * PER_PAGE, limit: PER_PAGE }),
      queryKey: ["boards", { page }],
    }
  }
  
  export const Route = createFileRoute("/_layout/boards")({
    component: Boards,
    validateSearch: (search) => boardsSearchSchema.parse(search),
  })
  
  function BoardsTable() {
    const navigate = useNavigate({ from: Route.fullPath })
    const { page } = Route.useSearch()
  
    const { data, isLoading, isPlaceholderData } = useQuery({
      ...getBoardsQueryOptions({ page }),
      placeholderData: (prevData) => prevData,
    })
  
    const setPage = (page: number) =>
      navigate({
        search: (prev: { [key: string]: string }) => ({ ...prev, page }),
      })
  
    const boards = data?.data.slice(0, PER_PAGE) ?? []
    const count = data?.count ?? 0
  
    if (isLoading) {
      return <PendingItems />
    }
  
    if (boards.length === 0) {
      return (
        <EmptyState.Root>
          <EmptyState.Content>
            <EmptyState.Indicator>
              <FiSearch />
            </EmptyState.Indicator>
            <VStack textAlign="center">
              <EmptyState.Title>You don't have any boards yet</EmptyState.Title>
              <EmptyState.Description>
                Add a new board to get started
              </EmptyState.Description>
            </VStack>
          </EmptyState.Content>
        </EmptyState.Root>
      )
    }
  
    return (
      <>
        <Table.Root size={{ base: "sm", md: "md" }}>
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader w="20%">ID</Table.ColumnHeader>
              <Table.ColumnHeader w="20%">Topic</Table.ColumnHeader>
              <Table.ColumnHeader w="20%">IP</Table.ColumnHeader>
              <Table.ColumnHeader w="20%">Last Seen</Table.ColumnHeader>
              <Table.ColumnHeader w="20%">Actions</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {boards?.map((board) => (
              <Table.Row key={board.id} opacity={isPlaceholderData ? 0.5 : 1}>
                <Table.Cell truncate maxW="20%">
                  {board.id}
                </Table.Cell>
                <Table.Cell truncate maxW="20%">
                  <Link to="/board-state/$id" params={{ id: String(board.id) }}>
                    <ChakraLink color="blue.500" _hover={{ textDecoration: "underline" }}>
                      {board.topic}
                    </ChakraLink>
                  </Link>
                </Table.Cell>
                <Table.Cell truncate maxW="20%">
                  {board.ip}
                </Table.Cell>
                <Table.Cell truncate maxW="20%">
                  {board.last_seen}
                </Table.Cell>
                <Table.Cell width="20%">
                  <ItemActionsMenu item={board} />
                </Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
        <Flex justifyContent="flex-end" mt={4}>
          <PaginationRoot
            count={count}
            pageSize={PER_PAGE}
            onPageChange={({ page }) => setPage(page)}
          >
            <Flex>
              <PaginationPrevTrigger />
              <PaginationItems />
              <PaginationNextTrigger />
            </Flex>
          </PaginationRoot>
        </Flex>
      </>
    )
  }
  
  function Boards() {
    return (
      <Container maxW="full">
        <Heading size="lg" pt={12}>
          Boards Management
        </Heading>
        <BoardsTable />
      </Container>
    )
  }
  