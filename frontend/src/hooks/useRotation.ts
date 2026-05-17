import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { rotationApi } from '@/lib/api'
import type { RotationDay } from '@/types'

const ROTATION_KEY = ['rotation', 'today'] as const

export const useRotation = () => {
  const queryClient = useQueryClient()

  const rotationQuery = useQuery({
    queryKey: ROTATION_KEY,
    queryFn: rotationApi.getToday,
  })

  const completeMutation = useMutation({
    mutationFn: ({ dayNumber, completed }: { dayNumber: number; completed: boolean }) =>
      rotationApi.markCompleted(dayNumber, completed),
    onMutate: async ({ completed }) => {
      await queryClient.cancelQueries({ queryKey: ROTATION_KEY })
      const previous = queryClient.getQueryData<RotationDay | null>(ROTATION_KEY)
      queryClient.setQueryData<RotationDay | null>(ROTATION_KEY, old =>
        old ? { ...old, completed_today: completed } : old
      )
      return { previous }
    },
    onError: (_err, _vars, context) => {
      if (context?.previous !== undefined) {
        queryClient.setQueryData(ROTATION_KEY, context.previous)
      }
    },
  })

  const setStartMutation = useMutation({
    mutationFn: (startDate: string) => rotationApi.setStartDate(startDate),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ROTATION_KEY }),
  })

  return {
    rotation: rotationQuery.data ?? null,
    isLoading: rotationQuery.isLoading,
    toggleComplete: (dayNumber: number, completed: boolean) =>
      completeMutation.mutate({ dayNumber, completed }),
    setStartDate: (date: string) => setStartMutation.mutate(date),
    isSettingStartDate: setStartMutation.isPending,
  }
}
