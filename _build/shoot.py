import sys, asyncio
from playwright.async_api import async_playwright
BASE=sys.argv[1]; OUT=sys.argv[2]; pages=sys.argv[3].split(',')
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
        for w,tag in ((390,'390'),(1280,'1280')):
            pg=await b.new_page(viewport={'width':w,'height':844 if w<500 else 900},device_scale_factor=1)
            for path in pages:
                await pg.goto(BASE+path,wait_until='networkidle',timeout=60000)
                await pg.evaluate('''async()=>{for(let y=0;y<document.body.scrollHeight;y+=500){window.scrollTo(0,y);await new Promise(r=>setTimeout(r,120));}window.scrollTo(0,0);}''')
                await pg.evaluate('''async()=>{document.querySelectorAll('[loading=lazy]').forEach(e=>e.loading='eager');await Promise.all([...document.images].map(i=>i.complete?1:new Promise(r=>{i.onload=i.onerror=r;})));}''')
                await pg.wait_for_timeout(2500)
                sw=await pg.evaluate('document.documentElement.scrollWidth')
                name=(path.strip('/') or 'home').replace('/','_')
                await pg.screenshot(path=f'{OUT}/{name}-{tag}.png',full_page=True)
                print(name,tag,'scrollWidth',sw)
            await pg.close()
        await b.close()
asyncio.run(main())
