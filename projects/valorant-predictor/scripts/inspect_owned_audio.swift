import Foundation
import CoreAudio

// Inspect only the explicitly supplied owned process tree. No audio is captured.
func address(_ selector: AudioObjectPropertySelector) -> AudioObjectPropertyAddress {
    AudioObjectPropertyAddress(mSelector:selector,mScope:kAudioObjectPropertyScopeGlobal,mElement:kAudioObjectPropertyElementMain)
}
func number(_ object: AudioObjectID,_ selector: AudioObjectPropertySelector) -> UInt32? {
    var value:UInt32=0;var size=UInt32(MemoryLayout<UInt32>.size);var property=address(selector)
    guard AudioObjectGetPropertyData(object,&property,0,nil,&size,&value)==noErr else{return nil}
    return value
}
let owned=Set(CommandLine.arguments.dropFirst().compactMap(Int32.init))
var property=address(kAudioHardwarePropertyProcessObjectList)
var size:UInt32=0
let status=AudioObjectGetPropertyDataSize(AudioObjectID(kAudioObjectSystemObject),&property,0,nil,&size)
var output:[[String:Any]]=[]
if status==noErr {
    var objects=[AudioObjectID](repeating:0,count:Int(size)/MemoryLayout<AudioObjectID>.size)
    let read=objects.withUnsafeMutableBytes{AudioObjectGetPropertyData(AudioObjectID(kAudioObjectSystemObject),&property,0,nil,&size,$0.baseAddress!)}
    if read==noErr {
        for object in objects {
            guard let pid=number(object,kAudioProcessPropertyPID),owned.contains(Int32(pid))else{continue}
            var row:[String:Any]=["pid":pid,"process_object_id":object]
            if let running=number(object,kAudioProcessPropertyIsRunningOutput){row["is_running_output"]=running}
            output.append(row)
        }
    }
}
print(String(data:try JSONSerialization.data(withJSONObject:["query_status":status,"owned_processes":output],options:[.sortedKeys]),encoding:.utf8)!)
