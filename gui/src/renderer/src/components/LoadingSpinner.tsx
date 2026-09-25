export default function LoadingSpinner(): JSX.Element {
  return (
    <div className="loading-panel h-full w-full">
      <span className="spinner animate-spin" role="status" aria-label="Loading" />
    </div>
  )
}
