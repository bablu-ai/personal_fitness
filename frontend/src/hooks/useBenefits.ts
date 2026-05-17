import { useQuery } from '@tanstack/react-query'
import { benefitsApi } from '@/lib/api'
import { QUERY_KEYS } from '@/constants'

export const useBenefits = () => {
  const query = useQuery({
    queryKey: QUERY_KEYS.todayBenefits,
    queryFn: benefitsApi.getToday,
  })

  return {
    scores:    query.data?.scores ?? [],
    isLoading: query.isLoading,
    error:     query.error,
  }
}
