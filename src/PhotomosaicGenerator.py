import ctypes

from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import scale
from skimage import io
from skimage.color import rgba2rgb
from skimage.transform import resize
from multiprocessing.pool import ThreadPool
from multiprocessing import Pool, Array
from contextlib import closing
from itertools import chain
from functools import partial
from os import walk
import numpy as np
import sys


class PhotomosaicGenerator:
    def __init__(self):
        self.input_images = None
        self.input_directory_path = None
        self.target_image = None
        self.output_image = None
        self.x_tiles = None
        self.y_tiles = None
        self.tile_height = None
        self.tile_width = None
        self.dir_path = None
        self.scores = None
        self.clusters = None
        self.tile_cluster_indexes = None

    def set_target_image(self, target_image_file_path):
        self.target_image = io.imread(target_image_file_path, plugin='matplotlib')
        if self.target_image.shape[2] == 4:
            self.target_image = rgba2rgb(self.target_image).astype(np.float64)  # **************** make image datatype uniform ***************
        self.output_image = self.target_image

    def pre_process_target(self, x_tiles, y_tiles):
        self.y_tiles = y_tiles
        self.x_tiles = x_tiles
        self.tile_height = self.target_image.shape[0] // y_tiles
        self.tile_width = self.target_image.shape[1] // x_tiles
        self.target_image = resize(self.target_image, (self.tile_height * y_tiles, self.tile_width * x_tiles),
                                   anti_aliasing=True)

    def set_input_directory_path(self, input_directory_path):
        self.input_directory_path = input_directory_path

    def pre_process_input(self, threads=7):
        self.input_images = []
        with closing(ThreadPool(threads)) as p:
            for dir_path, subdir_names, file_names in walk(self.input_directory_path):
                p.map(partial(self.pre_process_input_image, dir_path=dir_path), file_names)
        self.input_images = np.array(self.input_images)

    def pre_process_input_image(self, file_name, dir_path):
        if file_name[-4:] == '.jpg':
            self.input_images.append(resize(io.imread(dir_path + "\\" + file_name), (self.tile_height, self.tile_width),
                                            anti_aliasing=True))

    def fit_clusters(self):
        reduced_data = np.reshape(self.input_images, (self.input_images.shape[0],
                                                      self.input_images.shape[1] * self.input_images.shape[2] *
                                                      self.input_images.shape[3]))
        self.clusters = KMeans().fit(reduced_data)

    def find_cluster(self, target_tile, k_means):
        img = np.array((target_tile.flatten(),))
        cluster_num = k_means.predict(img)
        return (i for i, x in enumerate(k_means.labels_) if x == cluster_num)

    def match_tiles(self, processes=7):
        shared_arr = Array(ctypes.c_double, [0.0] * self.y_tiles * self.x_tiles)

        with closing(ThreadPool(processes=processes, initializer=self.match_tile_process_init,
                                initargs=(
                                shared_arr, self.target_image, self.tile_height, self.tile_width, self.find_cluster,
                                self.clusters, self.input_images, self.y_tiles, self.x_tiles,))) as p:
            p.map(self.match_tile, ((y, x) for y in range(self.y_tiles) for x in range(self.x_tiles)))
        arr = np.frombuffer(shared_arr.get_obj())
        self.tile_cluster_indexes = arr.reshape((self.y_tiles, self.x_tiles))

    @staticmethod
    def match_tile_process_init(shared_arr_, target_image_, tile_height_, tile_width_, find_cluster_, clusters_,
                                input_images_, y_tiles_, x_tiles_):
        global shared_arr
        global target_image
        global tile_height
        global tile_width
        global find_cluster
        global clusters
        global input_images
        global y_tiles
        global x_tiles

        shared_arr = shared_arr_
        target_image = target_image_
        tile_height = tile_height_
        tile_width = tile_width_
        find_cluster = find_cluster_
        clusters = clusters_
        input_images = input_images_
        y_tiles = y_tiles_
        x_tiles = x_tiles_

    @staticmethod
    def match_tile(position):
        y, x = position
        target_tile = target_image[y * tile_height:(y + 1) * tile_height, x * tile_width:(x + 1) * tile_width]
        cluster = find_cluster(target_tile, clusters)
        best_score = -sys.float_info.max
        for i in cluster:
            score = -abs(np.linalg.norm(target_tile - input_images[i]))
            if score > best_score:
                arr = np.frombuffer(shared_arr.get_obj())
                arr = arr.reshape((y_tiles, x_tiles))
                arr[y][x] = i
                if score > -3.5:
                    break
                else:
                    best_score = score

    def combine_images(self):
        self.tile_cluster_indexes = chain(*self.tile_cluster_indexes)
        self.output_image = self.input_images[int(next(self.tile_cluster_indexes))]
        for x in range(1, self.x_tiles):
            self.output_image = np.concatenate(
                (self.output_image, self.input_images[int(next(self.tile_cluster_indexes))]), axis=1)

        for y in range(1, self.y_tiles):
            columns = self.input_images[int(next(self.tile_cluster_indexes))]
            for x in range(1, self.x_tiles):
                columns = np.concatenate((columns, self.input_images[int(next(self.tile_cluster_indexes))]), axis=1)
            self.output_image = np.concatenate((self.output_image, columns), axis=0)

    def generate_image(self):
        if self.input_directory_path is None:
            if self.target_image is None:
                raise MissingComponentError('Cannot generate image - Input directory and target image are missing')
            else:
                raise MissingComponentError('Cannot generate image - Input directory is missing')
        elif self.target_image is None:
            raise MissingComponentError('Cannot generate image - Target image is missing')

        print('pre-processing target')
        self.pre_process_target(100, 100)

        print('pre-processing input')
        self.pre_process_input(threads=7)

        print('fitting clusters')
        self.fit_clusters()

        print('matching tiles')
        self.match_tiles()

        print('combining images')
        self.combine_images()

    def can_save_image(self):
        return 'Cannot save image - You must generate an image first before it can be saved' if self.output_image is None else None

    def save_image(self, output_directory_path):
        # if self.output_image is None:
        #     raise MissingComponentError('Cannot save image - You must generate an image first before it can be saved')
        if self.output_image.dtype == np.float64:
            self.output_image *= 255
            self.output_image = self.output_image.astype('int8')
        io.imsave(output_directory_path, self.output_image.astype(np.uint8), quality=100)

    def get_image(self):
        return self.output_image.copy()

    def get_target_image(self):
        return self.target_image.copy()


class MissingComponentError(Exception):
    pass
