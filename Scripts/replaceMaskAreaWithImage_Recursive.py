from os import path
from PIL import Image, ImageFilter
from arcpy import GetParameterAsText, GetParameter


def main():
    # Process Images in ImageFolder
    for i in inImageFolder:
        if i.endswith(imgExtension):
            inImage = path.join(inImageFolder, i)
            fileName = path.basename(inImage)
            inMask = path.join(inMaskFolder, fileName)
            # Check that Mask Raster Exists, otherwise bypass
            if path.exists(inMask):
                # Begin Processing Images
                rgbImage = Image.open(path.join(inImageFolder, inImage))
                mask = Image.open(
                    path.join(inMaskFolder, inImage)).convert('L').filter(ImageFilter.GaussianBlur(blurDistance))
                textureMask = Image.open(inTexture).resize(rgbImage.size)
                im = Image.composite(rgbImage, textureMask, mask)
                im.save(path.join(outFolder, fileName))
            # If mask does not exist then copy source image.
            else:
                if copy_unedited_images:
                    img = Image.open(inImage)
                    img.save(path.join(outFolder, fileName))


if __name__ == '__main__':
    debug = False
    if debug:
        ''' Seamless Texture Maps must be the same size as the source image'''
        inImageFolder = r'C:\Users\geof7015\Documents\ArcGIS\Projects\ArcGIS_Image_Designer\TestData\imgFolder'
        imgExtension = '.jpg'
        inMaskFolder = r'C:\Users\geof7015\Documents\ArcGIS\Projects\ArcGIS_Image_Designer\TestData\maskFolder'
        inTexture = r'C:\Users\geof7015\Documents\ArcGIS\Projects\ArcGIS_Image_Designer\Textures\Processed\sand1.jpg'
        outFolder = r'C:\Users\geof7015\Documents\ArcGIS\Projects\ArcGIS_Image_Designer\TestData\test'
        blurDistance = 10  # Distance in Pixels
        copy_unedited_images = True
    else:
        ''' Seamless Texture Maps must be the same size as the source image'''
        inImageFolder = GetParameterAsText(0)
        imgExtension = GetParameterAsText(1)
        inMaskFolder = GetParameterAsText(2)
        inTexture = GetParameterAsText(3)
        outFolder = GetParameterAsText(4)
        blurDistance = GetParameter(5)  # Distance in Pixels
        copy_unedited_images = GetParameterAsText(6)
    main()
