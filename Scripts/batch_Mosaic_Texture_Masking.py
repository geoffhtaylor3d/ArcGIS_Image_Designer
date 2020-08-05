# ----------------------------------------------------------------------------------------------------
# Name:        batch_mosaic_texture_masking.py
# Purpose:     Batch Processing Solution for:
#              Process for applying Seamless Textures to polygon masked areas across mosaic datasets
# Authors:     Geoff Taylor | Solution Engineer | Imagery & Remote Sensing
# Created:     08/04/2020
# Copyright:   (c) Esri 2020
# Licence:     Apache Version 2.0
# -----------------------------------------------------------------------------------------------------

from os import path, makedirs
from Mosaic_Texture_Masking import texture_images, get_images_and_stats


def main():
    from arcpy import CheckExtension, CheckOutExtension, CheckInExtension, ExecuteError, GetMessages, AddError,\
        ListDatasets, env, SetProgressor, SetProgressorLabel, SetProgressorPosition, ResetProgressor, Exists
    from arcpy.management import CreateFileGDB, CreateMosaicDataset, AddRastersToMosaicDataset
    from arcpy import Describe
    from os.path import join, exists
    from os import mkdir, makedirs

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
            AddError("PILLOW Library Not Detected. Install using Python Manager in ArcGIS Pro")
            print("PILLOW Library Not Detected. Install using Python Manager in ArcGIS Pro")
            exit()


        env.workspace = in_mosaic_gdb
        mosaics = ListDatasets("*", "Mosaic")
        file_count = len(mosaics)
        count = 0
        SetProgressor("step", "Begin Processing Files...", 0, file_count, 1)
        if not exists(out_folder):
            makedirs(out_folder)
        fileGDB = join(out_folder, "ortho_mosaics.gdb")
        if not Exists(fileGDB):
            CreateFileGDB(out_folder, "ortho_mosaics.gdb")
        for mosaic in mosaics:
            print("processing mosaic {0} of {1}".format(count+1, file_count))
            in_mosaic = join(in_mosaic_gdb, mosaic)
            i_list, extent = get_images_and_stats(in_mosaic)  # Obtain image statistics and info from mosaic for processing
            for i in i_list:  # Check that output folder is not the path of i
                if out_folder == path.dirname(i[0]):
                    AddError("outFolder cannot be the same folder/directory as images referenced in the mosaic dataset")
                    exit()
            if not path.exists(out_folder):
                makedirs(out_folder)
            out_tile_folder = join(out_folder, "tiles{}".format(count))
            mkdir(out_tile_folder)
            SetProgressorLabel("Texturing Mosaic {0}...".format(count))
            texture_images(i_list, extent, in_texture, in_polygon, out_tile_folder, method, blur_distance)  # Generate Texture-Masked tiles

            mosaic_name = "tiles{}_".format(count)
            mosaic_dataset = join(fileGDB, mosaic_name)
            SetProgressorLabel("Creating Mosaic Dataset for Tiles of {0}...".format(mosaic))
            sr = Describe(in_mosaic).spatialReference
            CreateMosaicDataset(fileGDB, mosaic_name, sr, num_bands, pixel_depth, product_definition, product_band_definitions)
            SetProgressorLabel("Adding of {0} to Mosaic Dataset...".format(mosaic))
            AddRastersToMosaicDataset(mosaic_dataset, "Raster Dataset", out_tile_folder, "UPDATE_CELL_SIZES",
                                      "UPDATE_BOUNDARY",
                                      "NO_OVERVIEWS", None, 0, 1500, None, '', "SUBFOLDERS", "ALLOW_DUPLICATES",
                                      "NO_PYRAMIDS", "NO_STATISTICS", "NO_THUMBNAILS", '', "NO_FORCE_SPATIAL_REFERENCE",
                                      "NO_STATISTICS", None, "NO_PIXEL_CACHE")
            SetProgressorPosition()
            count += 1
        ResetProgressor()
        CheckInExtension("ImageAnalyst")
    except LicenseError:
        AddError("Image Analyst license is unavailable")
        print("Image Analyst license is unavailable")
    except ExecuteError:
        print(GetMessages(2))


if __name__ == "__main__":
    debug = False
    if debug:
        in_mosaic_gdb = r'C:\Users\geof7015\Documents\ArcGIS\Projects\ArcGIS_Image_Designer\test\ortho_mosaic.gdb'
        in_texture = r'C:\Users\geof7015\Documents\ArcGIS\Projects\ArcGIS_Image_Designer\Textures\Processed\dune_vegetation_seamless.jpg'
        in_polygon = r'C:\Users\geof7015\Documents\ArcGIS\Projects\ArcGIS_Image_Designer\Galveston\Data\Esri_Processed\Dune_Outline.gdb\Galveston_Dune_Grass_Polys_Projected'
        out_folder = r'C:\Users\geof7015\Documents\ArcGIS\Projects\ArcGIS_Image_Designer\scratch_dunes'
        method = "GaussianBlur"  # "GaussianBlur", "BoxBlur", "None"
        blur_distance = 2  # Distance in Pixels
        pixel_depth = "8_BIT_UNSIGNED"
        num_bands = 3
        product_definition = "NATURAL_COLOR_RGB"
        product_band_definitions = "Red 630 690;Green 530 570;Blue 440 510"
    else:
        from arcpy import GetParameterAsText, GetParameter
        in_mosaic_gdb = GetParameterAsText(0)
        in_texture = GetParameterAsText(1)
        in_polygon = GetParameterAsText(2)
        out_folder = GetParameterAsText(3)
        method = GetParameterAsText(4)  # "GaussianBlur", "BoxBlur", "None"
        blur_distance = GetParameter(5)  # Distance in Pixels
        pixel_depth = GetParameterAsText(6)
        num_bands = GetParameter(7)
        product_definition = GetParameterAsText(8)
        product_band_definitions = GetParameterAsText(9)
    main()
