from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import scale
import numpy as np


def k_means_fit_images(input_images):
    reduced_data = np.reshape(input_images, (input_images.shape[0], input_images.shape[1]*input_images.shape[2]*input_images.shape[3]))
    k_means = KMeans().fit(reduced_data)
    return k_means


def k_means_find_cluster(target_tile, k_means):
    img = np.reshape(target_tile, (1, target_tile.shape[0]*target_tile.shape[1]*target_tile.shape[2]))
    cluster_num = k_means.predict(img)
    return (i for i, x in enumerate(k_means.labels_) if x == cluster_num)
