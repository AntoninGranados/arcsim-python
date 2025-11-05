import numpy as np
import scipy as sp

from pathlib import Path

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
    
    def save_obj(self, file_path: Path):
        with open(file_path, 'w') as f:
            for v in self.vertices:
                f.write(f"v {v[0]} {v[1]} {v[2]}\n")
            for face in self.faces:
                f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")


def poisson_plane_mesh(size: tuple[float, float], r: float, k: int = 30) -> Mesh:
    """
    Generates a 2D plane mesh (3D points with z=0) using Poisson Disk Sampling and Delaunay Triangulation
    """

    # Border points
    bottom = np.column_stack([np.arange(0, size[0]+r, r), np.full(int((size[0])/r)+1, 0)])
    top    = np.column_stack([np.arange(0, size[0]+r, r), np.full(int((size[0])/r)+1, size[1])])
    left   = np.column_stack([np.full(int((size[1])/r)+1, 0), np.arange(0, size[1]+r, r)])
    right  = np.column_stack([np.full(int((size[1])/r)+1, size[0]), np.arange(0, size[1]+r, r)])
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

    return Mesh(vertices=vertices, faces=faces)

def uniform_plane_mesh(size: tuple[float, float], r: float) -> Mesh:
    n_x = int(size[0] / r) + 1
    n_y = int(size[1] / r) + 1

    x = np.linspace(0, size[0], n_x)
    y = np.linspace(0, size[1], n_y)
    xv, yv = np.meshgrid(x, y, indexing='ij')

    vertices = np.column_stack([xv.flatten(), yv.flatten()])
    faces = sp.spatial.Delaunay(vertices).simplices

    vertices = np.column_stack([vertices, np.zeros(vertices.shape[0])]) # Add z=0 coordinate

    return Mesh(vertices=vertices, faces=faces)