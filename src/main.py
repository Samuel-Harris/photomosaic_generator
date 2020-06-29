from PhotomosaicGenerator import PhotomosaicGenerator
from GUI import run

from MSE_tile_matcher import MSE_match_images
from K_means_clusterer import k_means_fit_images, k_means_find_cluster
import time
import os


def main():
    photomosaic_generator = PhotomosaicGenerator()
    run(photomosaic_generator)


if __name__ == '__main__':
    main()

# def main():
#     # input_directory_path = os.path.abspath(input("What is the input photo directory path?"))
#     # C:\\my_stuff\\photomosaic_generator\\extremely_reduced_input_photos
#     input_directory_path = os.path.abspath(r"..\reduced_input_photos")
#
#     # output_directory_path = os.path.abspath(input("What is the output directory path?"))
#     # C:\\my_stuff\\photomosaic_generator\\output_photos
#     output_directory_path = os.path.abspath(r"..\output_photos\output_image.jpg")
#
#     # target_image_file_path = os.path.abspath(input("What is the target image?"))
#     # C:\\my_stuff\\photomosaic_generator\\target_image\\target_image.jpg
#     target_image_file_path = os.path.abspath(r"..\target_image\target_image.jpg")
#
#     # x_tiles = input("How many images in a row?")
#     x_tiles = 100
#     # y_tiles = input("How many images in a column?")
#     y_tiles = 100
#
#     total_start = time.time()
#
#     photomosaic_generator = PhotomosaicGenerator()
#
#     photomosaic_generator.set_target_image(target_image_file_path)
#
#     start = time.time()
#     # pre-processing target image
#     photomosaic_generator.pre_process_target(x_tiles, y_tiles)
#     end = time.time()
#     print("pre-processing target image: ", end - start, "s")
#
#     photomosaic_generator.set_input_directory_path(input_directory_path)
#
#     start = time.time()
#     # pre-processing input images
#     photomosaic_generator.pre_process_input(threads=7)
#     end = time.time()
#     print("pre-processing input images: ", end - start, "s")
#
#     start = time.time()
#     # fitting input images into clusters
#     photomosaic_generator.fit_clusters(k_means_fit_images, k_means_find_cluster)
#     end = time.time()
#     print("clustering input images: ", end - start, "s")
#
#     start = time.time()
#     # setting image matcher
#     photomosaic_generator.set_image_matcher(MSE_match_images)
#     end = time.time()
#     print("setting image matcher: ", end - start, "s")
#
#     start = time.time()
#     # matching tiles
#     photomosaic_generator.match_tiles(processes=4)
#     end = time.time()
#     print("matching tiles: ", end - start, "s")
#
#     start = time.time()
#     # combining images
#     photomosaic_generator.combine_images()
#     end = time.time()
#     print("combining images: ", end - start, "s")
#
#     total_end = time.time()
#
#     print("total time: ", total_end - total_start, "s")
#
#     photomosaic_generator.save_image(output_directory_path)
#
#     photomosaic_generator.show_image()
#
#
# if __name__ == '__main__':
#     main()
