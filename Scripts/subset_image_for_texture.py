# ----------------------------------------------------------------------------------------------------
# Name:        subset_image_for_texture.py
# Purpose:     Process for subsetting an portion of an interest for generating seamless texturemap from ortho
#              - TextureMap must be same size (x/y) as Image Tile
# Authors:     Geoff Taylor | Solution Engineer | Imagery & Remote Sensing
# Created:     06/05/2020
# Copyright:   (c) Esri 2020
# Licence:     Apache Version 2.0
# -----------------------------------------------------------------------------------------------------

from arcpy.management import Clip as ClipRaster


def subset_image(in_raster, area, out_raster):
    from arcpy import Describe
    from math import sqrt
    desc = Describe(in_raster)
    XMin = desc.extent.XMin
    YMin = desc.extent.YMin
    len = sqrt(area)
    clipping_extent = '{0} {1} {2} {3}'.format(XMin, YMin, XMin+len, YMin+len)
    ClipRaster(in_raster, clipping_extent, out_raster, "#", "#", "NONE")


def image_extent_2(in_polygon):
    from arcpy import Describe
    desc = Describe(in_polygon)
    return '{0} {1} {2} {3}'.format(desc.extent.XMin, desc.extent.YMin, desc.extent.XMax, desc.extent.YMax)


def subset_image_for_texture(in_image, in_polygon, area, out_raster):
    from os import path
    from arcpy import Describe, AddWarning
    from arcpy.management import Delete
    from math import sqrt
    temp_rast = path.join("in_memory", "temp_rast")
    ClipRaster(in_image, image_extent_2(in_polygon), temp_rast, "#", "#", "NONE")
    desc = Describe(temp_rast).children[0]
    height = desc.height
    width = desc.width
    cell_height = desc.meancell_height
    cell_width = desc.meancell_width
    r_length = height*cell_height
    r_width = width*cell_width
    if r_length > sqrt(area) and r_width > sqrt(area):
        subset_image(temp_rast, area, out_raster)
    else:
        AddWarning("Geometry Length and Width do not fit Area| Length = {0} | Width = {1}".format(r_length, r_width))
        AddWarning("Draw a larger area where length and width fit within the area as a square")
    Delete(temp_rast)


def main():
    from arcpy import CheckExtension, CheckOutExtension, CheckInExtension, ExecuteError, GetMessages

    class LicenseError(Exception):
        pass

    try:
        if CheckExtension("ImageAnalyst") == "Available":
            CheckOutExtension("ImageAnalyst")
        else:
            # raise a custom exception
            raise LicenseError
        subset_image_for_texture(in_image, in_polygon, area, out_image)
        CheckInExtension("ImageAnalyst")
    except LicenseError:
        print("Image Analyst license is unavailable")
    except ExecuteError:
        print(GetMessages(2))


if __name__ == "__main__":
    debug = False
    if debug:
        in_image = r'C:\Users\geof7015\Documents\ArcGIS\Projects\ArcGIS_Image_Designer\TestData\imgFolder\Ortho.jpg'
        in_polygon = r'C:\Users\geof7015\Documents\ArcGIS\Projects\ArcGIS_Image_Designer\ArcGIS_Image_Designer.gdb\subset_polygon'
        area = 400
        out_image = r'C:\Users\geof7015\Documents\ArcGIS\Projects\ArcGIS_Image_Designer\Textures\Unprocessed\test.jpg'
    else:
        from arcpy import GetParameterAsText, GetParameter
        in_image = GetParameterAsText(0)
        in_polygon = GetParameterAsText(1)
        area = GetParameter(2)
        out_image = GetParameterAsText(3)
    main()
