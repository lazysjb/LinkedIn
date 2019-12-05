from abc import ABC, abstractmethod

import numpy as np
from scipy.spatial.distance import mahalanobis
from scipy.stats import entropy


class DistanceMetric(ABC):

    def __init__(self, X, y, standardize=False):
        super().__init__()

        if standardize:
            self.X, self.y = self.standardize(X, y)
        else:
            self.X = X
            self.y = y

        self.n = self.X.shape[0]

    @abstractmethod
    def calc_distance(self):
        pass

    @staticmethod
    def standardize(X, y):
        """Get standard dev vector from X, and normalize both X and y"""
        stdev = X.std(axis=0)
        X_std = X / stdev
        y_std = y / stdev
        return X_std, y_std


class Euclidean(DistanceMetric):

    def __init__(self, X, y, standardize=False):
        super().__init__(X, y, standardize=standardize)

    def calc_distance(self):
        dist = np.linalg.norm(self.X - self.y, axis=1)
        return dist


class Cosine(DistanceMetric):

    def __init__(self, X, y, standardize=False):
        super().__init__(X, y, standardize=standardize)

    def calc_distance(self):
        """Define cosine distance as 1 - cosine similarity"""
        cosine_sim_num = self.X.dot(self.y)
        cosine_sim_denom = np.linalg.norm(self.X, axis=1) * np.linalg.norm(self.y)
        cosine_similarity = cosine_sim_num / cosine_sim_denom
        dist = 1 - cosine_similarity

        return dist


class Mahalanobis(DistanceMetric):

    def __init__(self, X, y, standardize=False):
        super().__init__(X, y, standardize=standardize)

    def calc_distance(self):
        V = np.cov(self.X, rowvar=False)
        VI = np.linalg.inv(V)

        dist = np.zeros(self.n)

        for i in range(self.n):
            dist[i] = mahalanobis(self.X[i], self.y, VI)

        return dist


class JSDivergence(DistanceMetric):

    def __init__(self, X, y, standardize=False):
        super().__init__(X, y, standardize=standardize)

    def calc_distance(self):
        """Calculate JS Divergence"""
        # https://stats.stackexchange.com/questions/7630/
        # clustering-should-i-use-the-jensen-shannon-divergence-or-its-square
        X_normalized = (self.X / self.X.sum(axis=1).reshape(-1, 1))
        y_normalized = self.y / self.y.sum()
        M = 0.5 * (X_normalized + y_normalized)

        dist = np.zeros(self.n)

        for i in range(self.n):
            # base 2 is following the convention in "Trajectories" paper
            kl_1 = entropy(X_normalized[i], M[i], base=2)
            kl_2 = entropy(y_normalized, M[i], base=2)
            dist[i] = 0.5 * (kl_1 + kl_2)

        # returning sqrt of the JS Divergence as a distance metric as suggested by
        # the statexchange link above
        return np.sqrt(dist)
