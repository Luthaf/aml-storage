#include <torch/script.h>

#include "equistore.hpp"

#include "equistore/torch/labels.hpp"
#include "equistore/torch/block.hpp"
#include "equistore/torch/tensor.hpp"

using namespace equistore_torch;


TORCH_LIBRARY(equistore, m) {
    m.class_<LabelsHolder>("Labels")
        .def(torch::init<std::vector<std::string>, torch::Tensor>())
        ;

    m.class_<TensorBlockHolder>("TensorBlock")
        .def(torch::init<torch::Tensor, TorchLabels, std::vector<TorchLabels>, TorchLabels>())
        ;

    m.class_<TensorMapHolder>("TensorMap")
        .def(torch::init<TorchLabels, std::vector<TorchTensorBlock>>())
        // .def_pickle(
        //     // __getstate__
        //     [](const torch::intrusive_ptr<TorchTensorMap>& self) -> std::string {
        //          // TODO
        //     },
        //     // __setstate__
        //     [](std::string state) -> torch::intrusive_ptr<TorchCalculator> {
        //         // TODO
        //     })
        ;
}
