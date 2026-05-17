import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '@/lib/api'
import { QUERY_KEYS } from '@/constants'

export const useDashboard = () => {
  const dailyQuery  = useQuery({ queryKey: QUERY_KEYS.dashDaily,   queryFn: () => dashboardApi.getDaily() })
  const weeklyQuery = useQuery({ queryKey: QUERY_KEYS.dashWeekly,  queryFn: () => dashboardApi.getWeekly() })
  const monthlyQuery= useQuery({ queryKey: QUERY_KEYS.dashMonthly, queryFn: () => dashboardApi.getMonthly() })

  return {
    daily:     dailyQuery.data  ?? [],
    weekly:    weeklyQuery.data ?? [],
    monthly:   monthlyQuery.data ?? [],
    isLoading: dailyQuery.isLoading || weeklyQuery.isLoading || monthlyQuery.isLoading,
  }
}
