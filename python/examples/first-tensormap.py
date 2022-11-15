"""
.. _userdoc-tutorials-first-tensormap:

Getting your first Tensormap
============================
"""

# %%
#
# We will start by importing all the required packages: the classic numpy;
# chemfiles to load data, and rascaline to compute representations. Afterward
# we will load the dataset using chemfiles.

import numpy as np

import equistore

equistore.Labels(names=["foo", "bar"], values=np.array([[1,1],[2,4]]))

# %%
#
# Rascaline
# ---------

# In this tutorial, we are going to use Rascaline calculators,
# https://github.com/Luthaf/rascaline, to generate equistore
# **TensorMaps** for atom-centered density correlations of molecules in our
# dataset. The spherical expansion(nu = 1) calculator and the SOAP Power
# spectrum (nu = 2) calculator will be used for this example.

# Hypers used
# -----------

# For this exercise, we choose the hyperparameters, :math:`max_radial = 3` 
# and :math:`max_angular = 2`)  for the number of spherical harmonics and radial
# basis functions used in the expansion respectively. As the **keys** of the
# equistore TensorMap are tuples in the form
# (*spherical_harmonics_l*, *species_center*), we would expect the number
# of **keys** = [(*max_angular*) + 1] x (*number of species_center*). As each
# key corresponds to a **TensorBlock**, the number of **keys** would be the
# same as the number of **TensorBlocks**. The **components** of the **TensorBlock**,
# correspond to the equivariant behaviour of the features calculated, with the
# number of **components** = (2 x *lambda* + 1) where lambda tags the behaviour
# under the irreducible SO(3) group action. For spherical expansion, the
# **properties** (manifests as the last dimension) in each **TensorBlock** are
# labelled by a tuple of the form (*number of neighbour_species*, *max_radial*)
# and thus, the number of **properties** in each **TensorBlock** = (*number of
# neighbour_species* x *max_radial*). Meanwhile for the SOAP power spectrum,
# the **properties** in each **TensorBlock** are labelled by a tuple of the form
# (*neighbour_species_a, radial_expansion_a, spherical_expansion_l_a,
# neighbour_species_b, radial_expansion_b, spherical_expansion_l_b*),
# and hence the number of **properties** in each **TensorBlock** =
# (:math: `*total number of species*^2 x *max_radial*^2`). Finally,
# the **samples** (manifests as rows) in each **TensorBlock** are organized
# in the fashion:(*atom_index*, *structure_index*), and thus the number of rows
# in each **TensorBlock** = *Total number of the chosen element in the dataset*,
# whereby the chosen element can be identified by the value of the *species_center*
# in the **key** of the **TensorBlock**. Hence, each **TensorBlock** will take the
# shape (*Number of **Samples***, *Number of **Components***, *Number of **Properties***)
# and each of them can be identified via its own **key**. 

# Using these hyperparameters for feature calculations on this dataset consisting
# of one frame of water, H2O [(O, H, H)], and one frame of ethanol
# [(O, C, C, H, H, H, H, H, H)], C2H5OH, the resulting **TensorMap** produced
# by Rascaline would contain [(*max_angular*) + 1] x (*number of species_center*)
# = [(2 + 1] x 3 = 9 **TensorBlocks** and **keys**. The list of **keys** would be
# [(0,1), (0,6), (0,8), (1,1), (1,6), (1,8), (2,1), (2,6), (2,8)], whereby the first
# index denotes the value of the *spherical_harmonics_l* and the second index denotes
# the proton number of the *species_center*. The number of **components** in the
# respective **Tensorblocks** would be [1, 1, 1, 3, 3, 3, 5, 5, 5], as calculated
# by number of **components** = (2 x *lambda* + 1) and each **TensorBlock** will
# contain 12 **samples** (rows), as there are a total of 12 atoms in this dataset.
# For spherical expansion,  each **TensorBlock** will have 9 **properties** as
# given by number of 
# **properties** = (*number of neighbour_species* x *max_radial*) = (3 x 3) = 9.

# Note: Depending on the hyperparameters chosen, some degree of feature selection
# might occur during computation, which affects the number of properties calculated.

# Navigating through the TensorMap
# --------------------------------

# Accessing different Blocks on the Tensormap
# -------------------------------------------

# There are three main ways to access blocks on the Tensormap, by index, keys or
# multiple keys at once. The first method involving index would require access blocks
# based on the order (??)

# The first tensorblock can be accessed using

# TensorMap.block(0)

# %%
#
# The second method involves calling the key of the TensorBlock directly using
# the tuple (*spherical_harmonics_l*, *species_center*)
#
# The tensorblock corresponding to key () can be accessed using

# TensorMap.key(key)

# %%
#
# Simple operations on TensorMaps
# -------------------------------
# 
# 1. Reshaping Blocks 
# 2. Reindexing Blocks 
# 3. Restructuring Blocks 
# 
# Keys to properties 
# keys to samples
# components to properties 
# 
# Creating your own TensorBlocks and TensorMap
# --------------------------------------------
# 
# In principle once you have defined blocks and keys, a TensorMap is simply
# obtained by collecting all the blocks into a common container. So how do we
# get these blocks? We need to define **Labels** for each dimension of the
# block values


# list_of_blocks = []
# list_of_blocks.append( TensorBlock(block.values = values,
# block.samples = samples, 
# block. properties = properties,
# block.components = components
# )
# )

# tensormap = TensorMap(blocks, keys)

# &&
#
# where values is an n-dim array with the actual data that you began with,
# whereas samples, properties, components are Label objects. 
# (make sure that the Label objetcs have been appropriately defined to follow
# this explanation)::

# samples = Labels( values, names)

# %%
#
# Going from tensormap to a dense array
# -------------------------------------
