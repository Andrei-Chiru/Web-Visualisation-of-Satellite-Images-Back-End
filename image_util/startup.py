from .models import Environment, Image, ImageManager, ImageFactory
import os, shutil

safe: str = ".SAFE/"
granule: str = "GRANULE/"

safe_folder_construction: str = f"{safe}{granule}"

output_format: str = "GTiff"
output_type: str = "Byte" # Byte/Int8/Int16/UInt16/UInt32/Int32/UInt64/Int64/Float32/Float64/CInt16/CInt32/CFloat32/CFloat64
min_val = 0
max_val = 255
width_percentage = 100
height_percentage = 100
start_level: int = 6
end_level: int = 13
web_viewer: str = "leaflet"
tilesize: int = 128

funcs = {
    "TC":   (lambda a, b : ImageManager().create_true_color(a, environment=b)),
    "NDVI": (lambda a, b : ImageManager().create_NDVI(a, environment=b)),
    "NDWI": (lambda a, b : ImageManager().create_NDWI(a, environment=b)),
    "NDMI": (lambda a, b : ImageManager().create_NDMI(a, environment=b))
}

class Creator():
    factory: ImageFactory = ImageFactory()          # Local ImageFactory() reference for tracking image IDs

    def get_granule(self, foldername: str, image_loc: str) -> str:
        """Get the granule folder title for the given .SAFE image located in the image_loc folder

        Keyword arguments:
        - foldername -- The name of the folder where the .SAFE data can be found
        - image_loc  -- The path to the location where the original images are stored
        
        Returns:
        - The name of the folder in which the granule data can be found for the specified .SAFE image

        Exceptions:
        - When either the foldername or the image_loc is invalid or cannot be traversed
        """

        try:
            matching: list[str] = os.listdir(f"{image_loc}{foldername}{safe_folder_construction}")     # Looks for files and folders within the folder given by the SAFE folder construction

            if not matching:        # No matching file could be found
                # raise Exception(f"\nPath does not contain matching file")
                raise Exception(f"Path [{image_loc}{foldername}{safe_folder_construction}] could not be found")
                # Removed because of printing user input

            return matching[0]      # The first found instance is the correct one
        
        except Exception as e:  # If foldername or image_loc could not be found it will be catched
            print(f"\nEXCEPTION: {e}")            # And it is reported.
            return None         # The method is required to return a string object, as such after an Exception it will return None

    def create_images(self, environment: Environment = Environment()) -> list[Image]:
        """Create all images located in the given image folder and store them in the assigned output folder

        Keyword arguments:
        - environment -- (Optional) Environment object with any changes in execution logic of the application (see Environment docs.)
        
        Returns:
        - The created list of Image objects
        """

        try:
            print(f"\nLOGGER: --> Starting image creation in [ {environment.create_input} ]")
            
            images: list[Image] = []
            
            if not os.path.exists(f"{environment.create_input}"):          # If the folder for fetching images from does not exist yet, create it
                os.makedirs(f"{environment.create_input}")
                print(f"\nLOGGER: The folder {environment.create_input} has been created where you are able to add the images you would like to store")

            files = os.listdir(environment.create_input)

            for file in files:
                if file.endswith(".SAFE"):                  # SAFE creation requires the foldername and the granule string
                    print(f"\nLOGGER: > Found {file}, creating .SAFE Image")

                    foldername: str = os.path.splitext(os.path.basename(file))[0]
                    granule: str = self.get_granule(foldername, environment.create_input)
                    if (granule != None):
                        image: Image = self.factory.safe_create(foldername, granule, environment)
                        images.append(image)                # Adding the created Image object to the images to be returned

                        print(f"\nLOGGER: < .SAFE image for {foldername} created")

                    else:
                        print(f"\nEXCEPTION - Image granule invalid. Skipping.")

                elif file.endswith(".tif"):                 # tif creation requires only the filename
                    print(f"\nLOGGER: > Found {file}, creating .tif Image")

                    filename: str = os.path.splitext(os.path.basename(file))[0]
                    image: Image = self.factory.tif_create(filename, environment)
                    images.append(image)                    # Adding the created Image object to the images to be returned
            
                    print(f"\nLOGGER: < .tif image for {filename} created")
        
            print(f"\nLOGGER: <-- Finished image creation in [ {environment.create_input} ]")
                
            return images
        
        except Exception as e:
            print(f"\nEXCEPTION: {e}")
            return []


class Renderer():

    def render(self, img: Image, name: str, environment: Environment = Environment()):
        """Render the algorithm specified by the given name on the specified Image object

        Keyword arguments:
        - img         -- The Image object on which the algorithm should be applied
        - name        -- The name of the algorithm to be applied
        - environment -- (Optional) Environment object with any changes in execution logic of the application (see Environment docs.)
        """
        
        image_path: str = funcs[name](img, environment)    # Perform the rendering of the specified algorithm using dictionary lookup
        match name:                                             # And add the path to this rendered file to the respective Image field
            case "TC":
                img.tc = image_path
            case "NDVI":
                img.ndvi = image_path
            case "NDWI":
                img.ndwi = image_path
            case "NDMI":
                img.ndmi = image_path      

    def render_images(self, images: list[Image], environment: Environment = Environment()) -> list[Image]:
        """Render all algorithms for all the provided images

        Keyword arguments:
        - images      -- The list of Image objects to be rendered
        - environment -- (Optional) Environment object with any changes in execution logic of the application (see Environment docs.)

        Returns:
        - The updated list of Image objects
        """

        try:
            print(f"\nLOGGER: --> Starting algorithm rendering")
            
            for image in images:    # Looping over all images, render all available algorithms

                print(f"\nLOGGER: > Rendering algorithms for Image {image.title}")

                self.render(image, "TC", environment=environment)
                self.render(image, "NDVI", environment=environment)
                self.render(image, "NDWI", environment=environment)
                self.render(image, "NDMI", environment=environment)

                print(f"\nLOGGER: < Algorithms for Image {image.title} rendered")
                
            print(f"\nLOGGER: <-- Finished algorithm rendering")

            return images
        
        
        except Exception as e:
            print(f"\nEXCEPTION: {e}")
            return []


class Tiler():
    # img#id/alg#id/level#id/x/y

    def tile_image(self, img: Image, rendered_path: str, alg_id: int, environment: Environment = Environment()):
        """Tile the algorithm output of the given image

        Keyword arguments:
        - img           -- The Image object for which the algorithm output should be tiled
        - rendered_path -- The path where the rendered algorithm output can be found
        - alg_id        -- The ID of the algorithm to be tiled ( 0 - TC | 1 - NDVI | 2 - NDWI | 3 - NDMI )
        - environment   -- (Optional) Environment object with any changes in execution logic of the application (see Environment docs.)
        """
        
        try:
            if not os.path.exists(environment.temp_output):          # If the folder for the temp images from does not exist yet, create it
                os.makedirs(environment.temp_output)
                print(f"\nLOGGER: The folder {environment.temp_output} has been created where the temporary tiling data will be stored")
            
            path_to_img_tiles: str = f"{environment.tile_output}{img.img_id}/{alg_id}/"             # Tiles_Location/img#id/alg#id/
            img_title_bare: str = os.path.splitext(os.path.basename(img.title))[0]                  # filename
            path_to_temp_img: str = f"{environment.temp_output}{img_title_bare}.tif"

            if not os.path.exists(path_to_img_tiles):          # If the folder for the tiled images from does not exist yet, create it
                os.makedirs(path_to_img_tiles)
                print(f"\nLOGGER: The folder {path_to_img_tiles} has been created where the tile data will be stored")

            # Using the GDAL libraries for tiling
            # os.system(f"gdal_translate -of {output_format} -ot {output_type} -scale {rendered_path} {path_to_temp_img}")
            os.system(f"gdal_translate -of {output_format} -ot {output_type} -scale {min_val} {max_val} -outsize {width_percentage}% {height_percentage}% {rendered_path} {path_to_temp_img}")
            os.system(f"gdal2tiles.py -z {start_level}-{end_level} -w {web_viewer} --tilesize={tilesize} {path_to_temp_img} {path_to_img_tiles}")
        
        except Exception as e:
            print(f"\nEXCEPTION: {e}")

    def tile_images(self, images: list[Image], environment: Environment = Environment()):
        """Tile the algorithm output of all given images

        Keyword arguments:
        - images     -- The Image objects for which the algorithm output should be tiled
        - environment   -- (Optional) Environment object with any changes in execution logic of the application (see Environment docs.)
        """
        
        print(f"\nLOGGER: --> Starting tiling")

        for img in images:      # Looping over all images, if their respective algorithm field is active, try to tile it

            print(f"\nLOGGER: > Tiling algorithm output for Image {img.title}")

            if (img.tc != None and img.tc != ""):
                 self.tile_image(img, img.tc, 0, environment=environment)

            if (img.ndvi != None and img.ndvi != ""):
                 self.tile_image(img, img.ndvi, 1, environment=environment)

            if (img.ndwi != None and img.ndwi != ""):
                 self.tile_image(img, img.ndwi, 2, environment=environment)

            if (img.ndmi != None and img.ndmi != ""):
                 self.tile_image(img, img.ndmi, 3, environment=environment)

            print(f"\nLOGGER: < Algorithm output for Image {img.title} tiled")
            
        print(f"\nLOGGER: <-- Finished tiling")


class Starter():
    def empty_dir(self, path):
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

    def cleanup(self, environment: Environment = Environment()):
        """Clean the file storage from existing temp files as well as leaflet.html
        files and tilemapresource.xml files
        """
        
        print(f"\nLOGGER: --> Starting cleanup of file storage")

        try:

            self.empty_dir(environment.temp_output)

            # Ugly but I wasn't sure how else to do this. TOO MANY FOLDERS
            img_folders = os.listdir(environment.tile_output)

            for img_folder in img_folders:

                if (os.path.isdir(f"{environment.tile_output}{img_folder}")):
                    alg_folders = os.listdir(f"{environment.tile_output}{img_folder}")

                    for alg_folder in alg_folders:

                        if (os.path.isdir(f"{environment.tile_output}{img_folder}{alg_folder}")):
                            level_folders = os.listdir(f"{environment.tile_output}{img_folder}{alg_folder}")

                            for level_folder in level_folders:

                                if (not os.path.isdir(f"{environment.tile_output}{img_folder}{alg_folder}{level_folder}")):

                                    if (os.path.exists(f"{environment.tile_output}{img_folder}{alg_folder}{level_folder}leaflet.html")):
                                        os.remove(f"{environment.tile_output}{img_folder}{alg_folder}{level_folder}leaflet.html")

                                    if (os.path.exists(f"{environment.tile_output}{img_folder}{alg_folder}{level_folder}tilemapresource.xml")):
                                        os.remove(f"{environment.tile_output}{img_folder}{alg_folder}{level_folder}tilemapresource.xml")

            print(f"\nLOGGER: <-- Cleaned up file storage")

        except Exception as e:
            print(f"\nEXCEPTION: {e}")

    def start_creating(self, environment: Environment = Environment()) -> list[Image]:
        """Start the creation of all images located in the given image folder
        and store them in the assigned output folder

        Keyword arguments:
        - environment -- (Optional) Environment object with any changes in execution logic of the application (see Environment docs.)
        
        Returns:
        - The created list of Image objects
        """

        creator: Creator = Creator()
        created: list[Image] = creator.create_images(environment=environment)     # Create the images
        
        return created
    
    def start_rendering(self, images: list[Image], environment: Environment = Environment()) -> list[Image]:
        """Start the rendering of all algorithms for all the provided images

        Keyword arguments:
        - images      -- The list of Image objects to be rendered
        - environment -- (Optional) Environment object with any changes in execution logic of the application (see Environment docs.)

        Returns:
        - The updated list of Image objects
        """

        renderer: Renderer = Renderer()
        rendered: list[Image] = renderer.render_images(images, environment=environment)      # Render the images
        
        return rendered
    
    def start_tiling(self, rendered: list[Image], environment: Environment = Environment()):
        """Start the tiling of the algorithm output of all given images

        Keyword arguments:
        - images      -- The Image objects for which the algorithm output should be tiled
        - environment -- (Optional) Environment object with any changes in execution logic of the application (see Environment docs.)
        """

        tiler: Tiler = Tiler()
        tiler.tile_images(rendered, environment=environment)                                 # Tile the images
    
    def start(self, environment: Environment = Environment()):
        """Startup the logic to-be-executed at the start of the server or tests. Will create,
        renpder and tile all images in the specified locations

        Keyword arguments:
        - environment   -- (Optional) Environment object with any changes in execution logic of the application (see Environment docs.)
        """
        
        created = []
        if (environment.create):
            # Create the images
            created: list[Image] = self.start_creating(environment=environment)   
            
        rendered = []
        if (environment.render):
            # Render the images
            rendered: list[Image] = self.start_rendering(created, environment=environment)   
            
        if (environment.tile):
            # Tile the images
            self.start_tiling(rendered, environment=environment)                         
            self.cleanup(environment=environment)
    
