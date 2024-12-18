from django.core.management.base import BaseCommand
from ...startup import Starter
from ...models import Environment
import sys
import api.views

class Command(BaseCommand):
    help = "Starts the application"

    def add_arguments(self, parser):
        parser.add_argument("-c", action='store_true', help='Enables the creation of image objects')
        parser.add_argument("-ci", type=str, help='Overrides the location where to-be-created images are stored')
        parser.add_argument("-co", type=str, help='Overrides the location where created image band data will be stored')
        parser.add_argument("-cf", action='store_true', help='Forces the application to recreate image band data')
        parser.add_argument("-r", action='store_true', help='Enables the rendering of algorithms')
        parser.add_argument("-ro", type=str, help='Overrides the location where rendered algorithm output will be stored')
        parser.add_argument("-rf", action='store_true', help='Forces the application to rerender the algorithm output')
        parser.add_argument("-t", action='store_true', help='Enables the tiling of algorithm output')
        parser.add_argument("-to", type=str, help='Overrides the location where tiled images will be stored')
        parser.add_argument("-tmp", type=str, help='Overrides the location where temporary images will be stored while tiling')

    def handle(self, *args, **options):
        environment: Environment = Environment()
        
        environment.create = options["c"]
        environment.render = options["r"]
        environment.tile = options["t"]
        environment.recreate = options["cf"]
        environment.rerender = options["rf"]
        
        if (options["ci"]):
            environment.create_input = options["ci"]
            
        if (options["co"]):
            environment.create_output = options["co"]
            
        if (options["ro"]):
            environment.render_output = options["ro"]
            
        if (options["to"]):
            environment.tile_output = options["to"]
            
        if (options["tmp"]):
            environment.temp_output = options["tmp"]
        
        Starter().start(environment=environment)
        api.views.TILES_DIRECTORY = environment.tile_output
        print(api.views.TILES_DIRECTORY)
