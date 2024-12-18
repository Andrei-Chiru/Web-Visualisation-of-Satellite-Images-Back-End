from django.db import models
import rasterio as rio
import numpy as np
import glob, json, os, warnings
        
warnings.filterwarnings("ignore")

path_to_data: str = "image_data/"

path_to_originals: str = "original_images/"
path_to_images: str = "images/"
path_to_output: str = "output/"
path_to_tiles: str = "tiles/"
path_to_temp: str = "temp/"

CREATE_INPUT_INIT: str = f"{path_to_data}{path_to_originals}"
CREATE_OUTPUT_INIT: str = f"{path_to_data}{path_to_images}"
RENDER_OUTPUT_INIT: str = f"{path_to_data}{path_to_output}"
TILE_OUTPUT_INIT: str = f"{path_to_data}{path_to_tiles}"
TEMP_OUTPUT_INIT: str = f"{path_to_data}{path_to_temp}"

CREATE_INIT = False
RENDER_INIT = False
TILE_INIT = False
FORCE_RECREATE_INIT = False
FORCE_RERENDER_INIT = False

image_folder: str = ".SAFE/GRANULE/"
image_data_folder: str = "/IMG_DATA/"

tif: str = ".tif"
data_file_type: str = ".jp2"
rendered_file_type: str = ".tiff"

output_tc_naming: str = "_TC"
output_ndvi_naming: str = "_NDVI"
output_ndwi_naming: str = "_NDWI"
output_ndmi_naming: str = "_NDMI"

tif_bands: dict[str, int] = {
    "B02": 3,
    "B03": 5,
    "B04": 7,
    "B08": 9,
    "B8A": 11,
    "B11": 1,
}

colors: dict[str, int] = {
    "Red": 1,
    "Green": 2,
    "Blue": 3
}

value_max: int = 255

true_color_inc: int = 1
ndvi_inc: int = 255
ndwi_inc: int = 255
ndmi_inc: int = 255

ndvi_size_reduction: int = 4
ndwi_size_reduction: int = 4

# Create your models here.
class Environment(models.Model):
    """Environment settings for locations and execution methods
    
    Fields:
        - create        -- (Optional) If the application should create the images
        - create_input  -- (Optional) The path to the location where the input images are stored
        - create_output -- (Optional) The path to the location where the storage band data of the images will be stored
        - recreate      -- (Optional) If images should be recreated even if their band files already exist
        - render        -- (Optional) If the application should render the images
        - render_output -- (Optional) The path to the location where the output images will be stored
        - rerender      -- (Optional) If images should be rerendered even if their algorithm output files already exist
        - tile          -- (Optional) If the application should tile the images
        - tile_output   -- (Optional) The path to the location where the tiles will be stored
        - temp_output   -- (Optional) The path to the location where the temporary file, used for tiling, will be stored
    """
        
    create = models.BooleanField(default=CREATE_INIT)
    create_input = models.CharField(max_length=100, default=CREATE_INPUT_INIT)
    create_output = models.CharField(max_length=100, default=CREATE_OUTPUT_INIT)
    recreate = models.BooleanField(default=FORCE_RECREATE_INIT)
    render = models.BooleanField(default=RENDER_INIT)
    render_output = models.CharField(max_length=100, default=RENDER_OUTPUT_INIT)
    rerender = models.BooleanField(default=FORCE_RERENDER_INIT)
    tile = models.BooleanField(default=TILE_INIT)
    tile_output = models.CharField(max_length=100, default=TILE_OUTPUT_INIT)
    temp_output = models.CharField(max_length=100, default=TEMP_OUTPUT_INIT)

    def __str__(self):
        return f"[\n  create: {self.create}\n  create_input: {self.create_input}\n  create_output: {self.create_output}\n  recreate: {self.recreate}\n  render: {self.render}\n  render_output: {self.render_output}\n  rerender: {self.rerender}\n  tile: {self.tile}\n  tile_output: {self.tile_output}\n  temp_output: {self.temp_output}\n]"

class Profile(models.Model):
    driver = models.CharField(max_length=100)
    dtype = models.CharField(max_length=100)
    nodata = models.CharField(max_length=100)
    width = models.IntegerField()
    height = models.IntegerField()
    count = models.IntegerField()
    crs = models.IntegerField()
    transform = models.CharField(max_length=200)
    blockxsize = models.IntegerField()
    blockysize = models.IntegerField()
    tiled = models.BooleanField()

    def __str__(self):
        return f"[\n    driver: {self.driver}\n    dtype: {self.dtype}\n    nodata: {self.nodata}\n    width: {self.width}\n    height: {self.height}\n    count: {self.count}\n    crs: {self.crs}\n    transform: {self.transform}\n    blockxsize: {self.blockxsize}\n    blockysize: {self.blockysize}\n    tiled: {self.tiled}\n  ]"


class ProfileFactory(models.Manager):
    def create_profile(self, profile: rio.profiles.Profile) -> Profile:
        """Create a local Profile object from the rasterio Profile data

        Keyword arguments:
        - profile -- The rasterio implementation of a profile

        Returns:
        - The project specific implementation of a Profile object
        """

        result: Profile  = Profile(
            driver = "GTiff",
            dtype = profile["dtype"],
            nodata = profile["nodata"],
            width = profile["width"],
            height = profile["height"],
            count = profile["count"],
            crs = profile["crs"].to_epsg(),
            blockxsize = profile["blockxsize"],
            blockysize = profile["blockysize"],
            tiled = profile["tiled"],
        )
        
        if ("transform" in profile):
            result.transform = json.dumps(profile["transform"])         # Dumping transform data to be able to fetch back to Affine
            
        return result

    def get_rio_profile(self, profile: Profile) -> rio.profiles.Profile:
        """Get the rasterio Profile object from the project specific Profile object

        Keyword arguments:
        - profile -- The project specific implementation of the Profile object

        Returns:
        - The rasterio implementation of a Profile object
        """

        result: rio.profiles.Profile = rio.profiles.Profile(
            driver=profile.driver,
            dtype = profile.dtype,
            nodata = profile.nodata,
            width = profile.width,
            height = profile.height,
            count = profile.count,
            crs = rio.crs.CRS.from_epsg(profile.crs),
            blockxsize = profile.blockxsize,
            blockysize = profile.blockysize,
            tiled = profile.tiled,
        )
        
        if (profile.transform):
            vals: list[int] = json.loads(profile.transform)
            result["transform"] = rio.Affine(vals[0], vals[1], vals[2], vals[3], vals[4], vals[5])      # Transform back to Affine
            
        return result


class ImageManager(models.Manager):

    def load(self, path: str) -> np.ndarray:
       """Load the data file at the given path

        Keyword arguments:
        - path -- The path where the data can be found

        Returns:
        - The loaded data
        """
       
       # Mainly moved to separate method so any future changes in loading can be handled here

       return rio.open(path).read(1)

    def create_true_color(self, image, environment: Environment = Environment()) -> str:
        """Render the True-Color visualization of the given image

        Keyword arguments:
        - image       -- The Image Model for which the True-Color image should be rendered
        - environment -- (Optional) Environment object with any changes in execution logic of the application (see Environment docs.)

        Returns:
        - Path to the True-Color generated rendered .tiff image
        """

        try:        # self.load(_) is able to raise an Exception
            if not os.path.exists(f"{environment.render_output}"):   # If the output folder does not exist yet, create it
                os.makedirs(f"{environment.render_output}")
                print(f"\nLOGGER: The folder {environment.render_output} has been created where the algorithm rendered images will be stored")

            image_path: str = f"{environment.render_output}{image.title}{output_tc_naming}{rendered_file_type}"

            if environment.rerender or not os.path.isfile(image_path):             # If we are forcefully recreating, create file regardless, if not, check if file already exists
            
                profile: rio.profiles.Profile = ProfileFactory().get_rio_profile(image.profile) # Fetching the data profile to use when opening the to-be-created image
                profile.update({"count": 3})                                                    # Update the profile to use 3 bands, introducing RGB format
                profile.update({"dtype": rio.dtypes.uint8})

                b4: np.ndarray = np.clip(self.load(image.b4) * true_color_inc, 0, value_max)           # Red band
                b3: np.ndarray = np.clip(self.load(image.b3) * true_color_inc, 0, value_max)           # Green band
                b2: np.ndarray = np.clip(self.load(image.b2) * true_color_inc, 0, value_max)           # Blue band
                with rio.open(image_path, 'w', **profile) as rgb:
                    rgb.write(b4, colors["Red"])          # Write all bands to the file. Multiplication by the True Color Increase used for higher vibrancy
                    rgb.write(b3, colors["Green"]) 
                    rgb.write(b2, colors["Blue"])
                    rgb.close()
            
            return image_path         # Return the name of the generated file
            
        except Exception as e:  # If any self.load(_) raises an exception it will be catched
            print(f"\nEXCEPTION: {e}")            # And it is reported.
            return None         # The method is required to return a string, as such after an Exception it will return None       
        

    def create_NDVI(self, image, environment: Environment = Environment()) -> str:
        """Render the NDVI visualization of the given image

        Keyword arguments:
        - image       -- The Image Model for which the NDVI image should be rendered
        - environment -- (Optional) Environment object with any changes in execution logic of the application (see Environment docs.)

        Returns:
        - Path to the NDVI generated rendered .tiff image
        """

        try:        # self.load(_) is able to raise an Exception 
            if not os.path.exists(f"{environment.render_output}"):       # If the output folder does not exist yet, create it
                os.makedirs(f"{environment.render_output}")
                print(f"\nLOGGER: The folder {environment.render_output} has been created where the algorithm rendered images will be stored")

            image_path: str = f"{environment.render_output}{image.title}{output_ndvi_naming}{rendered_file_type}"

            if environment.rerender or not os.path.isfile(image_path):                 # If we are forcefully recreating, create file regardless, if not, check if file already exists
                b4: np.ndarray = self.load(image.b4).astype('float64')      # Red band
                b8: np.ndarray = self.load(image.b8).astype('float64')      # Nir band

                ndvi: np.ndarray = np.where(b4 + b8 == 0., 0, ((b8 - b4) / (b8 + b4)))                      # Calculate the NDVI values
                #small_ndvi: np.ndarray = (ndvi[::ndvi_size_reduction, ::ndvi_size_reduction] + 1) / 2      # Reducing size of the NDVI images in relation to the resolution of the other algorithms (deprecated)
                                                                                                            # Since the tiff will be using int and the values are stored as floats [-1, 1],
                ndvi: np.ndarray = (ndvi + 1) / 2                                                    # conversion is done by adding 1 and dividing by 2

                profile: rio.profiles.Profile = ProfileFactory().get_rio_profile(image.profile)             # Fetching the data profile to use when opening the to-be-created image
                # profile.update({'width': b4.width//ndvi_size_reduction})      # Update the profile to use the correct sizing
                # profile.update({'height': b4.height//ndvi_size_reduction})
                profile.update({'count': 3})                                    # 3 bands for RGB, using only the Green band
                profile.update({"dtype": rio.dtypes.uint8})

                with rio.open(image_path, 'w', **profile) as img:
                    img.write(np.clip(ndvi * ndvi_inc, 0, value_max), colors["Green"])           # Write the NDVI data to the file. Multiplication by the NDVI Increase used for higher vibrancy
                    img.close()
                    
            return image_path   # Return the name of the generated file
            
        except Exception as e:  # If any self.load(_) raises an exception it will be catched
            print(f"\nEXCEPTION: {e}")            # And it is reported.
            return None         # The method is required to return a string, as such after an Exception it will return None
        
        
    def create_NDWI(self, image, environment: Environment = Environment()) -> str:
        """Render the NDWI visualization of the given image

        Keyword arguments:
        - image       -- The Image Model for which the NDWI image should be rendered
        - environment -- (Optional) Environment object with any changes in execution logic of the application (see Environment docs.)

        Returns:
        - Path to the NDWI generated rendered .tiff image
        """

        try:        # self.load(_) is able to raise an Exception 
            if not os.path.exists(f"{environment.render_output}"):       # If the output folder does not exist yet, create it
                os.makedirs(f"{environment.render_output}")
                print(f"\nLOGGER: The folder {environment.render_output} has been created where the algorithm rendered images will be stored")

            image_path: str = f"{environment.render_output}{image.title}{output_ndwi_naming}{rendered_file_type}"

            if environment.rerender or not os.path.isfile(image_path):                 # If we are forcefully recreating, create file regardless, if not, check if file already exists
                b3: np.ndarray = self.load(image.b3).astype('float64')      # Green band
                b8: np.ndarray = self.load(image.b8).astype('float64')      # Nir band

                ndwi: np.ndarray = np.where(b3 + b8 == 0., 0, ((b3 - b8) / (b3 + b8)))                      # Calculate the NDWI values
                # small_ndwi: np.ndarray = (ndwi[::ndwi_size_reduction, ::ndwi_size_reduction] + 1) / 2     # Reducing size of the NDWI images in relation to the resolution of the other algorithms (deprecated)
                                                                                                            # Since the tiff will be using int and the values are stored as floats [-1, 1],
                ndwi: np.ndarray = (ndwi + 1) / 2                                                     # conversion is done by adding 1 and dividing by 2

                profile: rio.profiles.Profile = ProfileFactory().get_rio_profile(image.profile)             # Fetching the data profile to use when opening the to-be-created image
                # profile.update({'width': b3.width//ndwi_size_reduction})      # Update the profile to use the correct sizing
                # profile.update({'height': b3.height//ndwi_size_reduction})
                profile.update({'count': 3})                                    # 3 bands for RGB, using only the Blue coloring
                profile.update({"dtype": rio.dtypes.uint8})

                with rio.open(image_path, 'w', **profile) as img:
                    img.write(np.clip(ndwi * ndwi_inc, 0, value_max), colors["Blue"])           # Write the NDWI data to the file. Multiplication by the NDWI Increase used for higher vibrancy
                    img.close()

            return image_path   # Return the name of the generated file
            
        except Exception as e:  # If any self.load(_) raises an exception it will be catched
            print(f"\nEXCEPTION: {e}")            # And it is reported.
            return None         # The method is required to return a string, as such after an Exception it will return None

        
    def create_NDMI(self, image, environment: Environment = Environment()) -> str:
        """Render the NDMI visualization of the given image

        Keyword arguments:
        - image       -- The Image Model for which the NDMI image should be rendered
        - environment -- (Optional) Environment object with any changes in execution logic of the application (see Environment docs.)

        Returns:
        - Path to the NDMI generated rendered .tiff image
        """

        try:        # self.load(_) is able to raise an Exception 
            if not os.path.exists(f"{environment.render_output}"):       # If the output folder does not exist yet, create it
                os.makedirs(f"{environment.render_output}")
                print(f"\nLOGGER: The folder {environment.render_output} has been created where the algorithm rendered images will be stored")
                
            image_path: str = f"{environment.render_output}{image.title}{output_ndmi_naming}{rendered_file_type}"

            if environment.rerender or not os.path.isfile(image_path):                 # If we are forcefully recreating, create file regardless, if we are not, check if file already exists
                b8a: np.ndarray = self.load(image.b8a).astype('float64')    # Nir band
                b11: np.ndarray = self.load(image.b11).astype('float64')    # Swir band

                ndmi: np.ndarray = np.where(b11 + b8a == 0., 0, ((b8a - b11) / (b8a + b11)))      # Calculate the NDMI values
                ndmi = (ndmi + 1) / 2                                                      # Since the tiff will be using int and the values are stored as floats [-1, 1],
                                                                                                # conversion is done by adding 1 and dividing by 2

                profile: rio.profiles.Profile = ProfileFactory().get_rio_profile(image.profile)   # Fetching the data profile to use when opening the to-be-created image
                profile.update({'count': 3})                        # 3 bands for RGB, using only the Red coloring
                profile.update({"dtype": rio.dtypes.uint8})

                with rio.open(image_path, 'w', **profile) as img:
                    img.write(np.clip(ndmi * ndmi_inc, 0, value_max), colors["Red"])      # Write the NDMI data to the file. Multiplication by the NDMI Increase used for higher vibrancy
                    img.close()
                    
            return image_path   # Return the name of the generated file
            
        except Exception as e:  # If any self.load(_) raises an exception it will be catched
            print(f"\nEXCEPTION: {e}")            # And it is reported.
            return None         # The method is required to return a string, as such after an Exception it will return None      
    

class Image(models.Model):
    img_id = models.IntegerField()                  # Id of the image
    title = models.CharField(max_length=100)        # Name of the image file
    b2 = models.CharField(max_length=100)           # The paths to the band files of the image
    b3 = models.CharField(max_length=100)
    b4 = models.CharField(max_length=100)
    b8 = models.CharField(max_length=100)
    b8a = models.CharField(max_length=100)
    b11 = models.CharField(max_length=100)
    tc = models.CharField(max_length=100)           # The paths to the algorithm files of the image
    ndvi = models.CharField(max_length=100)
    ndwi = models.CharField(max_length=100)
    ndmi = models.CharField(max_length=100)
    profile = models.OneToOneField(Profile, on_delete = models.CASCADE)     # The base profile of the image
    manager = ImageManager() 

    def __str__(self):
        return f"[\n  img_id: {self.img_id}\n  title: {self.title}\n  b2: {self.b2}\n  b3: {self.b3}\n  b4: {self.b4}\n  b8: {self.b8}\n  b8a: {self.b8a}\n  b11: {self.b11}\n  tc: {self.tc}\n  ndvi: {self.ndvi}\n  ndwi: {self.ndwi}\n  ndmi: {self.ndmi}\n  profile: {self.profile}\n]"


class ImageFactory(models.Manager):
    current_id: int = 0         # Internal value to keep track of currently to be assigned ID for images

    def get_resolution_path(self, path: str, granule: str, res: str) -> str:
        """Get the path to the folder for the resolution
        in which the specific band can be found.

        Keyword arguments:
        - path    -- The path to the image for which the resolution path should be returned 
        - granule -- The granule folder name for the given image
        - res     -- The given resolution where the chosen band data can be found

        Returns:
        - Path to the specified resolution folder
        """

        # refactored to different function to account for later changes in image model and paths

        return f"{path}{image_folder}{granule}{image_data_folder}{res}/"
    
    def get_data_path(self, path: str, to_find: str) -> str:
        """Get the path to the file which contains the specific band data.

        Keyword arguments:
        - path    -- The path to the folder where the respective file can be found
        - to_find -- Band name to be found

        Returns:
        - Path to the specified band data file

        Exceptions:
        - When path does not contain a matching file or the path cannot be reached
        """

        # refactored to different function to account for later changes in paths

        matching: list[str] = glob.glob(f"{path}*{to_find}*{data_file_type}")           # Looks for files matching the regex with the fitting file name,
                                                                                        # ending in file type, normally: ".jp2"

        if not matching:        # No matching file could be found
            # raise Exception(f"\nPath does not contain matching file")
            raise Exception(f"Path [{path}] does not contain matching file containing substring [{to_find}]")
            # Removed because of printing user input

        return matching[0]      # The first found instance is the correct one
    
    def manipulate_data(self, data: np.ndarray, multiply: int, max: int) -> np.ndarray:
        """Manipulates the data to be multiplied and clipped as desired

        Keyword arguments:
        - data     -- The data which needs to be manipulated
        - multiply -- The multiplication value the data should be multiplied by
        - max      -- The maximum value which can be held in the data after manipulation

        Returns:
        - The finalized manipulated data
        """

        new_data: np.ndarray = data * multiply  # Multiplication of the data
        return np.clip(new_data, 0, max)        # Clipping the data between 0 and the specified maximum value
    
    def tif_dump_band(self, all_band_data, band: str, title: str, environment: Environment = Environment()) -> str:
        """Dump the data for the given band and the given image stored in a .tif format

        Keyword arguments:
        - all_band_data -- All band data (unread) as an opened rasterio datasource
        - band          -- Band name for which to dump the data
        - title         -- The title of the image for which the band data should be dumped
        - environment   -- (Optional) Environment object with any changes in execution logic of the application (see Environment docs.)
        
        Returns:
        - Path to the generated band data file

        Exceptions:
        - When rasterio fails to open the to-be-generated file
        """

        try:
            band_dump_path: str = f"{environment.create_output}{title}_{band}{rendered_file_type}"   # Path to the generated file

            if environment.recreate or not os.path.isfile(band_dump_path):                     # If we are forcefully recreating, create file regardless, if not, check if file already exists

                band_data: np.ndarray = all_band_data.read(tif_bands[band])         # Using dictionary lookup to read the correct band data and then manipulate it for the .tif format
                band_data = self.manipulate_data(band_data, 1000, value_max)

                profile: rio.profiles.Profile = all_band_data.profile
                profile.update({'count': 1})                                        # Generated file should only contain 1 band and as such the profile should update to incorporate only 1 band

                with rio.open(band_dump_path, 'w', **profile) as band_dump:
                    band_dump.write(band_data, 1)   # Dump the band data to the file
                    band_dump.close()
            
            return band_dump_path                   # And finally return the string path to the generated file
        
        except Exception as e:  # If opening the to-be-generated file raises an exception it will be catched
            print(f"\nEXCEPTION: {e}")            # And it is reported.
            return None         # The method is required to return a string object, as such after an Exception it will return None
    
    def safe_dump_band(self, res_path: str, band: str, title: str, environment: Environment = Environment()) -> str:
        """Dump the data for the given band and the given image stored in a .SAFE format

        Keyword arguments:
        - res_path    -- The resolution path to the folder where the band data can be found
        - band        -- Band name for which to dump the data
        - title       -- The title of the image for which the band data should be dumped
        - environment -- (Optional) Environment object with any changes in execution logic of the application (see Environment docs.)
        
        Returns:
        - Path to the generated band data file

        Exceptions:
        - When the path does not contain a matching file or the path cannot be reached
        """

        try:
            band_dump_path: str = f"{environment.create_output}{title}_{band}{rendered_file_type}"   # Path to the generated file

            if environment.recreate or not os.path.isfile(band_dump_path):                         # If we are forcefully recreating, create file regardless, if not, check if file already exists
                band_data: np.ndarray = rio.open(self.get_data_path(res_path, band))    # Open the file at the path dedicated to the specified band
                profile: rio.profiles.Profile = band_data.profile
                profile.update({'count': 1})                                            # Generated file should only contain 1 band and as such the profile should update to incorporate only 1 band

                with rio.open(band_dump_path, 'w', **profile) as band_dump:
                    band_dump.write(band_data.read(1), 1)   # Dump the band data to the file
                    band_dump.close()
                
            return band_dump_path                           # And finally return the string path to the generated file
        
        except Exception as e:  # If opening the to-be-generated file raises an exception it will be catched
            print(f"\nEXCEPTION: {e}")            # And it is reported.
            return None         # The method is required to return a string object, as such after an Exception it will return None

    def tif_create(self, title: str, environment: Environment = Environment()) -> Image:
        """Creates an Image object based on the specified file in a .tif format

        Keyword arguments:
        - title       -- The title of the .tif image which can can be found in the provided location
        - environment -- (Optional) Environment object with any changes in execution logic of the application (see Environment docs.)

        Returns:
        - The created Image object

        Exceptions:
        - When the filename or the path to the data could not be opened by rasterio
        """

        try:
            with rio.open(f"{environment.create_input}{title}{tif}") as data:     # Open all the available data
                
                if not os.path.exists(f"{environment.create_output}"):
                    os.makedirs(f"{environment.create_output}")
                    print(f"\nLOGGER: The folder {environment.create_output} has been created where the image data will be stored")

                profile: Profile = ProfileFactory().create_profile(data.profile)

                b2: str = self.tif_dump_band(data, "B02", title, environment=environment)
                b3: str = self.tif_dump_band(data, "B03", title, environment=environment)     # And dump the bands to files
                b4: str = self.tif_dump_band(data, "B04", title, environment=environment)
                b8: str = self.tif_dump_band(data, "B08", title, environment=environment)
                b8a: str = self.tif_dump_band(data, "B8A", title, environment=environment)
                b11: str = self.tif_dump_band(data, "B11", title, environment=environment)

            # Create the Image object based on the returned paths and return it
            img: Image =  Image(img_id=self.current_id, title=title, b2=b2, b3=b3, b4=b4, b8=b8, b8a=b8a, b11=b11, profile=profile)
            self.current_id += 1
            return img
        
        except Exception as e:  # If opening the given filename raises an exception it will be catched
            print(f"\nEXCEPTION: {e}")            # And it is reported.
            return None         # The method is required to return an Image object, as such after an Exception it will return None

    def safe_create(self, title: str, granule: str, environment: Environment = Environment()) -> Image:
        """Creates an Image object based on the specified file in a .SAFE format

        Keyword arguments:
        - path        -- The title of the .SAFE image data (without file extention)
        - granule     -- The name of the granule folder inside of the .SAFE data
        - environment -- (Optional) Environment object with any changes in execution logic of the application (see Environment docs.)

        Returns:
        - The created Image

        Exceptions:
        - When the filename or the path to the data could not be opened by rasterio
        """
        try:
            res_path: str = self.get_resolution_path(f"{environment.create_input}{title}", granule, "R60m")   # Get the path to the band data
            profile: Profile = ProfileFactory().create_profile(rio.open(self.get_data_path(res_path, "B02")).profile)
            
            if not os.path.exists(f"{environment.create_output}"):
                os.makedirs(f"{environment.create_output}")
                print(f"\nLOGGER: The folder {environment.create_output} has been created where the image data will be stored")

            b2: str = self.safe_dump_band(res_path, "B02", title, environment=environment)
            b3: str = self.safe_dump_band(res_path, "B03", title, environment=environment)                   # And dump the bands to files
            b4: str = self.safe_dump_band(res_path, "B04", title, environment=environment)
            b8: str = self.safe_dump_band(res_path, "B8A", title, environment=environment)
            b8a: str = self.safe_dump_band(res_path, "B8A", title, environment=environment)
            b11: str = self.safe_dump_band(res_path, "B11", title, environment=environment)

            # Create the Image object based on the returned paths and return it
            img: Image = Image(img_id=self.current_id, title=title, b2=b2, b3=b3, b4=b4, b8=b8, b8a=b8a, b11=b11, profile=profile)
            self.current_id += 1
            return img
        
        except Exception as e:  # If opening the given foldername + granule raises an exception it will be catched
            print(f"\nEXCEPTION: {e}")            # And it is reported.
            return None         # The method is required to return an Image object, as such after an Exception it will return None