interface Logic {
  primary_lstm?: string
  secondary_patchtst?: string
  confluence?: boolean
  [key: string]: unknown
}

interface Props {
  reasoning: string
  logic?: Logic | string | null
}

export function ReasoningBlock({ reasoning, logic }: Props) {
  if (!reasoning && !logic) return null

  const isLogicObj = logic && typeof logic === 'object'

  return (
    <div className="bg-terminal-surface border border-terminal-border rounded-xl p-4 space-y-3">
      {reasoning && (
        <>
          <h3 className="text-sm font-semibold text-slate-200">Fusion Reasoning</h3>
          <p className="text-sm text-slate-400 leading-relaxed">{reasoning}</p>
        </>
      )}
      {isLogicObj && (
        <div className="flex flex-wrap gap-3 pt-1 border-t border-terminal-border">
          {(logic as Logic).primary_lstm && (
            <div className="text-xs text-slate-500">
              LSTM: <span className="text-slate-300">{String((logic as Logic).primary_lstm)}</span>
            </div>
          )}
          {(logic as Logic).secondary_patchtst && (
            <div className="text-xs text-slate-500">
              PatchTST: <span className="text-slate-300">{String((logic as Logic).secondary_patchtst)}</span>
            </div>
          )}
          {(logic as Logic).confluence != null && (
            <div className="text-xs text-slate-500">
              Confluence:{' '}
              <span className={(logic as Logic).confluence ? 'text-emerald-400' : 'text-rose-400'}>
                {(logic as Logic).confluence ? 'Yes' : 'No'}
              </span>
            </div>
          )}
        </div>
      )}
      {typeof logic === 'string' && logic && (
        <p className="text-xs text-slate-500 italic border-t border-terminal-border pt-2">{logic}</p>
      )}
    </div>
  )
}
