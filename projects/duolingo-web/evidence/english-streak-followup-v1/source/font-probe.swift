import AppKit
import CoreText
for name in ["font-0","font-1"] {
 let url=URL(fileURLWithPath:FileManager.default.currentDirectoryPath+"/projects/education-swift/Sources/LingoSeed/Resources/Reference/"+name+".ttf")
 CTFontManagerRegisterFontsForURL(url as CFURL,.process,nil)
 for d in CTFontManagerCreateFontDescriptorsFromURL(url as CFURL) as? [CTFontDescriptor] ?? [] {
  let f=CTFontCreateWithFontDescriptor(d,17,nil)
  print(name,CTFontCopyPostScriptName(f),CTFontCopyVariation(f) as Any)
 }
}
let d=CTFontDescriptorCreateWithAttributes([kCTFontNameAttribute:"DuolingoSans-Thin",kCTFontVariationAttribute:[NSNumber(value:0x77676874):NSNumber(value:700)]] as CFDictionary)
let f=CTFontCreateWithFontDescriptor(d,17,nil); print("native-700",CTFontCopyPostScriptName(f),CTFontCopyVariation(f) as Any)
