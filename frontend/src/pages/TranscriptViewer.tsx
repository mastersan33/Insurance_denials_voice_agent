import { useParams } from 'react-router-dom';
import { useTranscripts } from '../hooks/useQueries';
import { clsx } from 'clsx';

export default function TranscriptViewer() {
  const { id } = useParams<{ id: string }>();
  const { data: transcripts, isLoading } = useTranscripts(id || '');

  if (isLoading) {
    return <div className="flex items-center justify-center h-64">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Transcript</h2>
      <div className="rounded-xl border border-gray-200 bg-white p-6">
        {!transcripts || transcripts.length === 0 ? (
          <p className="text-center text-gray-500">No transcript available</p>
        ) : (
          <div className="space-y-4">
            {transcripts.map((entry: { id: string; speaker: string; content: string; confidence?: number }) => (
              <div
                key={entry.id}
                className={clsx(
                  'flex',
                  entry.speaker === 'agent' ? 'justify-end' : 'justify-start'
                )}
              >
                <div
                  className={clsx(
                    'max-w-[70%] rounded-lg px-4 py-2',
                    entry.speaker === 'agent'
                      ? 'bg-indigo-100 text-indigo-900'
                      : 'bg-gray-100 text-gray-900'
                  )}
                >
                  <p className="text-xs font-medium mb-1 capitalize">{entry.speaker}</p>
                  <p className="text-sm">{entry.content}</p>
                  {entry.confidence && (
                    <p className="text-xs text-gray-500 mt-1">
                      Confidence: {Math.round(entry.confidence * 100)}%
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
