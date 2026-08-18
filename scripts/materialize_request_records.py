import argparse
import base64
import json
import mimetypes
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Restore local artifact images as data URLs in sanitized request records.")
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.input.open("r", encoding="utf-8-sig") as source, args.output.open("w", encoding="utf-8", newline="\n") as destination:
        for line in source:
            if not line.strip():
                continue
            record = json.loads(line)
            for message in record.get("body", {}).get("messages", []):
                content = message.get("content")
                if not isinstance(content, list):
                    continue
                for item in content:
                    image_url = item.get("image_url")
                    if not isinstance(image_url, dict):
                        continue
                    url = image_url.get("url", "")
                    if not url.startswith("artifact://"):
                        continue
                    image_path = args.artifact_root / url.removeprefix("artifact://")
                    mime = mimetypes.guess_type(image_path.name)[0] or "image/png"
                    payload = base64.b64encode(image_path.read_bytes()).decode("ascii")
                    image_url["url"] = f"data:{mime};base64,{payload}"
            record.pop("artifact_image_sha256", None)
            destination.write(json.dumps(record, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
