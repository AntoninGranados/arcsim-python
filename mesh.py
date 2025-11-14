import numpy as np
import scipy as sp
import parse
from pathlib import Path
import matplotlib.pyplot as plt

from arcsim_config import Cloth

def display_cloth(cloth: Cloth) -> None:
    mesh = Mesh.load(cloth.mesh)
    vert = mesh.vertices

    # Apply transformations
    transform = cloth.transform
    if transform is not None:

        # Scale
        scale = transform.scale if hasattr(transform, "scale") else None
        if scale is not None:
            vert *= scale
        
        # Rotation
        rotate = transform.rotate if hasattr(transform, "rotate") else None
        R = np.eye(3)
        if rotate is not None:
            angle = np.radians(rotate.angle)
            axis = np.array([rotate.axis.x, rotate.axis.y, rotate.axis.z])
            axis = axis / np.linalg.norm(axis)
            R = np.array(sp.spatial.transform.Rotation.from_rotvec(angle * axis).as_matrix())

        vert = (R @ vert.T).T

        # Translation
        translate = transform.translate if hasattr(transform, "translate") else None
        if translate is not None:
            vert += np.array([[translate.x, translate.y, translate.z]])

    ax = plt.figure().add_subplot(projection="3d")
    ax.plot_trisurf(
        vert[:,0],
        vert[:,1],
        vert[:,2],
        triangles=mesh.faces,
    )
    ax.set_aspect("equal")
    plt.show()


class Mesh:
    vertices: np.ndarray
    faces: np.ndarray

    def __init__(self, vertices: np.ndarray | None = None, faces: np.ndarray | None = None):
        if vertices is not None:
            self.vertices = vertices
        if faces is not None:
            self.faces = faces

    def get_handles(self, points: np.ndarray, threshold: float = 0.1) -> list[int]:
        """
        Given a set of points, returns the indices of the closest vertices in the mesh. This points can be used as handles for the simulation

        The return value is an array of indices of shape (num_points,). If a point is further than threshold from any vertex, the index is -1
        """

        diff = points[:,None,:] - self.vertices[None,:,:]
        dist = np.linalg.norm(diff, axis=-1)
        closest = np.argmin(dist, axis=-1)

        out_of_bounds = np.min(dist, axis=-1) >= threshold
        closest[out_of_bounds] = -1
        return list(map(int, closest))
    
    def save(self, file_path: Path | str):
        with open(file_path, "w") as f:
            for v in self.vertices:
                f.write(f"v {v[0]} {v[1]} {v[2]}\n")
            for face in self.faces:
                f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")

    @staticmethod
    def load(file_path: Path | str) -> "Mesh":
        vertices = []
        faces = []
        with open(file_path, "r") as f:
            for l in f.readlines():
                l = l.strip()
                if l.startswith("v"):
                    vertices.append(list(map(float, parse.parse("v {} {} {}", l)))) # type: ignore
                if l.startswith("f") and "/" not in l:
                    faces.append(list(map(
                        lambda s: int(s)-1, parse.parse("f {} {} {}", l)     # type: ignore
                    )))
        
        mesh = Mesh()
        mesh.vertices = np.asarray(vertices)
        mesh.faces = np.asarray(faces)
        return mesh

    @staticmethod
    def poisson_plane(size: tuple[float, float], res: int, k: int = 30) -> Mesh:
        """
        Generates a 2D plane mesh (3D points with z=0) using Poisson Disk Sampling and Delaunay Triangulation
        """
        print("[INFO] Generating mesh ...")
        r = min(size) / res #! there can be some degenerate cases when the resolution does not match the size well
        # Border points
        length = np.arange(0, size[0]+r, r)
        width  = np.arange(0, size[1]+r, r)
        bottom = np.column_stack([length, np.full(len(length), 0)])
        top    = np.column_stack([length, np.full(len(length), size[1])])
        left   = np.column_stack([np.full(len(width), 0), width])
        right  = np.column_stack([np.full(len(width), size[0]), width])
        borders = np.unique(np.vstack([bottom, top, left, right]), axis=0)

        p = np.random.random((2,)) * np.array(size) # Initial random point
        vertices = list(borders) + [p]
        active = [p]

        while len(active) > 0:
            idx = np.random.choice(np.arange(len(active)))
            p = active[idx]
            found = False
            for _ in range(k):
                angle = np.random.uniform(0, 2*np.pi)
                radius = np.random.uniform(r, 2*r)
                new_p = p + radius * np.array([np.cos(angle), np.sin(angle)])
                if new_p[0] < 0 or new_p[0] > size[0] or new_p[1] < 0 or new_p[1] > size[1]:
                    continue
                dist = np.linalg.norm(new_p - np.array(vertices), axis=-1)
                if dist.min() > r:
                    active.append(new_p)
                    vertices.append(new_p)
                    found = True
            if not found:
                del active[idx]

        vertices = np.array(vertices)
        faces = sp.spatial.Delaunay(vertices).simplices

        vertices = np.column_stack([vertices, np.zeros(vertices.shape[0])]) # Add z=0 coordinate

        print("[INFO] Done generating mesh")
        return Mesh(vertices=vertices, faces=faces)

    @staticmethod
    def uniform_plane_mesh(size: tuple[float, float], r: float) -> Mesh:
        # TODO: change the `r: float` parameter to `res: int` like in poisson_plane
        print("[INFO] Generating mesh ...")

        n_x = int(size[0] / r) + 1
        n_y = int(size[1] / r) + 1

        x = np.linspace(0, size[0], n_x)
        y = np.linspace(0, size[1], n_y)
        xv, yv = np.meshgrid(x, y, indexing="ij")

        vertices = np.column_stack([xv.flatten(), yv.flatten()])
        faces = sp.spatial.Delaunay(vertices).simplices

        vertices = np.column_stack([vertices, np.zeros(vertices.shape[0])]) # Add z=0 coordinate

        print("[INFO] Done generating mesh")
        return Mesh(vertices=vertices, faces=faces)