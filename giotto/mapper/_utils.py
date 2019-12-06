from inspect import signature
from functools import partial

import numpy as np

from joblib import Parallel, delayed

from sklearn.pipeline import FeatureUnion, _transform_one, _fit_transform_one
from sklearn.preprocessing import FunctionTransformer


class ListFeatureUnion(FeatureUnion):
    def fit_transform(self, X, y=None, **fit_params):
        """Fit all transformers, transform the data and concatenate results.
        Parameters
        ----------
        X : iterable or array-like, depending on transformers
            Input data to be transformed.
        y : array-like, shape (n_samples, ...), optional
            Targets for supervised learning.
        Returns
        -------
        Xt : list of ndarray
            List of results of transformers.

        """
        results = self._parallel_func(X, y, fit_params, _fit_transform_one)
        if not results:
            # All transformers are None
            return np.zeros((X.shape[0], 0))

        Xt, transformers = zip(*results)
        self._update_transformer_list(transformers)
        Xt = list(Xt)
        return Xt

    def transform(self, X):
        """Transform X separately by each transformer, concatenate results.
        Parameters
        ----------
        X : iterable or array-like, depending on transformers
            Input data to be transformed.
        Returns
        -------
        Xt : list of ndarray
            List of results of transformers.

        """
        Xt = Parallel(n_jobs=self.n_jobs)(
            delayed(_transform_one)(trans, X, None, weight)
            for name, trans, weight in self._iter())
        if not Xt:
            # All transformers are None
            return np.zeros((X.shape[0], 0))
        Xt = list(Xt)
        return Xt


def make_func_apply_along_axis_1(func):
    return partial(np.apply_along_axis, func, 1)


def func_from_callable_on_rows(func):
    if func is None:
        return None
    func_params = signature(func).parameters
    if 'axis' in func_params:
        return partial(func, axis=1)
    return make_func_apply_along_axis_1(func)


def identity():
    return FunctionTransformer(validate=True)
