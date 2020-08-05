# ----------------------------------------------------------------------------------------------------
# Name:        mosaic_texture_masking.py
# Purpose:     Process for applying Seamless Textures to polygon masked areas across mosaic datasets
# Authors:     Geoff Taylor | Solution Engineer | Imagery & Remote Sensing
# Created:     08/04/2020
# Copyright:   (c) Esri 2020
# Licence:     Apache Version 2.0
# -----------------------------------------------------------------------------------------------------

from arcpy import Describe
from arcpy.management import ExportMosaicDatasetPaths, Delete
from os import path, makedirs
from arcpy import da


def texture_images(i_list, extent, in_texture, in_polygon, out_folder, method, blur_distance):
    max_height = max(i_list, key=lambda x: x[5])[5]
    max_width = max(i_list, key=lambda x: x[6])[6]
    for i in i_list:
        # TODO: Migrate to support multiple cores for faster processing time
        out_raster = path.join(out_folder, path.splitext(path.basename(i[0]))[0] + "_design.jpg")
        texture_image(i[0], i[5], i[6], i[7], max_height, max_width, in_texture, in_polygon, out_raster, method,
                      blur_distance)


def texture_image(in_image, height, width, position, max_height, max_width, in_texture, in_polygon, out_raster, method,
                  blur_distance):
    from create_mask import create_mask
    from fill_masked_image import mask_image
    from arcpy.management import BuildPyramids
    from pathlib import Path
    from PIL import Image

    # Convert the Modified polygon that now covers entire extent of Interest to Raster
    temp_mask_raster = path.join(path.dirname(out_raster), Path(out_raster).stem + "_mask.jpg")
    create_mask(in_image, in_polygon, temp_mask_raster)

    #################################
    # Apply Texture Map to Image
    ###############################
    # Prep Texture for process... Align
    def get_clip_ext(position):
        if position == "bl":
            return max_width-width, max_height-height, width, height
        if position == "tl":
            return max_width - width, max_height-height, width, height
        if position == "tr":
            return 0, max_height-height, width, max_height
        if position is "br":
            return 0, max_height - height, width, height
        if position == "l":
            return max_width - width, 0, width, height
        if position == "t":
            return 0, max_height-height, width, max_height
        if position == "r":
            return 0, 0, width, height
        if position == "b":
            return 0, max_height - height, width, height
        if position == "i":
            return 0, 0, width, height

    texture = Image.open(in_texture).resize((max_width, max_height), Image.ANTIALIAS)
    texture_cropped = texture.crop(get_clip_ext(position))

    mask_image(in_image,
               temp_mask_raster,
               texture_cropped,
               out_raster,
               method,
               blur_distance)
    BuildPyramids(out_raster, -1, "NONE", "NEAREST", "DEFAULT", 75, "OVERWRITE")
    Delete(temp_mask_raster)  # Delete Intermediate Data


def get_image_paths(in_mosaic):
    temp_image_table = path.join("in_memory", "temp_image_table")
    ExportMosaicDatasetPaths(in_mosaic, temp_image_table, '', "ALL", "RASTER;ITEM_CACHE")
    images = set([row[0] for row in da.SearchCursor(temp_image_table, "Path")])
    Delete(temp_image_table)
    return images


def get_images_and_stats(in_mosaic):
    images = get_image_paths(in_mosaic)
    s_list = []
    if isinstance(images, str):  # If input is single image set as list
        images = [images]
    # Obtain Extent Coords of each image
    for i in images:
        if i.lower().endswith('.jpg'):
            desc = Describe(i+"/Band_1")
            s_list.append([i, desc.extent.XMin, desc.extent.XMax, desc.extent.YMin, desc.extent.YMax, desc.height,
                           desc.width])
        else:
            if ".Overviews" not in i:
                desc = Describe(i)
                from arcpy import RasterToNumPyArray
                arr = RasterToNumPyArray(i+"/Blue", nodata_to_value=0)
                height, width = arr.shape
                s_list.append([i, desc.extent.XMin, desc.extent.XMax, desc.extent.YMin, desc.extent.YMax, height,
                               width])
                del arr
    # Determine Maximum and Minimum coord values from list
    # -- Note: The extent values from the mosaic differ from the actual tiles... esri bug on mosaics probably.
    XMin = min(s_list, key=lambda x: x[1])[1]
    XMax = max(s_list, key=lambda x: x[2])[2]
    YMin = min(s_list, key=lambda x: x[3])[3]
    YMax = max(s_list, key=lambda x: x[4])[4]
    extent = [XMin, XMax, YMin, YMax]
    # Detect of each image within the mosaic dataset
    c = 0
    for i in s_list:
        iXMin = i[1]
        iXMax = i[2]
        iYMin = i[3]
        iYMax = i[4]
        # Check for Corners
        if XMin == iXMin and YMin == iYMin:
            s_list[c].append("bl")
        elif XMin == iXMin and YMax == iYMax:
            s_list[c].append("tl")
        elif XMax == iXMax and YMax == iYMax:
            s_list[c].append("tr")
        elif XMax == iXMax and YMin == iYMin:
            s_list[c].append("br")
        # Check for Edges
        elif XMin == iXMin:
            s_list[c].append("l")
        elif YMax == iYMax:
            s_list[c].append("t")
        elif XMax == iXMax:
            s_list[c].append("r")
        elif YMin == iYMin:
            s_list[c].append("b")
        else:
            s_list[c].append("i")
        c += 1
    return s_list, extent


def main():
    from arcpy import CheckExtension, CheckOutExtension, CheckInExtension, ExecuteError, GetMessages, AddError

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
        i_list, extent = get_images_and_stats(in_mosaic)  # Obtain image statistics and info from mosaic for processing
        for i in i_list:  # Check that output folder is not the path of i
            if out_folder == path.dirname(i[0]):
                AddError("outFolder cannot be the same folder/directory as images referenced in the mosaic dataset")
                exit()
        if not path.exists(out_folder):
            makedirs(out_folder)
        texture_images(i_list, extent, in_texture, in_polygon, out_folder, method, blur_distance)  # Generate Texture-Masked tiles

        CheckInExtension("ImageAnalyst")
    except LicenseError:
        AddError("Image Analyst license is unavailable")
        print("Image Analyst license is unavailable")
    except ExecuteError:
        print(GetMessages(2))


if __name__ == "__main__":
    debug = False
    if debug:
        in_mosaic = r'C:\Users\geof7015\Documents\ArcGIS\Projects\ArcGIS_Image_Designer\test\ortho_mosaic.gdb\tile_27_test'
        in_texture = r'C:\Users\geof7015\Documents\ArcGIS\Projects\ArcGIS_Image_Designer\Textures\Processed\dune_vegetation_seamless.jpg'
        in_polygon = r'C:\Users\geof7015\Documents\ArcGIS\Projects\ArcGIS_Image_Designer\Galveston\Data\Esri_Processed\Dune_Outline.gdb\Galveston_Dune_Grass_Polys_Projected'
        out_folder = r'C:\Users\geof7015\Documents\ArcGIS\Projects\ArcGIS_Image_Designer\test\tile_dune'
        method = "GaussianBlur"  # "GaussianBlur", "BoxBlur", "None"
        blur_distance = 5  # Distance in Pixels
    else:
        from arcpy import GetParameterAsText, GetParameter
        in_mosaic = GetParameterAsText(0)
        in_texture = GetParameterAsText(1)
        in_polygon = GetParameterAsText(2)
        out_folder = GetParameterAsText(3)
        method = GetParameterAsText(4)  # "GaussianBlur", "BoxBlur", "None"
        blur_distance = GetParameter(5)  # Distance in Pixels
    main()
