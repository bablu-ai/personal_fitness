import { cn } from '@/lib/utils'
import type { DailyRow, WeeklyRow, MonthlyRow } from '@/types'

interface DailyTableProps { rows: DailyRow[] }
interface WeeklyTableProps { rows: WeeklyRow[] }
interface MonthlyTableProps { rows: MonthlyRow[] }

const PctCell = ({ pct }: { pct: number }) => (
  <span className={cn('font-semibold', pct >= 80 ? 'text-green-600' : pct >= 50 ? 'text-yellow-600' : pct > 0 ? 'text-red-500' : 'text-muted-foreground')}>
    {pct > 0 ? `${pct}%` : '—'}
  </span>
)

const TableHeader = ({ cols }: { cols: string[] }) => (
  <thead>
    <tr className="text-xs text-muted-foreground border-b">
      {cols.map(c => <th key={c} className="py-2 px-3 text-left font-medium">{c}</th>)}
    </tr>
  </thead>
)

export const DailyTable = ({ rows }: DailyTableProps) => (
  <div className="overflow-x-auto">
    <table className="w-full text-sm">
      <TableHeader cols={['Date', 'Done', 'Total', 'Rate']} />
      <tbody>
        {rows.map(r => (
          <tr key={r.date} className="border-b last:border-0 hover:bg-muted/30">
            <td className="py-2 px-3 text-muted-foreground">{r.date}</td>
            <td className="py-2 px-3">{r.completed}</td>
            <td className="py-2 px-3">{r.total}</td>
            <td className="py-2 px-3"><PctCell pct={r.completion_pct} /></td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
)

export const WeeklyTable = ({ rows }: WeeklyTableProps) => (
  <div className="overflow-x-auto">
    <table className="w-full text-sm">
      <TableHeader cols={['Week of', 'Done', 'Total', 'Days', 'Rate']} />
      <tbody>
        {rows.map(r => (
          <tr key={r.week_start} className="border-b last:border-0 hover:bg-muted/30">
            <td className="py-2 px-3 text-muted-foreground">{r.week_start}</td>
            <td className="py-2 px-3">{r.completed}</td>
            <td className="py-2 px-3">{r.total}</td>
            <td className="py-2 px-3">{r.days_tracked}/7</td>
            <td className="py-2 px-3"><PctCell pct={r.completion_pct} /></td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
)

export const MonthlyTable = ({ rows }: MonthlyTableProps) => (
  <div className="overflow-x-auto">
    <table className="w-full text-sm">
      <TableHeader cols={['Month', 'Done', 'Total', 'Days', 'Rate']} />
      <tbody>
        {rows.map(r => (
          <tr key={r.month} className="border-b last:border-0 hover:bg-muted/30">
            <td className="py-2 px-3 text-muted-foreground">{r.month}</td>
            <td className="py-2 px-3">{r.completed}</td>
            <td className="py-2 px-3">{r.total}</td>
            <td className="py-2 px-3">{r.days_tracked}</td>
            <td className="py-2 px-3"><PctCell pct={r.completion_pct} /></td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
)
