import AppKit
import CoreText
for name in ["font-0","font-1"] { CTFontManagerRegisterFontsForURL(URL(fileURLWithPath:"projects/education-swift/Sources/LingoSeed/Resources/Reference/\(name).ttf") as CFURL,.process,nil) }
var rows:[[String:Any]]=[]
for weight in [500,700] {
 let descriptor=CTFontDescriptorCreateWithAttributes([kCTFontNameAttribute:"DuolingoSans-Thin",kCTFontVariationAttribute:[NSNumber(value:0x77676874):NSNumber(value:weight)]] as CFDictionary)
 let font=CTFontCreateWithFontDescriptor(descriptor,19,nil)
 let line=CTLineCreateWithAttributedString(NSAttributedString(string:"设置状态",attributes:[.font:font]))
 let runs=CTLineGetGlyphRuns(line) as! [CTRun]
 rows.append(["weight":weight,"requested_postscript":CTFontCopyPostScriptName(font),"resolved_runs":runs.map { run -> [String:Any] in
  let attrs=CTRunGetAttributes(run) as NSDictionary;let f=attrs[kCTFontAttributeName] as! CTFont
  return ["family":CTFontCopyFamilyName(f),"postscript":CTFontCopyPostScriptName(f),"traits":CTFontCopyTraits(f)]
 },"width":CTLineGetTypographicBounds(line,nil,nil,nil)])
}
let data=try JSONSerialization.data(withJSONObject:rows,options:[.prettyPrinted,.sortedKeys]);FileHandle.standardOutput.write(data)
