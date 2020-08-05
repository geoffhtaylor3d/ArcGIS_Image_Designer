# ----------------------------------------------------------------------------------------------------
# Name:        generate_seamless_texturemap.py
# Purpose:     Process for creating Seamless TextureMaps from images
# Authors:     Geoff Taylor | Solution Engineer | Imagery & Remote Sensing
# Created:     07/21/2020
# Copyright:   (c) Esri 2020
# Licence:     Apache Version 2.0
# -----------------------------------------------------------------------------------------------------


def rreplace(s, match, repl, count=1):
    return repl.join(s.rsplit(match, count))


def seamless_texture(inImg, outImg):
    from os.path import isfile
    try:
        from PIL import Image
    except ModuleNotFoundError:
        from arcpy import AddError
        AddError("PILLOW Library Not Detected. Install using Python Manager in ArcGIS Pro")
        print("PILLOW Library Not Detected. Install using Python Manager in ArcGIS Pro")
        exit()

    # seamless version already exists, dont regenerate
    if isfile(outImg):
        print("Seamless image already exists, ignoring {0}...".format(inImg))
        exit()

    img = Image.open(inImg)
    print("Converting {0}...".format(inImg))
    sz = img.size
    region = []
    for i in range(4):
        region += [img.crop((0, 0, sz[0], sz[1]))]
    img = img.resize((sz[0] * 2, sz[1] * 2))

    region[1] = region[1].transpose(Image.FLIP_TOP_BOTTOM)

    region[2] = region[2].transpose(Image.FLIP_LEFT_RIGHT)

    region[3] = region[3].transpose(Image.FLIP_TOP_BOTTOM)
    region[3] = region[3].transpose(Image.FLIP_LEFT_RIGHT)

    img.paste(region[0], (0, 0, sz[0], sz[1]))
    img.paste(region[1], (0, sz[1], sz[0], sz[1] * 2))
    img.paste(region[2], (sz[0], 0, sz[0] * 2, sz[1]))
    img.paste(region[3], (sz[0], sz[1], sz[0] * 2, sz[1] * 2))
    img.save(outImg)


def main():
    from arcpy import ExecuteError, GetMessages, CheckOutExtension, CheckExtension, CheckInExtension

    class LicenseError(Exception):
        pass

    try:
        if CheckExtension("ImageAnalyst") == "Available":
            CheckOutExtension("ImageAnalyst")
        else:
            # raise a custom exception
            raise LicenseError

        seamless_texture(inImg, outImg)
        CheckInExtension("ImageAnalyst")
    except LicenseError:
        print("Image Analyst license is unavailable")
    except ExecuteError:
        print(GetMessages(2))


if __name__ == '__main__':
    debug = False
    if debug:
        inImg = r'..\Textures\Unprocessed\sand3.jpg'
        outImg = r'..\Textures\Processed\sand3.jpg'
    else:
        from arcpy import GetParameterAsText
        inImg = GetParameterAsText(0)
        outImg = GetParameterAsText(1)
    main()
