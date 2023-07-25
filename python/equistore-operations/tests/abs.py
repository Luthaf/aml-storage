"""Unit tests for the :py:func:`equistore.abs` function."""

import numpy as np
import pytest

import equistore
from equistore import TensorBlock, TensorMap

from . import utils


def tensor_complex():
    """Manipulate tensor to be a suitable test for the `abs` function."""

    tensor = utils.tensor()

    blocks = []
    for block in tensor:
        new_block = TensorBlock(
            values=-block.values + 3j,
            samples=block.samples,
            components=block.components,
            properties=block.properties,
        )

        for parameter, gradient in block.gradients():
            new_block.add_gradient(
                parameter=parameter,
                gradient=TensorBlock(
                    values=-gradient.values - 2j,
                    samples=gradient.samples,
                    components=gradient.components,
                    properties=gradient.properties,
                ),
            )

        blocks.append(new_block)

    return TensorMap(keys=tensor.keys, blocks=blocks)


def tensor_complex_result():
    blocks = []
    tensor = tensor_complex()
    for block in tensor:
        new_block = TensorBlock(
            values=np.abs(block.values),
            samples=block.samples,
            components=block.components,
            properties=block.properties,
        )

        for parameter, gradient in block.gradients():
            new_block.add_gradient(
                parameter=parameter,
                gradient=TensorBlock(
                    values=-gradient.values,
                    samples=gradient.samples,
                    components=gradient.components,
                    properties=gradient.properties,
                ),
            )

        blocks.append(new_block)

    return TensorMap(keys=tensor.keys, blocks=blocks)


@pytest.mark.parametrize("gradients", (True, False))
def test_abs(gradients):
    if not gradients:
        tensor = equistore.remove_gradients(tensor_complex())
        tensor_result = equistore.remove_gradients(tensor_complex_result())
    else:
        tensor = tensor_complex()
        tensor_result = tensor_complex_result()

    tensor_abs = equistore.abs(tensor)
    assert equistore.equal(tensor_abs, tensor_result)

    # Check the tensors haven't be modified in place
    assert not equistore.equal(tensor_abs, tensor)
