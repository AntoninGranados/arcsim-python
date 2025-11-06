from pathlib import Path
import numpy as np
from typing import Optional

class SimulationState:
    # Nodes
    verts: np.ndarray   # Material space
    nodes: np.ndarray   # World space
    nodes_velocity: Optional[np.ndarray]

    # Faces
    faces: np.ndarray
    face_material: Optional[np.ndarray] # TODO: not supported yet
    face_space: Optional[np.ndarray]    # TODO: not supported yet

    # Edges
    # TODO: implement

    # Field used when merging multiple SimulationObjects and initializing an empty object beforehand
    empty: bool

    def __init__(self, empty: bool = True):
        self.empty = empty

    def save_npz(self, path: Path | str) -> None:
        npz_dict = {
            "verts": self.verts,
            "nodes": self.nodes,
            "faces": self.faces,
        }
        if hasattr(self, "nodes_velocity"):
            npz_dict["nodes_velocity"] = self.nodes_velocity    # type: ignore

        np.savez(path, allow_pickle=True, **npz_dict)

    @staticmethod
    def load_npz(path: Path | str) -> "SimulationState":
        data = np.load(path, allow_pickle=True)
        obj = SimulationState(empty=False)
        
        obj.verts = data["verts"]
        obj.nodes = data["nodes"]
        obj.faces = data["faces"]
        if "nodes_velocity" in data:
            obj.nodes_velocity = data["nodes_velocity"]
        
        return obj

    @staticmethod
    def merge(obj1: "SimulationState", obj2: "SimulationState") -> "SimulationState":
        """
        Merges two simulation states, returning a new one containing both stacked along a time dimension (the first one).

        Note: this assumes both objects have the same number nodes/faces (e.g., this function does not currently support merging of remeshed objects).

        TODO: support merging of remeshed objects (use list instead of np.ndarrays in that case)
        """

        if obj1.empty: return obj2
        if obj2.empty: return obj1

        merged = SimulationState(empty=False)

        merged.faces = obj1.faces   # Assume obj1.faces == obj2.faces

        merged.verts = obj1.verts   # Assume obj1.verts == obj2.verts
        merged.nodes = np.vstack([obj1.nodes, obj2.nodes])
        if hasattr(obj1, "nodes_velocity") and hasattr(obj2, "nodes_velocity"):
            merged.nodes_velocity = np.vstack([obj1.nodes_velocity, obj2.nodes_velocity])   # type: ignore

        return merged

    @staticmethod
    def parse_obj(path: Path | str) -> "SimulationState":
        # TODO: add support for (and detect if present):
        # nodes
        # - `ny` plastic embedding
        # - `nv` node velocity
        # - `nl` node label

        # triangles
        # - `tm` triangle material index
        # - `tp` triangle bending (3x3)
        # - `ts` triangle stretching (3x3)
        # - `td` triangle damage

        # edges
        # - `e` edge (n1_index + 1, n2_ind + 1)
        # - `ea` edge ideal theta
        # - `ed` edge damage
        # - `ep` edge preserve

        f = []  # face: n_id/ms_id
        verts = []  # material space
        nodes = []  # world space

        world_to_mesh = {}

        with open(path, "r") as file:
            for line in file:
                if line.startswith("v"):       # Vertex
                    parts = line.strip().split()
                    vertex = list(map(float, parts[1:4]))
                    nodes.append(vertex)

                elif line.startswith("f"):     # Face
                    parts = line.strip().split()
                    face = [int(part.split("/")[0]) - 1 for part in parts[1:]]
                    f.append(face)
                    
                    mesh_face = [int(part.split("/")[1]) - 1 for part in parts[1:]]

                    for i in range(3):
                        world_to_mesh[face[i]] = mesh_face[i]
                
                elif line.startswith("ms"):    # Mesh
                    parts = line.strip().split()
                    mesh_vertex = list(map(float, parts[1:4]))
                    verts.append(mesh_vertex)

        world_to_mesh = np.array(list(world_to_mesh.items()))
        ind = np.argsort(world_to_mesh[:,0])
        verts = np.array(verts)[world_to_mesh[ind][:,1]]  # Sort so material and world positions are aligned

        sim_object = SimulationState(empty=False)
        sim_object.faces = np.array(f)
        sim_object.verts = np.array(verts)
        # Add dimension for time/frame (useful when merging `SimulationState`s)
        sim_object.nodes = np.expand_dims(np.array(nodes), axis=0)

        return sim_object