import numpy as np
from numpy.random import randint
from scipy.interpolate import interp1d
from scipy import sparse
from scipy.sparse.linalg import spsolve


def als_baseline(signal, lam=1e9, p=0.15, niter=10):
    """Asymmetric least squares method for baseline estimation

    The least squares approach is based on the asymmetric weighting
    of a Whittaker smoother to reduce noise in data. This consists
    in minimising


    .. math::

        S = \sum_iw_i(y_i - z_i)^2 + \lambda\sum_i(\Delta^2 z_i)^2


    For a noisy signal y fitted with a baseline z, with weights
    defined asymmetrically for an update parameter that favours a
    data points above the baseline to ones below it and a smoothing
    parameter :math:`\lambda`.
    This results in the iterative solution of the matrix equation
    .. math:: (W + \lambda D\'D)z = Wy
    W is a weight matrix and D is a second difference matrix

    Parameters
    ----------

    signal : array-like
        A NumPy array containing the signal

    lam : float
        Smoothing parameter (default = 1e9)

    p : float
        Update parameter for weight matrix (default = 0.15)

    niter : int
        Number of iterations needed (default = 10)

    Returns
    -------
    z : array-like
        NumPy array containing baseline.
    """

    length = signal.size

    # reshape signal to have control over matrices
    signal = signal.reshape((1, length))
    # Create a sparse difference matrix
    D = sparse.spdiags([1 * np.ones((length)), -2 * np.ones((length)), 1 * np.ones((length))],
                       (2, 1, 0), length - 2, length).T
    # initialise weights as all ones
    w = np.ones((1, length))

    for i in range(niter):
        # construct weight matrix
        W = sparse.spdiags(w, 0, length, length)

        # calculate (W + lambda D'D)
        Z = W + lam * D.dot(D.transpose())

        # solve for baseline
        z = spsolve(Z, (w * signal).T)

        # create masks for weight update
        mask1 = signal > z
        mask2 = signal < z
        w = p * mask1 + (1 - p) * mask2

    return z


def reject_point(timeseries, idx):
    diff = np.diff(timeseries)

    if abs(diff[idx - 1] - diff.mean()) > diff.std() * 2:
        return True
    else:
        return False


def iterative_remover(timeseries, decimation_rate=0.5, prob_dist=None):
    N = len(timeseries)
    x_t = randint(N)
    n_iter = int(round(N * decimation_rate))
    idxs, values = (np.zeros(n_iter, dtype=int), np.zeros(n_iter))
    idxs[n_iter - 1] = N - 1
    values[n_iter - 1] = timeseries[N - 1]
    values[0] = timeseries[0]
    it = 0
    while True:

        # for it in range(1, n_iter - 1):
        xd = randint(N)
        if xd != 0 and xd != N - 1 and xd not in idxs and not reject_point(timeseries, xd):
            it += 1

            idxs[it] = xd
            values[it] = timeseries[xd]
        if it >= n_iter - 2:
            break
    sorted_idxs = np.argsort(idxs)
    idxs = idxs[sorted_idxs]
    values = values[sorted_idxs]
    interpolator = interp1d(idxs, values, kind='cubic')
    new_idxs = np.linspace(0, N - 1, N)
    season = interpolator(new_idxs)
    remainer = timeseries - season
    return remainer, season
