import contextlib
import gc
import itertools
import os
import sys
from multiprocessing import pool
from os import path
import numpy as np
from sklearn import cluster
from skimage import color, io, transform, util


class PhotomosaicGenerator:
    """A class to generate photomosaics

    :method __init__: initialises photomosaic generator variables
    :method set_target_image: sets the image that the photomosaic generator is recreating
    :method set_input_directory_path: sets the directory from which the photomosaic tiles are retrieved
    :method pre_process_images: pre-processes the target image and images used as tiles for the photomosaic
    :method generate_photomosaic: creates a photomosaic from the pre-processed tiles and target image
    :method can_generate_photomosaic: checks whether a photomosaic can be created
    :method can_save_image: checks whether the output image can be saved (can be target image or photomosaic, whichever
     was last set/created)
    :method save_image: saves output image in given location
    :method get_output_image: returns a copy of the output image
    :method get_target_image: returns a copy of the target image
    """

    def __init__(self):
        """Initialise the variables of the photomosaic generator."""

        self.__target_image = None
        self.__target_image_file_path = None

        self.__input_images = None
        self.__redo_pre_processing = True  # true if target image location or input image directory has changed else
        # false
        self.__input_directory_path = None

        self.__clusters = None
        self.__tile_cluster_indexes = None

        self.__column_count = None
        self.__row_count = None
        self.__tile_height = None
        self.__tile_width = None

        self.__output_image = None

    def set_target_image(self, target_image_file_path):
        """Sets the target image of the photomosaic generator.

        :param target_image_file_path: the path to the target image
        """

        if self.__target_image_file_path != target_image_file_path:
            self.__target_image_file_path = target_image_file_path
            self.__redo_pre_processing = True
            self.__target_image = io.imread(target_image_file_path)
            if self.__target_image.shape[2] == 4:
                self.__target_image = color.rgba2rgb(self.__target_image)
            self.__target_image = util.img_as_ubyte(self.__target_image)
            self.__output_image = self.__target_image

    def __pre_process_target(self):
        """Resizes the target image so that it can have tiles of equal size."""

        self.__tile_height = self.__target_image.shape[0] // self.__row_count if \
            self.__row_count < self.__target_image.shape[0] else 1

        self.__tile_width = self.__target_image.shape[1] // self.__column_count if \
            self.__column_count < self.__target_image.shape[1] else 1

        self.__target_image = transform.resize(self.__target_image, (self.__tile_height * self.__row_count,
                                                                     self.__tile_width * self.__column_count),
                                               anti_aliasing=True, preserve_range=True).astype(np.uint8)

    def set_input_directory_path(self, input_directory_path):
        """Stores the directory of the input images that will be used as tiles.

        :param input_directory_path: the path to the directory of the input images
        :return:
        """

        if self.__input_directory_path != input_directory_path:
            self.__input_directory_path = input_directory_path
            self.__redo_pre_processing = True

    def __pre_process_tiles(self, threads=7):
        """Resizes and stores each image in the input image directory so that they can be used as tiles.

        :param threads: the number of threads used to do this task (default 7)
        """

        del self.__input_images
        gc.collect()  # garbage collects previous tiles so that multiple sets of tiles aren't held in memory
        # simultaneously
        with contextlib.closing(pool.ThreadPool(threads)) as p:
            self.__input_images = \
                np.array(p.map(self.__pre_process_tile,
                               filter(lambda filename: (filename.endswith('.jpg') or filename.endswith('.png')) and
                                                       path.isfile(path.join(self.__input_directory_path, filename)),
                                      os.listdir(self.__input_directory_path))))

    def __pre_process_tile(self, filename):
        """Opens an image and resizes it to be the correct height and width for a tile.

        :param filename: the name of the image
        :return: the resized tile
        """

        raw_img = io.imread(self.__input_directory_path + "\\" + filename)
        if raw_img.shape[2] == 4:
            raw_img = color.rgba2rgb(raw_img)
        raw_img = util.img_as_ubyte(raw_img)
        raw_img = transform.resize(raw_img, (self.__tile_height, self.__tile_width),
                                   anti_aliasing=False, preserve_range=True).astype(np.uint8)
        return util.img_as_ubyte(raw_img)

    def __fit_clusters(self):
        """Fits the tiles into clusters."""

        reduced_data = np.reshape(self.__input_images, (self.__input_images.shape[0],
                                                        self.__input_images.shape[1] * self.__input_images.shape[2] *
                                                        self.__input_images.shape[3]))
        self.__clusters = cluster.KMeans(n_clusters=min(24, len(self.__input_images))).fit(reduced_data)


    def pre_process_images(self, column_count, row_count):
        """Pre-processes the target image and images in the input image directory so that they are ready to be made into
        a photomosaic.

        :param column_count: the number of tiles in each row
        :param row_count: the number of tiles in each column
        """

        if self.__column_count != column_count or self.__row_count != row_count:
            self.__column_count = column_count
            self.__row_count = row_count
            self.__redo_pre_processing = True

        if self.__redo_pre_processing:
            self.__pre_process_target()
            self.__pre_process_tiles()
            self.__redo_pre_processing = False

        self.__fit_clusters()

    def __match_tiles(self):
        """Matches appropriate tiles to each position in the photomosaic."""

        self.__tile_cluster_indexes = np.zeros((self.__row_count, self.__column_count))

        for y, x in ((y, x) for y in range(self.__row_count) for x in range(self.__column_count)):
            self.__match_tile((y, x))

    def __match_tile(self, position):
        """Matches an appropriate tile to a position in the photomosaic."""

        y, x = position
        target_tile = self.__target_image[y * self.__tile_height:(y + 1) * self.__tile_height,
                                          x * self.__tile_width:(x + 1) * self.__tile_width]

        img = np.array((target_tile.flatten(),))
        cluster_num = self.__clusters.predict(img)
        img_indexes = (i for i, x in enumerate(self.__clusters.labels_) if x == cluster_num)

        best_score = -sys.float_info.max
        for i in img_indexes:
            score = -abs(np.linalg.norm(target_tile - self.__input_images[i]))
            if score > best_score:
                self.__tile_cluster_indexes[y, x] = i
                if score > -3.5:
                    break
                else:
                    best_score = score

    def __combine_tiles(self):
        """Combines selected tiles to create the photomosaic."""

        self.__tile_cluster_indexes = itertools.chain(*self.__tile_cluster_indexes)
        self.__output_image = self.__input_images[int(next(self.__tile_cluster_indexes))]

        for x in range(1, self.__column_count):
            self.__output_image = np.concatenate(
                (self.__output_image, self.__input_images[int(next(self.__tile_cluster_indexes))]), axis=1)

        for y in range(1, self.__row_count):
            columns = self.__input_images[int(next(self.__tile_cluster_indexes))]
            for x in range(1, self.__column_count):
                columns = np.concatenate((columns, self.__input_images[int(next(self.__tile_cluster_indexes))]), axis=1)
            self.__output_image = np.concatenate((self.__output_image, columns), axis=0)

        self.__output_image = util.img_as_ubyte(self.__output_image)

    def generate_photomosaic(self):
        """Creates a photomosaic from the pre-processed tiles and target image"""

        self.__match_tiles()
        self.__combine_tiles()

    def can_generate_photomosaic(self):
        """Checks whether a photomosaic can be created. Raises a MissingComponentError exception with appropriate error
        message if not.
        """

        if self.__input_directory_path is None:
            if self.__target_image is None:
                raise MissingComponentError('Cannot generate image. Input directory and target image are missing.')
            else:
                raise MissingComponentError('Cannot generate image. Input directory is missing.')
        elif self.__target_image is None:
            raise MissingComponentError('Cannot generate image. Target image is missing.')

    def can_save_image(self):
        """Checks whether the output image can be saved (can be target image or photomosaic, whichever was last
         set/created). Raises a MissingComponentError exception with appropriate error message if not.
        """

        if self.__output_image is None:
            raise MissingComponentError('Cannot save image. You must generate an image first before it can be saved.')

    def save_image(self, output_directory_path):
        """Saves output image in given location.

        :param output_directory_path: the location to save the output image in
        """

        io.imsave(output_directory_path, self.__output_image.astype(np.uint8), quality=100, plugin='pil')

    def get_output_image(self):
        """Returns a copy of the output image"""

        return self.__output_image.copy()

    def get_target_image(self):
        """Returns a copy of the target image"""

        return self.__target_image.copy()


class MissingComponentError(Exception):
    """A class specifically for exceptions involving using photomosaic generator methods without necessary components
    (e.g. calling can_save_image without there being an output_image to save).
    """

    pass
