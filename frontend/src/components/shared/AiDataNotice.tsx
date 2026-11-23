import { Info } from 'lucide-react';

interface AiDataNoticeProps {
  className?: string;
}

/**
 * Point-of-use disclosure for AI actions: says where the text goes and how to
 * keep it local. Keep the wording plain and consistent with Settings.
 */
export function AiDataNotice({ className = '' }: AiDataNoticeProps) {
  return (
    <div
      className={`flex items-start gap-2 rounded-lg border border-blue-200 bg-blue-50 p-3 text-xs text-blue-800 ${className}`}
    >
      <Info className='mt-0.5 h-4 w-4 flex-shrink-0 text-blue-600' />
      <p>
        The text you enter here is sent to the AI service configured in Settings
        to generate a reply. If the unit has a learning design, its outcomes and
        teaching approach are included as context too. If that service is Ollama
        running on your own computer, the text stays there. Avoid including
        personal details about individual students.
      </p>
    </div>
  );
}
