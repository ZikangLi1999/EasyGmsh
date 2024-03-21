"""
Generate reactangular mesh
@Author: LI Zikang
"""
import gmsh
import numpy as np


class RectMesh:
    
    def __init__(
        self,
        lx: np.ndarray[float], ly: np.ndarray[float],
        materials     : np.ndarray[int] = None,
        material_names: np.ndarray[str] = None
    ) -> None:
        self.x = lx # The coordinates of nodes (including 0)
        self.y = ly
        self.nx = len(self.x) - 1
        self.ny = len(self.y) - 1
        self._materials = materials
        self._material_names = material_names
    
    
    def generate(self, mesh_size: float) -> None:
        # Mesh size parameter
        self.mesh_size = mesh_size

        self.generate_nodes()
        self.generate_lines()
        self.generate_surfaces()
        self.generate_physical_groups()


    def generate_nodes(self) -> None:
        # Get coordinates of nodes
        if isinstance(self.x, list) and isinstance(self.y, list):
            self.x = np.array(self.x)
            self.y = np.array(self.y)

        # Generate nodes
        self.nodes = np.empty(shape=[self.nx + 1, self.ny + 1], dtype=int)
        for iy in range(self.ny + 1):
            for ix in range(self.nx + 1):
                x = self.x[ix]
                y = self.y[iy]
                self.nodes[ix, iy] = gmsh.model.geo.addPoint(x, y, 0., self.mesh_size)
                # if ix in [0, 1] and iy in [0, 1]:
                #     print(ix, iy, x, y, self.nodes[ix, iy])
        
        return None
    

    def generate_lines(self) -> None:
        # Get the lines along x-direction
        self.linex = np.empty(shape=[self.nx, self.ny + 1], dtype=int)
        for iy in range(self.ny + 1):
            for ix in range(self.nx):
                start = self.nodes[ix    , iy]
                end   = self.nodes[ix + 1, iy]
                self.linex[ix, iy] = gmsh.model.geo.addLine(start, end)
                # if iy in [0, 1] and ix == 0:
                #     print(start, end, self.linex[ix, iy])

        # Get the lines along y-direction
        self.liney = np.empty(shape=[self.nx + 1, self.ny], dtype=int)
        for ix in range(self.nx + 1):
            for iy in range(self.ny):
                start = self.nodes[ix, iy    ]
                end   = self.nodes[ix, iy + 1]
                self.liney[ix, iy] = gmsh.model.geo.addLine(start, end)
                # if ix in [0, 1] and iy == 0:
                #     print(start, end, self.liney[ix, iy])
        
        return None
    

    def generate_surfaces(self) -> None:
        self.curves = np.empty(shape=[self.nx, self.ny], dtype=int)
        self.surfaces = np.empty_like(self.curves)

        for iy in range(self.ny):
            for ix in range(self.nx):
                lines = [
                    + self.liney[ix + 1, iy    ],
                    - self.linex[ix    , iy + 1],
                    - self.liney[ix    , iy    ],
                    + self.linex[ix    , iy    ]
                ]
                self.curves[ix, iy] = gmsh.model.geo.addCurveLoop(lines)
                self.surfaces[ix, iy] = gmsh.model.geo.addPlaneSurface([self.curves[ix, iy]])
        
        return None
    

    def generate_physical_groups(self) -> None:
        if self._materials is None:
            raise RuntimeError("Materials not found.")
        
        self.n_matrial = len(self._materials)

        if self._material_names is None:
            self._material_names: list[str] = [str(i) for i in range(self.n_matrial)]
        
        self.physical_groups: list[dict[str, list[int]]] = [
            {
                "material_name": material_name,
                "entities": []
            }
            for material_name in self._material_names
        ]

        for iy in range(self.ny):
            for ix in range(self.nx):
                material_id: int = self._materials[self.ny - 1 - iy, ix] - 1
                entity_id  : int = self.surfaces[ix, iy]
                print(f"ix = {ix}; iy = {iy}")
                print(f"material_id = {material_id}; entity_id = {entity_id}; material_name = {self.physical_groups[material_id]['material_name']}")
                self.physical_groups[material_id]["entities"].append(entity_id)
        
        for group_id, group in enumerate(self.physical_groups):
            material_name: str = group["material_name"]
            entities: list[int] = group["entities"]
            gmsh.model.geo.addPhysicalGroup(2, entities, group_id + 1, name=material_name)
    

    def export_assembly_materials(self, path: str = None) -> None:
        if path is None:
            import os
            path = os.path.join(os.getcwd(), "assembly_mat.txt")
        
        if path.startswith('.'):
            import os
            import pathlib
            path = pathlib.Path(os.getcwd(), path)
        
        assembly_materials: list = []
        for group_id, group in enumerate(self.physical_groups):
            for entity in group["entities"]:
                assembly_materials.append([entity, group_id])
        
        assembly_materials = sorted(assembly_materials, key=lambda x: x[0])

        with open(path, 'w', encoding='utf-8') as f:
            for assembly_id, material_id in assembly_materials:
                f.write(f"{assembly_id:<5d} {material_id + 1:d}\n")


    @property
    def materials(self) -> np.ndarray[int]:
        return self._materials
    
    
    @materials.setter
    def materials(self, materials: np.ndarray[int]) -> None:
        self._materials = np.array(materials)
    

    @property
    def material_names(self) -> np.ndarray[str]:
        return self._material_names
    

    @material_names.setter
    def material_names(self, material_names: np.ndarray[str]) -> None:
        self._material_names = np.array(material_names)
    

    def greater(
            self,
            dim: int, bound: int,
            selected: list[np.ndarray[int]] = None
        ) -> list[np.ndarray[int]]:
        """
        Select the element(surface) with `dim`-direction ID greater than `bound`

        Input
        -----
        surfaces: [selected_x, selected_y] where each contains the ID of selected elements
        dim: 0 for x-direction, and 1 for y-direction
        bound: the boundary ID of desired zone (being included)
        """
        # If `selected` is not given, specify it with the IDs of all elements
        if selected is None:
            selected = [
                np.array(range(self.nx)),
                np.array(range(self.ny))
            ]
        
        # Select the elements with ID greater than or equal to `bound`
        selected[dim] = selected[dim][np.where(selected[dim] >= bound)]
        return selected
    

    def less(
            self,
            dim: int, bound: int,
            selected: list[np.ndarray[int]] = None
        ) -> list[np.ndarray[int]]:
        """
        Select the element(surface) with `dim`-direction ID less than `bound`

        Input
        -----
        surfaces: [selected_x, selected_y] where each contains the ID of selected elements
        dim: 0 for x-direction, and 1 for y-direction
        bound: the boundary ID of desired zone (being included)
        """
        # If `selected` is not given, specify it with the IDs of all elements
        if selected is None:
            selected = [
                np.array(range(self.nx)),
                np.array(range(self.ny))
            ]
        
        # Select the elements with ID greater than or equal to `bound`
        selected[dim] = selected[dim][np.where(selected[dim] <= bound)]
        return selected


    def equal(
            self,
            dim: int, bound: int,
            selected: list[np.ndarray[int]] = None
        ) -> list[np.ndarray[int]]:
        """
        Select the element(surface) with `dim`-direction ID less than `bound`

        Input
        -----
        surfaces: [selected_x, selected_y] where each contains the ID of selected elements
        dim: 0 for x-direction, and 1 for y-direction
        bound: the boundary ID of desired zone (being included)
        """
        # If `selected` is not given, specify it with the IDs of all elements
        if selected is None:
            selected = [
                np.array(range(self.nx)),
                np.array(range(self.ny))
            ]
        
        # Select the elements with ID greater than or equal to `bound`
        selected[dim] = selected[dim][np.where(selected[dim] == bound)]
        return selected


    @classmethod
    def join(cls, a: list[np.ndarray[int]], b: list[np.ndarray[int]]) -> list[np.ndarray[int]]:
        c = []
        for ai, bi in zip(a, b):
            ci = np.sort(np.unique(np.concatenate([ai, bi], axis=0)), axis=0)
            c.append(ci)
        return c


    def resolve(self, coord: list[np.ndarray[int]]) -> np.ndarray[int]:
        """
        Obtain the IDs of surfaces located by [x,y] coordinate

        Input
        -----
        ids: the [x,y] coordinate, [np.ndarray[int],np.ndarray[int]]
        """
        return self.surfaces[coord[0], coord[1]]


# ---------------------------------------------------------
# Parameters of C5G7 benchmark
# ---------------------------------------------------------

if __name__ == '__main__':
    gmsh.initialize()

    core = RectMesh(lx=3*21.42, ly=3*21.42, nx=3*17, ny=3*17)
    core.generate(mesh_size=1.0)

    # The code below groups elements into physical groups (material regions)
    # ---------------------- MOX 4.3% ----------------------
    mox43_coord = core.equal(0, 18 - 1)
    mox43_coord = core.greater(1, 1 - 1, mox43_coord)
    mox43_coord = core.less(1, 17 - 1, mox43_coord)     # -x boundary of MOX2
    mox43 = core.resolve(mox43_coord)

    mox43_coord = core.equal(0, 34 - 1)
    mox43_coord = core.greater(1, 1 - 1, mox43_coord)
    mox43_coord = core.less(1, 17 - 1, mox43_coord)     # +x boundary of MOX2

    mox43 = np.concatenate([
        mox43,
        core.resolve(mox43_coord)
    ], axis=0)

    mox43_coord = core.equal(1, 1 - 1)
    mox43_coord = core.greater(0, 19 - 1, mox43_coord)
    mox43_coord = core.less(0, 33 - 1, mox43_coord)     # -y boundary of MOX2

    mox43 = np.concatenate([
        mox43,
        core.resolve(mox43_coord)
    ], axis=0)

    mox43_coord = core.equal(1, 17 - 1)
    mox43_coord = core.greater(0, 19 - 1, mox43_coord)
    mox43_coord = core.less(0, 33 - 1, mox43_coord)     # +y boundary of MOX2

    mox43 = np.concatenate([
        mox43,
        core.resolve(mox43_coord)
    ], axis=0)

    mox43_coord = core.equal(0, 1 - 1)
    mox43_coord = core.greater(1, 18 - 1, mox43_coord)
    mox43_coord = core.less(1, 34 - 1, mox43_coord)     # -x boundary of MOX3
    mox43 = core.resolve(mox43_coord)

    mox43 = np.concatenate([
        mox43,
        core.resolve(mox43_coord)
    ], axis=0)

    mox43_coord = core.equal(0, 17 - 1)
    mox43_coord = core.greater(1, 18 - 1, mox43_coord)
    mox43_coord = core.less(1, 34 - 1, mox43_coord)     # +x boundary of MOX3

    mox43 = np.concatenate([
        mox43,
        core.resolve(mox43_coord)
    ], axis=0)

    mox43_coord = core.equal(1, 18 - 1)
    mox43_coord = core.greater(0, 2 - 1, mox43_coord)
    mox43_coord = core.less(0, 16 - 1, mox43_coord)     # -y boundary of MOX3

    mox43 = np.concatenate([
        mox43,
        core.resolve(mox43_coord)
    ], axis=0)

    mox43_coord = core.equal(1, 34 - 1)
    mox43_coord = core.greater(0, 2 - 1, mox43_coord)
    mox43_coord = core.less(0, 16 - 1, mox43_coord)     # +y boundary of MOX3

    mox43 = np.concatenate([
        mox43,
        core.resolve(mox43_coord)
    ], axis=0)

    print(mox43)

    # ---------------------- MOX 7.0% ----------------------


    # gmsh.model.geo.synchronize()
    # gmsh.model.mesh.generate(dim=2)
    # gmsh.write("test.msh")
    # gmsh.finalize()
