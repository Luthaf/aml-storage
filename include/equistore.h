/* ============    Automatically generated file, DOT NOT EDIT.    ============ *
 *                                                                             *
 *    This file is automatically generated from the equistore sources,         *
 *    using cbindgen. If you want to make change to this file (including       *
 *    documentation), make the corresponding changes in the rust sources.      *
 * =========================================================================== */

#ifndef EQUISTORE_H
#define EQUISTORE_H

#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>

/**
 * Status code used when a function succeeded
 */
#define EQS_SUCCESS 0

/**
 * Status code used when a function got an invalid parameter
 */
#define EQS_INVALID_PARAMETER_ERROR 1

/**
 * Status code used when a memory buffer is too small to fit the requested data
 */
#define EQS_BUFFER_SIZE_ERROR 254

/**
 * Status code used when there was an internal error, i.e. there is a bug
 * inside equistore itself
 */
#define EQS_INTERNAL_ERROR 255

/**
 * Basic building block for tensor map. A single block contains a n-dimensional
 * `eqs_array_t`, and n sets of `eqs_labels_t` (one for each dimension).
 *
 * A block can also contain gradients of the values with respect to a variety
 * of parameters. In this case, each gradient has a separate set of sample
 * and component labels but share the property labels with the values.
 */
typedef struct eqs_block_t eqs_block_t;

/**
 * Opaque type representing a `TensorMap`.
 */
typedef struct eqs_tensormap_t eqs_tensormap_t;

/**
 * Status type returned by all functions in the C API.
 *
 * The value 0 (`EQS_SUCCESS`) is used to indicate successful operations,
 * positive values are used by this library to indicate errors, while negative
 * values are reserved for users of this library to indicate their own errors
 * in callbacks.
 */
typedef int32_t eqs_status_t;

/**
 * A set of labels used to carry metadata associated with a tensor map.
 *
 * This is similar to a list of `count` named tuples, but stored as a 2D array
 * of shape `(count, size)`, with a set of names associated with the columns of
 * this array (often called *variables*). Each row/entry in this array is
 * unique, and they are often (but not always) sorted in lexicographic order.
 */
typedef struct eqs_labels_t {
  /**
   * internal: pointer to the rust `Labels` struct if any, null otherwise
   */
  const void *labels_ptr;
  /**
   * Names of the variables composing this set of labels. There are `size`
   * elements in this array, each being a NULL terminated UTF-8 string.
   */
  const char *const *names;
  /**
   * Pointer to the first element of a 2D row-major array of 32-bit signed
   * integer containing the values taken by the different variables in
   * `names`. Each row has `size` elements, and there are `count` rows in
   * total.
   */
  const int32_t *values;
  /**
   * Number of variables/size of a single entry in the set of labels
   */
  uintptr_t size;
  /**
   * Number entries in the set of labels
   */
  uintptr_t count;
} eqs_labels_t;

/**
 * A single 64-bit integer representing a data origin (numpy ndarray, rust
 * ndarray, torch tensor, fortran array, ...).
 */
typedef uint64_t eqs_data_origin_t;

/**
 * Representation of a single sample moved from an array to another one
 */
typedef struct eqs_sample_mapping_t {
  /**
   * index of the moved sample in the input array
   */
  uintptr_t input;
  /**
   * index of the moved sample in the output array
   */
  uintptr_t output;
} eqs_sample_mapping_t;

/**
 * `eqs_array_t` manages n-dimensional arrays used as data in a block or tensor
 * map. The array itself if opaque to this library and can come from multiple
 * sources: Rust program, a C/C++ program, a Fortran program, Python with numpy
 * or torch. The data does not have to live on CPU, or even on the same machine
 * where this code is executed.
 *
 * This struct contains a C-compatible manual implementation of a virtual table
 * (vtable, i.e. trait in Rust, pure virtual class in C++); allowing
 * manipulation of the array in an opaque way.
 */
typedef struct eqs_array_t {
  /**
   * User-provided data should be stored here, it will be passed as the
   * first parameter to all function pointers below.
   */
  void *ptr;
  /**
   * This function needs to store the "data origin" for this array in
   * `origin`. Users of `eqs_array_t` should register a single data
   * origin with `register_data_origin`, and use it for all compatible
   * arrays.
   */
  eqs_status_t (*origin)(const void *array, eqs_data_origin_t *origin);
  /**
   * Get the shape of the array managed by this `eqs_array_t` in the `*shape`
   * pointer, and the number of dimension (size of the `*shape` array) in
   * `*shape_count`.
   */
  eqs_status_t (*shape)(const void *array, const uintptr_t **shape, uintptr_t *shape_count);
  /**
   * Change the shape of the array managed by this `eqs_array_t` to the given
   * `shape`. `shape_count` must contain the number of elements in the
   * `shape` array
   */
  eqs_status_t (*reshape)(void *array, const uintptr_t *shape, uintptr_t shape_count);
  /**
   * Swap the axes `axis_1` and `axis_2` in this `array`.
   */
  eqs_status_t (*swap_axes)(void *array, uintptr_t axis_1, uintptr_t axis_2);
  /**
   * Create a new array with the same options as the current one (data type,
   * data location, etc.) and the requested `shape`; and store it in
   * `new_array`. The number of elements in the `shape` array should be given
   * in `shape_count`.
   *
   * The new array should be filled with zeros.
   */
  eqs_status_t (*create)(const void *array, const uintptr_t *shape, uintptr_t shape_count, struct eqs_array_t *new_array);
  /**
   * Make a copy of this `array` and return the new array in `new_array`
   */
  eqs_status_t (*copy)(const void *array, struct eqs_array_t *new_array);
  /**
   * Remove this array and free the associated memory. This function can be
   * set to `NULL` is there is no memory management to do.
   */
  void (*destroy)(void *array);
  /**
   * Set entries in the `output` array (the current array) taking data from
   * the `input` array. The `output` array is guaranteed to be created by
   * calling `eqs_array_t::create` with one of the arrays in the same block
   * or tensor map as the `input`.
   *
   * The `samples` array of size `samples_count` indicate where the data
   * should be moved from `input` to `output`.
   *
   * This function should copy data from `input[samples[i].input, ..., :]` to
   * `array[samples[i].output, ..., property_start:property_end]` for `i` up
   * to `samples_count`. All indexes are 0-based.
   */
  eqs_status_t (*move_samples_from)(void *output, const void *input, const struct eqs_sample_mapping_t *samples, uintptr_t samples_count, uintptr_t property_start, uintptr_t property_end);
} eqs_array_t;

#ifdef __cplusplus
extern "C" {
#endif // __cplusplus

/**
 * Get the last error message that was created on the current thread.
 *
 * @returns the last error message, as a NULL-terminated string
 */
const char *eqs_last_error(void);

/**
 * Get the position of the entry defined by the `values` array in the given set
 * of `labels`. This operation is only available if the labels correspond to a
 * set of Rust Labels (i.e. `labels.labels_ptr` is not NULL).
 *
 * @param labels set of labels coming from an `eqs_block_t` or an `eqs_tensormap_t`
 * @param values array containing the label to lookup
 * @param count size of the values array
 * @param result position of the values in the labels or -1 if the values
 *               were not found
 *
 * @returns The status code of this operation. If the status is not
 *          `EQS_SUCCESS`, you can use `eqs_last_error()` to get the full
 *          error message.
 */
eqs_status_t eqs_labels_position(struct eqs_labels_t labels,
                                 const int32_t *values,
                                 uint64_t count,
                                 int64_t *result);

/**
 * Register a new data origin with the given `name`. Calling this function
 * multiple times with the same name will give the same `eqs_data_origin_t`.
 *
 * @param name name of the data origin as an UTF-8 encoded NULL-terminated string
 * @param origin pointer to an `eqs_data_origin_t` where the origin will be stored
 *
 * @returns The status code of this operation. If the status is not
 *          `EQS_SUCCESS`, you can use `eqs_last_error()` to get the full
 *          error message.
 */
eqs_status_t eqs_register_data_origin(const char *name, eqs_data_origin_t *origin);

/**
 * Get the name used to register a given data `origin` in the given `buffer`
 *
 * @param origin pre-registered data origin
 * @param buffer buffer to be filled with the data origin name. The origin name
 *               will be written  as an UTF-8 encoded, NULL-terminated string
 * @param buffer_size size of the buffer
 *
 * @returns The status code of this operation. If the status is not
 *          `EQS_SUCCESS`, you can use `eqs_last_error()` to get the full
 *          error message.
 */
eqs_status_t eqs_get_data_origin(eqs_data_origin_t origin, char *buffer, uint64_t buffer_size);

/**
 * Create a new `eqs_block_t` with the given `data` and `samples`, `components`
 * and `properties` labels.
 *
 * The memory allocated by this function and the blocks should be released
 * using `eqs_block_free`, or moved into a tensor map using `eqs_tensormap`.
 *
 * @param data array handle containing the data for this block. The block takes
 *             ownership of the array, and will release it with
 *             `array.destroy(array.ptr)` when it no longer needs it.
 * @param samples sample labels corresponding to the first dimension of the data
 * @param components array of component labels corresponding to intermediary
 *                   dimensions of the data
 * @param components_count number of entries in the `components` array
 * @param properties property labels corresponding to the last dimension of the data
 *
 * @returns A pointer to the newly allocated block, or a `NULL` pointer in
 *          case of error. In case of error, you can use `eqs_last_error()`
 *          to get the error message.
 */
struct eqs_block_t *eqs_block(struct eqs_array_t data,
                              struct eqs_labels_t samples,
                              const struct eqs_labels_t *components,
                              uintptr_t components_count,
                              struct eqs_labels_t properties);

/**
 * Free the memory associated with a `block` previously created with
 * `eqs_block`.
 *
 * If `block` is `NULL`, this function does nothing.
 *
 * @param block pointer to an existing block, or `NULL`
 *
 * @returns The status code of this operation. If the status is not
 *          `EQS_SUCCESS`, you can use `eqs_last_error()` to get the full
 *          error message.
 */
eqs_status_t eqs_block_free(struct eqs_block_t *block);

/**
 * Make a copy of an `eqs_block_t`.
 *
 * The memory allocated by this function and the blocks should be released
 * using `eqs_block_free`, or moved into a tensor map using `eqs_tensormap`.
 *
 * @param block existing block to copy
 *
 * @returns A pointer to the newly allocated block, or a `NULL` pointer in
 *          case of error. In case of error, you can use `eqs_last_error()`
 *          to get the error message.
 */
struct eqs_block_t *eqs_block_copy(const struct eqs_block_t *block);

/**
 * Get the set of labels of the requested `kind` from this `block`.
 *
 * The `values_gradients` parameter controls whether this function looks up
 * labels for `"values"` or one of the gradients in this block.
 *
 * The resulting `labels.values` points inside memory owned by the block, and
 * as such is only valid until the block is destroyed with `eqs_block_free`, or
 * the containing tensor map is modified with one of the
 * `eqs_tensormap_keys_to_xxx` function.
 *
 * @param block pointer to an existing block
 * @param values_gradients either `"values"` or the name of gradients to lookup
 * @param axis axis/dimension of the data array for which you need the labels
 * @param labels pointer to an empty `eqs_labels_t` that will be set to the
 *               requested labels
 *
 * @returns The status code of this operation. If the status is not
 *          `EQS_SUCCESS`, you can use `eqs_last_error()` to get the full
 *          error message.
 */
eqs_status_t eqs_block_labels(const struct eqs_block_t *block,
                              const char *values_gradients,
                              uintptr_t axis,
                              struct eqs_labels_t *labels);

/**
 * Get the array handle for either values or one of the gradient in this `block`.
 *
 * The `values_gradients` parameter controls whether this function looks up
 * labels for `"values"` or one of the gradients in this block.
 *
 * @param block pointer to an existing block
 * @param values_gradients either `"values"` or the name of gradients to lookup
 * @param data pointer to an empty `eqs_array_t` that will be set to the
 *             requested array
 *
 * @returns The status code of this operation. If the status is not
 *          `EQS_SUCCESS`, you can use `eqs_last_error()` to get the full
 *          error message.
 */
eqs_status_t eqs_block_data(const struct eqs_block_t *block,
                            const char *values_gradients,
                            struct eqs_array_t *data);

/**
 * Add a new gradient to this `block` with the given `name`.
 *
 * @param block pointer to an existing block
 * @param data array containing the gradient data. The block takes
 *                 ownership of the array, and will release it with
 *                 `array.destroy(array.ptr)` when it no longer needs it.
 * @param parameter name of the gradient as a NULL-terminated UTF-8 string.
 *                  This is usually the parameter used when taking derivatives
 *                  (e.g. `"positions"`, `"cell"`, etc.)
 * @param samples sample labels for the gradient array. The components and
 *                property labels are supposed to match the values in this block
 * @param components array of component labels corresponding to intermediary
 *                   dimensions of the data
 * @param components_count number of entries in the `components` array
 *
 * @returns The status code of this operation. If the status is not
 *          `EQS_SUCCESS`, you can use `eqs_last_error()` to get the full
 *          error message.
 */
eqs_status_t eqs_block_add_gradient(struct eqs_block_t *block,
                                    const char *parameter,
                                    struct eqs_array_t data,
                                    struct eqs_labels_t samples,
                                    const struct eqs_labels_t *components,
                                    uintptr_t components_count);

/**
 * Get a list of all gradients defined in this `block` in the `parameters` array.
 *
 * @param block pointer to an existing block
 * @param parameters will be set to the first element of an array of
 *                   NULL-terminated UTF-8 strings containing all the
 *                   parameters for which a gradient exists in the block
 * @param count will be set to the number of elements in `parameters`
 *
 * @returns The status code of this operation. If the status is not
 *          `EQS_SUCCESS`, you can use `eqs_last_error()` to get the full
 *          error message.
 */
eqs_status_t eqs_block_gradients_list(struct eqs_block_t *block,
                                      const char *const **parameters,
                                      uint64_t *count);

/**
 * Create a new `eqs_tensormap_t` with the given `keys` and `blocks`.
 * `blocks_count` must be set to the number of entries in the blocks array.
 *
 * The new tensor map takes ownership of the blocks, which should not be
 * released separately.
 *
 * The memory allocated by this function and the blocks should be released
 * using `eqs_tensormap_free`.
 *
 * @param keys labels containing the keys associated with each block
 * @param blocks pointer to the first element of an array of blocks
 * @param blocks_count number of elements in the `blocks` array
 *
 * @returns A pointer to the newly allocated tensor map, or a `NULL` pointer in
 *          case of error. In case of error, you can use `eqs_last_error()`
 *          to get the error message.
 */
struct eqs_tensormap_t *eqs_tensormap(struct eqs_labels_t keys,
                                      struct eqs_block_t **blocks,
                                      uint64_t blocks_count);

/**
 * Free the memory associated with a `tensor` previously created with
 * `eqs_tensormap`.
 *
 * If `tensor` is `NULL`, this function does nothing.
 *
 * @param tensor pointer to an existing tensor map, or `NULL`
 *
 * @returns The status code of this operation. If the status is not
 *          `EQS_SUCCESS`, you can use `eqs_last_error()` to get the full
 *          error message.
 */
eqs_status_t eqs_tensormap_free(struct eqs_tensormap_t *tensor);

/**
 * Get the keys for the given `tensor` map. After a successful call to this
 * function, `keys.values` contains a pointer to memory inside the
 * `tensor` which is invalidated when the tensor map is freed with
 * `eqs_tensormap_free` or the set of keys is modified by calling one
 * of the `eqs_tensormap_keys_to_XXX` function.
 * @param tensor pointer to an existing tensor map
 * @param keys pointer to be filled with the keys of the tensor map
 *
 * @returns The status code of this operation. If the status is not
 *          `EQS_SUCCESS`, you can use `eqs_last_error()` to get the full
 *          error message.
 */
eqs_status_t eqs_tensormap_keys(const struct eqs_tensormap_t *tensor, struct eqs_labels_t *keys);

/**
 * Get a pointer to the `index`-th block in this tensor map.
 *
 * The block memory is still managed by the tensor map, this block should not
 * be freed. The block is invalidated when the tensor map is freed with
 * `eqs_tensormap_free` or the set of keys is modified by calling one
 * of the `eqs_tensormap_keys_to_XXX` function.
 *
 * @param tensor pointer to an existing tensor map
 * @param block pointer to be filled with a block
 * @param index index of the block to get
 *
 * @returns The status code of this operation. If the status is not
 *          `EQS_SUCCESS`, you can use `eqs_last_error()` to get the full
 *          error message.
 */
eqs_status_t eqs_tensormap_block_by_id(const struct eqs_tensormap_t *tensor,
                                       const struct eqs_block_t **block,
                                       uint64_t index);

/**
 * Get a pointer to the `block` in this `tensor` corresponding to the given
 * `selection`. The `selection` should have the same names/variables as the
 * keys for this tensor map, and only one entry, describing the
 * requested block.
 *
 * The block memory is still managed by the tensor map, this block should not
 * be freed. The block is invalidated when the tensor map is freed with
 * `eqs_tensormap_free` or the set of keys is modified by calling one
 * of the `eqs_tensormap_keys_to_XXX` function.
 *
 * @param tensor pointer to an existing tensor map
 * @param block pointer to be filled with a block
 * @param selection labels with a single entry describing which block is requested
 *
 * @returns The status code of this operation. If the status is not
 *          `EQS_SUCCESS`, you can use `eqs_last_error()` to get the full
 *          error message.
 */
eqs_status_t eqs_tensormap_block_selection(const struct eqs_tensormap_t *tensor,
                                           const struct eqs_block_t **block,
                                           struct eqs_labels_t selection);

/**
 * Merge blocks with the same value for selected keys variables along the
 * property axis.
 *
 * The variables (names) of `keys_to_move` will be moved from the keys to
 * the property labels, and blocks with the same remaining keys variables
 * will be merged together along the property axis.
 *
 * If `keys_to_move` does not contains any entries (`keys_to_move.count
 * == 0`), then the new property labels will contain entries corresponding
 * to the merged blocks only. For example, merging a block with key `a=0`
 * and properties `p=1, 2` with a block with key `a=2` and properties `p=1,
 * 3` will produce a block with properties `a, p = (0, 1), (0, 2), (2, 1),
 * (2, 3)`.
 *
 * If `keys_to_move` contains entries, then the property labels must be the
 * same for all the merged blocks. In that case, the merged property labels
 * will contains each of the entries of `keys_to_move` and then the current
 * property labels. For example, using `a=2, 3` in `keys_to_move`, and
 * blocks with properties `p=1, 2` will result in `a, p = (2, 1), (2, 2),
 * (3, 1), (3, 2)`.
 *
 * The new sample labels will contains all of the merged blocks sample
 * labels. The order of the samples is controlled by `sort_samples`. If
 * `sort_samples` is true, samples are re-ordered to keep them
 * lexicographically sorted. Otherwise they are kept in the order in which
 * they appear in the blocks.
 *
 * @param tensor pointer to an existing tensor map
 * @param keys_to_move description of the keys to move
 * @param sort_samples whether to sort the samples lexicographically after
 *                     merging blocks
 *
 * @returns The status code of this operation. If the status is not
 *          `EQS_SUCCESS`, you can use `eqs_last_error()` to get the full
 *          error message.
 */
eqs_status_t eqs_tensormap_keys_to_properties(struct eqs_tensormap_t *tensor,
                                              struct eqs_labels_t keys_to_move,
                                              bool sort_samples);

/**
 * Move the given variables from the component labels to the property labels
 * for each block in this tensor map.
 *
 * `variables` must be an array of `variables_count` NULL-terminated strings,
 * encoded as UTF-8.
 *
 * @param tensor pointer to an existing tensor map
 * @param variables names of the key variables to move to the properties
 * @param variables_count number of entries in the `variables` array
 *
 * @returns The status code of this operation. If the status is not
 *          `EQS_SUCCESS`, you can use `eqs_last_error()` to get the full
 *          error message.
 */
eqs_status_t eqs_tensormap_components_to_properties(struct eqs_tensormap_t *tensor,
                                                    const char *const *variables,
                                                    uint64_t variables_count);

/**
 * Merge blocks with the same value for selected keys variables along the
 * samples axis.
 *
 * The variables (names) of `keys_to_move` will be moved from the keys to
 * the sample labels, and blocks with the same remaining keys variables
 * will be merged together along the sample axis.
 *
 * `keys_to_move` must be empty (`keys_to_move.count == 0`), and the new
 * sample labels will contain entries corresponding to the merged blocks'
 * keys.
 *
 * The new sample labels will contains all of the merged blocks sample
 * labels. The order of the samples is controlled by `sort_samples`. If
 * `sort_samples` is true, samples are re-ordered to keep them
 * lexicographically sorted. Otherwise they are kept in the order in which
 * they appear in the blocks.
 *
 * This function is only implemented if all merged block have the same
 * property labels.
 *
 * @param tensor pointer to an existing tensor map
 * @param keys_to_move description of the keys to move
 * @param sort_samples whether to sort the samples lexicographically after
 *                     merging blocks or not
 *
 * @returns The status code of this operation. If the status is not
 *          `EQS_SUCCESS`, you can use `eqs_last_error()` to get the full
 *          error message.
 */
eqs_status_t eqs_tensormap_keys_to_samples(struct eqs_tensormap_t *tensor,
                                           struct eqs_labels_t keys_to_move,
                                           bool sort_samples);

#ifdef __cplusplus
} // extern "C"
#endif // __cplusplus

#endif /* EQUISTORE_H */
