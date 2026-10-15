// Use only with a native CUA App binding; captures via actual inspector UI.
export function installLosslessUI(app,fs,{url,output,windowUuid}) {
  const tree=()=>app.getAXState({emit:false,disableDiffing:true});
  const index=line=>Number(line.trim().match(/^\d+/)[0]);
  function pageGuard(ax) {
    if(!ax.includes('UUID='+windowUuid))throw Error('Owned screenshot page changed');
    const field=ax.split('\n').find(x=>x.includes('smart search field'))||'';
    if(!field.includes('Value: '+url))throw Error('Owned screenshot endpoint changed');
  }
  async function capture(stem) {
    if(!/^[a-z0-9-]+$/.test(stem))throw Error('Invalid screenshot stem');
    await fs.mkdir(output,{recursive:true});
    let ax=await tree();pageGuard(ax);
    await fs.writeFile(output+'/'+stem+'.ax.txt',ax,{flag:'wx'});
    await app.pressKey('super+alt+i');ax=await tree();
    const detach=ax.split('\n').find(x=>x.includes('button Detach into separate window'));
    if(detach){await app.click(index(detach));ax=await tree();}
    if(!ax.includes('standard window Web Inspector — '+new URL(url).hostname))throw Error('Owned inspector unavailable');
    const body=ax.split('\n').find(x=>/row .*Description: <body/.test(x));
    if(!body)throw Error('Actual body node unavailable');
    await app.click(index(body));ax=await tree();
    const selected=ax.split('\n').find(x=>/row \(selected(?:,[^)]*)?\) Description: <body/.test(x));
    if(!selected)throw Error('Actual body selection did not update');
    await fs.writeFile(output+'/'+stem+'.inspector.ax.txt',ax,{flag:'wx'});
    await app.click(index(selected),{mouseButton:'right'});ax=await tree();
    const menu=ax.split('\n').find(x=>x.includes('Capture Screenshot'));
    if(!menu)throw Error('Screenshot context menu unavailable');
    await app.click(index(menu));ax=await tree();
    const name=ax.split('\n').find(x=>x.includes('ID: saveAsNameTextField'));
    if(!name)throw Error('Actual PNG save dialog unavailable');
    await app.setValue(index(name),stem+'.png');await tree();
    await app.pressKey('super+shift+g');ax=await tree();
    const path=ax.split('\n').find(x=>x.includes('ID: PathTextField'));
    if(!path)throw Error('Go To Folder unavailable');
    await app.setValue(index(path),output);ax=await tree();
    if(!ax.includes('Value: '+output))throw Error('Owned folder did not update');
    await fs.writeFile(output+'/'+stem+'.folder.ax.txt',ax,{flag:'wx'});
    await app.pressKey('Return');ax=await tree();
    if(!ax.includes('Value: '+stem+'.png')||!ax.includes('Value: '+output.split('/').at(-1)))throw Error('Owned save target differs');
    await fs.writeFile(output+'/'+stem+'.save.ax.txt',ax,{flag:'wx'});
    const save=ax.split('\n').find(x=>x.includes('button Save, ID: OKButton'));
    await app.click(index(save));await tree();
    await app.pressKey('super+w');ax=await tree();pageGuard(ax);
    await fs.writeFile(output+'/'+stem+'.after.ax.txt',ax,{flag:'wx'});
    return {stem,bytes:(await fs.stat(output+'/'+stem+'.png')).size};
  }
  return {capture};
}
