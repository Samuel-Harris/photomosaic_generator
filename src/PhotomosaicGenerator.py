import ctypes
from skimage import io
from skimage.transform import resize
from multiprocessing.pool import ThreadPool
from multiprocessing import Pool, Array
from contextlib import closing
from itertools import chain
from functools import partial
from os import walk
import numpy as np
import sys
from sklearn.cluster import KMeans
from scipy import stats

class PhotomosaicGenerator:
    def __init__(self):
        self.input_images = None
        self.input_image_colours = None
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
        self.match_image = None
        self.find_cluster = None

    def set_target_image(self, target_image_file_path):
        self.target_image = io.imread(target_image_file_path)

    def pre_process_target(self, x_tiles, y_tiles):
        self.y_tiles = y_tiles
        self.x_tiles = x_tiles
        self.tile_height = self.target_image.shape[0] // y_tiles
        self.tile_width = self.target_image.shape[1] // x_tiles
        self.target_image = resize(self.target_image, (self.tile_height * y_tiles, self.tile_width * x_tiles), anti_aliasing=True)

    def set_input_directory_path(self, input_directory_path):
        self.input_directory_path = input_directory_path

    def pre_process_input(self, threads=7):
        self.input_images = []
        self.input_image_colours = []
        with closing(ThreadPool(threads)) as p:
            for dir_path, subdir_names, file_names in walk(self.input_directory_path):
                p.map(partial(self.pre_process_input_image, dir_path=dir_path), file_names)
        self.input_images = np.array(self.input_images)

    def pre_process_input_image(self, file_name, dir_path):
        if file_name[-4:] == '.jpg':
            img = resize(io.imread(dir_path + "\\" + file_name), (self.tile_height, self.tile_width), anti_aliasing=True)
            self.input_images.append(img)
            pixels = list(chain(*img))
            k_means = KMeans(n_clusters=4).fit(pixels)
            self.input_image_colours.append(k_means.cluster_centers_[stats.mode(k_means.labels_)[0][0]])

    # def fit_clusters(self, cluster_fit, find_cluster):
    #     self.clusters = cluster_fit(self.input_images)
    #     self.find_cluster = find_cluster

    # def match_tiles(self, processes=7):
    #     shared_arr = Array(ctypes.c_double, [0.0] * self.y_tiles * self.x_tiles)
    #     # self.tile_cluster_indexes = np.zeros((self.y_tiles, self.x_tiles))
    #
    #     with closing(Pool(processes=processes, initializer=self.match_tile_process_init,
    #                       initargs=(shared_arr, self.target_image, self.tile_height, self.tile_width, self.find_cluster,
    #                                 self.clusters, self.match_image, self.input_images, self.y_tiles, self.x_tiles,))) \
    #             as p:
    #         p.map(self.match_tile, ((y, x) for y in range(self.y_tiles) for x in range(self.x_tiles)))
    #     arr = np.frombuffer(shared_arr.get_obj())
    #     self.tile_cluster_indexes = arr.reshape((self.y_tiles, self.x_tiles))

    def match_tiles(self, processes=7):
        self.tile_cluster_indexes = np.zeros((self.y_tiles, self.x_tiles))

        with closing(ThreadPool(processes=1)) as p:
            p.map(self.match_tile, ((y, x) for y in range(self.y_tiles) for x in range(self.x_tiles)))

    def match_tile(self, position):
        y, x = position
        target_tile = self.target_image[y * self.tile_height:(y + 1) * self.tile_height, x * self.tile_width:(x + 1) * self.tile_width]
        colour = np.mean(list(chain(*target_tile)), axis=0)
        self.tile_cluster_indexes[y][x] = min(range(len(self.input_image_colours)), key=lambda i: sum(abs(self.input_image_colours[i]-colour)))

    # def match_tiles(self, processes=7):
    #     shared_arr = Array(ctypes.c_double, [0.0] * self.y_tiles * self.x_tiles)
    #     # self.tile_cluster_indexes = np.zeros((self.y_tiles, self.x_tiles))
    #
    #     with closing(ThreadPool(processes=processes, initializer=self.match_tile_process_init,
    #                             initargs=(shared_arr, self.target_image, self.tile_height, self.tile_width,
    #                                       self.find_cluster, self.clusters, self.match_image, self.input_images,
    #                                       self.y_tiles, self.x_tiles,))) as p:
    #         p.map(self.match_tile, ((y, x) for y in range(self.y_tiles) for x in range(self.x_tiles)))
    #     arr = np.frombuffer(shared_arr.get_obj())
    #     self.tile_cluster_indexes = arr.reshape((self.y_tiles, self.x_tiles))
    #
    # @staticmethod
    # def match_tile_process_init(shared_arr_, target_image_, tile_height_, tile_width_, find_cluster_, clusters_,
    #                             match_image_,
    #                             input_images_, y_tiles_, x_tiles_):
    #     global shared_arr
    #     global target_image
    #     global tile_height
    #     global tile_width
    #     global find_cluster
    #     global clusters
    #     global match_image
    #     global input_images
    #     global y_tiles
    #     global x_tiles
    #
    #     shared_arr = shared_arr_
    #     target_image = target_image_
    #     tile_height = tile_height_
    #     tile_width = tile_width_
    #     find_cluster = find_cluster_
    #     clusters = clusters_
    #     match_image = match_image_
    #     input_images = input_images_
    #     y_tiles = y_tiles_
    #     x_tiles = x_tiles_
    #
    # @staticmethod
    # def match_tile(position):
    #     y, x = position
    #     target_tile = target_image[y * tile_height:(y + 1) * tile_height, x * tile_width:(x + 1) * tile_width]
    #     cluster = find_cluster(target_tile, clusters)
    #     best_score = -sys.float_info.max
    #     for i in cluster:
    #         score = match_image(target_tile, input_images[i])
    #         if score > best_score:
    #             arr = np.frombuffer(shared_arr.get_obj())
    #             arr = arr.reshape((y_tiles, x_tiles))
    #             arr[y][x] = i
    #             if score > -3.5:
    #                 break
    #             else:
    #                 best_score = score

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

    def save_image(self, output_directory_path):
        io.imsave(output_directory_path, self.output_image, plugin='pil')

    def get_image(self):
        return self.output_image

    def show_image(self):
        io.imshow(self.target_image)
        io.show()
        io.imshow(self.output_image)
        io.show()
