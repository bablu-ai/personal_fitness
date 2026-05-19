import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { todosApi } from '@/lib/api'
import { QUERY_KEYS } from '@/constants'
import type { DailyTodo } from '@/types'

export const useTodos = () => {
  const queryClient = useQueryClient()

  const todosQuery = useQuery({
    queryKey: QUERY_KEYS.todayTodos,
    queryFn: todosApi.getToday,
  })

  const summaryQuery = useQuery({
    queryKey: QUERY_KEYS.todaySummary,
    queryFn: todosApi.getTodaySummary,
  })

  const necessarySupplementsQuery = useQuery({
    queryKey: QUERY_KEYS.necessarySupplements,
    queryFn: todosApi.getNecessarySupplements,
  })

  const toggleMutation = useMutation({
    mutationFn: ({ id, completed }: { id: string; completed: boolean }) =>
      todosApi.update(id, { completed }),
    onMutate: async ({ id, completed }) => {
      await queryClient.cancelQueries({ queryKey: QUERY_KEYS.todayTodos })
      const previous = queryClient.getQueryData<DailyTodo[]>(QUERY_KEYS.todayTodos)
      // Optimistic update
      queryClient.setQueryData<DailyTodo[]>(QUERY_KEYS.todayTodos, old =>
        old?.map(t => t.id === id ? { ...t, completed } : t) ?? []
      )
      return { previous }
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(QUERY_KEYS.todayTodos, context.previous)
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.todaySummary })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.todayBenefits })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.necessarySupplements })
    },
  })

  const todos = todosQuery.data ?? []
  const todosByPillar = todos.reduce<Record<string, DailyTodo[]>>((acc, todo) => {
    const pillar = todo.template.pillar
    if (!acc[pillar]) acc[pillar] = []
    acc[pillar].push(todo)
    return acc
  }, {})

  return {
    todos,
    todosByPillar,
    necessarySupplements: necessarySupplementsQuery.data ?? [],
    summary: summaryQuery.data,
    isLoading: todosQuery.isLoading,
    error: todosQuery.error,
    toggleTodo: (id: string, completed: boolean) => toggleMutation.mutate({ id, completed }),
  }
}
