export default function Loading() {
  return (
    <div className="container-x py-12" aria-busy="true" aria-label="Loading">
      <div className="skeleton" style={{ height: 36, width: 260, marginBottom: 12 }} />
      <div className="skeleton" style={{ height: 18, width: 160, marginBottom: 40 }} />
      <div className="grid-products">
        {Array.from({ length: 8 }, (_, i) => (
          <div key={i} className="card overflow-hidden">
            <div className="skeleton" style={{ aspectRatio: '1/1', borderRadius: 0 }} />
            <div className="p-4"><div className="skeleton" style={{ height: 14, width: '40%', marginBottom: 10 }} /><div className="skeleton" style={{ height: 20, width: '80%' }} /></div>
          </div>
        ))}
      </div>
    </div>
  );
}
