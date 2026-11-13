const fs=require('fs');
const urls=[['interior','https://avatars.mds.yandex.net/get-altay/4374841/2a000001775a5443520640f01801d4a3f4c2/XXL_height'],['detail','https://avatars.mds.yandex.net/get-altay/9742646/2a0000018a04740149f1b6809d7d821694bc/XXL_height'],['cup','https://avatars.mds.yandex.net/get-altay/14033308/2a0000019253468d746f730db91a6ed5c91e/XXL_height']];
Promise.all(urls.map(async([name,u])=>{let r=await fetch(u);if(!r.ok)throw Error(r.status);fs.writeFileSync('outputs/rybinsk-coffee/dist/assets/'+name+'.jpg',Buffer.from(await r.arrayBuffer()));console.log(name,r.status)}));
