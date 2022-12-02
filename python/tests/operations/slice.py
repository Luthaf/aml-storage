import os
import unittest
import warnings

import numpy as np

import equistore.io
import equistore.operations as fn
from equistore import Labels

DATA_ROOT = os.path.join(os.path.dirname(__file__), "..", "data")
TEST_FILE = "qm7-spherical-expansion.npz"


class TestSliceSamples(unittest.TestCase):
    """Slicing samples dimension of TensorMap and TensorBlock"""

    def setUp(self):
        self.tensor = equistore.io.load(
            os.path.join(DATA_ROOT, TEST_FILE),
            use_numpy=True,
        )

    def _check_sliced_block(self, block, sliced_block, structures_to_keep):
        # no slicing of properties has occurred
        self.assertTrue(np.all(block.properties == sliced_block.properties))

        # samples have been sliced to the correct dimension
        self.assertEqual(
            len(sliced_block.samples),
            len([s for s in block.samples["structure"] if s in structures_to_keep]),
        )

        # samples in sliced block only feature desired structure indices
        self.assertTrue(
            np.all([s in structures_to_keep for s in sliced_block.samples["structure"]])
        )

        # no components have been sliced
        self.assertEqual(len(sliced_block.components), len(block.components))
        for sliced_c, c in zip(sliced_block.components, block.components):
            self.assertTrue(np.all(sliced_c == c))

        # we have the right values
        samples_filter = np.array(
            [sample["structure"] in structures_to_keep for sample in block.samples]
        )
        self.assertTrue(
            np.all(sliced_block.values == block.values[samples_filter, ...])
        )

        for parameter, gradient in block.gradients():
            sliced_gradient = sliced_block.gradient(parameter)
            # no slicing of properties has occurred
            self.assertTrue(np.all(sliced_gradient.properties == gradient.properties))

            # samples have been updated to refer to the new samples
            self.assertLess(
                np.max(sliced_gradient.samples["sample"]),
                sliced_block.values.shape[0],
            )

            # other columns in the gradient samples have been sliced correctly
            gradient_sample_filter = samples_filter[gradient.samples["sample"]]
            if len(gradient.samples.names) > 0:
                expected = gradient.samples.asarray()[gradient_sample_filter, 1:]
                sliced_gradient_samples = sliced_gradient.samples.asarray()[:, 1:]
                self.assertTrue(np.all(sliced_gradient_samples == expected))

            # same components as the original
            self.assertEqual(len(gradient.components), len(sliced_gradient.components))
            for sliced_c, c in zip(sliced_gradient.components, gradient.components):
                self.assertTrue(np.all(sliced_c == c))

            expected = gradient.data[gradient_sample_filter]
            self.assertTrue(np.all(sliced_gradient.data == expected))

    def _check_empty_block(self, block, sliced_block):
        # sliced block has no values
        self.assertEqual(len(sliced_block.values.flatten()), 0)
        # sliced block has dimension zero for samples
        self.assertEqual(sliced_block.values.shape[0], 0)
        # sliced block has original dimension for properties
        self.assertEqual(sliced_block.values.shape[-1], block.values.shape[-1])

        for parameter, gradient in block.gradients():
            sliced_gradient = sliced_block.gradient(parameter)
            # no slicing of properties has occurred
            self.assertTrue(np.all(sliced_gradient.properties == gradient.properties))

            # sliced block contains zero samples
            self.assertEqual(sliced_gradient.data.shape[0], 0)

    def test_slice_block(self):
        # Slice only 'structures' 2, 4, 6, 8
        structures_to_keep = np.arange(2, 10, 2).reshape(-1, 1)
        samples_to_slice = Labels(
            names=["structure"],
            values=structures_to_keep,
        )
        block = self.tensor.block(0)
        sliced_block = fn.slice_block(
            block,
            samples_to_slice=samples_to_slice,
        )
        self._check_sliced_block(block, sliced_block, structures_to_keep)

        # ===== Slice to an empty block =====
        # Slice only 'structures' -1 (i.e. a sample that doesn't exist in the data)
        samples_to_slice = Labels(
            names=["structure"],
            values=np.array([-1]).reshape(-1, 1),
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sliced_block = fn.slice_block(
                block,
                samples_to_slice=samples_to_slice,
            )

        self._check_empty_block(block, sliced_block)

    def test_slice(self):
        # Slice only 'structures' 2, 4, 6, 8
        structures_to_keep = np.arange(2, 10, 2).reshape(-1, 1)
        samples_to_slice = Labels(
            names=["structure"],
            values=structures_to_keep,
        )
        sliced_tensor = fn.slice(
            self.tensor,
            samples_to_slice=samples_to_slice,
        )

        for key, block in self.tensor:
            sliced_block = sliced_tensor.block(key)
            self._check_sliced_block(block, sliced_block, structures_to_keep)

        # all the keys in the sliced tensor are in the original
        self.assertTrue(np.all(self.tensor.keys == sliced_tensor.keys))

        # ===== Slice to all empty blocks =====
        # Slice only 'structures' -1 (i.e. a sample that doesn't exist in the data)
        samples_to_slice = Labels(
            names=["structure"],
            values=np.array([-1]).reshape(-1, 1),
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sliced_tensor = fn.slice(
                self.tensor,
                samples_to_slice=samples_to_slice,
            )

        for _, block in sliced_tensor:
            # all blocks are empty
            self._check_empty_block(block, sliced_tensor.block(key))


class TestSliceProperties(unittest.TestCase):
    """Slicing property dimension of TensorMap and TensorBlock"""

    def setUp(self):
        self.tensor = equistore.io.load(
            os.path.join(DATA_ROOT, TEST_FILE),
            use_numpy=True,
        )

    def _check_sliced_block(self, block, sliced_block, radial_to_keep):
        # no slicing of samples has occurred
        self.assertTrue(np.all(block.samples == sliced_block.samples))

        # properties have been sliced to the correct dimension
        self.assertEqual(
            len(sliced_block.properties),
            len([n for n in block.properties["n"] if n in radial_to_keep]),
        )
        # properties in sliced block only feature desired radial indices
        self.assertTrue(
            np.all([n in radial_to_keep for n in sliced_block.properties["n"]])
        )

        # no components have been sliced
        self.assertEqual(len(sliced_block.components), len(block.components))
        for sliced_c, c in zip(sliced_block.components, block.components):
            self.assertTrue(np.all(sliced_c == c))

        # we have the right values
        property_filter = [
            property["n"] in radial_to_keep for property in block.properties
        ]
        self.assertTrue(
            np.all(sliced_block.values == block.values[..., property_filter])
        )

        for parameter, gradient in block.gradients():
            sliced_gradient = sliced_block.gradient(parameter)
            # no slicing of samples has occurred
            self.assertTrue(np.all(sliced_gradient.samples == gradient.samples))

            # properties have been sliced to the correct dimension
            self.assertEqual(
                len(sliced_gradient.properties),
                len([n for n in gradient.properties["n"] if n in radial_to_keep]),
            )
            # properties in sliced block only feature desired radial indices
            self.assertTrue(
                np.all([n in radial_to_keep for n in sliced_gradient.properties["n"]])
            )

            # same components as the original
            self.assertEqual(len(gradient.components), len(sliced_gradient.components))
            for sliced_c, c in zip(sliced_gradient.components, gradient.components):
                self.assertTrue(np.all(sliced_c == c))

            # we have the right values
            self.assertTrue(
                np.all(sliced_gradient.data == gradient.data[..., property_filter])
            )

    def _check_empty_block(self, block, sliced_block):
        # sliced block has no values
        self.assertEqual(len(sliced_block.values.flatten()), 0)
        # sliced block has dimension zero for properties
        self.assertEqual(sliced_block.values.shape[-1], 0)
        # sliced block has original dimension for samples
        self.assertEqual(sliced_block.values.shape[0], block.values.shape[0])

        for parameter, gradient in block.gradients():
            sliced_gradient = sliced_block.gradient(parameter)
            # no slicing of samples has occurred
            self.assertTrue(np.all(sliced_gradient.samples == gradient.samples))

            # sliced block contains zero properties
            self.assertEqual(sliced_gradient.data.shape[-1], 0)

    def test_slice_block(self):
        # Slice only 'n' (i.e. radial channels) 1, 3
        radial_to_keep = np.arange(1, 5, 2).reshape(-1, 1)
        properties_to_slice = Labels(
            names=["n"],
            values=radial_to_keep,
        )

        block = self.tensor.block(0)
        sliced_block = fn.slice_block(
            block,
            properties_to_slice=properties_to_slice,
        )
        self._check_sliced_block(block, sliced_block, radial_to_keep)

        # ===== Slice to an empty block =====
        # Slice only 'n' (i.e. radial channels) -1 (i.e. non-existent channel)
        properties_to_slice = Labels(
            names=["n"],
            values=np.array([-1]).reshape(-1, 1),
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sliced_block = fn.slice_block(
                block,
                properties_to_slice=properties_to_slice,
            )

        self._check_empty_block(block, sliced_block)

    def test_slice(self):
        # Slice only 'n' (i.e. radial channels) 1, 3
        radial_to_keep = np.arange(1, 5, 2).reshape(-1, 1)
        properties_to_slice = Labels(
            names=["n"],
            values=radial_to_keep,
        )

        sliced_tensor = fn.slice(
            self.tensor,
            properties_to_slice=properties_to_slice,
        )

        for key, block in self.tensor:
            sliced_block = sliced_tensor.block(key)
            self._check_sliced_block(block, sliced_block, radial_to_keep)

        # Check 5: all the keys in the sliced tensor are in the original
        self.assertTrue(np.all(self.tensor.keys == sliced_tensor.keys))

        # ===== Slice to all empty blocks =====
        # Slice only 'n' (i.e. radial channels) -1 (i.e. non-existent channel)
        properties_to_slice = Labels(
            names=["n"],
            values=np.array([-1]).reshape(-1, 1),
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sliced_tensor = fn.slice(
                self.tensor,
                properties_to_slice=properties_to_slice,
            )

        for key, block in self.tensor:
            sliced_block = sliced_tensor.block(key)
            self._check_empty_block(block, sliced_block)


class TestSliceBoth(unittest.TestCase):
    def test_slice_block(self):
        tensor = equistore.io.load(
            os.path.join(DATA_ROOT, TEST_FILE),
            use_numpy=True,
        )

        block = tensor.block(5)
        # Slice 'center' 1, 3, 5
        centers_to_keep = np.arange(1, 7, 2).reshape(-1, 1)
        samples_to_slice = Labels(
            names=["center"],
            values=centers_to_keep,
        )
        # Slice 'n' (i.e. radial channel) 0, 1, 2
        channels_to_keep = np.arange(0, 3).reshape(-1, 1)
        properties_to_slice = Labels(
            names=["n"],
            values=channels_to_keep,
        )

        sliced_block = fn.slice_block(
            block,
            samples_to_slice=samples_to_slice,
            properties_to_slice=properties_to_slice,
        )

        # only desired samples are in the output.
        self.assertTrue(
            np.all([c in centers_to_keep for c in sliced_block.samples["center"]])
        )

        # only desired properties are in the output
        self.assertTrue(
            np.all([n in channels_to_keep for n in sliced_block.properties["n"]])
        )

        # There are the correct number of samples
        self.assertEqual(
            sliced_block.values.shape[0],
            len([s for s in block.samples if s["center"] in centers_to_keep]),
        )

        # There are the correct number of properties
        self.assertEqual(
            sliced_block.values.shape[-1],
            len([p for p in block.properties if p["n"] in channels_to_keep]),
        )

        # we have the right values
        samples_filter = [
            sample["center"] in centers_to_keep for sample in block.samples
        ]
        properties_filter = [
            property["n"] in channels_to_keep for property in block.properties
        ]
        expected = block.values[samples_filter][..., properties_filter]
        self.assertTrue(np.all(sliced_block.values == expected))


class TestSliceErrorsWarnings(unittest.TestCase):
    def setUp(self):
        self.tensor = equistore.io.load(
            os.path.join(DATA_ROOT, TEST_FILE),
            use_numpy=True,
        )

    def test_slice_errors(self):
        centers_to_keep = np.arange(1, 7, 2).reshape(-1, 1)
        samples_to_slice = Labels(
            names=["center"],
            values=centers_to_keep,
        )

        with self.assertRaises(TypeError) as cm:
            fn.slice(self.tensor.block(0), samples_to_slice=samples_to_slice),

        self.assertEqual(
            str(cm.exception),
            "the input tensor must be a `TensorMap` object, if you want to "
            "to slice a `TensorBlock`, use `slice_block()` instead",
        )

        # passing samples_to_slice=np.array raises TypeError
        with self.assertRaises(TypeError) as cm:
            fn.slice(
                self.tensor,
                samples_to_slice=np.array([[5], [6]]),
            )

        self.assertEqual(
            str(cm.exception),
            "samples_to_slice must be a `Labels` object",
        )

        # passing properties_to_slice=np.array raises TypeError
        with self.assertRaises(TypeError) as cm:
            fn.slice(
                self.tensor,
                properties_to_slice=np.array([[5], [6]]),
            )

        self.assertEqual(
            str(cm.exception),
            "properties_to_slice must be a `Labels` object",
        )

    def test_slice_block_errors(self):
        centers_to_keep = np.arange(1, 7, 2).reshape(-1, 1)
        samples_to_slice = Labels(
            names=["center"],
            values=centers_to_keep,
        )

        with self.assertRaises(TypeError) as cm:
            fn.slice_block(self.tensor, samples_to_slice=samples_to_slice),

        self.assertEqual(
            str(cm.exception),
            "the input tensor must be a `TensorBlock` object, if you want to "
            "to slice a `TensorMap`, use `slice()` instead",
        )

        block = self.tensor.block(0)
        # passing samples_to_slice=np.array raises TypeError
        with self.assertRaises(TypeError) as cm:
            fn.slice_block(
                block,
                samples_to_slice=np.array([[5], [6]]),
            )

        self.assertEqual(
            str(cm.exception),
            "samples_to_slice must be a `Labels` object",
        )

        # passing properties_to_slice=np.array raises TypeError
        with self.assertRaises(TypeError) as cm:
            fn.slice_block(
                block,
                properties_to_slice=np.array([[5], [6]]),
            )

        self.assertEqual(
            str(cm.exception),
            "properties_to_slice must be a `Labels` object",
        )

    def test_warnings(self):
        # ==== warning when some empty blocks produced
        samples_to_slice = Labels(
            names=["structure"],
            values=np.array([2]).reshape(-1, 1),
        )

        with self.assertWarns(UserWarning) as cm:
            fn.slice(
                self.tensor,
                samples_to_slice=samples_to_slice,
            )

        self.assertIn(
            "Some TensorBlocks in the sliced TensorMap are now empty",
            str(cm.warning),
        )

        # ==== warning when only empty blocks are produced
        samples_to_slice = Labels(
            names=["structure"],
            values=np.array([-1]).reshape(-1, 1),
        )

        with self.assertWarns(UserWarning) as cm:
            fn.slice(
                self.tensor,
                samples_to_slice=samples_to_slice,
            )

        self.assertIn(
            "All TensorBlocks in the sliced TensorMap are now empty",
            str(cm.warning),
        )

        properties_to_slice = Labels(
            names=["n"],
            values=np.array([-1]).reshape(-1, 1),
        )

        with self.assertWarns(UserWarning) as cm:
            fn.slice(
                self.tensor,
                properties_to_slice=properties_to_slice,
            )

        self.assertIn(
            "All TensorBlocks in the sliced TensorMap are now empty",
            str(cm.warning),
        )


if __name__ == "__main__":
    unittest.main()
