import numpy as np

from equistore import TensorBlock, TensorMap

from . import _dispatch


def _dot_block(block1: TensorBlock, block2: TensorBlock) -> TensorBlock:
    """dot product (row) among two `TensorBlocks`.
    The `TensorBlocks` should have the same `properties`
    """

    if not np.all(block1.properties == block2.properties):
        raise ValueError("the two TensorBlocks should have the same properties ")

    if len(block2.components) > 0:
        raise ValueError("The second TensorBlock should not have components ")

    if len(block2.gradients_list()) > 0:
        raise ValueError(
            "The second TensorBlock should not have gradient informations "
        )

    values1 = block1.values
    values2 = block2.values
    values = _dispatch.dot(values1, values2)

    result_block = TensorBlock(
        values=values,
        samples=block1.samples,
        components=block1.components,
        properties=block2.samples,
    )

    if len(block1.gradients_list()) > 0:
        for parameter in block1.gradients_list():
            gradient = block1.gradient(parameter)

            gradient_data = _dispatch.dot(
                gradient.data, values2
            )  # gradient.data @ block2.values.T

            result_block.add_gradient(
                parameter,
                gradient_data,
                gradient.samples,
                gradient.components,
            )

    return result_block


def dot(tensor1: TensorMap, tensor2: TensorMap) -> TensorMap:
    """
    Computes the dot product among two :py:class:`TensorMap`s.
    The two :py:class:`TensorMap`s must have the same ``keys``.
    The resulting :py:class:`TensorMap`s will have the same keys of the two in input and
    each of its :py:class:`TensorBlock` will be the dot product
    of the two :py:class:`TensorBlock`s of the input for the corresponding key.

    :param tensor1: first :py:class:`TensorMap` to multiply
    :param tensor2: second :py:class:`TensorMap` to multiply
    """
    if len(tensor1.keys) != len(tensor2.keys) or (
        not np.all([key in tensor2.keys for key in tensor1.keys])
    ):
        raise ValueError("The two input tensorMaps should have the same keys")
    blocks = []
    for key, block1 in tensor1:
        block2 = tensor2.block(key)
        blocks.append(_dot_block(block1=block1, block2=block2))
    return TensorMap(tensor1.keys, blocks)
