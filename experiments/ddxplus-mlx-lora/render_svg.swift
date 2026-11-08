import AppKit
import WebKit

let arguments = CommandLine.arguments
guard arguments.count == 5,
      let width = Double(arguments[2]),
      let height = Double(arguments[3]),
      width > 0,
      height > 0,
      let svg = try? String(contentsOfFile: arguments[1], encoding: .utf8) else {
    FileHandle.standardError.write("Usage: swift render_svg.swift input.svg width height output.png\n".data(using: .utf8)!)
    exit(2)
}

final class SnapshotDelegate: NSObject, WKNavigationDelegate {
    let webView: WKWebView
    let output: String
    let window: NSWindow

    init(webView: WKWebView, output: String, window: NSWindow) {
        self.webView = webView
        self.output = output
        self.window = window
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            let configuration = WKSnapshotConfiguration()
            configuration.rect = self.webView.bounds
            self.webView.takeSnapshot(with: configuration) { image, error in
                defer { NSApplication.shared.terminate(nil) }
                guard error == nil,
                      let image,
                      let tiff = image.tiffRepresentation,
                      let bitmap = NSBitmapImageRep(data: tiff),
                      let png = bitmap.representation(using: .png, properties: [:]) else {
                    FileHandle.standardError.write("Snapshot failed: \(error?.localizedDescription ?? "image conversion failed")\n".data(using: .utf8)!)
                    exit(1)
                }
                do {
                    try png.write(to: URL(fileURLWithPath: self.output))
                    print("Rendered \(self.output) at \(bitmap.pixelsWide)x\(bitmap.pixelsHigh)")
                } catch {
                    FileHandle.standardError.write("Could not save image: \(error.localizedDescription)\n".data(using: .utf8)!)
                    exit(1)
                }
                self.window.orderOut(nil)
            }
        }
    }

    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        FileHandle.standardError.write("Rendering failed: \(error.localizedDescription)\n".data(using: .utf8)!)
        exit(1)
    }
}

let application = NSApplication.shared
application.setActivationPolicy(.accessory)
let frame = NSRect(x: 0, y: 0, width: width, height: height)
let window = NSWindow(contentRect: frame, styleMask: .borderless, backing: .buffered, defer: false)
let webView = WKWebView(frame: frame)
window.contentView = webView
let delegate = SnapshotDelegate(webView: webView, output: arguments[4], window: window)
webView.navigationDelegate = delegate
let document = "<!doctype html><html><head><meta charset=\"utf-8\"><style>html,body{margin:0;padding:0;width:\(Int(width))px;height:\(Int(height))px;overflow:hidden}svg{display:block}</style></head><body>\(svg)</body></html>"
webView.loadHTMLString(document, baseURL: nil)
window.orderBack(nil)
withExtendedLifetime(delegate) {
    application.run()
}
