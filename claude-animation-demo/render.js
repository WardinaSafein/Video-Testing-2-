const { chromium } = require('playwright'); const fs=require('fs'), path=require('path');
(async()=>{const dir=path.join(__dirname,'frames');fs.mkdirSync(dir,{recursive:true});
 const b=await chromium.launch();const p=await b.newPage({viewport:{width:1280,height:768}});
 await p.goto('file://'+path.join(__dirname,'scene.html'));
 const FPS=30,DUR=6;
 for(let i=0;i<FPS*DUR;i++){await p.evaluate(t=>render(t),i/FPS);
  await p.screenshot({path:path.join(dir,String(i).padStart(4,'0')+'.png')});}
 await b.close();})();
