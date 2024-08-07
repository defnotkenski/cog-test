import shutil
import os
import subprocess
import sys
import argparse
import zipfile
import tempfile

# TODO List ========================

# TODO: Automatically configure accelerate config.
# TODO: Upload JSON config file instead of TOML (wtf).
# TODO: Capture when subprocess is done (Maybe polling can work?).

# TODO List ========================

# Get the absolute path of the DIRECTORY containing THIS script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Insert SD_Scripts into PYTHONPATH
sys.path.insert(0, os.path.join(script_dir, "sd_scripts"))


def setup_parser() -> argparse.ArgumentParser:
    # Set up and add arguments for the parser

    parser = argparse.ArgumentParser()

    parser.add_argument("--output_dir", default=None, help="Path of output directory.")
    parser.add_argument("--train_data_zip", default=None, help="Path or training data in zip format.")
    parser.add_argument("--max_train_epochs", default=None, help="Number of epochs for training.")
    parser.add_argument("--pretrained_model_name_or_path", default="stabilityai/stable-diffusion-xl-base-1.0", help="Model to be trained with.")

    return parser


def get_executable_path(name: str) -> str:
    # Get path for accelerate executable.

    executable_path = shutil.which(name)
    if executable_path is None:
        return ""

    return executable_path


def accelerate_config_cmd(run_cmd: list) -> list:
    # Lay out accelerate arguments for the run command.

    run_cmd.append("--dynamo_backend")
    run_cmd.append("no")

    run_cmd.append("--dynamo_mode")
    run_cmd.append("default")

    run_cmd.append("--mixed_precision")
    run_cmd.append("fp16")

    run_cmd.append("--num_processes")
    run_cmd.append("1")

    run_cmd.append("--num_machines")
    run_cmd.append("1")

    run_cmd.append("--num_cpu_threads_per_process")
    run_cmd.append("2")

    return run_cmd


def execute_cmd(run_cmd: list) -> None:
    # Execute the training command

    # Reformat for user friendly display
    command_to_run = " ".join(run_cmd)
    print(f"Executing command: {command_to_run}")

    # Execute the command
    process = subprocess.Popen(run_cmd)

    # while True:
    #     line = process.stdout.readline()
    #     if not line and process.poll() is not None:
    #         break
    #     print(line.decode(), end="")

    # Remember, a return of None means the child process has not been terminated (wtf)
    if process.poll() is not None:
        print("Command could not be executed.")

    print("Command executed & running.")


def train_sdxl(args) -> None:
    # Begin actual training.

    # Extract zip file contents and empty into temp directory
    train_data_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(args.train_data_zip, "r") as zip_ref:
        zip_ref.extractall(train_data_dir)

    # Find the accelerate executable path
    accelerate_path = get_executable_path("accelerate")
    if accelerate_path == "":
        print("Accelerate executable not found.")
        return

    run_cmd = [f"{accelerate_path}", "launch"]
    # print(run_cmd)

    run_cmd = accelerate_config_cmd(run_cmd=run_cmd)
    # print(run_cmd)

    run_cmd.append(rf"{script_dir}/sd_scripts/sdxl_train.py")
    # print(run_cmd)

    run_cmd.append("--config_file")
    run_cmd.append(rf"{script_dir}/config_dreambooth.toml")
    # print(run_cmd)

    # Add SDXL script arguments
    run_cmd.append("--pretrained_model_name_or_path")
    run_cmd.append(rf"{args.pretrained_model_name_or_path}")

    run_cmd.append("--train_data_dir")
    run_cmd.append(rf"{train_data_dir}")

    run_cmd.append("--max_train_epochs")
    run_cmd.append(rf"{args.max_train_epochs}")

    run_cmd.append("--output_dir")
    run_cmd.append(rf"{args.output_dir}")

    run_cmd.append("--no_half_vae")

    execute_cmd(run_cmd=run_cmd)


if __name__ == "__main__":
    print("Starting training for SDXL Dreambooth niggaaa.")

    configured_parser = setup_parser()
    parsed_args = configured_parser.parse_args()

    train_sdxl(parsed_args)
