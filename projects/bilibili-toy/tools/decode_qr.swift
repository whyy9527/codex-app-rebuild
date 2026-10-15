// Analyze an existing owned-app screenshot; this does not capture any screen.
import Foundation
import Vision
import ImageIO

guard CommandLine.arguments.count == 2 else {
    fputs("Usage: decode_qr <existing-screenshot>\n", stderr)
    exit(2)
}
let url = URL(fileURLWithPath: CommandLine.arguments[1])
guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
      let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
    fputs("Screenshot cannot be decoded\n", stderr)
    exit(2)
}
let request = VNDetectBarcodesRequest()
request.symbologies = [.qr]
try VNImageRequestHandler(cgImage: image).perform([request])
let payloads = (request.results ?? []).compactMap { $0.payloadStringValue }.sorted()
let data = try JSONSerialization.data(withJSONObject: ["payloads": payloads], options: [.sortedKeys])
print(String(decoding: data, as: UTF8.self))
