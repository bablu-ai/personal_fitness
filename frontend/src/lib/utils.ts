import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs))

export const formatDate = (dateStr: string): string =>
  new Date(dateStr).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })

export const formatPillar = (pillar: string): string =>
  pillar.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
