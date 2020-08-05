# ----------------------------------------------------------------------------------------------------
# Name:        create_mask.py
# Purpose:     Process for creating RGB raster masks from polygons
# Authors:     Geoff Taylor | Solution Engineer | Imagery & Remote Sensing
# Created:     07/21/2020
# Copyright:   (c) Esri 2020
# Licence:     Apache Version 2.0
# -----------------------------------------------------------------------------------------------------


def raster_extent_polygon(in_raster):
    from arcpy import Array, Point, Polygon, Describe
    desc = Describe(in_raster)
    XMin = desc.extent.XMin
    XMax = desc.extent.XMax
    YMin = desc.extent.YMin
    YMax = desc.extent.YMax
    # Create a polygon geometry
    array = Array([Point(XMin, YMin),
                   Point(XMin, YMax),
                   Point(XMax, YMax),
                   Point(XMax, YMin)
                   ])
    return Polygon(array)


def image_extent(in_raster):
    from arcpy import Describe
    desc = Describe(in_raster)
    return "{0}, {1}, {2}, {3}".format(desc.extent.XMin, desc.extent.YMin, desc.extent.XMax, desc.extent.YMax)


def image_extent_2(in_raster):
    from arcpy import Describe
    desc = Describe(in_raster)
    return '{0} {1} {2} {3}'.format(desc.extent.XMin, desc.extent.YMin, desc.extent.XMax, desc.extent.YMax)


def generate_squares(in_polygon, in_raster):
    from arcpy import Describe, Array, Point, Polygon, da
    desc = Describe(in_raster)
    eXMin = desc.extent.XMin
    eYMin = desc.extent.YMin
    eXMax = desc.extent.XMax
    eYMax = desc.extent.YMax

    offset = 1
    sqLen = 1
    # Store extent values as list of coordinate
    blX = eXMin - offset
    blY = eYMin - offset
    bottom_left_square = Array([Point(blX-sqLen, blY-sqLen),
                                Point(blX-sqLen, blY),
                                Point(blX, blY),
                                Point(blX, blY-sqLen)])
    trX = eXMax + offset
    trY = eYMax + offset
    top_right_square = Array([Point(trX, trY),
                              Point(trX, trY+sqLen),
                              Point(trX+sqLen, trY+sqLen),
                              Point(trX+sqLen, trY)])
    # Get coordinate system
    # Open an InsertCursor and insert the new geometry
    cursor = da.InsertCursor(in_polygon, ['SHAPE@'])
    for sq in [bottom_left_square, top_right_square]:
        # Create a polygon geometry
        polygon = Polygon(sq)
        cursor.insertRow([polygon])
    # Delete cursor object
    del cursor


def create_mask(in_raster, in_polygon, out_raster):
    from os import path
    from arcpy import env, EnvManager, ResetEnvironments, AddError
    from arcpy.ia import Con, IsNull
    from arcpy.management import Delete, CopyRaster, GetCount, Clip as ClipRaster, GetRasterProperties
    from arcpy.conversion import PolygonToRaster
    from arcpy.analysis import Clip
    env.overwriteOutput = True

    # Clip raster and apply geometries at Bottom-left ant top-right corners to ensure Raster covers Ortho tile extent
    polygon_clipped = path.join("in_memory", "polygon_clipped")
    Clip(in_polygon, raster_extent_polygon(in_raster), polygon_clipped)
    generate_squares(polygon_clipped, in_raster)

    def is_masked(in_polygon):
        if int(GetCount(in_polygon)[0]) == 1:
            return True, int(GetCount(in_polygon)[0])
        if int(GetCount(in_polygon)[0]) == 2:
            return False, int(GetCount(in_polygon)[0])
        if int(GetCount(in_polygon)[0]) > 2:
            return True, int(GetCount(in_polygon)[0])

    _is_masked = is_masked(polygon_clipped)
    # Set the Environment Extent to the extent of the Ortho-Image as well as other settings to align.
    EnvManager(cellSize=in_raster, extent=image_extent(in_raster), snapRaster=in_raster)  # , mask=in_raster)
    file, extension = path.splitext(out_raster)
    # Convert the Modified polygon that now covers entire extent of Interest to Raster
    temp_raster = file + "Temp" + ".tif"
    PolygonToRaster(polygon_clipped, "OBJECTID", temp_raster, "CELL_CENTER", "", in_raster)
    Delete(polygon_clipped)
    # Clip the Polygon Raster
    temp_clip_rast = file + "TempClipped" + ".tif"
    ClipRaster(temp_raster, image_extent_2(in_raster), temp_clip_rast, in_raster, "-1", "NONE",
               "MAINTAIN_EXTENT")
    if _is_masked[0]:
        if _is_masked[1] < 4:
            mask_raster = Con(temp_clip_rast, 255, 0, "VALUE = 0")
        else:
            # Deal with Masks covering the entire image
            mask_raster = Con(IsNull(temp_clip_rast), 0, 255, "Value = 0")
            # Deal with Masks covering a corner of image
            if int(GetRasterProperties(mask_raster, "UNIQUEVALUECOUNT").getOutput(0)) < 2:
                Delete(mask_raster)
                mask_raster = Con(temp_clip_rast, 0, 255, "VALUE <= {0}".format(_is_masked[1] - 2))
    else:
        mask_raster = Con(temp_clip_rast, 255, 255, "VALUE = 0")
    temp_mask_raster = file + "TempMask" + ".tif"
    mask_raster.save(temp_mask_raster)

    ext = path.splitext(out_raster)[1]

    if "jpg" in ext.lower():
        # Convert the raster to .jpg format
        # Combine the band 3x for final output as RGB
        CopyRaster(temp_mask_raster, out_raster, '', None, '', "NONE", "ColormapToRGB", "8_BIT_UNSIGNED",
                   "NONE", "NONE", "JPEG", "NONE", "CURRENT_SLICE", "NO_TRANSPOSE")
    if "tif" in ext.lower():
        # Convert the raster to .jpg format
        # Combine the band 3x for final output as RGB
        CopyRaster(temp_mask_raster, out_raster, '', None, '', "NONE", "ColormapToRGB", "8_BIT_UNSIGNED",
                   "NONE", "NONE", "TIFF", "NONE", "CURRENT_SLICE", "NO_TRANSPOSE")
    if ext.lower() not in [".tif", ".jpg"]:
        AddError("Process Failed. Currently ony supports .jpg and .tif as output formats")
    # Delete Intermediate Data
    Delete(temp_clip_rast)
    Delete(temp_mask_raster)
    Delete(temp_raster)
    # Reset geoprocessing environment settings
    ResetEnvironments()


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

        create_mask(in_raster, in_polygon, out_raster)
        CheckInExtension("ImageAnalyst")
    except LicenseError:
        print("Image Analyst license is unavailable")
    except ExecuteError:
        print(GetMessages(2))


if __name__ == "__main__":
    debug = False
    if debug:
        in_raster = r'C:\Users\geof7015\Documents\ArcGIS\Projects\ArcGIS_Image_Designer\orthoTiled\Ortho17.JPG'
        in_polygon = r'C:\Users\geof7015\Documents\ArcGIS\Projects\ArcGIS_Image_Designer\ArcGIS_Image_Designer.gdb\Dunes'
        out_raster = r'C:\Users\geof7015\Documents\ArcGIS\Projects\ArcGIS_Image_Designer\TestData\maskFolder\Ortho17_mask.jpg'
    else:
        from arcpy import GetParameterAsText
        in_raster = GetParameterAsText(0)
        in_polygon = GetParameterAsText(1)
        out_raster = GetParameterAsText(2)
    main()
