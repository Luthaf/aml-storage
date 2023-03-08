import numpy as np
import pytest
from numpy.testing import assert_equal

import equistore
import equistore.status
from equistore import Labels, TensorBlock


class TestBlocks:
    @pytest.fixture
    def block(self):
        b = TensorBlock(
            values=np.full((3, 2), -1.0),
            samples=Labels(["samples"], np.array([[0], [2], [4]], dtype=np.int32)),
            components=[],
            properties=Labels(["properties"], np.array([[5], [3]], dtype=np.int32)),
        )

        return b

    def test_gradient_no_sample_error(self, block):
        with pytest.raises(
            equistore.status.EquistoreError,
            match="""invalid parameter: gradients samples must have at least """
            """one dimension named 'sample', we got none""",
        ):
            block.add_gradient(
                "parameter",
                data=np.zeros((0, 2)),
                samples=Labels([], np.empty((0, 2), dtype=np.int32)),
                components=[],
            )

    def test_repr(self, block):
        expected = """TensorBlock
    samples (3): ['samples']
    components (): []
    properties (2): ['properties']
    gradients: no"""
        assert block.__repr__() == expected

    def test_repr_zero_samples(self):
        block = TensorBlock(
            values=np.zeros((0, 2)),
            samples=Labels([], np.empty((0, 2), dtype=np.int32)),
            components=[],
            properties=Labels(["properties"], np.array([[5], [3]], dtype=np.int32)),
        )
        expected = """TensorBlock
    samples (0): []
    components (): []
    properties (2): ['properties']
    gradients: no"""
        assert block.__repr__() == expected

    def test_repr_zero_samples_gradient(self, block):
        block.add_gradient(
            "parameter",
            data=np.zeros((0, 2)),
            samples=Labels(["sample"], np.empty((0, 2), dtype=np.int32)),
            components=[],
        )

        expected_block = """TensorBlock
    samples (3): ['samples']
    components (): []
    properties (2): ['properties']
    gradients: ['parameter']"""

        assert block.__repr__() == expected_block

        expected_grad = """Gradient TensorBlock
parameter: 'parameter'
samples (0): ['sample']
components (): []
properties (2): ['properties']"""

        gradient = block.gradient("parameter")
        assert gradient.__repr__() == expected_grad

    def test_block_no_components(self, block):
        assert_equal(block.values, np.full((3, 2), -1.0))

        assert block.samples.names == ("samples",)
        assert len(block.samples) == 3
        assert tuple(block.samples[0]) == (0,)
        assert tuple(block.samples[1]) == (2,)
        assert tuple(block.samples[2]) == (4,)

        assert len(block.components) == 0

        assert block.properties.names == ("properties",)
        assert len(block.properties) == 2
        assert tuple(block.properties[0]) == (5,)
        assert tuple(block.properties[1]) == (3,)

    @pytest.fixture
    def block_components(self):
        b = TensorBlock(
            values=np.full((3, 3, 2, 2), -1.0),
            samples=Labels(["samples"], np.array([[0], [2], [4]], dtype=np.int32)),
            components=[
                Labels(["component_1"], np.array([[-1], [0], [1]], dtype=np.int32)),
                Labels(["component_2"], np.array([[-4], [1]], dtype=np.int32)),
            ],
            properties=Labels(["properties"], np.array([[5], [3]], dtype=np.int32)),
        )

        return b

    def test_block_with_components(self, block_components):
        expected = """TensorBlock
    samples (3): ['samples']
    components (3, 2): ['component_1', 'component_2']
    properties (2): ['properties']
    gradients: no"""
        assert block_components.__repr__() == expected

        assert_equal(block_components.values, np.full((3, 3, 2, 2), -1.0))

        assert block_components.samples.names == ("samples",)
        assert len(block_components.samples) == 3
        assert tuple(block_components.samples[0]) == (0,)
        assert tuple(block_components.samples[1]) == (2,)
        assert tuple(block_components.samples[2]) == (4,)

        assert len(block_components.components) == 2
        component_1 = block_components.components[0]
        assert component_1.names == ("component_1",)
        assert len(component_1) == 3
        assert tuple(component_1[0]) == (-1,)
        assert tuple(component_1[1]) == (0,)
        assert tuple(component_1[2]) == (1,)

        component_2 = block_components.components[1]
        assert component_2.names == ("component_2",)
        assert len(component_2) == 2
        assert tuple(component_2[0]) == (-4,)
        assert tuple(component_2[1]) == (1,)

        assert block_components.properties.names, ("properties",)
        assert len(block_components.properties) == 2
        assert tuple(block_components.properties[0]) == (5,)
        assert tuple(block_components.properties[1]) == (3,)

    def test_gradients(self, block_components):
        block_components.add_gradient(
            "parameter",
            data=np.full((2, 3, 2, 2), 11.0),
            samples=Labels(
                ["sample", "parameter"], np.array([[0, -2], [2, 3]], dtype=np.int32)
            ),
            components=[
                Labels(["component_1"], np.array([[-1], [0], [1]], dtype=np.int32)),
                Labels(["component_2"], np.array([[-4], [1]], dtype=np.int32)),
            ],
        )

        expected = """TensorBlock
    samples (3): ['samples']
    components (3, 2): ['component_1', 'component_2']
    properties (2): ['properties']
    gradients: ['parameter']"""
        assert block_components.__repr__() == expected

        assert block_components.has_gradient("parameter")
        assert not block_components.has_gradient("something else")

        assert block_components.gradients_list() == ["parameter"]

        gradient = block_components.gradient("parameter")

        expected_grad = """Gradient TensorBlock
parameter: 'parameter'
samples (2): ['sample', 'parameter']
components (3, 2): ['component_1', 'component_2']
properties (2): ['properties']"""
        assert gradient.__repr__() == expected_grad

        assert gradient.samples.names == ("sample", "parameter")
        assert len(gradient.samples) == 2
        assert tuple(gradient.samples[0]) == (0, -2)
        assert tuple(gradient.samples[1]) == (2, 3)

        assert_equal(gradient.data, np.full((2, 3, 2, 2), 11.0))

    def test_copy(self):
        block = TensorBlock(
            values=np.full((3, 3, 2), 2.0),
            samples=Labels(["samples"], np.array([[0], [2], [4]], dtype=np.int32)),
            components=[
                Labels(["component_1"], np.array([[-1], [0], [1]], dtype=np.int32)),
            ],
            properties=Labels(["properties"], np.array([[5], [3]], dtype=np.int32)),
        )
        copy = block.copy()
        block_values_id = id(block.values)

        del block

        assert id(copy.values) != block_values_id

        assert_equal(copy.values, np.full((3, 3, 2), 2.0))
        assert copy.samples.names == ("samples",)
        assert len(copy.samples) == 3
        assert tuple(copy.samples[0]) == (0,)
        assert tuple(copy.samples[1]) == (2,)
        assert tuple(copy.samples[2]) == (4,)

    def test_eq(self, block):
        assert equistore.equal_block(block, block) == (block == block)

    def test_neq(self, block, block_components):
        assert equistore.equal_block(block, block_components) == (
            block == block_components
        )
