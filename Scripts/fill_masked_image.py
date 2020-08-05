# ----------------------------------------------------------------------------------------------------
# Name:        fill_masked_image.py
# Purpose:     Process for replacing Masked areas of Imagery with Images or TextureMaps
# Authors:     Geoff Taylor | Solution Engineer | Imagery & Remote Sensing
# Created:     07/21/2020
# Copyright:   (c) Esri 2020
# Licence:     Apache Version 2.0
# -----------------------------------------------------------------------------------------------------


def copy_auxillary_files(in_file, out_file):
    from shutil import copyfile
    from os.path import splitext
    s = splitext(in_file)[0]
    d = splitext(out_file)[0]
    if ".jpg" in out_file.lower():
        for i in [".jgw", ".jpg.aux.xml", ".jpg.xml"]:  # Omitting Overviews! ".jpg.ovr"
            try:
                copyfile(s+i, d+i)
            except:
                pass
    else:
        print("File Type for transferring auxillary data not supported")


def mask_image(in_image,
               in_mask,
               in_texture,
               out_image,
               method,
               blur_distance):
    from os import remove
    from os.path import exists
    from PIL import Image, ImageFilter
    # Begin Processing Image
    rgb_image = Image.open(in_image)
    mask = Image.open(in_mask).convert('L').resize(rgb_image.size)
    masking_value = 0
    pixels = [mask.getpixel((i, j)) for j in range(mask.height) for i in range(mask.width)]
    if masking_value in pixels:  # If pixel in mask contain masking value
        # Check if the input texture map is already in PIL Open format... Required for time processing tool & Script.
        try:
            texture_mask = Image.open(in_texture).resize(rgb_image.size)
        except:
            texture_mask = in_texture.resize(rgb_image.size)
        if method == "BoxBlur":
            mask_blur = Image.open(in_mask).convert('L').filter(ImageFilter.GaussianBlur(blur_distance)).resize(
                rgb_image.size)
            im = Image.composite(rgb_image, texture_mask, mask_blur)
        if method == "GaussianBlur":
            mask_blur = Image.open(in_mask).convert('L').filter(ImageFilter.GaussianBlur(blur_distance)).resize(
                rgb_image.size)
            im = Image.composite(rgb_image, texture_mask, mask_blur)
        if method == "None":
            im = Image.composite(rgb_image, texture_mask, mask)
        if exists(out_image):
            remove(out_image)
        im.save(out_image)
        copy_auxillary_files(in_image, out_image)
    else:
        from arcpy.management import CopyRaster
        if ".jpg" in out_image.lower():
            CopyRaster(in_image, out_image, '', None, "256", "NONE", "NONE", "8_BIT_UNSIGNED", "NONE", "NONE", "JPEG",
                       "NONE", "CURRENT_SLICE", "NO_TRANSPOSE")
        if ".tif" in out_image.lower():
            CopyRaster(in_image, out_image, '', None, "256", "NONE", "NONE", "8_BIT_UNSIGNED", "NONE", "NONE", "TIFF",
                       "NONE", "CURRENT_SLICE", "NO_TRANSPOSE")


def main():
    from arcpy import CheckExtension, CheckOutExtension, CheckInExtension, ExecuteError, GetMessages, AddMessage
    from arcpy.management import BuildPyramids

    class LicenseError(Exception):
        pass

    try:
        if CheckExtension("ImageAnalyst") == "Available":
            CheckOutExtension("ImageAnalyst")
        else:
            # raise a custom exception
            raise LicenseError
        try:
            from PIL import Image
        except ModuleNotFoundError:
            from arcpy import AddError
            AddError("PILLOW Library Not Detected. Install using Python Manager in ArcGIS Pro")
            print("PILLOW Library Not Detected. Install using Python Manager in ArcGIS Pro")
            exit()

        mask_image(in_image,
                   in_mask,
                   in_texture,
                   out_image,
                   method,
                   blur_distance)
        AddMessage("Building Pyramids")
        BuildPyramids(out_image, -1, "NONE", "NEAREST", "DEFAULT", 75, "OVERWRITE")
        CheckInExtension("ImageAnalyst")

    except LicenseError:
        print("Image Analyst license is unavailable")
    except ExecuteError:
        print(GetMessages(2))


if __name__ == '__main__':
    debug = False
    if debug:
        ''' Seamless Texture Maps must be the same size as the source image'''
        in_image = r'C:\Users\geof7015\Documents\ArcGIS\Projects\ArcGIS_Image_Designer\TestData\imgFolder\Ortho.jpg'
        in_mask = r'C:\Users\geof7015\Documents\ArcGIS\Projects\ArcGIS_Image_Designer\TestData\maskFolder\dune8TestMask.tif'
        in_texture = r'C:\Users\geof7015\Documents\ArcGIS\Projects\ArcGIS_Image_Designer\Textures\Processed\coastal_steppe.jpg'
        out_image = r'C:\Users\geof7015\Documents\ArcGIS\Projects\ArcGIS_Image_Designer\TestData\test\Da_DuneOrtho.jpg'
        method = "None"  # "GaussianBlur", "BoxBlur", "None"
        blur_distance = 10  # Distance in Pixels
    else:
        from os.path import exists
        from arcpy import GetParameterAsText, GetParameter, AddMessage, AddWarning

        ''' Seamless Texture Maps must be the same size as the source image'''
        in_image = GetParameterAsText(0)
        in_mask = GetParameterAsText(1)
        in_texture = GetParameterAsText(2)
        out_image = GetParameterAsText(3)
        method = GetParameterAsText(4)  # "GaussianBlur", "BoxBlur", "None"
        blur_distance = GetParameter(5)  # Distance in Pixels

        for i in [in_image, in_mask, in_texture]:
            if not exists(i):
                AddWarning("{0} | Detected as non-existing".format(i))
                exit()

        AddMessage(blur_distance)
    main()
