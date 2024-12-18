from django.test import TestCase
from .models import Environment, Profile, ProfileFactory, ImageManager, Image, ImageFactory
from .startup import Creator, Renderer, Tiler, Starter
from django.test import TestCase
from unittest.mock import patch, MagicMock
import rasterio as rio
import numpy as np
import os, shutil

prof_factory: ProfileFactory = ProfileFactory()
img_factory: ImageFactory = ImageFactory()
img_manager: ImageManager = ImageManager()

path_to_data: str = "image_data/testing/"

path_to_originals: str = "original_images/"
original_location = f"{path_to_data}{path_to_originals}"

create_input_folder: str = "img/"
create_output_folder: str = "images/"
render_output_folder: str = "output/"
temp_output_folder: str = "temp/"
tiles_output_folder: str = "tiles/"
create_input_tiling_folder: str = "tiling/"

create_input_path: str = f"{path_to_data}{create_input_folder}"
create_output_path: str = f"{path_to_data}{create_output_folder}"
render_output_path: str = f"{path_to_data}{render_output_folder}"
temp_output_path: str = f"{path_to_data}{temp_output_folder}"
tiles_output_path: str = f"{path_to_data}{tiles_output_folder}"
create_input_tiling_path: str = f"{create_input_path}{create_input_tiling_folder}"

rendered_file_type: str = "tiff"

val_title_safe: str = "S2A_MSIL2A_20240323T092031_N0510_R093_T34TGL_20240323T125850"
inv_title_safe: str = "S2A_NOT_VALID"
val_granule: str = "L2A_T34TGL_A045707_20240323T092633"
inv_granule: str = "L2A_NOT_VALID"

val_title_tif: str = "Mosaic_Bulgaria"
inv_title_tif: str = "Not_Valid_File"

val_path_tif: str = f"{create_input_path}{val_title_tif}"
inv_path_tif: str = f"{create_input_path}{inv_title_tif}"

val_path_safe: str = f"{create_input_path}{val_title_safe}"
inv_path_safe: str = f"{create_input_path}{inv_title_safe}"

val_path: str = f"{create_input_path}{val_title_safe}.SAFE/GRANULE/{val_granule}/IMG_DATA/R60m/"
inv_path: str = f"{create_input_path}{inv_title_safe}.SAFE/GRANULE/{inv_granule}/IMG_DATA/R60m/"
inv_band_path: str = f"Nope"

val_to_find: str = "B02"
inv_to_find: str = "B999"

val_shape: tuple[int, int] = (200, 200)

DEFAULT_ENV = Environment(
    create_input=create_input_path,
    create_output=create_output_path,
    render_output=render_output_path,
    tile_output=tiles_output_path,
    temp_output=temp_output_path
)

def create_test(filename: str, width: int, height: int, start_width: int = 0, start_height: int = 0) -> str:
    img_path: str = f"{DEFAULT_ENV.create_input}{filename}.tif"   # Path to the file

    with rio.open(f"{original_location}{filename}.tif") as data:     # Open all the available data
        datas = []

        for i in range(1, 13):
            band_data: np.ndarray = data.read(i)[start_height:(start_height + height), start_width:(start_width + width)]         # Using dictionary lookup to read the correct band data and then manipulate it for the .tif format
            band_data = img_factory.manipulate_data(band_data, 100, 255)
            datas.append(band_data)

        profile: rio.profiles.Profile = data.profile 
        profile["width"] = width
        profile["height"] = height

        with rio.open(img_path, 'w', **profile) as band_dump:
            for i in range(12):
                band_dump.write(datas[i], i+1)   # Dump the band data to the file
            band_dump.close()

def empty_dir(path):
    """Remove all files and folders in the given path

    Keyword arguments:
    - path -- path where the files and folders whould be removed

    Exceptions:
    - When the specified path cannot be reached
    """

    # Taken from: https://www.tutorialspoint.com/How-to-delete-all-files-in-a-directory-with-Python

    try:
        files = os.listdir(path)
        for file in files:
            file_path = os.path.join(path, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
    
    except Exception as e:
        print(f"\nEXCEPTION: {e}")
        
def default_env() -> Environment:
    return Environment(
        create_input=DEFAULT_ENV.create_input,
        create_output=DEFAULT_ENV.create_output,
        render_output=DEFAULT_ENV.render_output,
        tile_output=DEFAULT_ENV.tile_output,
        temp_output=DEFAULT_ENV.temp_output
    )

def environment_equals(a: Environment, b: Environment) -> bool:
    # print(f"\nDEBUGGER: a = {a}\n\nb = {b}")
    if (a == None or b == None):
        return (a == None and b == None)
    if (a.create != b.create) or (a.create_input != b.create_input) or (a.create_output != b.create_output) or (a.recreate != b.recreate):
        return False
    if (a.render != b.render) or (a.render_output != b.render_output) or (a.rerender != b.rerender):
        return False
    if (a.tile != b.tile) or (a.tile_output != b.tile_output) or (a.temp_output != b.temp_output):
        return False
    return True

def profile_equals(a: Profile, b: Profile) -> bool:
    # print(f"\nDEBUGGER: a = {a}\n\nb = {b}")
    if (a == None or b == None):
        return (a == None and b == None)
    if (a.driver != b.driver) or (a.dtype != b.dtype) or (a.nodata != b.nodata):
        return False
    if (a.width != b.width) or (a.height != b.height) or (a.count != b.count):
        return False
    if (a.crs != b.crs) or (a.transform != b.transform):
        return False
    if (a.blockxsize != b.blockxsize) or (a.blockysize != b.blockysize) or (a.tiled != b.tiled):
        return False
    return True

def rio_profile_equals(a: rio.profiles.Profile, b: rio.profiles.Profile) -> bool:
    # print(f"\nDEBUGGER: a = {a}\n\nb = {b}")
    if (a == None or b == None):
        return (a == None and b == None)
    if (a["driver"] != b["driver"]) or (a["dtype"] != b["dtype"]) or (a["nodata"] != b["nodata"]):
        return False
    if (a["width"] != b["width"]) or (a["height"] != b["height"]) or (a["count"] != b["count"]):
        return False
    if (a["crs"] != b["crs"]):
        return False
    if (a["blockxsize"] != b["blockxsize"]) or (a["blockysize"] != b["blockysize"]) or (a["tiled"] != b["tiled"]):
        return False
    return True

def image_equals(a: Image, b: Image) -> bool:
    # print(f"\nDEBUGGER: a = {a}\n\nb = {b}")
    if (a == None or b == None):
        return (a == None and b == None)
    if (a.title != b.title):
        return False
    if (a.b2 != b.b2) or (a.b3 != b.b3) or (a.b4 != b.b4) or (a.b8 != b.b8) or (a.b8a != b.b8a) or (a.b11 != b.b11):
        return False
    if (a.tc != b.tc) or (a.ndvi != b.ndvi) or (a.ndwi != b.ndwi) or (a.ndmi != b.ndmi):
        return False
    return profile_equals(a.profile, b.profile)


# Environment Tests
class EnvironmentTestCase(TestCase):
    def setUp(self):
        global environment, environment_string
        environment = Environment(
            create = True,
            create_input = "a",
            create_output = "b",
            recreate = True,
            render = True,
            render_output = "c",
            rerender = True,
            tile = True,
            tile_output = "d",
            temp_output = "e"
        )
        environment_string = f"[\n  create: True\n  create_input: a\n  create_output: b\n  recreate: True\n  render: True\n  render_output: c\n  rerender: True\n  tile: True\n  tile_output: d\n  temp_output: e\n]"
    
    def test_environment_str(self):
        # Valid execution
        self.assertEqual(environment.__str__(), environment_string)  


# Profile Tests
class ProfileTestCase(TestCase):
    def setUp(self):
        global profile, profile_string
        profile = Profile(
            driver = "a",
            dtype = "b",
            nodata = "c",
            width = 1,
            height = 2,
            count = 3,
            crs = 4,
            transform = "d",
            blockxsize = 5,
            blockysize = 6,
            tiled = True
        )
        profile_string = "[\n    driver: a\n    dtype: b\n    nodata: c\n    width: 1\n    height: 2\n    count: 3\n    crs: 4\n    transform: d\n    blockxsize: 5\n    blockysize: 6\n    tiled: True\n  ]"
    
    def test_profile_str(self):
        # Valid execution
        self.assertEqual(profile.__str__(), profile_string)   


# ProfileFactory Tests
class ProfileFactoryTestCase(TestCase):
    def setUp(self):
        global driver, dtype, nodata, width, height, count, crs, blockxsize, blockysize, tiled
        driver = "GTiff"
        dtype = "uint8"
        nodata = 0
        width = 4
        height = 3
        count = 2
        crs = 7801
        blockxsize = 256
        blockysize = 256
        tiled = True
        
        global rio_profile, profile
        rio_profile = rio.profiles.Profile(driver=driver, dtype=dtype, nodata=nodata, width=width, height=height, count=count, crs=rio.crs.CRS.from_epsg(crs), blockxsize=blockxsize, blockysize=blockysize, tiled=tiled)
        profile = Profile(driver=driver, dtype=dtype, nodata=nodata, width=width, height=height, count=count, crs=crs, blockxsize=blockxsize, blockysize=blockysize, tiled=tiled)
    
    def test_profilefactory_create_profile(self):
        result: Profile = prof_factory.create_profile(rio_profile)
        self.assertTrue(profile_equals(result, profile))
    
    def test_profilefactory_get_rio_profile(self):
        result: Profile = prof_factory.get_rio_profile(profile)
        self.assertTrue(rio_profile_equals(result, rio_profile))
    
    
# ImageManager Tests
class ImageManagerTestCase(TestCase):
    def get_valid_img(self, val: Image) -> Image:
        return Image(
            title=val.title,
            b2 = val.b2,
            b3 = val.b3,
            b4 = val.b4,
            b8 = val.b8,
            b8a = val.b8a,
            b11 = val.b11,
            profile = val.profile
        )
    
    def setUp(self):
        global env
        env = default_env()
        
        global img_val_tif, img_val_safe
        img_val_tif = img_factory.tif_create(val_title_tif, env)
        img_val_safe = img_factory.safe_create(val_title_safe, val_granule, env)

        global img_inv_b2, img_inv_b3, img_inv_b4, img_inv_b8, img_inv_b8a, img_inv_b11
        img_inv_b2 = self.get_valid_img(img_val_tif)
        img_inv_b2.b2 = inv_band_path
        
        img_inv_b3 = self.get_valid_img(img_val_tif)
        img_inv_b3.b3 = inv_band_path
        
        img_inv_b4 = self.get_valid_img(img_val_tif)
        img_inv_b4.b4 = inv_band_path
        
        img_inv_b8 = self.get_valid_img(img_val_tif)
        img_inv_b8.b8 = inv_band_path
        
        img_inv_b8a = self.get_valid_img(img_val_tif)
        img_inv_b8a.b8a = inv_band_path
        
        img_inv_b11 = self.get_valid_img(img_val_tif)
        img_inv_b11.b11 = inv_band_path

    def test_imagemanager_load(self):
        # Valid execution
        self.assertEqual(img_manager.load(img_val_tif.b2).shape, val_shape)
            
        # Try to access a non-existing path
        with self.assertRaises(Exception):
            img_manager.load(inv_band_path)

    def test_imagemanager_create_true_color(self):
        empty_dir(env.render_output)

        # Valid execution
        self.assertEqual(img_manager.create_true_color(img_val_safe, env), 
                        f"{env.render_output}{val_title_safe}_TC.tiff")                       # Since the image_data/original_images folder is in the .gitignore and I am unsure on if we are allowed to upload
        self.assertTrue(os.path.isfile(f"{env.render_output}{val_title_safe}_TC.tiff"))       # example satelite images yet to test with I commented this out in the meantime
        
        self.assertEqual(img_manager.create_true_color(img_val_tif, env), 
                        f"{env.render_output}{val_title_tif}_TC.tiff")  
        self.assertTrue(os.path.isfile(f"{env.render_output}{val_title_tif}_TC.tiff"))
        
        # Images with invalid input (b2, b3 or b4 for True Color)
        self.assertIsNone(img_manager.create_true_color(None))
        
        env.rerender = True
        self.assertIsNone(img_manager.create_true_color(img_inv_b2, env))
        self.assertIsNone(img_manager.create_true_color(img_inv_b3, env))
        self.assertIsNone(img_manager.create_true_color(img_inv_b4, env))

        # Case output folder does not exist yet
        shutil.rmtree(env.render_output)

        self.assertEqual(img_manager.create_true_color(img_val_tif, env), 
                        f"{env.render_output}{val_title_tif}_TC.tiff")  
        
        self.assertTrue(os.path.exists(env.render_output))
        self.assertTrue(os.path.isfile(f"{env.render_output}{val_title_tif}_TC.tiff"))

    @patch('rasterio.open')
    @patch('glob.glob')
    def test_images_create_true_color_with_mocks(self, mock_glob, mock_rio_open):
        env.rerender = True

        # Mock the file search results
        mock_glob.side_effect = [
            [f"{val_path_tif}B04.jp2"], [f"{val_path_tif}B03.jp2"], [f"{val_path_tif}B02.jp2"]
        ]

        # Mock the rasterio dataset reader
        mock_dataset = MagicMock()
        mock_dataset.read.return_value = np.ones((100, 100))
        mock_dataset.profile = {
            'driver': 'GTiff',
            'dtype': 'uint16',
            'nodata': None,
            'width': 100,
            'height': 100,
            'count': 1,
            'crs': rio.crs.CRS.from_epsg(4326),
            'transform': rio.transform.Affine(1.0, 0.0, 0.0, 0.0, -1.0, 0.0)
        }
        mock_rio_open.return_value = mock_dataset

        with patch('rasterio.open', mock_rio_open):
            path = Image.manager.create_true_color(img_val_tif, env)
            self.assertIsNotNone(path)
            self.assertTrue(path.endswith('_TC.tiff'))

    def test_imagemanager_create_NDVI(self):
        # Valid execution
        empty_dir(env.render_output)

        self.assertEqual(img_manager.create_NDVI(img_val_safe, env), 
                        f"{env.render_output}{val_title_safe}_NDVI.tiff")                     # Since the image_data/original_images folder is in the .gitignore and I am unsure on if we are allowed to upload
        self.assertTrue(os.path.isfile(f"{env.render_output}{val_title_safe}_NDVI.tiff"))     # example satelite images yet to test with I commented this out in the meantime
        
        self.assertEqual(img_manager.create_NDVI(img_val_tif, env), 
                        f"{env.render_output}{val_title_tif}_NDVI.tiff") 
        self.assertTrue(os.path.isfile(f"{env.render_output}{val_title_tif}_NDVI.tiff"))

        # Images with invalid input (b4 or b8 for NDVI)
        self.assertIsNone(img_manager.create_NDVI(None))
        
        env.rerender = True
        self.assertIsNone(img_manager.create_NDVI(img_inv_b4, env))
        self.assertIsNone(img_manager.create_NDVI(img_inv_b8, env))

        # Case output folder does not exist yet
        shutil.rmtree(env.render_output)

        self.assertEqual(img_manager.create_NDVI(img_val_tif, env), 
                        f"{env.render_output}{val_title_tif}_NDVI.tiff")  
        
        self.assertTrue(os.path.exists(env.render_output))
        self.assertTrue(os.path.isfile(f"{env.render_output}{val_title_tif}_NDVI.tiff"))

    @patch('rasterio.open')
    @patch('glob.glob')
    def test_images_create_NDVI_with_mocks(self, mock_glob, mock_rio_open):
        env.rerender = True

        # Mock the file search results
        mock_glob.side_effect = [
            [f"{val_path_tif}B04.jp2"], [f"{val_path_tif}B08.jp2"]
        ]

        # Mock the rasterio dataset reader
        mock_dataset = MagicMock()
        mock_dataset.read.return_value = np.ones((100, 100))
        mock_dataset.profile = {
            'driver': 'GTiff',
            'dtype': 'uint16',
            'nodata': None,
            'width': 100,
            'height': 100,
            'count': 1,
            'crs': rio.crs.CRS.from_epsg(4326),
            'transform': rio.transform.Affine(1.0, 0.0, 0.0, 0.0, -1.0, 0.0)
        }
        mock_rio_open.return_value = mock_dataset

        with patch('rasterio.open', mock_rio_open):
            path = Image.manager.create_NDVI(img_val_tif, env)
            self.assertIsNotNone(path)
            self.assertTrue(path.endswith('_NDVI.tiff'))

    def test_imagemanager_create_NDWI(self):
        empty_dir(env.render_output)

        # Valid execution
        self.assertEqual(img_manager.create_NDWI(img_val_safe, env), 
                        f"{env.render_output}{val_title_safe}_NDWI.tiff")                     # Since the image_data/original_images folder is in the .gitignore and I am unsure on if we are allowed to upload
        self.assertTrue(os.path.isfile(f"{env.render_output}{val_title_safe}_NDWI.tiff"))     # example satelite images yet to test with I commented this out in the meantime
        
        self.assertEqual(img_manager.create_NDWI(img_val_tif, env), 
                        f"{env.render_output}{val_title_tif}_NDWI.tiff") 
        self.assertTrue(os.path.isfile(f"{env.render_output}{val_title_tif}_NDWI.tiff"))

        # Images with invalid input (b3 or b8 for NDWI)
        self.assertIsNone(img_manager.create_NDWI(None))

        env.rerender = True
        self.assertIsNone(img_manager.create_NDWI(img_inv_b3, env))
        self.assertIsNone(img_manager.create_NDWI(img_inv_b8, env))

        # Case output folder does not exist yet
        shutil.rmtree(env.render_output)

        self.assertEqual(img_manager.create_NDWI(img_val_tif, env), 
                        f"{env.render_output}{val_title_tif}_NDWI.tiff")  
        
        self.assertTrue(os.path.exists(env.render_output))
        self.assertTrue(os.path.isfile(f"{env.render_output}{val_title_tif}_NDWI.tiff"))

    @patch('rasterio.open')
    @patch('glob.glob')
    def test_images_create_NDWI_with_mocks(self, mock_glob, mock_rio_open):
        env.rerender = True
        
        # Mock the file search results
        mock_glob.side_effect = [
            [f"{val_path_tif}B8.jp2"], [f"{val_path_tif}B3.jp2"]
        ]

        # Mock the rasterio dataset reader
        mock_dataset = MagicMock()
        mock_dataset.read.return_value = np.ones((100, 100))
        mock_dataset.profile = {
            'driver': 'GTiff',
            'dtype': 'uint16',
            'nodata': None,
            'width': 100,
            'height': 100,
            'count': 1,
            'crs': rio.crs.CRS.from_epsg(4326),
            'transform': rio.transform.Affine(1.0, 0.0, 0.0, 0.0, -1.0, 0.0)
        }
        mock_rio_open.return_value = mock_dataset

        with patch('rasterio.open', mock_rio_open):
            path = Image.manager.create_NDWI(img_val_tif,  env)
            self.assertIsNotNone(path)
            self.assertTrue(path.endswith('_NDWI.tiff'))

    def test_imagemanager_create_NDMI(self):
        empty_dir(env.render_output)

        # Valid execution
        self.assertEqual(img_manager.create_NDMI(img_val_safe, env), 
                        f"{env.render_output}{val_title_safe}_NDMI.tiff")                     # Since the image_data/original_images folder is in the .gitignore and I am unsure on if we are allowed to upload
        self.assertTrue(os.path.isfile(f"{env.render_output}{val_title_safe}_NDMI.tiff"))     # example satelite images yet to test with I commented this out in the meantime
        
        self.assertEqual(img_manager.create_NDMI(img_val_tif, env), 
                        f"{env.render_output}{val_title_tif}_NDMI.tiff") 
        self.assertTrue(os.path.isfile(f"{env.render_output}{val_title_tif}_NDMI.tiff"))

        # Images with invalid input (b8a or b11 for NDMI)
        self.assertIsNone(img_manager.create_NDMI(None))
    
        env.rerender = True
        self.assertIsNone(img_manager.create_NDMI(img_inv_b8a, env))
        self.assertIsNone(img_manager.create_NDMI(img_inv_b11, env))

        # Case output folder does not exist yet
        shutil.rmtree(env.render_output)

        self.assertEqual(img_manager.create_NDMI(img_val_tif, env), 
                        f"{env.render_output}{val_title_tif}_NDMI.tiff")  
        
        self.assertTrue(os.path.exists(env.render_output))
        self.assertTrue(os.path.isfile(f"{env.render_output}{val_title_tif}_NDMI.tiff"))


    @patch('rasterio.open')
    @patch('glob.glob')
    def test_imagemanager_create_NDMI_with_mocks(self, mock_glob, mock_rio_open):
        env.rerender = True

        # Mock the file search results
        mock_glob.side_effect = [
            [f"{val_path_tif}B8A.jp2"], [f"{val_path_tif}B11.jp2"]
        ]

        # Mock the rasterio dataset reader
        mock_dataset = MagicMock()
        mock_dataset.read.return_value = np.ones((100, 100))
        mock_dataset.profile = {
            'driver': 'GTiff',
            'dtype': 'uint16',
            'nodata': None,
            'width': 100,
            'height': 100,
            'count': 1,
            'crs': rio.crs.CRS.from_epsg(4326),
            'transform': rio.transform.Affine(1.0, 0.0, 0.0, 0.0, -1.0, 0.0)
        }
        mock_rio_open.return_value = mock_dataset

        with patch('rasterio.open', mock_rio_open):
            path = Image.manager.create_NDWI(img_val_tif, env)
            self.assertIsNotNone(path)
            self.assertTrue(path.endswith('_NDWI.tiff'))
    

# Image Tests
class ImageTestCase(TestCase):
    def setUp(self):
        global profile, profile_string, img, img_string
        profile = Profile(
            driver = "a",
            dtype = "b",
            nodata = "c",
            width = 1,
            height = 2,
            count = 3,
            crs = 4,
            transform = "d",
            blockxsize = 5,
            blockysize = 6,
            tiled = True
        )
        profile_string = "[\n    driver: a\n    dtype: b\n    nodata: c\n    width: 1\n    height: 2\n    count: 3\n    crs: 4\n    transform: d\n    blockxsize: 5\n    blockysize: 6\n    tiled: True\n  ]"
        
        img = Image(
            img_id = 1,
            title = "title",
            b2 = "b2",
            b3 = "b3",
            b4 = "b4",
            b8 = "b8",
            b8a = "b8a",
            b11 = "b11",
            tc = "tc",
            ndvi = "ndvi",
            ndwi = "ndwi",
            ndmi = "ndmi",
            profile = profile
        )
        img_string = f"[\n  img_id: 1\n  title: title\n  b2: b2\n  b3: b3\n  b4: b4\n  b8: b8\n  b8a: b8a\n  b11: b11\n  tc: tc\n  ndvi: ndvi\n  ndwi: ndwi\n  ndmi: ndmi\n  profile: {profile_string}\n]"
    
    def test_image_str(self):
        # Valid execution
        self.assertEqual(img.__str__(), img_string)    
    
    
# ImageFactory Tests
class ImageFactoryTestCase(TestCase):
    def setUp(self):
        global env
        env = default_env()
        
    def test_imagefactory_get_resolution_path(self):
        # Valid execution
        res = "R60m"
        self.assertEqual(img_factory.get_resolution_path(val_path_safe, val_granule, res), 
                         val_path)

    def test_imagefactory_get_data_path(self):
        # Valid execution
        expected_path = f"{env.create_input}{val_title_safe}.SAFE/GRANULE/{val_granule}/IMG_DATA/R60m/T34TGL_20240323T092031_B02_60m.jp2"
        self.assertEqual(img_factory.get_data_path(val_path, val_to_find), 
                        expected_path)
    
        # Try to access a non-existing path
        with self.assertRaises(Exception):
            img_factory.get_data_path(inv_path, val_to_find)

        # Try to access file not in the specified (existing) folder
        with self.assertRaises(Exception):
            img_factory.get_data_path(val_path, inv_to_find)

    def test_imagefactory_manipulate_data(self):
        data: np.ndarray = np.array([[1, 2], [3, 4]])
        neg_data: np.ndarray = np.array([[-0.01, 2], [3, 4]])
        
        # Only multiplication test
        result: np.ndarray = img_factory.manipulate_data(data, 10, 50)
        np.testing.assert_array_equal(result, np.array([[10, 20], [30, 40]]))
        
        # Also test top clipping
        result: np.ndarray = img_factory.manipulate_data(data, 10, 31)
        np.testing.assert_array_equal(result, np.array([[10, 20], [30, 31]]))
        
        # Also test bottom clipping
        result: np.ndarray = img_factory.manipulate_data(neg_data, 10, 31)
        np.testing.assert_array_equal(result, np.array([[0, 20], [30, 31]]))
    
    def test_imagefactory_tif_dump_band(self):
        empty_dir(env.create_output)

        with rio.open(f"{env.create_input}{val_title_tif}.tif") as data:
            # Case NOT force_recreate and file does not exist yet + valid execution
            result: str = img_factory.tif_dump_band(data, val_to_find, val_title_tif, env)
            self.assertEqual(result, f"{env.create_output}{val_title_tif}_{val_to_find}.tiff")
            self.assertTrue(os.path.isfile(result))

            # Case NOT force_recreate and file does exist
            result = img_factory.tif_dump_band(data, val_to_find, val_title_tif, env)
            self.assertEqual(result, f"{env.create_output}{val_title_tif}_{val_to_find}.tiff")

            data.close()

        empty_dir(env.create_output)

        with rio.open(f"{env.create_input}{val_title_tif}.tif") as data:
            # Case force_recreate + valid execution
            env.recreate = True
            result = img_factory.tif_dump_band(data, val_to_find, val_title_tif, env)
            self.assertEqual(result, f"{env.create_output}{val_title_tif}_{val_to_find}.tiff")
            self.assertTrue(os.path.isfile(result))

            # Case invalid band
            self.assertIsNone(img_factory.tif_dump_band(data, inv_to_find, val_title_tif, env))

            data.close()
    
    def test_imagefactory_safe_dump_band(self):
        empty_dir(env.create_output)

        # Case NOT force_recreate and file does not exist yet + valid execution
        result: str = img_factory.safe_dump_band(val_path, val_to_find, val_title_safe, env)
        self.assertEqual(result, f"{env.create_output}{val_title_safe}_{val_to_find}.tiff")
        self.assertTrue(os.path.isfile(result))

        # Case NOT force_recreate and file does exist
        result = img_factory.safe_dump_band(val_path, val_to_find, val_title_safe, env)
        self.assertEqual(result, f"{env.create_output}{val_title_safe}_{val_to_find}.tiff")


        empty_dir(env.create_output)

        # Case force_recreate + valid execution
        env.recreate = True
        result = img_factory.safe_dump_band(val_path, val_to_find, val_title_safe, env)
        self.assertEqual(result, f"{env.create_output}{val_title_safe}_{val_to_find}.tiff")
        self.assertTrue(os.path.isfile(result))

        # Case invalid band
        self.assertIsNone(img_factory.safe_dump_band(val_path, inv_to_find, val_title_safe, env))

        # Case folder could not be opened
        self.assertIsNone(img_factory.safe_dump_band(inv_path, val_to_find, val_title_safe, env))   
    
    def test_imagefactory_tif_create(self):
        empty_dir(env.create_output)

        # Valid execution
        img: Image = img_factory.tif_create(val_title_tif, env)
        self.assertEqual(img.title, val_title_tif)

        self.assertEqual(img.b2, f"{env.create_output}{val_title_tif}_B02.tiff")
        self.assertTrue(os.path.isfile(img.b2))

        self.assertEqual(img.b3, f"{env.create_output}{val_title_tif}_B03.tiff")
        self.assertTrue(os.path.isfile(img.b3))

        self.assertEqual(img.b4, f"{env.create_output}{val_title_tif}_B04.tiff")
        self.assertTrue(os.path.isfile(img.b4))

        self.assertEqual(img.b8, f"{env.create_output}{val_title_tif}_B08.tiff")
        self.assertTrue(os.path.isfile(img.b8))

        self.assertEqual(img.b8a, f"{env.create_output}{val_title_tif}_B8A.tiff")
        self.assertTrue(os.path.isfile(img.b8a))

        self.assertEqual(img.b11, f"{env.create_output}{val_title_tif}_B11.tiff")
        self.assertTrue(os.path.isfile(img.b11))

        # Case folder could not be opened
        self.assertIsNone(img_factory.tif_create(inv_title_tif, env))

        # Case images folder does not exist yet
        shutil.rmtree(env.create_output)

        img: Image = img_factory.tif_create(val_title_tif, env)
        self.assertTrue(os.path.exists(env.create_output))
            
    def test_imagefactory_safe_create(self):
        empty_dir(env.create_output)

        # Valid execution
        img: Image = img_factory.safe_create(val_title_safe, val_granule, env)
        self.assertEqual(img.title, val_title_safe)

        self.assertEqual(img.b2, f"{env.create_output}{val_title_safe}_B02.tiff")
        self.assertTrue(os.path.isfile(img.b2))

        self.assertEqual(img.b3, f"{env.create_output}{val_title_safe}_B03.tiff")
        self.assertTrue(os.path.isfile(img.b3))

        self.assertEqual(img.b4, f"{env.create_output}{val_title_safe}_B04.tiff")
        self.assertTrue(os.path.isfile(img.b4))

        self.assertEqual(img.b8, f"{env.create_output}{val_title_safe}_B8A.tiff")
        self.assertTrue(os.path.isfile(img.b8))

        self.assertEqual(img.b8a, f"{env.create_output}{val_title_safe}_B8A.tiff")
        self.assertTrue(os.path.isfile(img.b8a))

        self.assertEqual(img.b11, f"{env.create_output}{val_title_safe}_B11.tiff")
        self.assertTrue(os.path.isfile(img.b11))

        # Case invalid title
        self.assertIsNone(img_factory.safe_create(inv_title_safe, val_granule, env))

        # Case invalid granule
        self.assertIsNone(img_factory.safe_create(val_title_safe, inv_granule, env))

        # Case images folder does not exist yet
        shutil.rmtree(env.create_output)

        img: Image = img_factory.safe_create(val_title_safe, val_granule, env)
        self.assertTrue(os.path.exists(env.create_output))


# Creator Tests
class CreatorTestCase(TestCase):
    def setUp(self):
        global env
        env = default_env()
        
    def test_creator_get_granule(self):
        # Valid execution
        self.assertEqual(Creator().get_granule(val_title_safe, env.create_input), val_granule)

        # Getting granule with an invalid safe title
        self.assertIsNone(Creator().get_granule(inv_title_safe, env.create_input))

        # Getting granule with an invalid image location
        self.assertIsNone(Creator().get_granule(val_title_safe, "Nope"))

    def test_creator_create_images(self):
        # Valid execution
        empty_dir(env.create_output)
        Creator().create_images(env)

        self.assertTrue(os.path.isfile(f"{env.create_output}{val_title_tif}_B02.{rendered_file_type}"))
        self.assertTrue(os.path.isfile(f"{env.create_output}{val_title_tif}_B03.{rendered_file_type}"))
        self.assertTrue(os.path.isfile(f"{env.create_output}{val_title_tif}_B04.{rendered_file_type}"))
        self.assertTrue(os.path.isfile(f"{env.create_output}{val_title_tif}_B08.{rendered_file_type}"))
        self.assertTrue(os.path.isfile(f"{env.create_output}{val_title_tif}_B8A.{rendered_file_type}"))
        self.assertTrue(os.path.isfile(f"{env.create_output}{val_title_tif}_B11.{rendered_file_type}"))

        self.assertTrue(os.path.isfile(f"{env.create_output}{val_title_safe}_B02.{rendered_file_type}"))
        self.assertTrue(os.path.isfile(f"{env.create_output}{val_title_safe}_B03.{rendered_file_type}"))
        self.assertTrue(os.path.isfile(f"{env.create_output}{val_title_safe}_B04.{rendered_file_type}"))
        self.assertTrue(os.path.isfile(f"{env.create_output}{val_title_safe}_B8A.{rendered_file_type}"))
        self.assertTrue(os.path.isfile(f"{env.create_output}{val_title_safe}_B11.{rendered_file_type}"))

        # Case folder does not exist
        env.create_input = "Nope"
        self.assertEqual(Creator().create_images(env), [])


# Renderer Tests
class RendererTestCase(TestCase):
    def setUp(self):
        global env
        env = default_env()
        
        global img_val_tif, img_val_safe
        img_val_tif = img_factory.tif_create(val_title_tif, env)
        img_val_safe = img_factory.safe_create(val_title_safe, val_granule, env)

    def test_renderer_render(self):
        # Valid execution
        img_val_tif.tc = None
        renderer: Renderer = Renderer()
        renderer.render(img_val_tif, "TC", env)
        self.assertEqual(img_val_tif.tc, f"{env.render_output}{img_val_tif.title}_TC.{rendered_file_type}")
        
        # Check if first gets overwritten
        env.rerender = True
        renderer.render(img_val_tif, "TC", env)
        self.assertEqual(img_val_tif.tc, f"{env.render_output}{img_val_tif.title}_TC.{rendered_file_type}")

    def test_renderer_render_images(self):
        # Valid execution
        renderer: Renderer = Renderer()
        
        images: list[Image] = renderer.render_images([img_val_tif], env)
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0].tc, f"{env.render_output}{img_val_tif.title}_TC.{rendered_file_type}")
        self.assertEqual(images[0].ndvi, f"{env.render_output}{img_val_tif.title}_NDVI.{rendered_file_type}")
        self.assertEqual(images[0].ndwi, f"{env.render_output}{img_val_tif.title}_NDWI.{rendered_file_type}")
        self.assertEqual(images[0].ndmi, f"{env.render_output}{img_val_tif.title}_NDMI.{rendered_file_type}")

        # Image location does not exist
        self.assertEqual(Renderer().render_images(None), [])


# Tiler Tests
class TilerTestCase(TestCase):
    def setUp(self):
        global env
        env = default_env()
        
        global img_val_tif, img_val_safe
        img_val_tif = img_factory.tif_create(val_title_tif, env)
        img_val_safe = img_factory.safe_create(val_title_safe, val_granule, env)

    def test_tiler_tile_image(self):
        empty_dir(env.tile_output)
        rendered: list[Image] = Renderer().render_images([img_val_tif], env)

        # Valid execution
        Tiler().tile_image(rendered[0], rendered[0].tc, 0, env)

        self.assertTrue(os.path.exists(f"{env.tile_output}{rendered[0].img_id}/"))
        self.assertTrue(os.path.exists(f"{env.tile_output}{rendered[0].img_id}/0/"))

    def test_tiler_tile_images(self):
        empty_dir(env.tile_output)
        rendered: list[Image] = Renderer().render_images([img_val_tif], env)

        # Valid execution
        Tiler().tile_images(rendered, env)
        self.assertTrue(os.path.exists(f"{env.tile_output}{rendered[0].img_id}/"))
        self.assertTrue(os.path.exists(f"{env.tile_output}{rendered[0].img_id}/0/"))
        self.assertTrue(os.path.exists(f"{env.tile_output}{rendered[0].img_id}/1/"))
        self.assertTrue(os.path.exists(f"{env.tile_output}{rendered[0].img_id}/2/"))
        self.assertTrue(os.path.exists(f"{env.tile_output}{rendered[0].img_id}/3/"))

        # Case alg = ""
        empty_dir(env.tile_output)
        rendered[0].tc = ""
        Tiler().tile_images(rendered, env)

        # Case alg = None
        empty_dir(env.tile_output)
        rendered[0].ndwi = None
        Tiler().tile_images(rendered, env)


# Starter Tests
class StarterTestCase(TestCase):
    def setUp(self):
        global env
        env = default_env()
        
        global img_val_tif, img_val_safe
        img_val_tif = img_factory.tif_create(val_title_tif, env)
        img_val_safe = img_factory.safe_create(val_title_safe, val_granule, env)

    def test_starter_start_creating(self):
        # print("TESTIMAGE CREATION!!!!!!!!!!!!!!!!!!!!!!!")
        # create_test("Mosaic_Bulgaria", 1000, 1000, 4000, 3000)

        empty_dir(env.create_output)

        # Valid execution
        images: list[Image] = Starter().start_creating(env)

        self.assertEqual(len(images), 2)

        img_val_tif.tc = ""
        img_val_tif.ndvi = ""
        img_val_tif.ndwi = ""
        img_val_tif.ndmi = ""

        self.assertTrue(image_equals(images[0], img_val_tif))

        img_val_safe.tc = ""
        img_val_safe.ndvi = ""
        img_val_safe.ndwi = ""
        img_val_safe.ndmi = ""

        self.assertTrue(image_equals(images[1], img_val_safe))

    def test_starter_start_rendering(self):
        empty_dir(env.create_output)
        empty_dir(env.render_output)

        # Valid execution
        images: list[Image] = Starter().start_creating(env)
        rendered: list[Image] = Starter().start_rendering(images, env)

        self.assertEqual(len(rendered), 2)

        self.assertIsNotNone(rendered[0].tc)
        self.assertIsNotNone(rendered[0].ndvi)
        self.assertIsNotNone(rendered[0].ndwi)
        self.assertIsNotNone(rendered[0].ndmi)
        
        self.assertIsNotNone(rendered[1].tc)
        self.assertIsNotNone(rendered[1].ndvi)
        self.assertIsNotNone(rendered[1].ndwi)
        self.assertIsNotNone(rendered[1].ndmi)

        self.assertTrue(os.path.exists(f"{rendered[0].tc}"))
        self.assertTrue(os.path.exists(f"{rendered[0].ndvi}"))
        self.assertTrue(os.path.exists(f"{rendered[0].ndwi}"))
        self.assertTrue(os.path.exists(f"{rendered[0].ndmi}"))

        self.assertTrue(os.path.exists(f"{rendered[1].tc}"))
        self.assertTrue(os.path.exists(f"{rendered[1].ndvi}"))
        self.assertTrue(os.path.exists(f"{rendered[1].ndwi}"))
        self.assertTrue(os.path.exists(f"{rendered[1].ndmi}"))

    def test_starter_start_tiling(self):
        empty_dir(env.create_output)
        empty_dir(env.render_output)
        empty_dir(env.tile_output)
        
        # Set image input folder to the creation input location for testing tiling
        env.create_input = create_input_tiling_path

        # Valid execution
        images: list[Image] = Starter().start_creating(env)
        rendered: list[Image] = Starter().start_rendering(images, env)
        Starter().start_tiling(rendered, env)

        self.assertTrue(os.path.exists(f"{env.tile_output}{rendered[0].img_id}/"))
        self.assertTrue(os.path.exists(f"{env.tile_output}{rendered[0].img_id}/0/"))
        self.assertTrue(os.path.exists(f"{env.tile_output}{rendered[0].img_id}/1/"))
        self.assertTrue(os.path.exists(f"{env.tile_output}{rendered[0].img_id}/2/"))
        self.assertTrue(os.path.exists(f"{env.tile_output}{rendered[0].img_id}/3/"))

    def test_starter_start(self):
        empty_dir(env.create_output)
        empty_dir(env.render_output)
        empty_dir(env.tile_output)

        # Check if it does nothing when called with create, render and tile on False
        Starter().start(env)
        
        # Valid execution no-tile
        env.create = True
        env.render = True
        
        # Set image input folder to the creation input location for testing tiling
        env.create_input = create_input_tiling_path
        
        Starter().start(env)
        self.assertTrue(os.path.isfile(f"{env.create_output}{val_title_tif}_B02.{rendered_file_type}"))
        self.assertTrue(os.path.isfile(f"{env.create_output}{val_title_tif}_B03.{rendered_file_type}"))
        self.assertTrue(os.path.isfile(f"{env.create_output}{val_title_tif}_B04.{rendered_file_type}"))
        self.assertTrue(os.path.isfile(f"{env.create_output}{val_title_tif}_B08.{rendered_file_type}"))
        self.assertTrue(os.path.isfile(f"{env.create_output}{val_title_tif}_B8A.{rendered_file_type}"))
        self.assertTrue(os.path.isfile(f"{env.create_output}{val_title_tif}_B11.{rendered_file_type}"))

        # Valid execution retile
        empty_dir(env.create_output)
        empty_dir(env.render_output)
        empty_dir(env.tile_output)

        env.tile = True
        Starter().start(env)

        files = os.listdir(f"{env.tile_output}")

        self.assertTrue(os.path.exists(f"{env.tile_output}{files[0]}/"))
        self.assertTrue(os.path.exists(f"{env.tile_output}{files[0]}/0/"))
        self.assertTrue(os.path.exists(f"{env.tile_output}{files[0]}/1/"))
        self.assertTrue(os.path.exists(f"{env.tile_output}{files[0]}/2/"))
        self.assertTrue(os.path.exists(f"{env.tile_output}{files[0]}/3/"))

