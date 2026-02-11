import { useQuery } from '@tanstack/react-query'
import { apiGet } from './client'
import type { Profile } from '../types'

export function useProfile() {
  return useQuery({
    queryKey: ['profile'],
    queryFn: () => apiGet<Profile>('/profile/'),
  })
}
