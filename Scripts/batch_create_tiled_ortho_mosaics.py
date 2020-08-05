# ----------------------------------------------------------------------------------------------------
# Name:        batch_create_tiled_ortho_mosaics.py
# Purpose:     Batch Processing Solution for:
#              Process for applying Seamless Textures to polygon masked areas across mosaic datasets
# Authors:     Geoff Taylor | Solution Engineer | Imagery & Remote Sensing
# Created:     08/04/2020
# Copyright:   (c) Esri 2020
# Licence:     Apache Version 2.0
# -----------------------------------------------------------------------------------------------------


def batch_create_tiled_ortho_mosaics(in_folder, image_format, num_bands, pixel_depth, product_definition,
                                     product_band_definitions, pixel_size, out_folder):
    from arcpy.management import CreateMosaicDataset, AddRastersToMosaicDataset, SplitRaster, CreateFileGDB, Delete
    from arcpy import Describe, env
    from arcpy import SetProgressor, SetProgressorLabel, SetProgressorPosition, ResetProgressor
    from os.path import join, exists
    from os import listdir, mkdir, makedirs

    env.overwriteOutput = True

    if not exists(out_folder):
        makedirs(out_folder)

    CreateFileGDB(out_folder, "scratch_mosaics.gdb")
    scratchGDB = join(out_folder, "scratch_mosaics.gdb")
    CreateFileGDB(out_folder, "ortho_mosaics.gdb")
    fileGDB = join(out_folder, "ortho_mosaics.gdb")
    count = 0
    images = [f for f in listdir(in_folder) if f.lower().endswith(image_format.lower())]
    num_images = len(images)
    SetProgressor("step", "Begin Processing Files...", 0, num_images, 1)
    for fileName in images:
        print("processing Image {0} of {1}".format(count, num_images))
        file = join(in_folder, fileName)
        sr = Describe(file).spatialReference
        Name = "mosaic{}".format(count)
        SetProgressorLabel("Creating Mosaic Dataset for {0}...".format(fileName))
        CreateMosaicDataset(scratchGDB, Name, sr, num_bands, pixel_depth, product_definition, product_band_definitions)
        mosaic_dataset = join(scratchGDB, Name)
        SetProgressorLabel("Adding Rasters to Mosaic Dataset for {0}...".format(fileName))
        AddRastersToMosaicDataset(mosaic_dataset, "Raster Dataset", file, "UPDATE_CELL_SIZES", "UPDATE_BOUNDARY",
                                  "NO_OVERVIEWS", None, 0, 1500, None, '', "SUBFOLDERS", "ALLOW_DUPLICATES",
                                  "NO_PYRAMIDS", "NO_STATISTICS", "NO_THUMBNAILS", '', "NO_FORCE_SPATIAL_REFERENCE",
                                  "NO_STATISTICS", None, "NO_PIXEL_CACHE")
        out_tile_folder = join(out_folder, "tiles{}".format(count))
        mkdir(out_tile_folder)
        SetProgressorLabel("Splitting Rasters into Small Tiles for {0}...".format(fileName))
        SplitRaster(mosaic_dataset, out_tile_folder, "tile", "SIZE_OF_TILE", "JPEG", "NEAREST", "1 1",
                    "{0} {0}".format(pixel_size), 0, "PIXELS", None, None, None, "NONE", "DEFAULT", '')
        Delete(mosaic_dataset)
        mosaic_name = "tiles{}_".format(count)
        mosaic_dataset = join(fileGDB, mosaic_name)
        SetProgressorLabel("Creating Mosaic Dataset for Tiles of {0}...".format(fileName))
        CreateMosaicDataset(fileGDB, mosaic_name, sr, num_bands, pixel_depth, product_definition,
                            product_band_definitions)
        SetProgressorLabel("Adding of {0} to Mosaic Dataset...".format(fileName))
        AddRastersToMosaicDataset(mosaic_dataset, "Raster Dataset", out_tile_folder, "UPDATE_CELL_SIZES", "UPDATE_BOUNDARY",
                                  "NO_OVERVIEWS", None, 0, 1500, None, '', "SUBFOLDERS", "ALLOW_DUPLICATES",
                                  "NO_PYRAMIDS", "NO_STATISTICS", "NO_THUMBNAILS", '', "NO_FORCE_SPATIAL_REFERENCE",
                                  "NO_STATISTICS", None, "NO_PIXEL_CACHE")
        SetProgressorPosition()
        count += 1
    Delete(scratchGDB)
    ResetProgressor()


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

        batch_create_tiled_ortho_mosaics(in_folder, image_format, num_bands, pixel_depth, product_definition,
                                         product_band_definitions, pixel_size, out_folder)

        CheckInExtension("ImageAnalyst")
    except LicenseError:
        AddError("Image Analyst license is unavailable")
        print("Image Analyst license is unavailable")
    except ExecuteError:
        print(GetMessages(2))


if __name__ == "__main__":
    debug = False
    if debug:
        in_folder = r'C:\Users\geof7015\Documents\ArcGIS\Projects\ArcGIS_Image_Designer\Galveston\Data\NAIP'
        image_format = "jp2"
        pixel_depth = "8_BIT_UNSIGNED"
        num_bands = 3
        product_definition = "NATURAL_COLOR_RGB"
        product_band_definitions = "Red 630 690;Green 530 570;Blue 440 510"
        pixel_size = 1000
        out_folder = r'C:\Users\geof7015\Documents\ArcGIS\Projects\ArcGIS_Image_Designer\scratch'
    else:
        from arcpy import GetParameterAsText, GetParameter
        in_folder = GetParameterAsText(0)
        image_format = GetParameterAsText(1)
        pixel_depth = GetParameterAsText(2)
        num_bands = GetParameter(3)
        product_definition = GetParameterAsText(4)
        product_band_definitions = GetParameterAsText(5)
        pixel_size = GetParameter(6)
        out_folder = GetParameterAsText(7)
        from arcpy import AddMessage
        for m in [in_folder, image_format, pixel_depth, num_bands, product_definition, product_band_definitions, pixel_size, out_folder]:
            AddMessage(m)
    main()
