export function LoadingSpinner({ text = '加载中...' }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 gap-4">
      <div className="w-10 h-10 border-2 border-purple-500/30 border-t-purple-400 rounded-full animate-spin" />
      <p className="text-gray-400 text-sm">{text}</p>
    </div>
  );
}
