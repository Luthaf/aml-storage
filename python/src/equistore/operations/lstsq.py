import warnings

import numpy as np

from equistore import TensorBlock, TensorMap

from . import _dispatch


def lstsq(X: TensorMap, Y: TensorMap, rcond) -> TensorMap:
    """
    Solve a linear system among two :py:class:`TensorMap`.
    Return the least-squares solution
    to a linear equation X * w = Y for the unknown w.
    Where X , w, Y are all :py:class:`TensorMap`

    rcond:
    Cut-off ratio for small singular values of a.
    None chose the default value for numpy or pytorch
    """
    if rcond is None:
        warnings.warn(
            "WARNING rcond is set to None, which will trigger the default behaviour \
            which is different between numpy and torch lstsq function, \
            and might depend on the version you are using."
        )

    if len(X) != len(Y) or (not np.all([key in Y.keys for key in X.keys])):
        raise ValueError("The two input TensorMap should have the same keys")

    blocks = []
    for key, blockX in X:
        blockY = Y.block(key)
        blocks.append(_lstsq_block(blockX, blockY, rcond=rcond))

    return TensorMap(X.keys, blocks)


def _lstsq_block(X: TensorBlock, Y: TensorBlock, rcond) -> TensorBlock:
    """
    Solve a linear system among two :py:class:`TensorBlock`.
    Return the least-squares solution
    to a linear equation X * w = Y for the unknown w.
    Where X , w, Y are all :py:class:`TensorBlock`
    """
    # TODO properties and samples not in the same order
    if not np.all(X.samples == Y.samples):
        raise ValueError(
            "The two input TensorBlock should have the same samples\
            and in the same order"
        )
    if len(X.components) > 0:
        if len(X.components) != len(Y.components):
            raise ValueError(
                "The two input TensorBlock should have the same components\
                    and in the same order"
            )
        for ic, Xcomp in enumerate(X.components):
            if not np.all(Xcomp == Y.components[ic]):
                raise ValueError(
                    "The two input TensorBlock should have the same components\
                    and in the same order"
                )

    valuesX = X.values.reshape(-1, X.values.shape[-1])
    valuesY = Y.values.reshape(-1, Y.values.shape[-1])
    if len(X.gradients_list()) > 0:
        if len(X.gradients_list()) != len(Y.gradients_list()) or (
            not np.all(
                [parameter in Y.gradients_list() for parameter in X.gradients_list()]
            )
        ):
            raise ValueError("The two input TensorBlock should have the same gradients")

        for parameter, Xgradient in X.gradients():
            X_grad_data_reshape = Xgradient.data.reshape(-1, X.values.shape[-1])
            Ygradient = Y.gradient(parameter)
            Y_grad_data_reshape = Ygradient.data.reshape(-1, Y.values.shape[-1])
            valuesY = _dispatch.vstack((valuesY, Y_grad_data_reshape))
            valuesX = _dispatch.vstack((valuesX, X_grad_data_reshape))

    Xshape = valuesX.shape
    if len(Xshape) != 2:
        raise ValueError("X.values should be a 2D array")

    valuesw = _dispatch.lstsq(valuesX, valuesY, rcond=rcond)

    w = TensorBlock(
        values=valuesw.T,
        samples=Y.properties,
        components=[],
        properties=X.properties,
    )

    return w
