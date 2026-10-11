import AppKit
import CoreText
import Foundation
let url=URL(fileURLWithPath:"projects/education-swift/Sources/LingoSeed/Resources/Reference/font-0.ttf")
CTFontManagerRegisterFontsForURL(url as CFURL,.process,nil)
for weight in [400,500] {
 let descriptor=CTFontDescriptorCreateWithAttributes([kCTFontNameAttribute:"DuolingoSans-Thin",kCTFontVariationAttribute:[NSNumber(value:0x77676874):NSNumber(value:weight)]] as CFDictionary)
 let font=CTFontCreateWithFontDescriptor(descriptor,20,nil)
 for text in ["No","ice","please","No __, please."] {
  let line=CTLineCreateWithAttributedString(NSAttributedString(string:text,attributes:[.font:font]))
  print(weight,text,CTLineGetTypographicBounds(line,nil,nil,nil))
 }
}
