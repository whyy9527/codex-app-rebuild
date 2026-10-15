import Foundation
import CoreAudio
import AVFoundation

// Capture outgoing audio of the supplied owned application's descendant processes.
// The tap includes an explicit process-object list. No global tap or mic device.
func property(_ selector:AudioObjectPropertySelector)->AudioObjectPropertyAddress {
    AudioObjectPropertyAddress(mSelector:selector,mScope:kAudioObjectPropertyScopeGlobal,mElement:kAudioObjectPropertyElementMain)
}
func checked(_ status:OSStatus,_ action:String)throws {
    if status != noErr {throw NSError(domain:"OwnedProcessAudio",code:Int(status),userInfo:[NSLocalizedDescriptionKey:action])}
}
func integer(_ object:AudioObjectID,_ selector:AudioObjectPropertySelector)throws->UInt32 {
    var p=property(selector);var size:UInt32=4;var value:UInt32=0
    try checked(AudioObjectGetPropertyData(object,&p,0,nil,&size,&value),"Read process integer")
    return value
}
func processObjects()throws->[AudioObjectID] {
    var p=property(kAudioHardwarePropertyProcessObjectList);var size:UInt32=0
    try checked(AudioObjectGetPropertyDataSize(AudioObjectID(kAudioObjectSystemObject),&p,0,nil,&size),"Read audio process list size")
    var objects=[AudioObjectID](repeating:0,count:Int(size)/4)
    try objects.withUnsafeMutableBytes {bytes in try checked(AudioObjectGetPropertyData(AudioObjectID(kAudioObjectSystemObject),&p,0,nil,&size,bytes.baseAddress!),"Read audio process list")}
    return objects
}
func ownedTree(_ root:Int32)throws->Set<Int32> {
    let ps=Process();let pipe=Pipe();ps.executableURL=URL(fileURLWithPath:"/bin/ps");ps.arguments=["-axo","pid=,ppid="];ps.standardOutput=pipe;try ps.run()
    let data=pipe.fileHandleForReading.readDataToEndOfFile();ps.waitUntilExit()
    guard ps.terminationStatus==0 else{throw NSError(domain:"OwnedProcessAudio",code:1)}
    let pairs=String(decoding:data,as:UTF8.self).split(separator:"\n").compactMap {line->(Int32,Int32)? in
        let ids=line.split(whereSeparator:{$0==" "||$0=="\t"}).compactMap{Int32($0)}
        return ids.count==2 ? (ids[0],ids[1]):nil
    }
    var owned:Set<Int32>=[root]
    while true {let children=Set(pairs.filter{owned.contains($0.1)}.map{$0.0});if children.isSubset(of:owned){break};owned.formUnion(children)}
    return owned
}
final class Sink:@unchecked Sendable {
    let format:AVAudioFormat
    let file:AVAudioFile
    var frames:Int64=0,samples:Int64=0
    var peak:Float=0,energy:Double=0
    var failure:String?
    init(_ format:AVAudioFormat,_ destination:URL)throws {
        self.format=format
        file=try AVAudioFile(forWriting:destination,settings:format.settings,commonFormat:.pcmFormatFloat32,interleaved:format.isInterleaved)
    }
    func consume(_ source:UnsafePointer<AudioBufferList>) {
        let inputs=UnsafeMutableAudioBufferListPointer(UnsafeMutablePointer(mutating:source))
        guard let first=inputs.first,format.streamDescription.pointee.mBytesPerFrame>0 else{return}
        let count=first.mDataByteSize/format.streamDescription.pointee.mBytesPerFrame
        guard count>0,let pcm=AVAudioPCMBuffer(pcmFormat:format,frameCapacity:count)else{return}
        pcm.frameLength=count
        let outputs=UnsafeMutableAudioBufferListPointer(pcm.mutableAudioBufferList)
        guard inputs.count==outputs.count else{failure="Unexpected tap channel layout";return}
        for i in 0..<inputs.count {
            guard let input=inputs[i].mData,let output=outputs[i].mData else{continue}
            let bytes=min(Int(inputs[i].mDataByteSize),Int(outputs[i].mDataByteSize));memcpy(output,input,bytes)
            let values=input.assumingMemoryBound(to:Float.self)
            for n in 0..<(bytes/4){let v=values[n];peak=max(peak,abs(v));energy+=Double(v)*Double(v)}
            samples+=Int64(bytes/4)
        }
        do {try file.write(from:pcm);frames+=Int64(count)}catch{failure=String(describing:error)}
    }
}
@main struct CaptureOwnedProcessAudio {
    static func main()throws {
        let args=CommandLine.arguments
        guard args.count==4,let pid=Int32(args[1]),pid>1,let duration=Double(args[3]),duration.isFinite,duration>0,duration<=60 else{throw NSError(domain:"OwnedProcessAudio",code:2)}
        let destination=URL(fileURLWithPath:args[2]);let owned=try ownedTree(pid)
        var selected:[AudioObjectID]=[];var selectedPids:[UInt32]=[]
        for object in try processObjects() {
            let p=try integer(object,kAudioProcessPropertyPID)
            if owned.contains(Int32(p)){selected.append(object);selectedPids.append(p)}
        }
        guard !selected.isEmpty else{throw NSError(domain:"OwnedProcessAudio",code:3,userInfo:[NSLocalizedDescriptionKey:"No audio process belongs to supplied owned tree; initialize product audio first"])}
        let description=CATapDescription(stereoMixdownOfProcesses:selected)
        description.name="VALORANT owned browser verification";description.uuid=UUID();description.muteBehavior = .unmuted
        var tap:AudioObjectID=0
        try checked(AudioHardwareCreateProcessTap(description,&tap),"Create explicit owned-process tap")
        defer {AudioHardwareDestroyProcessTap(tap)}
        var address=property(kAudioTapPropertyFormat);var asbd=AudioStreamBasicDescription();var size=UInt32(MemoryLayout<AudioStreamBasicDescription>.size)
        try checked(AudioObjectGetPropertyData(tap,&address,0,nil,&size,&asbd),"Read tap format")
        guard asbd.mFormatID==kAudioFormatLinearPCM,asbd.mFormatFlags&kAudioFormatFlagIsFloat != 0,asbd.mBitsPerChannel==32,let format=AVAudioFormat(streamDescription:&asbd)else{throw NSError(domain:"OwnedProcessAudio",code:4,userInfo:[NSLocalizedDescriptionKey:"Unsupported tap PCM format"])}
        let aggregateDescription:[String:Any]=[
            kAudioAggregateDeviceNameKey:"VALORANT private output tap",kAudioAggregateDeviceUIDKey:UUID().uuidString,
            kAudioAggregateDeviceIsPrivateKey:true,kAudioAggregateDeviceTapAutoStartKey:true,
            kAudioAggregateDeviceTapListKey:[[kAudioSubTapUIDKey:description.uuid.uuidString,kAudioSubTapDriftCompensationKey:true]]]
        var aggregate:AudioObjectID=0
        try checked(AudioHardwareCreateAggregateDevice(aggregateDescription as CFDictionary,&aggregate),"Create private tap aggregate")
        defer {AudioHardwareDestroyAggregateDevice(aggregate)}
        let queue=DispatchQueue(label:"valorant-owned-process-output");let sink=try Sink(format,destination)
        var proc:AudioDeviceIOProcID?
        try checked(AudioDeviceCreateIOProcIDWithBlock(&proc,aggregate,queue){_,input,_,_,_ in sink.consume(input)},"Create audio output reader")
        defer {if let proc {AudioDeviceDestroyIOProcID(aggregate,proc)}}
        try checked(AudioDeviceStart(aggregate,proc),"Start owned process output capture")
        print("READY owned process audio capture");fflush(stdout)
        Thread.sleep(forTimeInterval:duration)
        try checked(AudioDeviceStop(aggregate,proc),"Stop owned process output capture");queue.sync{}
        var receipt:[String:Any]=["kind":"owned_process_audio_tap","owned_pid":pid,"owned_pid_tree":owned.sorted(),"captured_pids":selectedPids,"process_object_ids":selected,"microphone":false,"filter_mode":"explicit_owned_process_objects","excludes_current_process_audio":false,"duration_seconds":duration,"frames":sink.frames,"samples":sink.samples,"peak":sink.peak,"rms":sink.samples>0 ? sqrt(sink.energy/Double(sink.samples)):0,"sample_rate":format.sampleRate,"channels":format.channelCount]
        if let failure=sink.failure{receipt["failure"]=failure}
        try JSONSerialization.data(withJSONObject:receipt,options:[.prettyPrinted,.sortedKeys]).write(to:destination.appendingPathExtension("json"))
        print(String(data:try JSONSerialization.data(withJSONObject:receipt,options:[.sortedKeys]),encoding:.utf8)!)
    }
}
