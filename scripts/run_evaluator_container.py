import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Run one submitted plotting program in the frozen evaluator container."
    )
    parser.add_argument("--code", type=Path, required=True, help="Submitted Python file.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--image", default="relation-chart-evaluator:py38")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    code = args.code.resolve()
    if not code.is_file():
        raise FileNotFoundError(code)
    if shutil.which("docker") is None:
        raise RuntimeError("Docker is not available on PATH.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "code": code.name,
        "image": args.image,
        "timeout_seconds": args.timeout,
        "status": "not_started",
    }

    with tempfile.TemporaryDirectory(prefix="relation-chart-eval-") as temporary:
        work_dir = Path(temporary).resolve()
        shutil.copy2(code, work_dir / "target_code.py")
        container_name = f"relation-chart-eval-{work_dir.name[-12:].lower()}"
        command = [
            "docker",
            "run",
            "--rm",
            "--name",
            container_name,
            "--network",
            "none",
            "--read-only",
            "--cpus",
            "1.0",
            "--memory",
            "2g",
            "--pids-limit",
            "128",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=256m",
            "--mount",
            f"type=bind,source={work_dir},target=/work",
            args.image,
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=args.timeout,
                check=False,
            )
            report.update(
                {
                    "returncode": completed.returncode,
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                }
            )
            rendered = work_dir / "target_image.png"
            if completed.returncode == 0 and rendered.is_file():
                shutil.copy2(rendered, args.output_dir / "target_image.png")
                report["status"] = "ok"
            else:
                report["status"] = "failed"
        except subprocess.TimeoutExpired as error:
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            report.update(
                {
                    "status": "timeout",
                    "returncode": None,
                    "stdout": error.stdout or "",
                    "stderr": error.stderr or "",
                }
            )

    (args.output_dir / "container_run.json").write_text(
        json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8"
    )
    if report["status"] != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
