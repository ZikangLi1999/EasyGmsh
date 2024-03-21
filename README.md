# EasyGmsh

## Overview
EasyGmsh is developed to help you generate finite element mesh with [Gmsh](https://gmsh.info) easily.

## Install
(TODO)

## Basic Usage
Only reactangular mesh is supported till now.

### RectMesh
You can easily generate a structured rectangular mesh using RectMesh.
<details>
<summary>Click here to read the example</summary>

```python
# Generate coarse mesh for TWIGL benchmark
import gmsh
import numpy as np
from EasyGmsh import RectMesh

"""
Material Configuration:

80  | ----------------- |
    y   3  |  3  |  3   |
56  | ----------------- |
    |   2  |  1  |  3   |
24  | ----------------- |
    |   3  |  2  |  3   |
 0  |________ x ________|
    0      24    56    80

Material ID & Name:
1: TWIGL-MAT1
2: TWIGL-MAT2
3: TWIGL-MAT3
"""

gmsh.initialize()

# Describe the mesh structure
nodes = np.array([0., 24., 56., 80.])
material_names = np.array(["TWIGL-MAT1", "TWIGL-MAT2", "TWIGL-MAT3"])
materials = np.array([
    [3, 3, 3],
    [2, 1, 3],
    [3, 2, 3]
]) # material id starts at 1 but not 0

# Create RectMesh
twigl_mesh = RectMesh(
    lx = nodes,
    ly = nodes,
    material_names = material_names,
    materials = materials
)
twigl_mesh.generate(mesh_size = MESH_LEVEL)
twigl_mesh.export_assembly_materials(path = "./input/assembly_info.txt")

# Generate mesh using Gmsh
gmsh.model.geo.synchronize()
gmsh.model.mesh.generate(dim=2)
gmsh.write("input/mesh.msh")
gmsh.fltk.run()
gmsh.finalize()
```

</details>


> Version: 0.1  
> Written by LI Zikang, Mar. 2024.  
> Latest Edit in Mar. 2024.
