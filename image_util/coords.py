from osgeo import gdal, osr

def get_geotiff_bounds(file_path):
    # Open the dataset
    ds = gdal.Open(file_path)
    if ds is None:
        print('Could not open file')
        return

    # Get the source projection
    source_proj = osr.SpatialReference()
    source_proj.ImportFromWkt(ds.GetProjection())

    # Create the destination projection (WGS84)
    target_proj = osr.SpatialReference()
    target_proj.ImportFromEPSG(4326)

    # Create a coordinate transformation
    transform = osr.CoordinateTransformation(source_proj, target_proj)

    # Get the geotransform
    gt = ds.GetGeoTransform()

    # Get the dimensions
    width = ds.RasterXSize
    height = ds.RasterYSize

    # Get the corner coordinates in the source projection
    ulx, uly = gt[0], gt[3]
    lrx, lry = gt[0] + width*gt[1], gt[3] + height*gt[5]

    # Transform the corner coordinates to the destination projection
    ul_lon, ul_lat, _ = transform.TransformPoint(ulx, uly)
    lr_lon, lr_lat, _ = transform.TransformPoint(lrx, lry)

    return ul_lon, ul_lat, lr_lon, lr_lat

if __name__ == "__main__":
    file_path = '../image_data/image.tif'  # Replace with your file path
    ul_lon, ul_lat, lr_lon, lr_lat = get_geotiff_bounds(file_path)
    print(f'Upper Left: ({ul_lon}, {ul_lat})')
    print(f'Lower Right: ({lr_lon}, {lr_lat})')