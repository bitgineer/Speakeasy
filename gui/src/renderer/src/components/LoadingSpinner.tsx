
export default function LoadingSpinner(): JSX.Element {
  return (
    <div className="flex items-center justify-center h-full w-full min-h-[200px]">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
    </div>
  )
}
