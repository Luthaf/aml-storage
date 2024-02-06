import io

import pytest
import torch
from torch.nn import Module, Sigmoid

from metatensor.torch import Labels, allclose_raise
from metatensor.torch.learn.nn import ModuleMap

from .utils import TORCH_KWARGS, single_block_tensor  # noqa F401


try:
    if torch.cuda.is_available():
        HAS_CUDA = True
    else:
        HAS_CUDA = False
except ImportError:
    HAS_CUDA = False


class MockModule(Module):
    def __init__(self, in_features, out_features):
        super().__init__()
        self._linear = torch.nn.Linear(in_features, out_features)
        self._activation = Sigmoid()
        self._last_layer = torch.nn.Linear(out_features, 1)

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        return self._last_layer(self._activation(self._linear(input)))


@pytest.fixture(scope="function", autouse=True)
def set_random_generator():
    """Set the random generator to same seed before each test is run.
    Otherwise test behaviour is dependend on the order of the tests
    in this file and the number of parameters of the test.
    """
    torch.random.manual_seed(122578741812)


@pytest.fixture(scope="function", autouse=True)
def set_default_torch_resources():
    torch.set_default_device(TORCH_KWARGS["device"])
    torch.set_default_dtype(TORCH_KWARGS["dtype"])


@pytest.mark.parametrize(
    "out_properties", [None, [Labels(["a", "b"], torch.tensor([[1, 1]]))]]
)
def test_module_map_single_block_tensor(
    single_block_tensor, out_properties  # noqa F811
):
    modules = []
    for key in single_block_tensor.keys:
        modules.append(
            MockModule(
                in_features=len(single_block_tensor.block(key).properties),
                out_features=5,
            )
        )

    tensor_module = ModuleMap(
        single_block_tensor.keys, modules, out_properties=out_properties
    )
    with torch.no_grad():
        out_tensor = tensor_module(single_block_tensor)

    for i, item in enumerate(single_block_tensor.items()):
        key, block = item
        module = modules[i]
        assert (
            tensor_module.get_module(key) is module
        ), "modules should be initialized in the same order as keys"

        with torch.no_grad():
            ref_values = module(block.values)
        out_block = out_tensor.block(key)
        assert torch.allclose(ref_values, out_block.values)
        if out_properties is None:
            assert out_block.properties == Labels.range("_", len(out_block.properties))
        else:
            assert out_block.properties == out_properties[0]

        for parameter, gradient in block.gradients():
            with torch.no_grad():
                ref_gradient_values = module(gradient.values)
            assert torch.allclose(
                ref_gradient_values, out_block.gradient(parameter).values
            )
            if out_properties is None:
                assert out_block.gradient(parameter).properties == Labels.range(
                    "_", len(out_block.gradient(parameter).properties)
                )
            else:
                assert out_block.gradient(parameter).properties == out_properties[0]


@pytest.mark.parametrize(
    "out_properties", [None, [Labels(["a", "b"], torch.tensor([[1, 1]]))]]
)
@pytest.mark.skipif(not HAS_CUDA, reason="requires cuda")
def test_cuda_module_map_to(single_block_tensor, out_properties):  # noqa F811
    """
    We set the correct default device for initialization and check if the module this
    works once the default device has been changed. This catches cases where the default
    device or a hard coded device is used for tensor created within the forward
    function.
    """
    # check if default device cuda -> cpu
    torch.set_default_device("cuda")
    modules = []
    for key in single_block_tensor.keys:
        modules.append(
            MockModule(
                in_features=len(single_block_tensor.block(key).properties),
                out_features=5,
            )
        )
    # recreate out_properties to move to default device to check if `to` operation later
    # moves them to correct device
    if out_properties is not None:
        out_properties = [
            out_properties_label.to(torch.device("cuda"))
            for out_properties_label in out_properties
        ]
    tensor_module = ModuleMap(
        single_block_tensor.keys, modules, out_properties=out_properties
    )
    tensor_module.to("cpu")
    single_block_tensor = single_block_tensor.to(device="cpu")
    with torch.no_grad():
        out_tensor = tensor_module(single_block_tensor)
    assert out_tensor.device.type == "cpu"

    # cpu -> cuda
    torch.set_default_device("cpu")
    modules = []
    for key in single_block_tensor.keys:
        modules.append(
            MockModule(
                in_features=len(single_block_tensor.block(key).properties),
                out_features=5,
            )
        )
    # recreate out_properties to move to default device to check if `to` operation later
    # moves them to correct device
    if out_properties is not None:
        out_properties = [
            out_properties_label.to("cpu") for out_properties_label in out_properties
        ]
    tensor_module = ModuleMap(
        single_block_tensor.keys, modules, out_properties=out_properties
    )
    tensor_module.to("cuda")
    single_block_tensor = single_block_tensor.to(device="cuda")
    with torch.no_grad():
        out_tensor = tensor_module(single_block_tensor)

    assert out_tensor.device.type == "cuda"


def test_torchscript_module_map(single_block_tensor):  # noqa F811
    modules = []
    for key in single_block_tensor.keys:
        modules.append(
            MockModule(
                in_features=len(single_block_tensor.block(key).properties),
                out_features=5,
            )
        )
    tensor_module = ModuleMap(single_block_tensor.keys, modules)
    ref_tensor = tensor_module(single_block_tensor)

    tensor_module_script = torch.jit.script(tensor_module)
    out_tensor = tensor_module_script(single_block_tensor)

    allclose_raise(ref_tensor, out_tensor)

    # tests if member functions work that do not appear in forward
    tensor_module_script.get_module(single_block_tensor.keys[0])

    # test save load
    scripted = torch.jit.script(tensor_module_script)
    buffer = io.BytesIO()
    torch.jit.save(scripted, buffer)
    buffer.seek(0)
    torch.jit.load(buffer)
    buffer.close()
