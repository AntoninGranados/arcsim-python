import subprocess
import sys
import glob

from pathlib import Path
import json
from tqdm import tqdm
from time import sleep

import numpy as np

from arcsim_config import *
from simulation_state import SimulationState, NodeType


class ARCSimRunner():
    def __init__(self, config: Config | Path | str, arcsim_build: Path | str = Path("arcsim", "bin", "arcsim")):
        self.arcsim_build = arcsim_build
        
        self.config = config
        self.temporary_config = False
        if type(config) == Path or type(config) == str:
            self.config_file = config
        elif type(config) == Config:
            self.config_file = config.upload()
            self.temporary_config = True

    def run_simulation(self, out_dir: Path | str) -> Path:
        # Create the output directory if it doesn"t exist
        Path(out_dir).mkdir(parents=True, exist_ok=True)

        # Compute total frames for progress bar
        config_json = json.load(open(self.config_file, "r"))
        total_frames = config_json["end_time"]/config_json["frame_time"]
        sub_steps = config_json["frame_steps"]

        # Ex: ./arcsim/bin/arcsim simulateoffline config.json ./out/
        cmd = [self.arcsim_build, "simulateoffline", self.config_file, out_dir]
        process_cmd = " ".join([str(e) for e in cmd])
        process = subprocess.Popen(process_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Continually read ARCSim"s output and update progress bar
        try:
            pbar = tqdm(total=int(total_frames), desc="[DEBUG] Simulating", file=sys.stdout)
            while process.poll() is None:
                if process.stdout:
                    nextline = process.stdout.readline().decode("utf-8").strip()
                    
                    if nextline.startswith("Sim frame"):
                        frame = int(nextline.split("[")[-1].split("]")[0])
                        if frame % sub_steps == 0:
                            pbar.update(1)

        finally:
            pbar.close()

            # Check for errors
            if process.stderr is not None:
                errors = process.stderr.readlines()
                if len(errors) > 0:
                    for l in errors:
                        print(f"[ERROR] {l.decode("utf-8").strip()}")
                    exit(1)

            print("[INFO] Done simulating")
            
            # Wait and terminate the process (ARCSim)
            if process.poll() is None:
                process.terminate()
                process.kill()

            elif self.temporary_config:
                self.config.cleanup(self.config_file)   # type: ignore

        return Path(out_dir)
    
    def generate_obj(self, out_dir: Path):
        # Ex: ./arcsim/bin/arcsim generate ./out/
        cmd = [self.arcsim_build, "generate", out_dir]
        process_cmd = " ".join([str(e) for e in cmd])
        process = subprocess.Popen(process_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        loading = ["⢎⡰","⢎⡡","⢎⡑","⢎⠱","⠎⡱","⢊⡱","⢌⡱","⢆⡱"]
        i = 0
        while process.poll() is None:
            print(f"[DEBUG] Generating .obj files — {loading[i%len(loading)]}", end="\r")
            i += 1
            sleep(0.1)

        print("\n[INFO] Done generating .obj file")

    def load_obj(self, out_dir: Path) -> SimulationState:
        print("[INFO] Loading .obj files ...")
        obj_files = glob.glob(str(Path(out_dir, "[!obs]*.obj")))
        obj_files = sorted(obj_files)

        config_json = json.load(open(self.config_file, "r"))

        sim_object = SimulationState()
        for obj_file in obj_files:
            single_sim_obj = SimulationState.parse_obj(obj_file)
            
            single_sim_obj.node_type = np.full(single_sim_obj.nodes.shape[:2], NodeType.NORMAL)
            if config_json["handles"] is not None:
                single_sim_obj.node_type[:,config_json["handles"][0]["nodes"]] = NodeType.HANDLE

            sim_object = SimulationState.merge(sim_object, single_sim_obj)

        print("[INFO] Done loading .obj files")
        return sim_object


if __name__ == "__main__":
    material = Material(
        data = "arcsim/materials/camel-ponte-roma.json",
        thicken = 2,
        strain_limits = [0.95, 1.05],
    )

    remeshing = Remesh(
        refine_angle = 0.3,
        refine_compression = 0.01,
        refine_velocity = 1,
        size = [20e-3, 500e-3],
        aspect_min = 0.2,
    )

    cloth = Cloth(
        mesh = "arcsim/meshes/flag.obj",
        transform = Transform(
            translate = Vec3(0, 0, 0),
            rotate = Rotation(angle = 45, axis = Vec3(0, 1, 0))
        ),
        materials = [material],
        remeshing = remeshing
    )

    config = Config(
        frame_time = 0.04,
        frame_steps = 8,
        end_time = 10,

        cloths = [cloth],
        handles = [Handle(nodes = [0, 3])],

        gravity = Vec3(9.81, 0, 0),
        wind = Wind(
            velocity = Vec3(10, 0, 0),
            density = 1,
            drag = 0
        ),
        magic = Magic(repulsion_thickness = 10e-3, collision_stiffness = 1e6),
        disable = ["popfilter"],
    )

    
    out_dir = Path("out")
    arcsim = ARCSimRunner(config, Path("arcsim", "bin", "arcsim"))
    arcsim.run_simulation(out_dir)
    arcsim.generate_obj(out_dir)
