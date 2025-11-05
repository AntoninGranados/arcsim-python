import subprocess
import sys

from pathlib import Path
import json
from tqdm import tqdm
from time import sleep

from config import *


class ARCSim():
    def __init__(self, arcsim_build: Path = Path("arcsim", "bin", "arcsim")):
        self.arcsim_build = arcsim_build

    def run_simulation(self, config: Config | Path, out_dir: Path):
        # Create the output directory if it doesn't exist
        out_dir.mkdir(parents=True, exist_ok=True)

        if type(config) == Path:
            config_file = config
        elif type(config) == Config:
            config_file = config.upload()

        # Compute total frames for progress bar
        config_json = json.load(open(config_file, "r"))
        total_frames = config_json["end_time"]/config_json["frame_time"]
        sub_steps = config_json["frame_steps"]

        # Ex: ./arcsim/bin/arcsim simulateoffline config.json ./out/
        cmd = [self.arcsim_build, "simulateoffline", config_file, out_dir]
        process_cmd = " ".join([str(e) for e in cmd])
        process = subprocess.Popen(process_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Continually read ARCSim's output and update progress bar
        try:
            pbar = tqdm(total=int(total_frames), desc="[DEBUG] Simulating", file=sys.stdout)
            while process.poll() is None:
                if process.stdout:
                    nextline = process.stdout.readline().decode("utf-8").strip()
                    
                    if nextline.startswith("Sim frame"):
                        frame = int(nextline.split("[")[-1].split("]")[0])
                        if frame % sub_steps == 0:
                            pbar.update(1)

            print("[INFO] Done simulating")

        finally:
            pbar.close()

            # Check for errors
            if process.stderr is not None:
                errors = process.stderr.readlines()
                if len(errors) > 0:
                    for l in errors:
                        print(f"[ERROR] {l.decode("utf-8").strip()}")
                    exit(1)
            
            # Wait and terminate the process (ARCSim)
            if process.poll() is None:
                process.terminate()
                process.kill()

            elif type(config) == Config:
                config.cleanup(config_file)

        return out_dir
    
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

    arcsim = ARCSim(Path("arcsim", "bin", "arcsim"))
    arcsim.run_simulation(config, out_dir)
    arcsim.generate_obj(out_dir)

