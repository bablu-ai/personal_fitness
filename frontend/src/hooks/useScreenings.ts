import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { screeningsApi } from '@/lib/api'

const DUE_KEY = ['screenings', 'due'] as const

export const useScreenings = () => {
  const queryClient = useQueryClient()

  const dueQuery = useQuery({
    queryKey: DUE_KEY,
    queryFn: screeningsApi.getDue,
  })

  const doneMutation = useMutation({
    mutationFn: ({ id, date, notes }: { id: string; date?: string; notes?: string }) =>
      screeningsApi.markDone(id, date, notes),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: DUE_KEY }),
  })

  return {
    dueScreenings: dueQuery.data ?? [],
    isLoading: dueQuery.isLoading,
    markDone: (id: string, date?: string) => doneMutation.mutate({ id, date }),
  }
}
