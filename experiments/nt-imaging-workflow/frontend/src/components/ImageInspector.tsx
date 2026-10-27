import { useRef, useState } from 'react'

export default function ImageInspector({ src, label = 'Derived synthetic demonstration radiograph' }: { src: string; label?: string }) {
  const [zoom, setZoom] = useState(1)
  const viewport = useRef<HTMLDivElement>(null)
  const drag = useRef<{ x: number; y: number; left: number; top: number } | null>(null)
  function pointerDown(event: React.PointerEvent<HTMLDivElement>) {
    const node = viewport.current!
    drag.current = { x: event.clientX, y: event.clientY, left: node.scrollLeft, top: node.scrollTop }
    node.setPointerCapture(event.pointerId)
  }
  function pointerMove(event: React.PointerEvent<HTMLDivElement>) {
    if (!drag.current || !viewport.current) return
    viewport.current.scrollLeft = drag.current.left - (event.clientX - drag.current.x)
    viewport.current.scrollTop = drag.current.top - (event.clientY - drag.current.y)
  }
  function pointerUp(event: React.PointerEvent<HTMLDivElement>) {
    drag.current = null
    viewport.current?.releasePointerCapture(event.pointerId)
  }
  return <div className="image-inspector"><div className="image-tools" aria-label="Image zoom controls"><button className="button subtle" aria-label="Zoom out" disabled={zoom <= 1} onClick={() => setZoom((value) => Math.max(1, value - 0.5))}>−</button><span aria-live="polite">{Math.round(zoom * 100)}%</span><button className="button subtle" aria-label="Zoom in" disabled={zoom >= 3} onClick={() => setZoom((value) => Math.min(3, value + 0.5))}>+</button><button className="button subtle" onClick={() => { setZoom(1); viewport.current?.scrollTo({ left: 0, top: 0 }) }}>Reset</button></div><div className="image-viewport" ref={viewport} onPointerDown={pointerDown} onPointerMove={pointerMove} onPointerUp={pointerUp} onPointerCancel={pointerUp} role="img" aria-label="Derived synthetic radiograph. Drag to pan when zoomed."><img src={src} alt={label} style={{ width: `${zoom * 100}%` }} /></div><p className="image-caption">Use +/− to zoom; drag the image to pan. The original unsanitized input is never sent to the model.</p></div>
}
