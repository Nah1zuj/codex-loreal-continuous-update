/** Decode a user-selected file locally, strip metadata and downscale; never upload here. */
export async function preparePhoto(file:File):Promise<string>{
 if(!['image/jpeg','image/png','image/webp'].includes(file.type))throw new Error('Please select a JPEG, PNG or WebP image')
 if(file.size>15*1024*1024)throw new Error('Please select an image smaller than 15 MB')
 const bitmap=await createImageBitmap(file)
 try{
  const scale=Math.min(1,1024/Math.max(bitmap.width,bitmap.height));const canvas=document.createElement('canvas')
  canvas.width=Math.max(1,Math.round(bitmap.width*scale));canvas.height=Math.max(1,Math.round(bitmap.height*scale))
  try{const context=canvas.getContext('2d');if(!context)throw new Error('Local image preparation is unavailable');context.drawImage(bitmap,0,0,canvas.width,canvas.height);const image=canvas.toDataURL('image/jpeg',.8);if(image.length>3_000_000)throw new Error('Image is too large after resizing');return image}finally{canvas.width=canvas.height=0}
 }finally{bitmap.close()}
}
