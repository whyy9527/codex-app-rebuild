import AppKit
import CoreText
let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let dir = root.appendingPathComponent("projects/education-swift/Sources/LingoSeed/Resources/Reference")
for n in ["font-0", "font-1"] {
 let url=dir.appendingPathComponent(n+".ttf")
 if let descriptors=CTFontManagerCreateFontDescriptorsFromURL(url as CFURL) as? [CTFontDescriptor] {
  for d in descriptors {
   let f=CTFontCreateWithFontDescriptor(d,15,nil)
   print(n,CTFontCopyPostScriptName(f),CTFontCopyVariationAxes(f) ?? [] as CFArray,CTFontCopyVariation(f) ?? [:] as CFDictionary)
  }
 }
 CTFontManagerRegisterFontsForURL(url as CFURL,.process,nil)
}
for weight in [400,500,700] {
 let descriptor=CTFontDescriptorCreateWithAttributes([kCTFontNameAttribute:"DuolingoSans-Thin",kCTFontVariationAttribute:[NSNumber(value:0x77676874):NSNumber(value:weight)]] as CFDictionary)
 let f=CTFontCreateWithFontDescriptor(descriptor,15,nil)
 print("requested",weight,"resolved",CTFontCopyPostScriptName(f),CTFontCopyVariation(f) ?? [:] as CFDictionary,CTFontCopyTraits(f))
}
