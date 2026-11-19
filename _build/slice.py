import sys
from PIL import Image
f=sys.argv[1]; h_slice=int(sys.argv[2]) if len(sys.argv)>2 else 1800
im=Image.open(f); w,h=im.size; scale=min(1, 700/w) if w>700 else 1
n=0
for y in range(0,h,h_slice):
    c=im.crop((0,y,w,min(h,y+h_slice)))
    if scale<1: c=c.resize((int(w*scale),int(c.size[1]*scale)))
    c.save(f.replace('.png',f'_s{n}.png')); n+=1
print(f,im.size,n)
